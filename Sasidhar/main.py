import pyaudio
import wave



def record_audio_interactive(filename="temp_audio.wav"):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    RATE = 44100
    
    p = pyaudio.PyAudio()

    # Stream object
    stream = p.open(format=FORMAT,
                    channels=CHANNELS,
                    rate=RATE,
                    input=True,
                    frames_per_buffer=CHUNK)

    frames = [] # list of chunks (frames)

    print("\n---------------------------------------------------------")
    input("-> Press Enter to start recording your answer.")
    print("-> Recording... Press Ctrl+C to stop.")

    try:
        # read audio
        while True:
            data = stream.read(CHUNK)
            frames.append(data)
    except KeyboardInterrupt: # Ctrl + C pressed
        print("-> Recording finished.")
        print("---------------------------------------------------------")

    stream.stop_stream()
    stream.close()
    p.terminate()

    # Save the recorded data as a WAV file
    with wave.open(filename, 'wb') as fp: # fp in write byte mode
        # set data configuration
        fp.setnchannels(CHANNELS)
        fp.setsampwidth(p.get_sample_size(FORMAT))
        fp.setframerate(RATE)
        
        # write frames into file
        fp.writeframes(b''.join(frames))
    
    return filename

if __name__ == "__main__":
    record_audio_interactive()