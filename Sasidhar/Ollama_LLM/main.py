import ollama   # pip install ollama
import json
from datetime import datetime


MODEL = 'llama3.1:8b-instruct-q4_K_M'
MAX_QUESTIONS = 10
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


def start_ai_interview():
    
    skills_list = extract_skills_from_jd()
    
    # print("--- Skills List ---")
    # print(skills_list)
    
    conversation_context = None
    
    prompt = f"""
        You are a professional interviewer for the position of {JOB_ROLE}.
        The primary skills for this role are: {skills_list}.

        **Interview Rules:**
        
        - **IMPORTANT:** This is a simulated oral interview. All questions must be conceptual and designed to be answered verbally. **Do not ask the candidate to 'write code', 'provide a script', or 'implement a function'.** Instead, ask them to explain concepts, describe their approach, or discuss design patterns. For example, instead of "Write a function...", ask "How would you approach...".

        - Your output must ONLY be the next interview question.
        - Do not provide any commentary, feedback, or greetings after the first question.
        - After the candidate greets you, respond with a welcoming introduction and ONLY your first technical question.
        - After each candidate response, immediately ask the next relevant technical question.
        - If a response is nonsensical, simply move on to the next question.

        Your entire output, for every turn, must be a single technical interview question and nothing else.
    """
    
    # print("\n--- DEGUB ---\n")
    # print(prompt)
    # print("\n--- DEGUB ---\n")
    
    total_analysis = list()
    
    for _ in range(MAX_QUESTIONS):
        debug = dict()
        
        start = datetime.now()
        
        try:
            response = ollama.generate(
                model=MODEL,
                prompt=prompt,
                context=conversation_context,
            )
        except ConnectionError as e:
            print("--- Unable to connect to Ollama. ---")
            print(f"Error: {e}")
            print("---------------------------------------------")
            return
            
        end = datetime.now()
        debug["question_generation_time"] = (end - start).total_seconds()
        
        
        ai_question = response["response"]
        print(f"\nAI Interviewer: {ai_question}")
        
        conversation_context = response["context"]
        
        candidate_answer = input("\nYour Answer: ")
        
        prompt = candidate_answer
        
        start = datetime.now()
        analysis = analyze_answer(ai_question, candidate_answer)
        end = datetime.now()
        
        debug["analysis_time"] = (end - start).total_seconds()
        
        analysis["question"] = ai_question
        analysis["candidate_answer"] = candidate_answer
        analysis["debug"] = debug
        
        total_analysis.append(analysis)
    
    print("\n AI Interviewer: Thank you for your time. That concludes the interview.")
    
    with open("output.json" , "w") as fp:
        json.dump(total_analysis, fp, indent=2)
    
    print("\n Analysis Report Saved.")


def analyze_answer(question, answer):
    
    analysis_prompt = f"""
        You are an expert technical interviewer for a {JOB_ROLE} position.
        Analyze the candidate's answer based on the question asked.

        **Interview Question:**
        "{question}"

        **Candidate's Answer:**
        "{answer}"

        **Instructions:**
        1. **Handle Poor Answers:** If the answer is empty, irrelevant, or nonsensical (e.g., "bla bla"), you **must** assign a score of 0 to all categories. The feedback must be critical, stating the response is unacceptable.
        2.  **IMPORTANT CONTEXT:** The candidate is in a conversational AI interview. They are expected to provide conceptual answers in natural language, **not code snippets.** **You must evaluate the clarity and correctness of their conceptual explanation, not their ability to write code live.** Do not penalize the answer for lacking code, even if the question implies implementation.
        3. **Generate JSON Output:** Your entire response **must be a single, valid JSON object**. It must contain these keys:
           - `technical_depth`: An integer score from 0 to 10.
           - `communication_clarity`: An integer score from 0 to 10.
           - `problem_solving`: An integer score from 0 to 10.
           - `job_relevance`: An integer score from 0 to 10.
           - `feedback`: A mandatory string of 2-3 sentences of constructive feedback.
    """
    
    try:
        response = ollama.generate(
            model=MODEL,
            prompt=analysis_prompt,
        )
    except ConnectionError as e:
        print("--- Unable to connect to Ollama. ---")
        print(f"Error: {e}")
        print("---------------------------------------------")
        return {"Error": str(e)}
    
    response_dict = parse_json_response(response["response"])
    
    if response_dict:
        response_dict["overall"] = round((response_dict["technical_depth"] + response_dict["communication_clarity"] + response_dict["problem_solving"] + response_dict["job_relevance"]) / 4, 1)
    
    return response_dict if response_dict else {"raw_output": response["response"]}

def parse_json_response(response_text):
    try:
        start_index = response_text.find('{')
        
        end_index = response_text.rfind('}')
        
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = response_text[start_index : end_index + 1]
            return json.loads(json_str)
            
    except json.JSONDecodeError as e:
        print(f"JSONDecodeError: {e}")
        print("--- Could not parse the following string: ---")
        print(repr(response_text))
        print("---------------------------------------------")
        
    return None

def extract_skills_from_jd():
    jd_extract_prompt = f"""
        You are a skilled HR professional and AI prompt engineer.

        Given the following job description for a {JOB_ROLE}, identify the main technical skills, tools, concepts, and professional competencies required for this role. Your output must be a clean Python list of strings, with each string describing a single key skill, knowledge area, or requirement. Do not include benefits, company culture, or generic statements—focus on what a candidate should be able to do, know, or demonstrate.

        Job Description:
        \"\"\"
        {JOB_DESCRIPTION}
        \"\"\"

        Return ONLY a valid Python list of skill/topic strings.
    """
    
    try:
        respone = ollama.generate(
            model=MODEL,
            prompt=jd_extract_prompt,
        )
        
        start_index = respone["response"].find('[')
        
        end_index = respone["response"].rfind(']')
        
        if start_index != -1 and end_index != -1 and end_index > start_index:
            json_str = respone["response"][start_index : end_index + 1]
            return json.loads(json_str)
    
    except ConnectionError as e:
        print("--- Unable to connect to Ollama. ---")
        print(f"Error: {e}")
        print("---------------------------------------------")
    
    except Exception as e:
        print(f"Error: {e}")
        print(respone["response"])
        print("---------------------------------------------")
    
    return []
        
        
        


if __name__ == "__main__":
    start_ai_interview()
    
    