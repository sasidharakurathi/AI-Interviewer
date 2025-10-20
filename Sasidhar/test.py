import mysql.connector

DB_HOST = "127.0.0.1"
DB_USER = "root"
DB_PASSWORD = "2004"
DB_NAME = "ai_interviewer"

MAX_QUESTIONS = 1
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


conn = mysql.connector.connect(
    host=DB_HOST,
    user=DB_USER,
    password=DB_PASSWORD,
    database=DB_NAME
)

cursor = conn.cursor()

query = """
    INSERT INTO interviews (job_role, job_description, candidate_experience, max_questions)
    VALUES (%s, %s, %s, %s);
"""

cursor.execute(query, (JOB_ROLE, JOB_DESCRIPTION, CANDIDATE_EXPERIENCE, MAX_QUESTIONS))
conn.commit()