import sounddevice as sd
import numpy as np
import wave
import json
from datetime import datetime

from Gemini_API.ai_interviewer import TechnicalInterviewer, HRInterviewer
from Whisper_SpeechtoText.speech_to_text import SpeechToText


def record_audio(filename="temp_audio.wav", duration=None):
    CHUNK = 1024
    FORMAT = np.int16
    CHANNELS = 1
    RATE = 44100

    print("\n---------------------------------------------------------")
    input("-> Press Enter to start recording your answer.")
    print("-> Recording... Press Ctrl+C to stop.")

    frames = []

    try:
        if duration:
            # Fixed duration recording
            recording = sd.rec(int(duration * RATE), samplerate=RATE, channels=CHANNELS, dtype=FORMAT)
            sd.wait()
            frames = recording
        else:
            # Infinite recording until Ctrl+C
            with sd.InputStream(samplerate=RATE, channels=CHANNELS, dtype=FORMAT, blocksize=CHUNK) as stream:
                while True:
                    data, _ = stream.read(CHUNK)
                    frames.append(data)
    except KeyboardInterrupt:
        print("-> Recording finished.")
        print("---------------------------------------------------------")

    # Convert frames to numpy array
    if isinstance(frames, list):
        frames = np.concatenate(frames, axis=0)

    # Save as WAV
    with wave.open(filename, 'wb') as fp:
        fp.setnchannels(CHANNELS)
        fp.setsampwidth(np.dtype(FORMAT).itemsize)
        fp.setframerate(RATE)
        fp.writeframes(frames.tobytes())

    return filename


def integration_testing():
    MAX_QUESTIONS = 5
    JOB_ROLE = "Python Developer"
    JOB_DESCRIPTION = """
        Position: Python Developer
        Location: Vijayawada, India
        Type: Full-Time | Entry-Level

        Role Overview
        Join our team as a Python Developer and launch your backend development career! We're seeking a motivated and curious fresher ready to dive into building scalable, data-driven applications. This role is ideal for someone who enjoys working with Python's core data structures and has a basic familiarity with MySQL.

        Primary Responsibilities
        - Develop, test, and manage backend systems in Python, leveraging clean and efficient data structures
        - Write and optimize MySQL queries for seamless CRUD operations
        - Work closely with frontend teams to integrate APIs and enable continuous data exchange
        - Debug, refactor, and enhance backend code for optimal reliability and performance
        - Contribute to documentation and participate in deployment activities

        Key Skills & Qualifications
        - Strong grasp of Python basics: lists, dictionaries, tuples, sets, and object-oriented programming
        - Exposure to version control systems (preferably Git)
        - Analytical mindset with good problem-solving and algorithmic thinking skills

        What You'll Gain
        - Mentoring by experienced senior developers
        - Opportunities to work on real-world projects and grow your professional portfolio
        - Supportive, collaborative work environment
        - Pathways to advance into full-stack development and beyond
    """
    CANDIDATE_EXPERIENCE = "Fresher (0-1 years)" 
    
    print("\nStarting Technical Interview: \n")
    technical_output_path = "./Gemini_API/oop_output/technical_output.json"
    
    speech_to_text = SpeechToText()
    
    technical_interviewer = TechnicalInterviewer(JOB_ROLE, JOB_DESCRIPTION, CANDIDATE_EXPERIENCE, MAX_QUESTIONS)
    questions_list = technical_interviewer.generate_questions()
    
    if not questions_list:
        print("\n Failed to generate questions")
        quit()
    
    total_analysis = []

    for ai_question in questions_list:
        debug = {}
        
        print(f"\nAI Interviewer: {ai_question}")

        # candidate_answer = input("\nYour Answer: ")
        audio_file_path = "./Whisper_SpeechtoText/audio_files" + "/temp_audio.wav"
        record_audio(audio_file_path)
        candidate_answer, time_taken = speech_to_text.transcribe(audio_file_path)

        start = datetime.now()
        analysis = technical_interviewer.analyze_answer(ai_question, candidate_answer)
        end = datetime.now()

        analysis["question"] = ai_question
        analysis["candidate_answer"] = candidate_answer
        
        debug["analysis_time"] = (end - start).total_seconds()
        analysis["debug"] = debug
        
        total_analysis.append(analysis)


    print("\nAI Interviewer: Thank you for your time. That concludes the interview.")

    with open(technical_output_path, "w") as fp:
        json.dump(total_analysis, fp, indent=4)

    print(f"\nAnalysis Report Saved to {technical_output_path}.")
    print("\nEnd of Interview...\n")


if __name__ == "__main__":
    # record_audio()
    integration_testing()