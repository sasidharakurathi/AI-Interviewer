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


def analyze_hr_answer(question, answer):
    """Analyzes the candidate's answer for behavioral qualities."""

    analysis_prompt = f"""
        You are an expert HR manager evaluating a candidate's response in a behavioral interview.

        **Context:**
        - **Interview Question:** "{question}"
        - **Candidate's Answer:** "{answer}"

        ---
        **EVALUATION INSTRUCTIONS:**

        1.  **Focus on the 'HOW', not the 'WHAT':** Evaluate *how* the candidate structures their answer, their thought process, and the soft skills they demonstrate. A great answer often follows the STAR method (Situation, Task, Action, Result).

        2.  **SCORING RUBRIC (0-10):**
            - `communication_clarity`: 0=Incoherent or very hard to follow. 5=Understandable but could be better structured. 10=Clear, concise, and well-structured.
            - `problem_solving_approach`: 0=No clear approach or avoids the question. 5=Describes a logical process. 10=Demonstrates a thoughtful, structured, and proactive approach to challenges.
            - `teamwork_collaboration`: 0=Shows no evidence of teamwork; uses "I" exclusively in team contexts. 5=Mentions working with others. 10=Highlights specific positive contributions to a team and clearly values collaboration.
            - `alignment_with_values`: 0=Response indicates values that conflict with a professional environment (e.g., blaming others). 5=Neutral response. 10=Demonstrates positive professional values like ownership, curiosity, and integrity.

        3.  **CONSTRUCTIVE FEEDBACK:** The `feedback` field is mandatory. Provide 2-3 sentences of feedback on the answer's structure and the soft skills demonstrated.

        4.  **JSON OUTPUT:** Your entire response MUST be a single, valid JSON object with the required keys.
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
            overall_score = (
                response_dict.get("communication_clarity", 0) +
                response_dict.get("problem_solving_approach", 0) +
                response_dict.get("teamwork_collaboration", 0) +
                response_dict.get("alignment_with_values", 0)
                ) / 4
            response_dict["overall"] = round(overall_score, 1)
            return response_dict
            
    return {"raw_output": raw_response}

def start_ai_hr_interview():

    question_generation_prompt = f"""
        You are an expert HR Interviewer creating a question set for a first-round behavioral interview.

        **Primary Goal:**
        Generate a set of behavioral and situational questions to assess a candidate's soft skills, problem-solving approach, and cultural fit for a {JOB_ROLE} position.

        **Candidate's Experience Level:** {CANDIDATE_EXPERIENCE}

        ---
        **CRITICAL INSTRUCTIONS:**

        1.  **GENERATE ALL QUESTIONS:** You must generate exactly {MAX_QUESTIONS} unique questions.

        2.  **QUESTION FOCUS:** The questions MUST be behavioral or situational. Do NOT ask technical questions. Focus on these areas:
            - **Teamwork & Collaboration:** "Describe a time you had a conflict with a coworker..."
            - **Problem-Solving & Adaptability:** "Tell me about a time you faced an unexpected challenge..."
            - **Motivation & Work Ethic:** "What motivates you to do your best work?"
            - **Ownership & Initiative:** "Describe a project you initiated yourself."

        3.  **ADJUST FOR EXPERIENCE:** For a **Fresher**, you can ask about academic projects or hypothetical situations. For an **experienced** candidate, ask for specific examples from their past jobs.

        4.  **OUTPUT FORMAT (CRITICAL):** Your entire output MUST be a single, valid JSON object with a single key "questions", which contains an array of {MAX_QUESTIONS} strings.
    """

    print("AI Interviewer: Generating interview questions...")
    try:
        model = genai.GenerativeModel(MODEL_FOR_QUESTIONS)
        response = model.generate_content(question_generation_prompt)
        question_data = parse_json_response(response.text)
        
        # # --- Debug ---
        # with open("./output/hr_questions.json" , "w") as fp:
        #     json.dump(question_data, fp, indent=4)
        #     return
        # # --- Debug ---

        if (not question_data) or ("questions" not in question_data) or (not isinstance(question_data["questions"], list)):
            print("\nError: Failed to parse the question list from the API.")
            print(f"Raw Response: {response.text}")
            return

        questions_list = question_data["questions"]
        print(f"Successfully generated {len(questions_list)} questions. The interview will now begin.")

    except Exception as e:
        print(f"--- Gemini API Error (Model: {MODEL_FOR_QUESTIONS}) ---")
        print(f"Error: {e}")
        return

    total_analysis = []
    for ai_question in questions_list:
        print(f"\nAI Interviewer: {ai_question}")

        candidate_answer = input("\nYour Answer: ")

        start = datetime.now()
        analysis = analyze_hr_answer(ai_question, candidate_answer)
        end = datetime.now()

        analysis["question"] = ai_question
        analysis["candidate_answer"] = candidate_answer
        analysis["debug"] = {"analysis_time": (end - start).total_seconds()}
        total_analysis.append(analysis)


    print("\nAI Interviewer: Thank you for your time. That concludes the interview.")

    with open("./output/hr_output.json", "w") as fp:
        json.dump(total_analysis, fp, indent=4)

    print("\nHR Analysis Report Saved to hr_output.json.")


if __name__ == "__main__":
    start_ai_hr_interview()