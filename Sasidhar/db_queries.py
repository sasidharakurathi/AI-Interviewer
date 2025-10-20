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
    
    cursor.execute("SELECT * FROM answers WHERE interview_id = %s ORDER BY id ASC", (interview_id, ))
    rows = cursor.fetchall()
    
    analysis = []
    
    for row in rows:
        analysis.append({
            "interview_id": row[1],
            "interview_type": row[2],
            "question": row[3],
            "answer": row[4],
            "analysis": json.loads(row[5]),
        })
    
    # print(f"{analysis = }")
    
    return analysis
    
    
# get_candidate_interview_analysis("4e12515d-470f-4296-a6ba-15cd58b22d6e")

    
    
    
