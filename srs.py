import socket
import json
import _thread
import time
import struct
import ctypes
import array
import arrow
import wave
import scipy.io.wavfile
import numpy

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
PACKET_HEADER_LENGTH = 2 + 2 + 2  # https://github.com/ciribob/DCS-SimpleRadioStandalone/blob/91f7e575347b1113c5e2bb08cba0031c53201f23/DCS-SR-Common/Network/UDPVoicePacket.cs#L35
FIXED_PACKET_LENGTH = 4 + 8 + 0 + GUID_LENGTH + GUID_LENGTH  # https://github.com/ciribob/DCS-SimpleRadioStandalone/blob/91f7e575347b1113c5e2bb08cba0031c53201f23/DCS-SR-Common/Network/UDPVoicePacket.cs#L45
FREQUENCY_SEGMENT_LENGTH = 8 + 1 + 1  # https://github.com/ciribob/DCS-SimpleRadioStandalone/blob/91f7e575347b1113c5e2bb08cba0031c53201f23/DCS-SR-Common/Network/UDPVoicePacket.cs#L40


class DecoderStructDoNotUse(ctypes.Structure):
    pass


class OpusDecoder:
    def __init__(self, bitrate, channels, dll_path, buffer_size=192000):
        self.bitrate = bitrate
        self.channels = channels
        self.dll_path = dll_path
        self.decoder_obj = None
        self.decode_func = None
        self.frame_count = self.get_frame_count(buffer_size)

    def create(self):
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
        self.decoder_obj = create_func(ctypes.c_int(self.bitrate), ctypes.c_int(self.channels), ctypes.byref(create_decoder_result))
        if create_decoder_result.value != 0:
            raise Exception("Failed to create decoder state object: {}".format(create_decoder_result))

    def decode(self, voice_packet):
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
        return array.array('h', decoded_bytes[:decoded_byte_count * self.channels]).tobytes()

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
    def __init__(self, frequency, decoder, out_file):
        self.frequency = frequency
        self.opus_decoder = decoder
        self.opus_decoder.create()
        # zero out the file (yes there are easier ways to do it)
        wave_file = wave.open(out_file, 'wb')
        wave_file.setnchannels(2)
        wave_file.setframerate(48000)
        wave_file.setsampwidth(2)
        wave_file.close()

        #self.out_file_handle = wave_file
        self.out_file = out_file
        self.receiving = False
        self.buffer = b''
        self.last_received_time = None

    def write_audio(self, data):
        # this apparently appends by default (and manages the file being open/closed)
        scipy.io.wavfile.write(self.out_file, 48000, numpy.frombuffer(data, dtype=float))


class SRSRecorder:
    def __init__(self):
        self.host = '47.13.59.190' #'127.0.0.1'
        self.host = '127.0.0.1'
        self.port = 5002
        self.nick = 'RECORDER'
        self.version = '1.9.2.1'
        self.client_guid = 'Cg1jAqxRakO0NxsDQnCcpg'
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

    def __del__(self):
        pass
        #for file in self.freq_to_file_handle.values():
        #    file.close()

    def connect(self):
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
        while True:
            data = self.tcp_socket.recv(8092)
            #print("got data", data.decode())
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
        parsed = json.loads(msg)
        msg_type = parsed['MsgType']
        '''
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
            print("got radio update:", msg)
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
        self.state_blob['MsgType'] = MSG_RADIO_UPDATE
        self.state_blob['Client']['Coalition'] = 2
        self.state_blob['Client']['RadioInfo']['unit'] = 'A-10C'
        self.state_blob['Client']['RadioInfo']['radios'][1]['modulation'] = 0
        # testing telling SRS we are listening to a particular frequency
        self.state_blob['Client']['RadioInfo']['radios'][1]['freq'] = 305000000.0
        self.state_blob['Client']['RadioInfo']['radios'][1]['name'] = 'AN/ARC-210(V) AM'
        self.state_blob['Client']['RadioInfo']['radios'][2]['modulation'] = 0
        self.state_blob['Client']['RadioInfo']['radios'][3]['modulation'] = 1
        for x in range(0, 11):
            self.state_blob['Client']['RadioInfo']['radios'][x]['secFreq'] = 0.0

        self.tcp_socket.sendall(json.dumps(self.state_blob, separators=(',', ':')).encode() + '\n'.encode())
        self.connecting = False
        _thread.start_new_thread(self.spawn_udp_voice, ())
        _thread.start_new_thread(self.spawn_udp_cmd, ())

    def spawn_udp_cmd(self):
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
            # remove the continue to print out incoming CMD traffic
            #continue
            #print("CMD >>", (message), address)

    def parse_cmd(self, message):
        try:
            msg = json.loads(message[28:].decode())
        except Exception as e:
            #print(e)
            return
        for radio in msg['RadioReceivingState']:
            if radio and radio['IsReceiving'] != self.receiving:
                self.receiving = radio['IsReceiving']
                #print("Receiving:", radio['IsReceiving'])

    def spawn_udp_voice(self):
        print("Spawned UDP listener")
        self.udp_socket_voice = socket.socket(family=socket.AF_INET, type=socket.SOCK_DGRAM, proto=socket.IPPROTO_UDP)
        self.udp_socket_voice.sendto(self.client_guid.encode(), (self.host, 5002))
        message, address = self.udp_socket_voice.recvfrom(65535)
        print("Initial sync:", message, address)
        #self.udp_socket.bind(('0.0.0.0', 5003))
        self.read_udp()

    def read_udp(self):
        while True:
            message, address = self.udp_socket_voice.recvfrom(65535)
            #print(len(message), address)
            if address[0] != self.host:
                # random stuff, not actually from the server
                print("ignoring message")
                continue
            # print("got data", data.decode())
            if len(message) == 22:
                # this is called a ping in the docs. I haven't seen it happen yet though
                print("caught ping or something lulz")
                continue
            print(message)
            self.parse_voice(message)

    def parse_voice(self, message):
        current_time = arrow.now()
        #print("caught voice")
        if len(message) > PACKET_HEADER_LENGTH + FIXED_PACKET_LENGTH + FREQUENCY_SEGMENT_LENGTH:
            if self.check_valid_traffic(message):
                parsed_voice = self.decode_voice_packet(message)
                if parsed_voice:
                    for freq in parsed_voice['frequencies']:
                        if freq not in self.radios.keys():
                            self.radios[freq] = Radio(
                                frequency=48000,
                                decoder=OpusDecoder(48000, 2, 'C:\\Program Files\\DCS-SimpleRadio-Standalone\\opus.dll'),
                                out_file=str(freq) + '.wav',
                            )
                            self.radios[freq].last_received_time = current_time

                        parsed_frames = self.radios[freq].opus_decoder.decode(parsed_voice)
                        if parsed_frames:
                            #self.radios[freq].out_file_handle.writeframes(parsed_frames)
                            self.radios[freq].write_audio(parsed_frames)
                            if current_time != self.radios[freq].last_received_time:
                                # this is not the first message, we may need to generate silence
                                pass
                        else:
                            # silence? something?
                            pass
                    #print(parsed_voice)
            else:
                print("VOICE >> DISCARDED INVALID MESSAGE:", message)
            #print("VOICE >>", sender_guid, raw_transmission)
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
        # checking is done here - https://github.com/ciribob/DCS-SimpleRadioStandalone/blob/c8f233a0eede26dc825499aa9dc86ccb4aa8df6d/DCS-SR-Client/Network/UDPVoiceHandler.cs#L326
        # we want all traffic for now
        return True


if __name__ == '__main__':
    recorder = SRSRecorder()
    recorder.connect()
