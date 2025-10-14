import google.generativeai as genai
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv() #loads .env file


GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY, transport='rest')   # transport='rest' suppress warning messages. 
MODEL_FOR_QUESTIONS = 'gemini-2.5-flash-lite' # model for question generation
MODEL_FOR_ANALYSIS = 'gemini-2.5-flash' # model for candidate answer analysis

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
    - Hands-on experience with basic MySQL queries, joins, and indexing strategies
    - Exposure to version control systems (preferably Git)
    - Analytical mindset with good problem-solving and algorithmic thinking skills

    What You'll Gain
    - Mentoring by experienced senior developers
    - Opportunities to work on real-world projects and grow your professional portfolio
    - Supportive, collaborative work environment
    - Pathways to advance into full-stack development and beyond
"""

CANDIDATE_EXPERIENCE = "Fresher (0-1 years)" 
# CANDIDATE_EXPERIENCE = "Mid-Level (2-5 years)"
# CANDIDATE_EXPERIENCE = "Senior (5+ years)"



def parse_json_response(response_text):
    """JSON Parser"""
    
    if not response_text or type(response_text) != str:
        return None
    
    try:
        start_index = response_text.find('{')
        end_index = response_text.rfind('}')
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = response_text[start_index : end_index + 1]
            return json.loads(json_str)
        
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        print(f"Response Text: {response_text}")
        
    return None

def analyze_answer(question, answer):
    """Anaylses the candidate answer and generates scores, feedback."""
    
    analysis_prompt = f"""
        You are an expert technical interviewer for a {JOB_ROLE} position.
        Analyze the candidate's answer based on the question asked.

        **Interview Question:** "{question}"
        **Candidate's Answer:** "{answer}"

        Instructions:
        1. Handle Poor Answers: If the answer is empty, irrelevant, or nonsensical, you must assign a score of 0.
        2. Evaluate the clarity and correctness of their conceptual explanation, not their ability to write code.
        3. Your entire response must be a single, valid JSON object with these keys:
           - `technical_depth`: An integer score from 0 to 10.
           - `communication_clarity`: An integer score from 0 to 10.
           - `problem_solving`: An integer score from 0 to 10.
           - `job_relevance`: An integer score from 0 to 10.
           - `feedback`: A mandatory string of 2-3 sentences of constructive feedback.
    """
    
    try:
        model = genai.GenerativeModel(MODEL_FOR_ANALYSIS)
        response = model.generate_content(analysis_prompt)
        raw_response = response.text
    except Exception as e:
        print(f"--- Gemini API Error (Model: {MODEL_FOR_ANALYSIS}) ---")
        print(f"Error: {e}")
        raw_response = None
    
    if raw_response:
        response_dict = parse_json_response(raw_response)
        if response_dict:
            
            # average score
            overall_score = (
                response_dict.get("technical_depth", 0) + 
                response_dict.get("communication_clarity", 0) + 
                response_dict.get("problem_solving", 0) + 
                response_dict.get("job_relevance", 0)
                ) / 4
            
            response_dict["overall"] = round(overall_score, 1)
            
            return response_dict
            
    return {"raw_output": raw_response}



def start_ai_interview():

    total_analysis = []

    system_prompt = f"""
        You are a professional, robotic interviewer for the position of {JOB_ROLE}.
        Your task is to ask questions strictly related to this Job Description:
        
        Job Description:
        {JOB_DESCRIPTION}

        **Interview Rules:**
        
        - **Adjust Difficulty:** The candidate has identified as a **{CANDIDATE_EXPERIENCE}** developer. You MUST tailor the difficulty of your questions accordingly.

        - **CRITICAL: DO NOT EXPLAIN.** Under no circumstances should you provide the correct answer, explain a concept, or offer clarification, even if the candidate is wrong or says "I don't know." Your only function is to ask the next question.

        - **CRITICAL: BE DIRECT AND ROBOTIC.** Do not use any conversational filler or transitions. Do not reference the candidate's previous answers (e.g., "You mentioned X...", "That's a good point..."). Ask the next question directly and coldly, as if you are reading from a script.

        - **NO CODE:** All questions must be conceptual. Do not ask the candidate to 'write code'.
        
        - **OUTPUT FORMAT:** Your entire output, for every turn, MUST be a single technical interview question and nothing else. No greetings, no commentary, no feedback.
    """
    
    model = genai.GenerativeModel(MODEL_FOR_QUESTIONS)
    
    chat_session = model.start_chat(history=[
        {'role': 'user', 'parts': [system_prompt]},
        {'role': 'model', 'parts': ["Understood. I am ready to begin the interview."]}
    ])
    
    print("AI Interviewer: Hello! To begin the interview, please start with a greeting.")
    candidate_answer = input("\nYour Answer: ")

    for _ in range(MAX_QUESTIONS):
        debug = {}
        
        start = datetime.now()        
        response = chat_session.send_message(candidate_answer)
        end = datetime.now()
        
        debug["question_generation_time"] = (end - start).total_seconds()
        
        ai_question = response.text.strip()
        print(f"\nAI Interviewer: {ai_question}")
        
        candidate_answer = input("\nYour Answer: ")
        
        start = datetime.now()
        analysis = analyze_answer(ai_question, candidate_answer)
        end = datetime.now()
        
        analysis_time = (end - start).total_seconds()
        debug["analysis_time"] = analysis_time
        
        analysis["question"] = ai_question
        analysis["candidate_answer"] = candidate_answer
        analysis["debug"] = debug
        total_analysis.append(analysis)
        

    print("\nAI Interviewer: Thank you for your time. That concludes the interview.")
    
    # save total analysis into output.json
    with open("output.json", "w") as fp:
        json.dump(total_analysis, fp, indent=4)
    
    print("\n Analysis Report Saved.")


if __name__ == "__main__":
    start_ai_interview()