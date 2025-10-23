# fastapi dev server.py --port 5000
# python -m http.server 8080

from fastapi import FastAPI, HTTPException, UploadFile, File, Form
from fastapi.middleware.cors import CORSMiddleware
import uuid
import mysql.connector
import json
import os
from dotenv import load_dotenv

from Gemini_API.ai_interviewer import TechnicalInterviewer, HRInterviewer
from Whisper_SpeechtoText.speech_to_text import SpeechToText

import db_queries

load_dotenv()

# MAX_QUESTIONS = 1
# JOB_ROLE = "Python Developer"
# JOB_DESCRIPTION = """
#     Position: Python Developer
#     Location: Vijayawada, India
#     Type: Full-Time | Entry-Level

#     Role Overview
#     Join our team as a Python Developer and launch your backend development career! We're seeking a motivated and curious fresher ready to dive into building scalable, data-driven applications. This role is ideal for someone who enjoys working with Python's core data structures and has a basic familiarity with MySQL.

#     Primary Responsibilities
#     - Develop, test, and manage backend systems in Python, leveraging clean and efficient data structures
#     - Write and optimize MySQL queries for seamless CRUD operations
#     - Work closely with frontend teams to integrate APIs and enable continuous data exchange
#     - Debug, refactor, and enhance backend code for optimal reliability and performance
#     - Contribute to documentation and participate in deployment activities

#     Key Skills & Qualifications
#     - Strong grasp of Python basics: lists, dictionaries, tuples, sets, and object-oriented programming
#     - Exposure to version control systems (preferably Git)
#     - Analytical mindset with good problem-solving and algorithmic thinking skills

#     What You'll Gain
#     - Mentoring by experienced senior developers
#     - Opportunities to work on real-world projects and grow your professional portfolio
#     - Supportive, collaborative work environment
#     - Pathways to advance into full-stack development and beyond
# """
CANDIDATE_EXPERIENCE = "Fresher (0-1 years)" 

app = FastAPI()

origins = [
    "*",
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

stt_instance = SpeechToText()

### --- Test APIs --- 
@app.get("/get-all-interviews")
def get_all_interviews():
        
    interviews = db_queries.get_interviews()
    
    return interviews


@app.post("/start-technical-interview/{candidate_interview_id}")
def start_technical_interview(candidate_interview_id: int):
    
    selected_interview = db_queries.get_interviews(candidate_interview_id)
    
    job_role = selected_interview[0].get("job_role")
    job_description = selected_interview[0].get("job_description")
    max_questions = selected_interview[0].get("max_questions")
    
    interview_id = str(uuid.uuid4())
    
    interviewer = TechnicalInterviewer(
        job_role=job_role,
        job_description=job_description,
        candidate_experience=CANDIDATE_EXPERIENCE,
        max_questions=max_questions
    )
    questions = interviewer.generate_questions()
    
    if not questions:
        raise HTTPException(status_code=500, detail="Failed to generate interview questions.")
        
    db_connection = None
    try:
        db_connection = db_queries.get_db_connection()
        cursor = db_connection.cursor()
        
        insert_query = """
        INSERT INTO candidate_interviews (candidate_interview_id, interview_type, job_role, candidate_experience, questions, status, current_question_index)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        questions_json = json.dumps(questions)
        
        cursor.execute(insert_query, (interview_id, 'technical', job_role, CANDIDATE_EXPERIENCE, questions_json, 'in_progress', 0))
        
        
        db_connection.commit()
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Failed to create interview session: {err}")
    finally:
        if db_connection and db_connection.is_connected():
            cursor.close()
            db_connection.close()
            
    return {
        "message": "Technical interview started successfully.",
        "interview_id": interview_id,
        "question_number": 1,
        "total_questions": len(questions),
        "question": questions[0]
    }
    
@app.post("/start-hr-interview/{candidate_interview_id}")
def start_hr_interview(candidate_interview_id: int):
    selected_interview = db_queries.get_interviews(candidate_interview_id)
    
    job_role = selected_interview[0].get("job_role")
    job_description = selected_interview[0].get("job_description")
    max_questions = selected_interview[0].get("max_questions") 
    
    interview_id = str(uuid.uuid4())
    
    interviewer = HRInterviewer(
        job_role=job_role,
        job_description=job_description,
        candidate_experience=CANDIDATE_EXPERIENCE,
        max_questions=max_questions
    )
    questions = interviewer.generate_questions()
    
    if not questions:
        raise HTTPException(status_code=500, detail="Failed to generate HR interview questions.")
        
    db_connection = None
    try:
        db_connection = db_queries.get_db_connection()
        cursor = db_connection.cursor()
        
        insert_query = """
        INSERT INTO candidate_interviews (candidate_interview_id, interview_type, job_role, candidate_experience, questions, status, current_question_index)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        """
        questions_json = json.dumps(questions)
        
        cursor.execute(insert_query, (interview_id, 'hr', job_role, CANDIDATE_EXPERIENCE, questions_json, 'in_progress', 0))
        db_connection.commit()
        
    except mysql.connector.Error as err:
        raise HTTPException(status_code=500, detail=f"Failed to create HR interview session: {err}")
    finally:
        if db_connection and db_connection.is_connected():
            cursor.close()
            db_connection.close()
            
    return {
        "message": "HR interview started successfully.",
        "interview_id": interview_id,
        "question_number": 1,
        "total_questions": len(questions),
        "question": questions[0]
    }
    


@app.post("/submit-answer/{interview_id}")
async def submit_answer(interview_id: int, candidate_interview_id: str = Form(...), audio_file: UploadFile = File(...)):
    
    interview = db_queries.get_interviews(interview_id)
    job_description = interview[0].get("job_description")

    db_connection = None
    try:
        db_connection = db_queries.get_db_connection()
        cursor = db_connection.cursor(dictionary=True)
        
        cursor.execute("SELECT * FROM candidate_interviews WHERE candidate_interview_id = %s", (candidate_interview_id,))
        interview = cursor.fetchone()
        
        if not interview:
            raise HTTPException(status_code=404, detail="Interview session not found.")
        
        if interview['status'] == 'completed':
            return {"message": "This interview has already been completed."}
        
        if interview['status'] == 'not_started':
            return {"message": "This interview is not yet started."}


        temp_audio_path = f"temp_{candidate_interview_id}.wav"
        with open(temp_audio_path, "wb") as f:
            f.write(await audio_file.read())
            
        transcribed_text, _ = stt_instance.transcribe(temp_audio_path)
        os.remove(temp_audio_path)

        questions = json.loads(interview['questions'])
        current_question_index = interview['current_question_index']
        current_question = questions[current_question_index]
        
        interview_type = interview.get('interview_type', 'technical')
        
        if interview_type == 'technical':
            interviewer = TechnicalInterviewer(
                job_role=interview['job_role'],
                job_description=job_description,
                candidate_experience=interview['candidate_experience']
            )
        elif interview_type == 'hr':
            interviewer = HRInterviewer(
                job_role=interview['job_role'],
                job_description=job_description,
                candidate_experience=interview['candidate_experience']
            )
            
        analysis = interviewer.analyze_answer(current_question, transcribed_text)

        insert_answer_query = """
        INSERT INTO answers (candidate_interview_id, interview_type, question_text, answer_text, analysis)
        VALUES (%s, %s, %s, %s, %s)
        """
        cursor.execute(insert_answer_query, (candidate_interview_id, interview_type, current_question, transcribed_text, json.dumps(analysis)))

        next_question_index = current_question_index + 1
        response = {}

        if next_question_index >= len(questions):
            cursor.execute("UPDATE candidate_interviews SET status = 'completed', current_question_index = %s WHERE candidate_interview_id = %s", (next_question_index, candidate_interview_id))
            response = {
                "message": "Interview completed. Thank you!",
                "interview_id": interview_id,
                "final_analysis": analysis
            }
        else:
            cursor.execute("UPDATE candidate_interviews SET current_question_index = %s WHERE candidate_interview_id = %s", (next_question_index, candidate_interview_id))
            response = {
                "message": "Answer received. Here is the next question.",
                "interview_id": interview_id,
                "question_number": next_question_index + 1,
                "total_questions": len(questions),
                "question": questions[next_question_index],
                "previous_answer_analysis": analysis
            }
            
        db_connection.commit()
        return response

    except Exception as e:
        if db_connection:
            db_connection.rollback()
        raise HTTPException(status_code=500, detail=f"An error occurred: {str(e)}")
    finally:
        if db_connection and db_connection.is_connected():
            cursor.close()
            db_connection.close()
            
                 
@app.get("/candidate-interview/{interview_id}")
def get_interview_details(interview_id: str):
    analysis = db_queries.get_candidate_interview_analysis(interview_id)

    return analysis
    
    # return {
    #     "interview_id": interview["interview_id"],
    #     "job_role": interview["job_role"],
    #     "candidate_experience": interview["candidate_experience"],
    #     "date": interview.get("created_at", ""),
    #     "questions": json.loads(interview["questions"]),
    #     "answers": answers,
    #     "status": interview["status"]
    # }
    
    
### --- ATS Integrated APIs --- 

@app.post("/start-interview/{candidate_interview_id}")
def start_interview(candidate_interview_id: str):
    candidate_interview_details = db_queries.get_candidate_interview_details(candidate_interview_id)
    
    if candidate_interview_details is None:
        return {
            "error": True,
            "errorDescription": "Candidate Interview ID not found",
        }
        
    if candidate_interview_details["status"] == "not_started":
        job_role = candidate_interview_details.get("job_role")
        job_description = candidate_interview_details.get("job_description")
        candidate_experience = candidate_interview_details.get("candidate_experience")
        max_questions = candidate_interview_details.get("max_questions")
        interview_type = candidate_interview_details.get("interview_type")
        interview_id = candidate_interview_details.get("interview_id")

        if interview_type == 'technical':
            interviewer = TechnicalInterviewer(
                job_role=job_role,
                job_description=job_description,
                candidate_experience=candidate_experience,
                max_questions=max_questions
            )
        elif interview_type == 'hr':
            interviewer = HRInterviewer(
                job_role=job_role,
                job_description=job_description,
                candidate_experience=candidate_experience,
                max_questions=max_questions
            )
            
        
        questions = interviewer.generate_questions()
        if not questions:
            print("Failed to generate interview questions.")
            return {
                "error": True,
                "errorDescription": "Failed to generate interview questions.",
            }
        
        try:
            conn = db_queries.get_db_connection()
            cursor = conn.cursor()
            
            query = "UPDATE candidate_interviews SET questions = %s, status = %s WHERE candidate_interview_id = %s;"
            cursor.execute(query, (json.dumps(questions), 'in_progress', candidate_interview_id))
            conn.commit()
        
        except Exception as e:
            print("Error while updating questions in candidate_interviews.")
            print(f"Error: {e}")
            
            return {
                "error": True,
                "errorDescription": "Error while updating questions in candidate_interviews.",
            }
            
        finally:
            cursor.close()
            conn.close()
            
        
        print("Returing crt details")
        return {
            "message": "Technical interview started successfully.",
            "candidate_interview_id": candidate_interview_id,
            "question_number": 1,
            "total_questions": len(questions),
            "question": questions[0],
            "interview_id": interview_id,
            "error": False,
        }
    
    elif candidate_interview_details["status"] == "in_progress":
        return {"error": True, "errorDescription": "Interview already started"}

    elif candidate_interview_details["status"] == "completed":
        return {"error": True, "errorDescription": "This interview has already been completed."}    
        
        
# progress -> not_started, in_progress, completed