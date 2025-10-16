import whisper
import torch
from dotenv import load_dotenv
import os
from datetime import datetime

load_dotenv()


class SpeechToText:
    def __init__(self):
        self.WHISPER_MODEL_NAME = os.environ.get("WHISPER_MODEL_NAME") # load Whisper model name from .env
        self.device = "cuda" if self.__isCudaAvailable() else "cpu" # use nvida gpu to run model if available
        
        self.model = whisper.load_model(self.WHISPER_MODEL_NAME, self.device) # load whisper model
        
        print(f"Whisper {self.WHISPER_MODEL_NAME} Model loaded successfully.")
        
    def transcribe(self, audio_file):
        """ Returns: Audio Text, Time Taken to Transcribe """
        if self.model:
            try:
                start = datetime.now()
                result = self.model.transcribe(audio_file)
                end = datetime.now()
                
                time_taken = (end - start).total_seconds()
                
                return result["text"].strip() , time_taken
                
            except Exception as e:
                print(f"\n--- Error while Transcribing audio file: {audio_file} ---")
                print(f"\nError Details: {e}\n")
                
        else:
            print("\n--- Whisper Model is not loaded. ---\n")
        
        return None
    
    def __isCudaAvailable(self):
        """ Check if cuda drivers are available """
        return torch.cuda.is_available()
    

def test_stt():
    stt = SpeechToText()
    
    AUDIO_FILES_DIR = os.environ.get("AUDIO_FILES_DIR")
    STT_OUTPUT_DIR = os.environ.get("STT_OUTPUT_DIR")
    
    output_file = "stt.txt"
    
    audio_files = os.listdir(AUDIO_FILES_DIR)
    
    for audio_file in audio_files:
        
        audio_file_path = AUDIO_FILES_DIR + f"/{audio_file}"
        
        text, time_taken = stt.transcribe(audio_file_path)
        
        with open(f"{STT_OUTPUT_DIR}/{output_file}", "a") as fp:
            fp.write(f"\n--- File name {audio_file} ---\n")
            fp.write(f"Time taken: {time_taken}\n")
            fp.write(text + "\n")
    
    
def test():
    from pprint import pprint
    audio_files = os.listdir("./audio_files")
    pprint(audio_files)

if __name__ == "__main__":
    test_stt()
    # test()