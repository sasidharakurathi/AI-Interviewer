import ollama
import json
from datetime import datetime


MODEL = 'llama3.1:8b-instruct-q4_K_M'
JOB_ROLE = "Python Developer"
JOB_DESCRIPTION = """
    Position: Python Developer - Fresher
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

MAX_QUESTIONS = 5

def start_ai_interview():
    
    conversation_context = None
    
    prompt = f"""
        Act as a professional interviewer for the position of {JOB_ROLE}.
        The required skills and job description are as follows:
        \"\"\" 
        {JOB_DESCRIPTION}
        \"\"\"

        Only act as the interviewer—do not write or summarize the conversation at once, and do not explain your questions.

        Start with a welcoming introduction and then ask one clear, specific interview question at a time, strictly relevant to the {JOB_ROLE} role and especially to the required skills and responsibilities listed above.

        Do NOT ask questions that require the candidate to write executable code. Questions must be answerable with an oral explanation, algorithm, concept, example of code in words, or discussion of relevant experience.

        Focus on technical concepts, practical usage, problem-solving, best practices, architecture, OOP, debugging, data structures, frameworks, behavioral skills—and especially on the skills, tools, or technologies mentioned in the job description.

        **Crucially, your response must contain ONLY the next interview question and nothing else. Do not provide feedback or filler—just the next question.**

        Wait for my answer before asking the next question. After I greet you, respond with your greeting and begin the interview by asking only your first question.
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
    You are an expert technical interviewer for the position of {JOB_ROLE}.
    Analyze the following candidate's answer to the interview question.

    Interview Question: {question}
    Candidate's Answer: {answer}

    Instructions:
    - If the answer is empty, very short, irrelevant, only filler/nonsense (examples: "idk", "bla bla", "boo", random text, unrelated comments, or simply says 'I don't know'), you **must** assign 0 for every score: technical_depth, communication_clarity, problem_solving, job_relevance, and overall.
    - For such cases, provide strictly critical feedback: state the response does not meet interview standards, is unacceptable, and should demonstrate relevant knowledge clearly.

    Evaluate the answer according to:
    1. Technical depth (1-10)
    2. Communication clarity (1-10)
    3. Problem-solving approach (1-10)
    4. Relevance to the job role (1-10)
    5. Overall impression (1-10)

    Provide:
    1. The five scores as JSON (with keys: technical_depth, communication_clarity, problem_solving, job_relevance, overall)
    2. 2-3 sentences of personalized constructive feedback explaining the candidate's strengths and possible areas of improvement.

    Return ONLY a valid JSON object like:
    {{
      "technical_depth": X,
      "communication_clarity": X,
      "problem_solving": X,
      "job_relevance": X,
      "overall": X,
      "feedback": "<feedback text>"
    }}
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

if __name__ == "__main__":
    start_ai_interview()
    
    