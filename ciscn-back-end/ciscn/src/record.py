import pyaudio
import wave
import time
import Queue
import thread
import os

def record(filename="output.wav",recordTime=5):
    CHUNK = 512
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 16000
    RECORD_SECONDS = recordTime
    WAVE_OUTPUT_FILENAME = filename

    p = pyaudio.PyAudio()
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)
    frames = []
    for i in range(0, int(RATE / CHUNK * RECORD_SECONDS)):
        data = stream.read(CHUNK)
        frames.append(data)
    stream.stop_stream()
    stream.close()
    p.terminate()
    wf = wave.open(WAVE_OUTPUT_FILENAME, 'wb')
    wf.setnchannels(CHANNELS)
    wf.setsampwidth(p.get_sample_size(FORMAT))
    wf.setframerate(RATE)
    wf.writeframes(b''.join(frames))
    wf.close()

def deleteOldFile():
    global filenameQueue
    time.sleep(25)
    while True:
        os.system("rm "+filenameQueue.get())
        print "Remove older file"
        time.sleep(6)

if __name__ == "__main__":
    global filenameQueue
    filenameQueue=Queue.Queue(200)
    raw_input("enter to continue")
    wavFrame=0
    thread.start_new_thread(deleteOldFile,())
    while True:
        print wavFrame
        record(str(wavFrame)+".wav",5)
        filenameQueue.put(str(wavFrame)+".wav")
        wavFrame+=1
