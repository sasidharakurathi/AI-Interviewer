# In this version, we are calling gemini api for generation every single question.
# Advantage: previous question and answer context is provided for next question.
# Disadvantage: More API Calls

import google.generativeai as genai
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv() #loads .env file


GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY, transport='rest')   # transport='rest' suppress warning messages. 
MODEL_FOR_QUESTIONS = os.environ.get("MODEL_FOR_QUESTIONS") # model for question generation
MODEL_FOR_ANALYSIS = os.environ.get("MODEL_FOR_ANALYSIS") # model for candidate answer analysis

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

# CANDIDATE_EXPERIENCE = "Fresher (0-1 years)" 
# CANDIDATE_EXPERIENCE = "Mid-Level (2-5 years)"
CANDIDATE_EXPERIENCE = "Senior (5+ years)"



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
        You are an expert technical hiring manager for a {JOB_ROLE} position.
        Your task is to analyze a candidate's answer to an interview question with precision and objectivity.

        **Context:**
        - **Interview Question:** "{question}"
        - **Candidate's Stated Experience:** "{CANDIDATE_EXPERIENCE}"
        - **Candidate's Answer:** "{answer}"

        ---
        **EVALUATION INSTRUCTIONS:**

        1.  **CALIBRATE FOR EXPERIENCE:** Your evaluation MUST be calibrated to the candidate's experience level.
            - A **Senior** is expected to provide deep, nuanced answers with real-world examples and trade-off analysis.
            - A **Fresher** is expected to provide correct, textbook-level definitions.
            - **An excellent answer for a Fresher might be a poor answer for a Senior.** Adjust your scores accordingly.

        2.  **HANDLE POOR ANSWERS:** If the answer is empty, completely irrelevant (e.g., "I don't know"), or nonsensical, assign a score of 0 for all categories and provide feedback explaining why.

        3.  **SCORING RUBRIC (0-10):**
            - `technical_depth`: 0=Incorrect/No answer. 5=Correct but basic. 10=Deep, nuanced, considers edge cases and trade-offs.
            - `communication_clarity`: 0=Incoherent. 5=Understandable but disorganized. 10=Clear, concise, and well-structured.
            - `problem_solving`: 0=No attempt. 5=Identifies the core concept. 10=Applies the concept to solve a hypothetical problem or discusses practical implications.
            - `job_relevance`: 0=Irrelevant skill. 5=Related to the job description. 10=Directly addresses a key skill required for the role.

        4.  **CONSTRUCTIVE FEEDBACK:** The `feedback` field is mandatory. Provide 2-3 sentences of specific, actionable feedback. Mention what the candidate did well and what they could improve upon.

        5.  **JSON OUTPUT:** Your entire response must be a single, valid JSON object with no extra text or explanations. The required keys are: `technical_depth`, `communication_clarity`, `problem_solving`, `job_relevance`, and `feedback`.
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
        You are an expert technical interviewer conducting an interview for the position of {JOB_ROLE}.
        Your persona is that of a direct, professional, and robotic AI.

        **Primary Goal:**
        Assess the candidate's conceptual knowledge based on the provided job description and their stated experience level.

        **Job Description for Context:**
        {JOB_DESCRIPTION}

        **Candidate's Stated Experience Level:** {CANDIDATE_EXPERIENCE}

        ---
        **CRITICAL INSTRUCTIONS:**

        1.  **ADJUST QUESTION DIFFICULTY (VERY IMPORTANT):** You MUST tailor your questions to the candidate's experience level.
            - **If Fresher (0-1 years):** Ask about fundamental concepts, definitions, and basic syntax. (e.g., "What is the difference between a list and a tuple in Python?").
            - **If Mid-Level (2-5 years):** Ask about practical applications, common libraries, and comparisons. (e.g., "Describe a scenario where using a tuple as a dictionary key is advantageous.").
            - **If Senior (5+ years):** Ask about architectural design, scalability, performance optimization, and strategic trade-offs. (e.g., "Discuss the Global Interpreter Lock (GIL) and its implications for concurrent programming in Python. How would you design a high-concurrency application to mitigate its effects?").

        2.  **QUESTION COUNT:** Ask exactly {MAX_QUESTIONS} questions. Cover a range of topics from the job description (Python, MySQL, Git, Problem-Solving).

        3.  **NO EXPLANATIONS:** Never explain concepts, provide answers, or give hints. If the candidate gives a wrong answer or says "I don't know," your only job is to ask the next question from your list.

        4.  **ROBOTIC TONE:** Be direct and concise. Avoid conversational filler like "Great," "That's interesting," or "Let's move on." Do not refer to previous answers.

        5.  **CONCEPTUAL QUESTIONS ONLY:** Do not ask the candidate to write or debug code.

        6.  **OUTPUT FORMAT:** Your entire response for each turn must ONLY be the text of the interview question. Do not include greetings, question numbers, or any other text.
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
    with open("./output/output.json", "w") as fp:
        json.dump(total_analysis, fp, indent=4)
    
    print("\n Analysis Report Saved.")


if __name__ == "__main__":
    start_ai_interview()