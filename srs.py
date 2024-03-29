import socket
import json
import _thread
import threading
import struct
import ctypes
import array
import arrow
import wave
import os
import soundfile
import configparser
import grpc
from grpc._channel import _InactiveRpcError, _MultiThreadedRendezvous
from dcs.mission.v0 import mission_pb2_grpc, mission_pb2
from dcs.hook.v0 import hook_pb2_grpc, hook_pb2

MSG_UPDATE = 0
MSG_PING = 1
MSG_SYNC = 2
MSG_RADIO_UPDATE = 3
MSG_SERVER_SETTINGS = 4
MSG_CLIENT_DISCONNECT = 5
MSG_VERSION_MISMATCH = 6
MSG_E_AWACS_PW = 7
MSG_E_AWACS_DC = 8

# voice decoding constants
GUID_LENGTH = 22
# https://github.com/ciribob/DCS-SimpleRadioStandalone/blob/91f7e575347b1113c5e2bb08cba0031c53201f23/DCS-SR-Common/Network/UDPVoicePacket.cs#L35
PACKET_HEADER_LENGTH = 2 + 2 + 2
# https://github.com/ciribob/DCS-SimpleRadioStandalone/blob/91f7e575347b1113c5e2bb08cba0031c53201f23/DCS-SR-Common/Network/UDPVoicePacket.cs#L45
FIXED_PACKET_LENGTH = 4 + 8 + 0 + GUID_LENGTH + GUID_LENGTH
# https://github.com/ciribob/DCS-SimpleRadioStandalone/blob/91f7e575347b1113c5e2bb08cba0031c53201f23/DCS-SR-Common/Network/UDPVoicePacket.cs#L40
FREQUENCY_SEGMENT_LENGTH = 8 + 1 + 1


class DecoderStructDoNotUse(ctypes.Structure):
    """
    We need some sort of object in order for decoding state to be stored
    As the name implies, this class is not intended to be used outside of being passed around libopus
    """
    pass


class OpusDecoder:
    """
    Python decoder which simplifies the calls to the underlying DLL (which does all of the heavy lifting)
    Intended usage is to create the object, call create() (which creates the state object) and then decode at will
    See https://opus-codec.org/docs/opus_api-1.3.1/group__opus__decoder.html for more information
    """
    def __init__(self, bitrate, channels, dll_path, buffer_size=192000):
        self.bitrate = bitrate
        self.channels = channels
        # This is not a native Python implementation. You must reference an Opus DLL capable of doing the actual
        #   decoding
        self.dll_path = dll_path
        # Opus decoding is stateful; as such, we must track where we are in decoding. This object does that.
        self.decoder_obj = None
        # This is the actual function within the DLL. Called to decode packets.
        self.decode_func = None
        self.frame_count = self.get_frame_count(buffer_size)

    def create(self):
        """
        Creates the Opus decoder as described in
            https://opus-codec.org/docs/opus_api-1.3.1/group__opus__decoder.html#ga753f6fe0b699c81cfd47d70c8e15a0bd
        Must be called prior to decode()
        :return:
            N/A
        """

        # pre-populate input and output types
        create_func = ctypes.CDLL(self.dll_path).opus_decoder_create
        create_func.argtypes = [
            ctypes.c_int,
            ctypes.c_int,
            ctypes.POINTER(ctypes.c_int)
        ]
        create_func.restype = ctypes.POINTER(DecoderStructDoNotUse)
        self.decode_func = ctypes.CDLL(self.dll_path).opus_decode
        self.decode_func.argtypes = [
            ctypes.POINTER(DecoderStructDoNotUse),
            ctypes.POINTER(ctypes.c_ubyte),
            ctypes.c_int32,
            ctypes.POINTER(ctypes.c_int16),
            ctypes.c_int,
            ctypes.c_int,
        ]
        self.decode_func.restype = ctypes.c_int

        # set up is complete, create the decoder state
        create_decoder_result = ctypes.c_int()  # used to track outcome of attempt to create decoder state object
        self.decoder_obj = create_func(
            ctypes.c_int(self.bitrate),
            ctypes.c_int(self.channels),
            ctypes.byref(create_decoder_result),
        )
        if create_decoder_result.value != 0:
            raise Exception("Failed to create decoder state object: {}".format(create_decoder_result))

    def decode(self, voice_packet):
        """
        Perform the actual decoding of Opus packets as described on
            https://opus-codec.org/docs/opus_api-1.3.1/group__opus__decoder.html#ga7d1111f64c36027ddcb81799df9b3fc9
        You MUST call create() first
        :param voice_packet:
            A dict containing a packet containing voice data
            {
                'audio_part1_bytes': b'',
                'audio_part1_length': 0,
            }
        :return:
            A bytes object containing raw PCM data
        """
        if not self.decoder_obj:
            raise Exception("You must call create() first")
        data_pointer = ctypes.cast(voice_packet['audio_part1_bytes'], ctypes.POINTER(ctypes.c_ubyte))
        decoded_bytes = ctypes.cast(ctypes.pointer((ctypes.c_int16 * self.frame_count)()), ctypes.POINTER(ctypes.c_int16))
        decoded_byte_count = self.decode_func(
            self.decoder_obj,
            data_pointer,
            ctypes.c_int(voice_packet['audio_part1_length']),
            decoded_bytes,
            ctypes.c_int(self.frame_count),
            ctypes.c_int(0),
        )
        return array.array('h', decoded_bytes[:decoded_byte_count * self.channels]).tobytes(), decoded_byte_count / self.bitrate

    @staticmethod
    def get_frame_count(buffer_size):
        """
            //  seems like bitrate should be required
            var bitrate = 16;
            var bytesPerSample = bitrate / 8 * OutputChannels;
            return bufferSize / bytesPerSample;
        """
        bitrate = 16
        bytes_per_sample = bitrate / 8
        return int(buffer_size / bytes_per_sample)


class Radio:
    """
    Intended to track all data related to a given frequency for SRS
    """
    def __init__(self, frequency, decoder, out_file):
        now = arrow.now()
        self.sample_rate = 48000  # this should probably be specified upstream, but for now we know it'll be 48,000
        self.frequency = frequency
        # decoder should be an OpusDecoder object
        self.opus_decoder = decoder
        self.opus_decoder.create()
        # for testing, we want to overwrite existing recordings. This will probably get removed as the project matures
        # zero out the file (yes there are easier ways to do it)
        if not os.path.exists(os.path.dirname(out_file)):
            print(f"ERROR:: Audio recording path for file {out_file} was not found, please select an existing path")
            exit(5)
        wave_file = wave.open(out_file, 'wb')
        wave_file.setnchannels(2)
        wave_file.setframerate(self.sample_rate)
        wave_file.setsampwidth(2)
        self.out_file = soundfile.SoundFile(out_file, 'wb', samplerate=48000, channels=1)
        self.receiving = False
        self.started_receiving = False
        self.buffer = b''
        self.last_received_time = now
        self.last_stream_ended = None
        self.need_to_close_gap = True
        self.last_tick = None
        self.lock = threading.Lock()
        self.received_audio = False
        # TODO we will fix last_received_time and last_received_start at 2000 after jeremy works in tomorrow
        self.last_rx = None
        self.last_rx_extended = None
        self.ms_silence = b'000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
        self.previous_delta = 0

    def write_audio(self, data):
        self.out_file.writeframes(data)

    def flush_buffer(self):
        if self.buffer:
            self.out_file.buffer_write(self.buffer, 'int32')
            self.out_file.flush()
            self.buffer = b''

    def generate_silence(self, duration):
        # the buffered write seems to fall flat with large amounts of write. although we shouldn't be calling with a
        #  large duration, validate that assumption by only writing 5 seconds at a time
        while duration > 5:
            self.out_file.buffer_write(
                self.ms_silence * int(5 * 1000 * 2),
                'int32',
            )
            self.out_file.flush()
            duration -= 5
        # duration is seconds but we want ms so * 1000. the file expects two channels so * 2
        self.out_file.buffer_write(
            self.ms_silence * (int((round(duration, 2) + 0.001) * 1000 * 2)),
            'int32',
        )
        # the docs have zero mention of when flush should be called - and in fact only mention write(),
        #   not buffer_write()
        # as such, we flush whenever we write to validate that we don't end up with missing data
        self.out_file.flush()


class SRSRecorder:
    """
    An object used to record select frequencies on an SRS server. Intended to be used in conjunction with TacView for
        better debriefs
    """
    def __init__(self, **kwargs):
        """
        Initializes the recorder
        :param kwargs:
            Optional arguments.
            sample_rate
                Sample rate used to write audio. Highly recommend you do not change this as it's what SRS uses and
                    I'm not entirely sure that Opus will appreciate anything but that.
        """
        config = configparser.ConfigParser()
        config.read(kwargs.get('conf', 'config.ini'))
        conf = {
            'srs': {
                'ip': config.get('srs', 'ip'),
                'port': config.get('srs', 'port'),
                'nick': config.get('srs', 'nick'),
                'version': config.get('srs', 'version'),
                'guid': config.get('srs', 'guid'),
                'rx': config.get('srs', 'rx'),
            },
            'recorder': {
                'opus_dll': config.get('recorder', 'opus_dll'),
                'freqs': config.get('recorder', 'freq').split(','),
                'output': config.get('recorder', 'output'),
            },
        }

        self.output_dir = conf['recorder']['output']
        freqs = [float(x) for x in conf['recorder']['freqs']]
        self.host = conf['srs']['ip']
        self.port = int(conf['srs']['port'])
        self.nick = conf['srs']['nick']
        self.version = conf['srs']['version']
        # this is the ID used on the SRS network. I changed a single character in mine. No idea if it's unique or even
        #   if it needs to be
        self.client_guid = conf['srs']['guid']
        # Default server settings to what I observed on my server.
        # Not currently used, but could be in the future...
        self.server_settings = {
            'CLIENT_EXPORT_ENABLED': False,
            'EXTERNAL_AWACS_MODE': False,
            'COALITION_AUDIO_SECURITY': False,
            'SPECTATORS_AUDIO_DISABLED': False,
            'LOS_ENABLED': False,
            'DISTANCE_ENABLED': False,
            'IRL_RADIO_TX': False,
            'IRL_RADIO_RX_INTERFERENCE': False,
            'RADIO_EXPANSION': False,
            'ALLOW_RADIO_ENCRYPTION': True,
            'TEST_FREQUENCIES': '247.2,120.3',
            'GLOBAL_LOBBY_FREQUENCIES': '248.22',
            'SHOW_TUNED_COUNT': False,
            'LOTATC_EXPORT_ENABLED': True,
            'LOTATC_EXPORT_PORT': '10712',
            'LOTATC_EXPORT_IP': '127.0.0.1',
            'SHOW_TRANSMITTER_NAME': False,
            'RETRANSMISSION_NODE_LIMIT': 0,
        }
        self.connected_clients = []
        # track our own state. Sometimes sent to the SRS server to update it on where we are and all that jazz
        self.state_blob = {
            "Client": {
                "ClientGuid": self.client_guid,
                "Name": self.nick,
                "Seat": 0,
                "Coalition": 0,
                "RadioInfo": {
                    "radios": [],
                    "unit": "",
                    "unitId": 16807932,
                    "iff": {
                        "control": 0,
                        "mode1": 0,
                        "mode3": 0,
                        "mode4": False,
                        "mic": -1,
                        "status": 0,
                    }
                },
                "LatLngPosition": {
                    "lat": 0.0,
                    "lng": 0.0,
                    "alt": 0.0
                },
            },
            "MsgType": MSG_SYNC,
            "Version": self.version,
        }
        self.connecting = True
        self.radios = {}
        self.receiving = False
        self.stop_audio_tick = True
        # default mission start time to SOMETHING in case we miss the mission start
        self.mission_start_time = arrow.now()
        # we preload the RX sounds to cut down on latency later
        if not os.path.exists(conf['srs']['rx']):
            print("ERROR:: Could not find RX sound file, please check the configuration")
            exit(6)
        rx_file = wave.open(
            conf['srs']['rx'],
            'rb'
        )
        self.rx = rx_file.readframes(9999)
        rx_file.close()
        # Opus DLL path
        self.opus_dll = conf['recorder']['opus_dll']
        if not os.path.exists(self.opus_dll):
            print("ERROR:: Could not find Opus DLL - try installing SRS?")
            os._exit(1)
        # set the sample rate
        self.sample_rate = kwargs.get('sample_rate', 48000)
        # set the frequencies we want to listen to
        try:
            self.freqs = [x * 1000000 for x in freqs]
        except Exception:
            raise Exception("ERROR:: Invalid frequencies were detected. Note that frequencies should be numerical")
            os._exit(2)
        # set up sockets for communication with the server
        self.tcp_socket = None
        self.udp_socket_voice = None
        self.udp_socket_cmd = None
        self.packet_log = open('packets.txt', 'wb')
        self.msn_name = 'UNKNOWN_MIZ'

    def __del__(self):
        for freq, radio in self.radios.items():
            now = arrow.now()
            radio.generate_silence((now - radio.last_stream_ended).total_seconds())
            radio.out_file.close()

    def __exit__(self):
        for freq, radio in self.radios.items():
            now = arrow.now()
            radio.generate_silence((now - radio.last_stream_ended).total_seconds())
            radio.out_file.close()

    def grpc_connect(self):
        """
        Block until we successfully connect to the DCS-gRPC server, then initialize the SRS connect sequence
        :return:
        """
        self.msn_name = self.await_mission_start()
        self.connect()

    def connect(self):
        """
        Connect to the SRS server and begin reading TCP traffic
        :return:
        """
        connect_blob = self.state_blob
        for x in range(0, 11):
            connect_blob['Client']['RadioInfo']['radios'].append({
                'enc': False,
                'encKey': 0,
                'freq': 1.0,
                'modulation': 3,
                'secFreq': 1.0,
                'retransmit': False,
            })
        # TODO: handle being unable to connect to SRS server
        self.tcp_socket = socket.socket()
        try:
            self.tcp_socket.connect((self.host, self.port))
        except ConnectionRefusedError:
            print("ERROR:: Unable to connect to SRS server, validate the IP address and port are correct")
            exit(2)
        self.tcp_socket.sendall(json.dumps(connect_blob, separators=(',', ':')).encode() + '\n'.encode())
        print("[SRS::Command] Connected to server")
        self.read_tcp()

    def read_tcp(self):
        """
        Read TCP traffic forever. Mostly ignored right now, but can be used in the future
        :return:
            Does not return
        """
        while True:
            data = self.tcp_socket.recv(65536)
            lines = data.decode().splitlines()
            if data == b'':
                print("WARN:: Connection closed")
                break
            if lines:
                for line in lines:
                    self.parse_response(line)
            elif data:
                print("WARN:: YOU SHOULD NEVER SEE THIS", data)

    def parse_response(self, msg):
        """
        Parses data sent over the SRS TCP connection. This is mostly state updates, e.g. a new client connecting
        :param msg:
            Message sent from the server. Expected to be a JSON blob
        :return:
        """
        parsed = json.loads(msg)
        msg_type = parsed['MsgType']
        '''
        Types of messages
        MSG_UPDATE = 0
        MSG_PING = 1
        MSG_SYNC = 2
        MSG_RADIO_UPDATE = 3
        MSG_SERVER_SETTINGS = 4
        MSG_CLIENT_DISCONNECT = 5
        MSG_VERSION_MISMATCH = 6
        MSG_E_AWACS_PW = 7
        MSG_E_AWACS_DC = 8
        '''
        if msg_type == MSG_UPDATE:
            # these are sent on a regular basis so we know where people are
            pass
        elif msg_type == MSG_PING:
            pass
        elif msg_type == MSG_SYNC:
            # sync is sent when major events happen (e.g. connecting)
            if self.connecting:
                self.send_slotted()
                return
        elif msg_type == MSG_RADIO_UPDATE:
            # I think this is sent when you slot?
            #print("got radio update:", msg)
            pass
        elif msg_type == MSG_SERVER_SETTINGS:
            # sent when you first connect
            pass
        elif msg_type == MSG_CLIENT_DISCONNECT:
            # I assume this is sent when someone drops but I'm not sure yet
            print("WARNING:: Got disconnect:", msg)
        elif msg_type == MSG_VERSION_MISMATCH:
            # sent if we're running an incompatible version
            print("ERROR:: Got version mismatch - quitting")
            exit(1)
        elif msg_type == MSG_E_AWACS_PW or msg_type == MSG_E_AWACS_DC:
            # passworded radio stuff. will likely never care about this
            pass
        else:
            pass
            #print("IN >>", parsed)
        if 'Clients' in parsed.keys():
            # we get the currently connected clients, not a delta. reset the list so we can build it again
            self.connected_clients = []
            for client in parsed['Clients']:
                self.connected_clients.append({
                    'ClientGuid': client['ClientGuid'],
                    'Name': client['Name'],
                })

    def send_slotted(self):
        """
        Tells the SRS server we are in game and notifies it which radios we have and which frequencies they are tuned to
        Additionally spawns the UDP threads to receive voice and voice-cmd data
        :return:
            N/A
        """
        self.state_blob['MsgType'] = MSG_RADIO_UPDATE
        self.state_blob['Client']['Coalition'] = 2
        self.state_blob['Client']['RadioInfo']['unit'] = 'A-10C'
        # tell SRS we are listening to particular frequencies so we record traffic on all flight comms
        for i, freq in enumerate(self.freqs):
            self.state_blob['Client']['RadioInfo']['radios'][i + 1]['freq'] = freq
            self.state_blob['Client']['RadioInfo']['radios'][i + 1]['name'] = 'AN/ARC-210(V) AM'
            self.state_blob['Client']['RadioInfo']['radios'][i + 1]['modulation'] = 0
            self.radios[freq] = Radio(
                frequency=freq,
                decoder=OpusDecoder(self.sample_rate, 2, self.opus_dll),
                out_file=os.path.join(
                    self.output_dir,
                    f"{str(arrow.now().date()).replace('-', '')}_{self.msn_name}_{str(freq / 1000000)}.ogg",
                ),
            )
        for x in range(0, 11):
            self.state_blob['Client']['RadioInfo']['radios'][x]['secFreq'] = 0.0

        self.tcp_socket.sendall(json.dumps(self.state_blob, separators=(',', ':')).encode() + '\n'.encode())
        self.connecting = False
        _thread.start_new_thread(self.spawn_udp_voice, ())
        _thread.start_new_thread(self.spawn_udp_cmd, ())
        _thread.start_new_thread(self.spawn_mission_tracker, ())

    def await_mission_start(self):
        """
        Attempts to connect to the DCS-gRPC exporter and blocks until the mission is started
        :return:
            STRING: msn_name - Fully qualified mission name
        """
        self.print("Command", "attempting to connect to DCS-GRPC")
        unpaused = False

        while not unpaused:
            try:
                channel = grpc.insecure_channel('127.0.0.1:50051')
                stub = mission_pb2_grpc.MissionServiceStub(channel)
                hook_stub = hook_pb2_grpc.HookServiceStub(channel)
                while not unpaused:
                    # check if the mission has started
                    cur_time = stub.GetScenarioCurrentTime(mission_pb2.StreamEventsRequest())
                    start_time = stub.GetScenarioStartTime(mission_pb2.StreamEventsRequest())
                    if cur_time != start_time:
                        msn_name = hook_stub.GetMissionFilename(hook_pb2.GetMissionFilenameRequest()).name
                        self.print("DCS::Mission", "caught unpause")
                        return msn_name[msn_name.rfind('\\') + 1: -4]
            except Exception as e:
                # grpc doesn't raise a helpful exception, so just catch all of them
                if not isinstance(e, _InactiveRpcError):
                    # only print errors not related to failing to connect
                    self.print("error", f"DCS-GRPC caught exception: type {type(e)}, msg {e}")
                pass

    def spawn_udp_cmd(self):
        """
        UDP command connection. I haven't seen a lot of useful data sent over this, but it's possible there is good stuff
        For the purposes of testing, a UDP packet containing 'abcd' in characters 28-32 will cause the packet to be
            treated as an incoming voice packet. This permits easy calling into the voice decoding code without having
            to muck around with how it's received or do complex spoofing a client sending traffic junk
        :return:
            N/A
        """
        self.udp_socket_cmd = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        self.udp_socket_cmd.sendto('hello'.encode(), (self.host, self.port))
        while True:
            message, address = self.udp_socket_cmd.recvfrom(65535)
            if message[28:32] == b'abcd':
                self.parse_voice(message[32:])
            try:
                self.parse_cmd(message)
            except KeyError:
                pass
            except Exception as e:
                pass
                print(e)

    def parse_cmd(self, message):
        try:
            msg = json.loads(message[28:].decode())
        except Exception as e:
            return
        for radio in msg['RadioReceivingState']:
            if radio and radio['IsReceiving'] != self.receiving:
                self.receiving = radio['IsReceiving']

    def spawn_mission_tracker(self):
        # do initial setup stuff
        self.mission_start_time = arrow.now()
        self.print("command", f"Caught mission start at {arrow.now()}")
        if self.stop_audio_tick:
            self.stop_audio_tick = False
            _thread.start_new_thread(self.audio_tick, ())
        ended = False

        while not ended:
            try:
                channel = grpc.insecure_channel('127.0.0.1:50051')
                stub = mission_pb2_grpc.MissionServiceStub(channel)
                while not ended:
                    # check if the mission has ended
                    response_stream = stub.StreamEvents(mission_pb2.StreamEventsRequest())
                    for response in response_stream:
                        event_name = response.WhichOneof("event")
                        if event_name == 'mission_end':
                            ended = True
            except Exception as e:
                # grpc doesn't raise a helpful exception, so just catch all of them
                if isinstance(e, _InactiveRpcError) or isinstance(e, _MultiThreadedRendezvous):
                    # if we can't connect at this stage, the mission has ended (or we've lost connectivity)
                    ended = True
                else:
                    # only print errors not related to failing to connect
                    self.print("error", f"DCS-GRPC caught exception: type {type(e)}, msg {e}")
                pass
        self.print("command", f"Caught mission end at {arrow.now()}")
        self.packet_log.close()
        self.stop_audio_tick = True

    def spawn_udp_voice(self):
        """
        Create the initial UDP connection and hand things off to the listener function
        :return:
            N/A
        """
        print("[SRS::Voice] Spawned UDP listener")
        self.udp_socket_voice = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        self.udp_socket_voice.sendto(self.client_guid.encode(), (self.host, self.port))
        message, address = self.udp_socket_voice.recvfrom(65535)
        self.read_udp()

    def read_udp(self):
        """
        Listen for voice traffic and attempt to parse/handle it if it's received
        :return:
            N/A
        """
        while True:
            message, address = self.udp_socket_voice.recvfrom(65535)
            if address[0] != self.host:
                # random stuff, not actually from the server
                print("ignoring message")
                continue
            # print("got data", data.decode())
            if len(message) == 22:
                # this is called a ping in the docs. I haven't seen it happen yet though
                print("caught ping or something lulz")
                continue
            self.parse_voice(message)

    def parse_voice(self, message):
        """
        Handles incoming voice traffic. This is the code that connects all of the bits
        :param message:
            UDP packet sent by SRS
        :return:
            N/A
        """
        current_time = arrow.now()
        # check of the message contains data
        if len(message) > PACKET_HEADER_LENGTH + FIXED_PACKET_LENGTH + FREQUENCY_SEGMENT_LENGTH:
            # check if the packet is valid
            if self.check_valid_traffic(message):
                # decode the (UDP) packet
                parsed_voice = self.decode_voice_packet(message)
                if parsed_voice:
                    # a single packet can contain multiple frequencies worth of data
                    for freq in parsed_voice['frequencies']:
                        # decode the (opus) packet
                        parsed_frames, decoded_length = self.radios[freq].opus_decoder.decode(parsed_voice)
                        self.radios[freq].last_rx = current_time
                        self.radios[freq].last_rx_extended = current_time.shift(seconds=decoded_length)
                        if not self.radios[freq].receiving:
                            # we have begun to receive a new stream, generate silence to fill the gap before it started
                            duration = (current_time - self.radios[freq].last_tick).total_seconds()
                            if self.radios[freq].last_tick and duration > 0:
                                if not self.radios[freq].received_audio:
                                    # we do not pre-generate silence on the first stream
                                    self.radios[freq].received_audio = True
                                    self.print('audio', f'Detected first audio stream on {freq}',self.radios[freq])
                                else:
                                    # pre-generate silence before the stream begins
                                    self.radios[freq].lock.acquire()
                                    self.radios[freq].generate_silence(duration)
                                    self.radios[freq].lock.release()
                            # update the radio to indicate that a new stream has begun
                            self.radios[freq].started_receiving = True
                        if parsed_frames:
                            self.radios[freq].lock.acquire()
                            self.radios[freq].buffer += parsed_frames
                            self.radios[freq].lock.release()
                        self.radios[freq].receiving = True
            else:
                print("WARN:: VOICE >> DISCARDED INVALID MESSAGE:", message)
        else:
            print("WARN:: VOICE >> MESSAGE TOO SHORT:", len(message), message)

    @staticmethod
    def decode_voice_packet(message):
        try:
            receiving_guid = message[-GUID_LENGTH:].decode()
            original_guid = message[-GUID_LENGTH * 2:-GUID_LENGTH].decode()
            message_without_guid = message[0:-GUID_LENGTH * 2]
            retransmission_count = int(message_without_guid[-1])
            packet_length = int(message_without_guid[0])
            ecn_audio_1 = int(message_without_guid[2])
            freq_length = int(message_without_guid[4])
            freq_count = int(freq_length / FREQUENCY_SEGMENT_LENGTH)
            to_decode = message_without_guid[6:ecn_audio_1]

            frequencies = []
            modulations = []
            encryptions = []
            frequency_offset = PACKET_HEADER_LENGTH + ecn_audio_1
            for x in range(0, freq_count):
                frequencies.append(struct.unpack('d', message_without_guid[frequency_offset:frequency_offset+8])[0])
                modulations.append(message_without_guid[frequency_offset + 8])
                encryptions.append(message_without_guid[frequency_offset + 9])
                frequency_offset += FREQUENCY_SEGMENT_LENGTH
            unit_id = int(struct.unpack('i', message_without_guid[PACKET_HEADER_LENGTH + ecn_audio_1 + freq_length:PACKET_HEADER_LENGTH + ecn_audio_1 + freq_length + 4])[0])
            packet_number = int(message_without_guid[PACKET_HEADER_LENGTH + ecn_audio_1 + freq_length + 4])

            return {
                'guid': receiving_guid,
                'audio_part1_bytes': to_decode,
                'audio_part1_length': ecn_audio_1,
                'frequencies': frequencies,
                'unit_id': unit_id,
                'encryptions': encryptions,
                'modulations': modulations,
                'packet_number': packet_number,
                'packet_length': packet_length,
                'original_client_guid': original_guid,
                'original_client_guid_bytes': '',
                'retransmission_count': retransmission_count,
            }
        except Exception as e:
            #print(e)
            return None

    def check_valid_traffic(self, message):
        # checking is done here -
        # https://github.com/ciribob/DCS-SimpleRadioStandalone/blob/c8f233a0eede26dc825499aa9dc86ccb4aa8df6d/DCS-SR-Client/Network/UDPVoiceHandler.cs#L326
        # we want all traffic for now
        return True

    def audio_tick(self):
        while not self.stop_audio_tick:
            for freq, radio in self.radios.items():
                now = arrow.now()
                if not radio.last_tick:
                    radio.last_tick = now
                tick_delta = (now - radio.last_tick).total_seconds()
                if radio.last_rx:
                    rx_delta = (now - radio.last_rx).total_seconds()
                else:
                    rx_delta = 0

                if radio.receiving and radio.started_receiving:
                    # we have just started receiving a new stream
                    """
                    self.print(
                        "audio",
                        f"Started receiving new stream",
                        radio,
                    )
                    """
                    radio.started_receiving = False
                    # based on test playbacks, this might not even be needed...
                    # radio.buffer += self.rx
                elif radio.receiving and rx_delta > 0.2:
                    # it's been >= 200 ms since we last received a packet, update state to show the stream is over
                    radio.receiving = False
                    # write out all of the data we've buffered
                    radio.lock.acquire()
                    radio.flush_buffer()
                    # this generation may not even be needed now that we're doing constant error correcting
                    silence_needed = round(len(radio.out_file) / radio.out_file.samplerate - (arrow.now() - self.mission_start_time).total_seconds(), 4) * -1
                    if silence_needed > 0:
                        radio.generate_silence(silence_needed)
                        #self.print("audio", f"ERROR CORRECTING with {silence_needed} seconds of one-off silence ;););)", radio)
                    radio.lock.release()
                    radio.last_rx = None
                    radio.last_rx_extended = None
                    radio.last_tick = now
                elif not radio.started_receiving and not radio.receiving and tick_delta >= 1:
                    # we're not receiving and it's been that way for >= 1 second
                    if not radio.last_rx:
                        # check if we've run out of sync and attempt to put us back
                        time_elapsed = (arrow.now() - self.mission_start_time).total_seconds()
                        recording_delta = round(len(radio.out_file) / radio.out_file.samplerate - time_elapsed, 4)
                        radio.lock.acquire()
                        if recording_delta < 0:
                            # stop trying to be smart and just close the gap
                            radio.generate_silence(recording_delta * -1)
                            #self.print("audio", f"Generating {recording_delta * -1} seconds of silence", radio)
                        else:
                            #self.print("audio", "Skipping silence generation as we're ahead", radio)
                            pass
                        radio.lock.release()
                    radio.last_tick = now
        os._exit(0)

    def print(self, group, message, radio=None):
        if self.mission_start_time:
            delta = (arrow.now() - self.mission_start_time).total_seconds()
            if radio:
                delta = round(len(radio.out_file) / radio.out_file.samplerate - delta, 4)
                print(f"{group.upper()}:: [t+{(arrow.now() - self.mission_start_time).total_seconds()} | r+{len(radio.out_file) / radio.out_file.samplerate} | d={delta}, dd={round(delta - radio.previous_delta, 2)}] {message}")
                radio.previous_delta = delta
            else:
                print(f"{group.upper()}:: [t+{(arrow.now() - self.mission_start_time).total_seconds()}] {message}")
        else:
            print(f"{group.upper()}:: {message}")


class Environment:
    def __init__(self):
        pass

    def get_dcs_install_paths(self):
        install_paths = []
        check_paths = ['DCS.openbeta', 'DCS']
        base_path = os.path.expandvars('%USERPROFILE%') + '\\Saved Games'

        for path in check_paths:
            cur_path = base_path + '\\' + path
            if os.path.exists(cur_path):
                install_paths.append(cur_path)

        return install_paths

    def get_tacview_paths(self):
        install_paths = []
        check_paths = [
            os.path.join('Tacview', 'AddOns'),
        ]
        base_path = os.path.expandvars('%APPDATA%')

        for path in check_paths:
            cur_path = os.path.join(base_path, path)
            if os.path.exists(cur_path):
                install_paths.append(cur_path)
        return install_paths

    def populate_export(self, path):
        import shutil
        destination_path = path + '\\Scripts\\srs_recorder.lua'
        if not os.path.isfile(destination_path):
            print("Couldn't find srs_recorder.lua, installing")
            # copy the recorder file (done first so if it fails we don't muck with the export.lua file)
            shutil.copyfile('scripts\\srs_recorder.lua', path + '\\Scripts\\srs_recorder.lua')
            # validate that the export file exists at all
            export_file = path + '\\Scripts\\Export.lua'
            mode = 'a'
            if not os.path.isfile(export_file):
                mode = 'w'
            # make a backup of the file before we mess things up
            shutil.copyfile(export_file, export_file + '.srs_recorder_backup')
            in_fh = open('scripts\\export.lua', 'r')
            contents = in_fh.readlines()
            with open(export_file, mode) as export_fh:
                export_fh.writelines(contents)
            print("Install completed")

    def configure(self):
        # old version
        #paths = self.get_dcs_install_paths()
        #for path in paths:
        #    self.populate_export(path)
        paths = self.get_tacview_paths()
        for path in paths:
            self.populate_addon(path)

    def populate_addon(self, path):
        addon_directory = 'srs_recorder'
        import shutil
        destination_path = os.path.join(path, addon_directory, 'main.lua')
        if not os.path.isdir(os.path.dirname(destination_path)):
            print("Couldn't find srs_recorder Tacview addon, creating folder")
            os.mkdir(os.path.join(path, addon_directory))
        if not os.path.isfile(destination_path):
            print("\tinstalling addon")
            # copy the recorder file (done first so if it fails we don't muck with the export.lua file)
            shutil.copyfile(os.path.join('scripts', 'main.lua'), destination_path)
            print("Install completed")


if __name__ == '__main__':
    e = Environment()
    e.configure()
    recorder = SRSRecorder()
    recorder.grpc_connect()
