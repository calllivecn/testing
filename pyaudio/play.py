"""PyAudio Example: Play a WAVE file."""
import sys
import wave

import pyaudio
CHUNK = 4096

if len(sys.argv) < 2:
    print(f"Plays a wave file.\n\nUsage: {sys.argv[0]} filename.wav [loop count]")
    sys.exit(-1)


wf = wave.open(sys.argv[1], 'rb')

p = pyaudio.PyAudio()
stream = p.open(format=p.get_format_from_width(wf.getsampwidth()),
                channels=wf.getnchannels(),
                rate=wf.getframerate(),
                output=True)
                #output_device_index=6)
#print(data[:16])
#print(isinstance(data,bytes),'data length:',len(data))

try:
    count = sys.argv[2]
except IndexError:
    count = "1"

loop = int(count)

for i in range(loop):
    wf.setpos(0)
    while (data := wf.readframes(CHUNK)) != b"":
        stream.write(data)

wf.close()
stream.stop_stream()
stream.close()
p.terminate()

