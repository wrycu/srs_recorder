import socket
import json
import _thread
import struct
import ctypes
import array
import arrow
import wave
import os
import soundfile

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
        self.sample_rate = 48000  # this should probably be specified upstream, but for now we know it'll be 48,000
        self.frequency = frequency
        # decoder should be an OpusDecoder object
        self.opus_decoder = decoder
        self.opus_decoder.create()
        # for testing, we want to overwrite existing recordings. This will probably get removed as the project matures
        # zero out the file (yes there are easier ways to do it)
        wave_file = wave.open(out_file, 'wb')
        wave_file.setnchannels(2)
        wave_file.setframerate(self.sample_rate)
        wave_file.setsampwidth(2)
        self.out_file = soundfile.SoundFile(out_file, 'wb', samplerate=48000, channels=1)
        self.receiving = False
        self.started_receiving = False
        self.buffer = b''
        self.last_received_time = arrow.now()
        self.last_stream_ended = None
        self.stream_duration = 0
        self.need_to_close_gap = True
        self.last_tick = None

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
        ms_silence = b'000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000000'
        while duration > 5:
            self.out_file.buffer_write(
                ms_silence * int(5 * 1000 * 2),
                'int32',
            )
            self.out_file.flush()
            duration -= 5
        # duration is seconds but we want ms so * 1000. the file expects two channels so * 2
        self.out_file.buffer_write(
            ms_silence * int(duration * 1000 * 2),
            'int32',
        )
        # the docs have zero mention of when flush should be called - and in fact only mention write(),
        #   not buffer_write()
        # as such, we flush whenever we write to validate that we don't end up with missing data
        self.out_file.flush()


class SRSRecorder:
    def __init__(self):
        self.host = '127.0.0.1'
        self.port = 5002
        self.nick = 'RECORDER'
        self.version = '1.9.2.1'
        # this is the ID used on the SRS network. I changed a single character in mine. No idea if it's unique
        #   or even if it needs to be. Hope stuff works :)
        self.client_guid = 'Cg1jAqxRakO0NxsDQnCcpg'
        # track the server settings. Not really used now, but could come in handy in the long term
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
        self.tcp_socket = None
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
        self.udp_socket_voice = None
        self.udp_socket_cmd = None
        self.radios = {}
        self.receiving = False
        self.stop_audio_tick = False
        self.mission_start_time = None
        rx_path = 'C:\\Program Files\\DCS-SimpleRadio-Standalone\\Radio-RX-1600.wav'
        rx_file = wave.open(rx_path, 'rb')
        self.rx = rx_file.readframes(9999)
        rx_file.close()

    def __del__(self):
        print("AUDIO:: caught __del__")
        for freq, radio in self.radios.items():
            now = arrow.now()
            radio.generate_silence((now - radio.last_stream_ended).total_seconds())
            radio.out_file.close()

    def __exit__(self):
        print("AUDIO:: caught __exit__")
        for freq, radio in self.radios.items():
            now = arrow.now()
            radio.generate_silence((now - radio.last_stream_ended).total_seconds())
            radio.out_file.close()

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

        self.tcp_socket = socket.socket()
        self.tcp_socket.connect((self.host, self.port))
        self.tcp_socket.sendall(json.dumps(connect_blob, separators=(',', ':')).encode() + '\n'.encode())
        self.read_tcp()

    def read_tcp(self):
        """
        Read TCP traffic forever. Mostly ignored right now, but can be used in the future
        :return:
            Does not return
        """
        while True:
            data = self.tcp_socket.recv(8092)
            lines = data.decode().splitlines()
            if data == b'':
                print("Connection closed")
                break
            if lines:
                for line in lines:
                    self.parse_response(line)
            elif data:
                print("YOU SHOULD NEVER SEE THIS", data)

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
            print("Got update")
            pass
        elif msg_type == MSG_PING:
            print("ping... pong")
            pass
        elif msg_type == MSG_SYNC:
            # sync is sent when major events happen (e.g. connecting)
            print("Got sync")
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
            print("Got disconnect:", msg)
        elif msg_type == MSG_VERSION_MISMATCH:
            # sent if we're running an incompatible version
            print("Got version mismatch - quitting")
            exit(1)
        elif msg_type == MSG_E_AWACS_PW or msg_type == MSG_E_AWACS_DC:
            # passworded radio stuff. will likely never care about this
            pass
        else:
            print("IN >>", parsed)
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
        self.state_blob['Client']['RadioInfo']['radios'][1]['modulation'] = 0
        self.state_blob['Client']['RadioInfo']['radios'][2]['modulation'] = 0
        self.state_blob['Client']['RadioInfo']['radios'][3]['modulation'] = 0
        # tell SRS we are listening to particular frequencies so we record traffic on all flight comms
        # TODO: make a function to determine the radio (assuming it's enforced by SRS that certain radios can only hear
        #  certain freqs)
        self.state_blob['Client']['RadioInfo']['radios'][1]['freq'] = 305000000.0
        self.state_blob['Client']['RadioInfo']['radios'][1]['name'] = 'AN/ARC-210(V) AM'
        self.state_blob['Client']['RadioInfo']['radios'][2]['freq'] = 32000000.0
        self.state_blob['Client']['RadioInfo']['radios'][2]['name'] = 'AN/ARC-210(V) AM'
        self.state_blob['Client']['RadioInfo']['radios'][3]['freq'] = 311000000.0
        self.state_blob['Client']['RadioInfo']['radios'][3]['name'] = 'AN/ARC-210(V) AM'
        for x in range(0, 11):
            self.state_blob['Client']['RadioInfo']['radios'][x]['secFreq'] = 0.0

        self.tcp_socket.sendall(json.dumps(self.state_blob, separators=(',', ':')).encode() + '\n'.encode())
        self.connecting = False
        _thread.start_new_thread(self.spawn_udp_voice, ())
        _thread.start_new_thread(self.spawn_udp_cmd, ())
        _thread.start_new_thread(self.audio_tick, ())
        _thread.start_new_thread(self.spawn_mission_tracker, ())

    def spawn_udp_cmd(self):
        """
        UDP command connection. I haven't seen a lot of useful data sent over this, but it's possible there is good stuff
        For the purposes of testing, a UDP packet containing 'abcd' in characters 28-32 will cause the packet to be
            treated as an incoming voice packet. This permits easy calling into the voice decoding code without having
            to muck around with how it's received or do complex spoofing a client sending traffic junk
        :return:
            N/A
        """
        self.udp_socket_cmd = socket.socket(family=socket.AF_INET, type=socket.SOCK_RAW, proto=socket.IPPROTO_UDP)
        self.udp_socket_cmd.sendto('hello'.encode(), (self.host, 5002))
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
        udp_mission_sock = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        udp_mission_sock.bind(('127.0.0.1', 5190))
        while True:
            message = udp_mission_sock.recv(65535)
            if message == b'MISSION_START' and not self.mission_start_time:
                self.mission_start_time = arrow.now()
                print("Caught mission start", self.mission_start_time)
            elif message == b'MISSION_END':
                print("Caught mission end")
                os._exit(0)

    def spawn_udp_voice(self):
        """
        Create the initial UDP connection and hand things off to the listener function
        :return:
            N/A
        """
        print("Spawned UDP listener")
        self.udp_socket_voice = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        self.udp_socket_voice.sendto(self.client_guid.encode(), (self.host, 5002))
        message, address = self.udp_socket_voice.recvfrom(65535)
        print("Initial sync:", message, address)
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
                        # check if this is the first time we have seen this frequency and do some initial set up if so
                        if freq not in self.radios.keys():
                            self.radios[freq] = Radio(
                                frequency=freq,
                                decoder=OpusDecoder(48000, 2, 'C:\\Program Files\\DCS-SimpleRadio-Standalone\\opus.dll'),
                                out_file=str(freq) + '.ogg',
                            )
                            # check if the mission has been running since before we heard audio on this freq and add it
                            #   if it has
                            if not self.mission_start_time:
                                self.mission_start_time = current_time
                            mission_start_delta = (current_time - self.mission_start_time).total_seconds()
                            if mission_start_delta:
                                self.radios[freq].generate_silence(mission_start_delta)
                        self.radios[freq].last_received_time = current_time
                        # decode the (opus) packet
                        parsed_frames, decoded_length = self.radios[freq].opus_decoder.decode(parsed_voice)
                        self.radios[freq].stream_duration += decoded_length
                        if not self.radios[freq].receiving:
                            if self.radios[freq].last_tick and (current_time - self.radios[freq].last_tick).total_seconds() > 0:
                                print("AUDIO:: Pre-generating {} seconds of silence".format(
                                    (current_time - self.radios[freq].last_tick).total_seconds()))
                                self.radios[freq].generate_silence(
                                    (current_time - self.radios[freq].last_tick).total_seconds())
                            self.radios[freq].started_receiving = True
                        if parsed_frames:
                            self.radios[freq].buffer += parsed_frames
                        self.radios[freq].receiving = True
            else:
                print("VOICE >> DISCARDED INVALID MESSAGE:", message)
        else:
            print("VOICE >> MESSAGE TOO SHORT:", len(message), message)

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
        duration = 0
        while not self.stop_audio_tick:
            try:
                for freq, radio in self.radios.items():
                    now = arrow.now()
                    if not radio.last_tick:
                        radio.last_tick = now
                    time_delta = (now - radio.last_received_time).total_seconds()

                    # check if we've gone > 200ms since the last packet was received
                    if radio.receiving and time_delta > 0.2:
                        print("AUDIO:: No longer receiving at {} | Stream duration was {}".format(now, radio.stream_duration))
                        # update the radio state to indicate we are no longer receiving
                        # since we're not currently _exactly_ thread safe, let's set this to false first in an attempt
                        #   to avoid overriding the flag if we receive data while running this function
                        radio.stream_duration = 0
                        radio.receiving = False
                        # write out all of the data we've buffered
                        radio.flush_buffer()
                        radio.last_stream_ended = now.shift(seconds=-time_delta)
                    elif radio.receiving and radio.started_receiving:
                        print("AUDIO:: Started receiving new stream", now, "| Silence duration was", duration, "seconds")
                        print("AUDIO:: New stream was", now - self.mission_start_time, "from start of mission")
                        # we have just started receiving a new stream
                        radio.started_receiving = False
                        duration = 0
                        #radio.buffer += self.rx
                    elif not radio.started_receiving and not radio.receiving and (now - radio.last_tick).total_seconds() >= 1:
                        duration += (now - radio.last_tick).total_seconds()
                        if radio.last_stream_ended:
                            print("AUDIO:: Generating {} seconds of silence".format((now - radio.last_stream_ended).total_seconds()))
                            radio.generate_silence((now - radio.last_stream_ended).total_seconds())
                            radio.last_stream_ended = None
                            radio.last_tick = now
                        else:
                            print("AUDIO:: Generating {} seconds of silence".format((now - radio.last_tick).total_seconds()))
                            radio.generate_silence((now - radio.last_tick).total_seconds())
                        radio.last_tick = now
            except RuntimeError:
                # Dictionary size changes based on the freqs we encounter
                # we can address this by pre-loading the radios based on the number of freqs we're going to be listening
                # to, but for now just pass
                pass


if __name__ == '__main__':
    recorder = SRSRecorder()
    recorder.connect()
