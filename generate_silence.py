import srs

# fake an arbitrary amount of silence so we can test stuff

recorder = srs.SRSRecorder()
recorder.radios['305000000.0'] = srs.Radio(
    frequency='305000000.0',
    decoder=srs.OpusDecoder(48000, 2, 'C:\\Program Files\\DCS-SimpleRadio-Standalone\\opus.dll'),
    out_file=str('305000000.0') + '_auto_generated.ogg',
)
recorder.radios['305000000.0'].generate_silence(90)
