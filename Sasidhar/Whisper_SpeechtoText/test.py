import whisper
from datetime import datetime


# result = whisper.available_models()
# model = whisper.load_model("small.en", "cpu")
model = whisper.load_model("small.en","cuda")

for i in range(1,6):
    
    audio_file = f"./audio_files/audio{i}.mp3"

    start = datetime.now()
    result = model.transcribe(audio_file)
    end = datetime.now()

    print(result["text"])
    # print(f"Time taken: {(end-start).total_seconds()}")s

    with open("./output/stt.txt" , "a") as fp:
        fp.write(f"\n--- File name {audio_file} ---\n")
        fp.write(f"Time taken: {(end-start).total_seconds()}\n")
        fp.write(result["text"].strip() + "\n")
