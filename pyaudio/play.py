"""PyAudio Example: Play a WAVE file."""
import pyaudio
import wave
import sys
CHUNK = 4096

if len(sys.argv) < 1:
    print("Plays a wave file.\n\nUsage: %s filename.wav" % sys.argv[0])
    exit(-1)


wf = wave.open(sys.argv[1], 'rb')
p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)
                #output_device_index=6)
#print(data[:16])
#print(isinstance(data,bytes),'data length:',len(data))

while (data := wf.readframes(CHUNK)) != b"":
    stream.write(data)

wf.close()

stream.stop_stream()
stream.close()
p.terminate()

