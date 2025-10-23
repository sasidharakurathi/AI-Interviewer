import mysql.connector
from dotenv import load_dotenv
import os
import json

load_dotenv()

def get_db_connection():
    try:
        conn = mysql.connector.connect(
            host=os.environ.get("DB_HOST"),
            user=os.environ.get("DB_USER"),
            password=os.environ.get("DB_PASSWORD"),
            database=os.environ.get("DB_NAME")
        )
        return conn
    except mysql.connector.Error as err:
        print(f"Database connection error: {err}")
        
def get_interviews(id=None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if id is None:
        query = "SELECT * FROM interviews"
        cursor.execute(query)
    else:
        query = """
            SELECT * FROM interviews WHERE id = %s;
        """
        cursor.execute(query, (id, ))
    
    rows = cursor.fetchall()
    
    interviews = [
        {
            "id": row[0],
            "job_role": row[1],
            "job_description": row[2],
            "max_questions": row[3],
        }
        
        for row in rows
    ]
    
    return interviews


def get_candidate_interview_analysis(interview_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM answers WHERE candidate_interview_id = %s ORDER BY id ASC", (interview_id, ))
    rows = cursor.fetchall()
    
    analysis = [
        {
            "interview_id": row[1],
            "interview_type": row[2],
            "question": row[3],
            "answer": row[4],
            "analysis": json.loads(row[5]),
        }
        for row in rows
    ]
    
    # print(f"{analysis = }")
    
    return analysis

def get_candidate_interview_details(candidate_interview_id):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM candidate_interviews WHERE candidate_interview_id = %s;"
    
    cursor.execute(query, (candidate_interview_id, ))
    candidate_interview_row = cursor.fetchone()
    
    
    if not candidate_interview_row:
        return None
    
    query = "SELECT * FROM interviews WHERE job_role = %s;"
    cursor.execute(query, (candidate_interview_row[3], )) # job_role
    interview_details = cursor.fetchone()
    
    if not interview_details:
        return None
    
    details = {
        "candidate_interview_id": candidate_interview_row[1],
        "interview_type": candidate_interview_row[2],
        "job_role": candidate_interview_row[3],
        "candidate_experience": candidate_interview_row[4],
        "questions": json.loads(candidate_interview_row[5]),
        "status": candidate_interview_row[6],
        "current_question_index": candidate_interview_row[7],
        
        "job_description": interview_details[2],
        "max_questions": interview_details[3],
        "interview_id": interview_details[0],
    }
    
    return details
    
    
# result = get_candidate_interview_details("dd4bb390-fae3-495f-b5f0-b7f97a8998c1")
# print(result)
    
    
    
