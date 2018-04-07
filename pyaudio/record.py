"""PyAudio example: Record a few seconds of audio and save to a WAVE file."""
import struct
import array
import wave
import pyaudio
CHUNK = 4096
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 16000
RECORD_SECONDS = 5
WAVE_OUTPUT_FILENAME = "output.wav"

def save(wave_output_filename="output.pcm"):
    with wave.open(wave_output_filename, 'wb') as wf:
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))

p = pyaudio.PyAudio()
stream = p.open(
    format=FORMAT,
    channels=CHANNELS,
    rate=RATE,
    input=True,
    #input_device_index=6,
    frames_per_buffer=CHUNK)

print("* recording")

frames = []

# 过滤小声音
# 事实证明没用～～～
def voice(voice_data):
    voice = struct.Struct("<h")
    data = []
    for v in array.array("h",voice_data):
        if 5000 <= v:
            data.append(voice.pack(v))
    return data

for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
    data = stream.read(CHUNK)
    #frames += voice(data)
    frames.append(data)
print("* done recording")

stream.stop_stream()
stream.close()
p.terminate()

with open('output.pcm','w+b') as wf:
    wf.write(b''.join(frames))
