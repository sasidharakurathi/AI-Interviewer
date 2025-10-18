# Implemented AI Technical and HR Interviewer using OOP.
# This approach generates all the questions initially.
# And anaylses each and every candidate answer.

import google.generativeai as genai
import json
import os
from datetime import datetime
from dotenv import load_dotenv

load_dotenv() #loads .env file

GOOGLE_API_KEY = os.environ.get("GOOGLE_API_KEY")
genai.configure(api_key=GOOGLE_API_KEY, transport='rest') # transport='rest' suppress warning messages. 


class Interviewer:
    def __init__(self, job_role, job_description, candidate_experience, max_questions=5):
        
        self.model_for_questions = os.environ.get("MODEL_FOR_QUESTIONS") # model for question generation
        self.model_for_analysis = os.environ.get("MODEL_FOR_ANALYSIS") # model for candidate answer analysis
        
        self.job_role = job_role
        self.job_description = job_description
        self.candidate_experience = candidate_experience
        self.max_questions = max_questions
        
        self.questions_model = genai.GenerativeModel(self.model_for_questions) # question generation model object
        self.analysis_model = genai.GenerativeModel(self.model_for_analysis) # analysis model object
        
        self.technical_questions_path = os.environ.get("TECHNICAL_QUESTIONS_PATH")
        self.hr_questions_path = os.environ.get("HR_QUESTIONS_PATH")
    
    def parse_json_response(self, response_text):
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

class TechnicalInterviewer(Interviewer):
    """ AI Technical Interviewer """
    
    def __init__(self, job_role, job_description, candidate_experience, max_questions=5):
        super().__init__(job_role, job_description, candidate_experience, max_questions)
        
    def analyze_answer(self, question, answer):
        """Anaylses the candidate answer and generates scores, feedback."""
        
        analysis_prompt = f"""
            You are an expert technical hiring manager for a {self.job_role} position.
            Your task is to analyze a candidate's answer to an interview question with precision and objectivity.

            **Context:**
            - **Interview Question:** "{question}"
            - **Candidate's Stated Experience:** "{self.candidate_experience}"
            - **Candidate's Answer:** "{answer}"

            ---
            **EVALUATION INSTRUCTIONS:**
            
            1.  **IGNORE TRANSCRIPTION ERRORS:** The candidate's answer is a raw transcript. You MUST IGNORE any lack of punctuation, grammatical errors, or run-on sentences. Focus ONLY on the content and clarity of their spoken ideas.

            2.  **CALIBRATE FOR EXPERIENCE:** Your evaluation MUST be calibrated to the candidate's experience level.
                - A **Senior** is expected to provide deep, nuanced answers with real-world examples and trade-off analysis.
                - A **Fresher** is expected to provide correct, textbook-level definitions.
                - **An excellent answer for a Fresher might be a poor answer for a Senior.** Adjust your scores accordingly.

            3.  **HANDLE POOR ANSWERS:** If the answer is empty, completely irrelevant (e.g., "I don't know"), or nonsensical, assign a score of 0 for all categories and provide feedback explaining why.

            4.  **SCORING RUBRIC (0-10):**
                - `technical_depth`: 0=Incorrect/No answer. 5=Correct but basic. 10=Deep, nuanced, considers edge cases and trade-offs.
                - `communication_clarity`: 0=Incoherent. 5=Understandable but disorganized. 10=Clear, concise, and well-structured.
                - `problem_solving`: 0=No attempt. 5=Identifies the core concept. 10=Applies the concept to solve a hypothetical problem or discusses practical implications.
                - `job_relevance`: 0=Irrelevant skill. 5=Related to the job description. 10=Directly addresses a key skill required for the role.

            5.  **CONSTRUCTIVE FEEDBACK:** The `feedback` field is mandatory. Provide 2-3 sentences of specific, actionable feedback. Mention what the candidate did well and what they could improve upon.

            6.  **JSON OUTPUT:** Your entire response must be a single, valid JSON object with no extra text or explanations. The required keys are: `technical_depth`, `communication_clarity`, `problem_solving`, `job_relevance`, and `feedback`.
        """
        
        try:
            response = self.analysis_model.generate_content(analysis_prompt)
            raw_response = response.text
        except Exception as e:
            print(f"--- Gemini API Error (Model: {self.model_for_analysis}) ---")
            print(f"Error: {e}")
            raw_response = None
        
        if raw_response:
            response_dict = self.parse_json_response(raw_response)
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
    
    def generate_questions(self):
        """ Generates and returns Technical questions based on job description and experience """
        
        question_generation_prompt = f"""
            You are an expert technical interviewer creating a question set for a {self.job_role} interview.

            **Primary Goal:**
            Generate a complete set of interview questions based on the job description and the candidate's experience level.

            **Job Description for Context:**
            {self.job_description}

            **Candidate's Stated Experience Level:** {self.candidate_experience}

            ---
            **CRITICAL INSTRUCTIONS:**

            1.  **GENERATE ALL QUESTIONS:** You must generate exactly {self.max_questions} unique questions in a single response.

            2.  **ENSURE VARIETY:** The questions must be distinct from each other. Avoid common, cliché interview questions. Be creative and focus on practical, thought-provoking scenarios relevant to the job.
            
            3.  **ADJUST QUESTION DIFFICULTY:** You MUST tailor the questions to the candidate's experience level.
                - **If Fresher:** Ask about fundamental concepts, definitions, and basic syntax.
                - **If Mid-Level:** Ask about practical applications, common libraries, and comparisons.
                - **If Senior:** Ask about architectural design, scalability, performance optimization, and strategic trade-offs.

            4.  **TOPIC COVERAGE:** Ensure the questions cover a range of topics from the job description (e.g., Python, MySQL, Git, Problem-Solving).

            5.  **OUTPUT FORMAT (CRITICAL):** Your entire output MUST be a single, valid JSON object.
                - The JSON object should have a single key named "questions".
                - The value of "questions" must be an array of {self.max_questions} strings.
                - Each string in the array is one interview question.
                - Example: {{"questions": ["Question 1?", "Question 2?"]}}
        """

        print("AI Interviewer: Generating interview questions.")
        try:
            
            generation_config = genai.types.GenerationConfig(temperature=0.8)
            
            response = self.questions_model.generate_content(question_generation_prompt, generation_config=generation_config)
            question_data = self.parse_json_response(response.text)
            
            # # --- Debug ---
            # with open(self.technical_questions_path , "w") as fp:
            #     json.dump(question_data, fp, indent=4)
            #     return
            # # --- Debug ---

            if (not question_data) or ("questions" not in question_data) or (not isinstance(question_data["questions"], list)):
                print("\nError: Failed to parse the question list from the API. The response might not be valid JSON.")
                print(f"Raw Response: {response.text}")
                return None

            questions_list = question_data["questions"]
            print(f"Successfully generated {len(questions_list)} questions.")
            
            return questions_list

        except Exception as e:
            print(f"--- Gemini API Error during question generation (Model: {self.model_for_questions}) ---")
            print(f"Error: {e}")
            return None


class HRInterviewer(Interviewer):
    """ AI HR Interviewer """
    
    def __init__(self, job_role, job_description, candidate_experience, max_questions=5):
        super().__init__(job_role, job_description, candidate_experience, max_questions)
        
    def analyze_answer(self, question, answer):
        """Analyzes the candidate's answer for behavioral qualities."""

        analysis_prompt = f"""
            You are an expert HR manager evaluating a candidate's response in a behavioral interview.

            **Context:**
            - **Interview Question:** "{question}"
            - **Candidate's Answer:** "{answer}"

            ---
            **EVALUATION INSTRUCTIONS:**
            
            1.  **IGNORE TRANSCRIPTION ERRORS:** The candidate's answer is a raw transcript. You MUST IGNORE any lack of punctuation, grammatical errors, or run-on sentences. Focus ONLY on the content and clarity of their spoken ideas.

            2.  **Focus on the 'HOW', not the 'WHAT':** Evaluate *how* the candidate structures their answer, their thought process, and the soft skills they demonstrate. A great answer often follows the STAR method (Situation, Task, Action, Result).

            3.  **SCORING RUBRIC (0-10):**
                - `communication_clarity`: 0=Incoherent or very hard to follow. 5=Understandable but could be better structured. 10=Clear, concise, and well-structured.
                - `problem_solving_approach`: 0=No clear approach or avoids the question. 5=Describes a logical process. 10=Demonstrates a thoughtful, structured, and proactive approach to challenges.
                - `teamwork_collaboration`: 0=Shows no evidence of teamwork; uses "I" exclusively in team contexts. 5=Mentions working with others. 10=Highlights specific positive contributions to a team and clearly values collaboration.
                - `alignment_with_values`: 0=Response indicates values that conflict with a professional environment (e.g., blaming others). 5=Neutral response. 10=Demonstrates positive professional values like ownership, curiosity, and integrity.

            4.  **CONSTRUCTIVE FEEDBACK:** The `feedback` field is mandatory. Provide 2-3 sentences of feedback on the answer's structure and the soft skills demonstrated.

            5.  **JSON OUTPUT:** Your entire response MUST be a single, valid JSON object with the required keys.
        """
        try:
            
            response = self.analysis_model.generate_content(analysis_prompt)
            raw_response = response.text
            
        except Exception as e:
            print(f"--- Gemini API Error (Model: {self.model_for_analysis}) ---")
            print(f"Error: {e}")
            raw_response = None
            
        if raw_response:
            response_dict = self.parse_json_response(raw_response)
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
    
    def generate_questions(self):
        """ Generates and returns behavioral and situational questions """
        
        question_generation_prompt = f"""
            You are an expert HR Interviewer creating a question set for a behavioral interview.

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
            
            generation_config = genai.types.GenerationConfig(temperature=0.8)
            
            response = self.questions_model.generate_content(question_generation_prompt, generation_config=generation_config)
            question_data = self.parse_json_response(response.text)
            
            # # --- Debug ---
            # with open(self.hr_questions_path , "w") as fp:
            #     json.dump(question_data, fp, indent=4)
            #     return
            # # --- Debug ---

            if (not question_data) or ("questions" not in question_data) or (not isinstance(question_data["questions"], list)):
                print("\nError: Failed to parse the question list from the API.")
                print(f"Raw Response: {response.text}")
                return None

            questions_list = question_data["questions"]
            print(f"Successfully generated {len(questions_list)} questions.")
            
            return questions_list

        except Exception as e:
            print(f"--- Gemini API Error (Model: {self.model_for_questions}) ---")
            print(f"Error: {e}")
            return None
        
def start_ai_technical_interview(job_role, job_description, candidate_experience, max_questions=5):
    
    technical_output_path = os.environ.get("TECHNICAL_OUTPUT_PATH")
    
    technical_interviewer = TechnicalInterviewer(job_role, job_description, candidate_experience, max_questions)
    questions_list = technical_interviewer.generate_questions()
    
    if not questions_list:
        print("\n Failed to generate questions")
        quit()
    
    total_analysis = []

    for ai_question in questions_list:
        debug = {}
        
        print(f"\nAI Interviewer: {ai_question}")

        candidate_answer = input("\nYour Answer: ")

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

def start_ai_hr_interview(job_role, job_description, candidate_experience, max_questions=5):
    
    hr_output_path = os.environ.get("HR_OUTPUT_PATH")
    
    hr_interviewer = HRInterviewer(job_role, job_description, candidate_experience, max_questions)
    questions_list = hr_interviewer.generate_questions()
    
    total_analysis = []
    for ai_question in questions_list:
        print(f"\nAI Interviewer: {ai_question}")

        candidate_answer = input("\nYour Answer: ")

        start = datetime.now()
        analysis = hr_interviewer.analyze_answer(ai_question, candidate_answer)
        end = datetime.now()

        analysis["question"] = ai_question
        analysis["candidate_answer"] = candidate_answer
        analysis["debug"] = {"analysis_time": (end - start).total_seconds()}
        total_analysis.append(analysis)


    print("\nAI Interviewer: Thank you for your time. That concludes the interview.")

    with open(hr_output_path, "w") as fp:
        json.dump(total_analysis, fp, indent=4)

    print(f"\nHR Analysis Report Saved to {hr_output_path}.")


if __name__ == "__main__":
    
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
        - Hands-on experience with basic MySQL queries, joins, and indexing strategies
        - Exposure to version control systems (preferably Git)
        - Analytical mindset with good problem-solving and algorithmic thinking skills

        What You'll Gain
        - Mentoring by experienced senior developers
        - Opportunities to work on real-world projects and grow your professional portfolio
        - Supportive, collaborative work environment
        - Pathways to advance into full-stack development and beyond
    """

    # JOB_ROLE = "Java Developer"
    # JOB_DESCRIPTION = """
    #     Java Developer
    #     Location: Vijayawada

    #     Employment Type: Full-Time

    #     Job Overview
    #     We are seeking a passionate and detail-oriented Java Developer Fresher to join our software development team. You will work on building scalable and efficient Java-based applications, collaborating with senior developers and learning the full software development lifecycle.

    #     Key Responsibilities
    #     Assist in designing, developing, and maintaining Java applications.
    #     Write clean, efficient, and testable code using Java and related technologies.
    #     Participate in debugging, testing, and documenting software components.
    #     Collaborate with cross-functional teams to deliver high-quality solutions.
    #     Learn and apply best practices in software engineering and agile development.
        
    #     Required Skills
    #     Strong understanding of Core Java, OOP concepts, and basic data structures.
    #     Familiarity with Java frameworks like Spring or Hibernate (academic/project exposure is fine).
    #     Basic knowledge of SQL and relational databases.
    #     Exposure to HTML, CSS, JavaScript is a plus.
    #     Good problem-solving and communication skills.
    #     Ability to work in a team and adapt to new technologies.
        
    #     Educational Qualification
    #     Bachelor's degree in Computer Science, Information Technology, or related field.
    #     Final-year students or recent graduates with relevant academic projects are encouraged to apply.
    # """

    CANDIDATE_EXPERIENCE = "Fresher (0-1 years)" 
    # CANDIDATE_EXPERIENCE = "Mid-Level (2-5 years)"
    # CANDIDATE_EXPERIENCE = "Senior (5+ years)"
    
    print("\nStarting Technical Interview: \n")
    start_ai_technical_interview(JOB_ROLE, JOB_DESCRIPTION, CANDIDATE_EXPERIENCE, MAX_QUESTIONS)
    
    print("\nStarting HR Interview: \n")
    start_ai_hr_interview(JOB_ROLE, JOB_DESCRIPTION, CANDIDATE_EXPERIENCE, MAX_QUESTIONS)
    
    print("\nEnd of Interview...\n")
    
    