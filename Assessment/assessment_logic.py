import re
from collections import defaultdict
from groq import Groq

def extract_assessment_data(assessments):
    metadata = assessments.get("metadata", {})
    role = assessments.get("role", "")  # Fixed key
    job_description = assessments.get("job_description", "")  # Fixed key
    level_of_seniority = assessments.get("level_of_seniority", "")  # Fixed key
    questions = assessments.get("questions", [])
    questions_json = {"questions": questions}
    return metadata, role, job_description, level_of_seniority, questions_json


def unified_assessment(metadata, role, job_description, level_of_seniority, questions_json, api_key, model):
    prompt_for_assessment = f"""
    You are a seasoned and rigorous evaluator tasked with assessing a candidate's responses during a structured interview.
    Your goal is to evaluate technical skills for each question and soft skills collectively across all responses, considering the job role, description, and level of seniority provided.

    Candidate Details:
    - Job Role: {role}
    - Level of Seniority: {level_of_seniority}
    - Job Description: {job_description}

    Questions and Responses:
    {questions_json}

    Evaluation Criteria:

    1. Soft Skills Assessment:
       Consider all the answers and evaluate the soft skills of the interviewee.
       - Soft Skills Identified: List the key soft skills demonstrated or implied across all responses.
       - Soft Skills Score: Assign a collective score out of 5 based on relevance, clarity, and effectiveness shown across all answers.
       - Reasoning: Briefly explain why the soft skills were identified and justify the score assigned.

    2. Technical Assessment (Per Question):
       For each question, provide the following detailed evaluation:
       - Question: The question asked.
       - Technical Skill: The specific technical skill(s) assessed in the question.
       - Score: Assign a score out of 5 based on the following dimensions:
         - Relevance: How directly the answer addresses the question.
         - Clarity: How well the answer is articulated and structured.
         - Depth: How comprehensively the candidate demonstrates knowledge and understanding.
         - Accuracy: Whether the answer contains any incorrect or misleading information.
         - Alignment with Seniority: How well the answer matches expectations for the stated level of seniority.
       - Evaluation Comment: Provide a precise, concise, and constructive comment highlighting strengths and areas for improvement.

      Scoring Guidance:
      - A score of 5 reflects exceptional alignment with expectations for the given criterion and seniority level.
      - A score of 3 reflects satisfactory performance with room for improvement.
      - A score of 0 reflects significant shortcomings.

    Output Format:
    For Soft Skills:
    *Soft Skills Identified*: [List soft skills]
    *Soft Skills Score*: [0-5]
    *Soft Skills Reasoning*: [Reason for score]

    For each question:
    *Question ID*:
    *Question*: [The question asked]
    *Technical Score*: [0-5]
    *Technical Evaluation Comment*: [Comment]

    Instructions:
    - Be strict and unbiased in your evaluation.
    - Provide concise yet thorough reasoning for all scores.
    - DO NOT INCLUDE ADDITIONAL COMMENTARY OR NOTES BEYOND THE OUTPUT FORMAT.
    """

    client = Groq(api_key=api_key)
    llm_response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt_for_assessment}]
    )
    return llm_response.choices[0].message.content

def add_skills_to_assessment_result(assessment_result, assessments):
    # Parse the LLM's response
    result_lines = assessment_result.split("\n")

    # Map questions from assessments by their question text
    questions_by_text = {q["question"]: q for q in assessments["questions"]}

    # Initialize variables for the updated result
    updated_result_lines = []
    current_question_text = None

    # Iterate through the parsed response
    for line in result_lines:
        if line.startswith("*Question*:"):
            # Extract the current question text
            current_question_text = line.split(":")[1].strip().strip("*")
            updated_result_lines.append(line)  # Keep the Question line
        elif current_question_text and line.startswith("*Technical Score*:"):
            # Add the skill after the Question line
            skill = questions_by_text.get(current_question_text, {}).get("skill", "Unknown Skill")
            updated_result_lines.append(f"*Skill*: {skill}")  # Add skill after question
            updated_result_lines.append(line)  # Keep the rest of the line
        else:
            updated_result_lines.append(line)  # Keep other lines as is

    # Join the updated lines back into a single string
    updated_assessment_result = "\n".join(updated_result_lines)
    return updated_assessment_result


def parse_assessment_result(data):
    soft_skills_match = re.search(r"\*Soft Skills Identified\*: (.+?)\n\*Soft Skills Score\*: (\d+)\n\*Soft Skills Reasoning\*: (.+)", data)
    
    if soft_skills_match:
        soft_skills_identified = soft_skills_match.group(1)
        soft_skills_score = int(soft_skills_match.group(2))
        soft_skills_reasoning = soft_skills_match.group(3)
    else:
        soft_skills_identified = "N/A"
        soft_skills_score = 0
        soft_skills_reasoning = "N/A"

    questions = re.findall(
        r"\*Question\*: (.+?)\n\*Skill\*: (.+?)\n\*Technical Score\*: (\d+)\n\*Technical Evaluation Comment\*: (.+?)(?:\n|$)",
        data
    )

    skills_scores = defaultdict(lambda: {"total": 0, "count": 0, "max": 0})
    for _, skill, score, _ in questions:
        score = int(score)
        skills_scores[skill]["total"] += score
        skills_scores[skill]["count"] += 1
        skills_scores[skill]["max"] += 5

    skill_summary = {skill: {"total": scores["total"], "max": scores["max"]} for skill, scores in skills_scores.items()}

    return soft_skills_identified, soft_skills_score, soft_skills_reasoning, questions, skill_summary

def calculate_candidate_score(questions):
    return sum(int(score) for _, _, score, _ in questions)

def calculate_total_possible_score(questions):
    return len(questions) * 5

def skill_wise_assessment(questions, skill_scores, api_key, model):
    prompt_for_skill_wise_assessment = f"""
    You are an expert evaluator tasked with assessing the candidate's performance based on the following data.

    Your goal is to provide:
      1. Skill-wise scores: Evaluate each skill based on the scores provided.
      2. Strengths: Highlight the candidate's general strengths for each skill.
      3. Areas of Improvement: Identify the general areas where the candidate needs to improve for each skill.

      Technical Skills and Evaluations:
      {questions} (this contains the question, skill, score out of 5, evaluation comment)
      {skill_scores} (these contain the total score for each skill and the max possible score)

      Output Format:
      For each skill:
      -*Skill*: [Skill Name]
      -*Total Score*: [Total score for the skill]
      -*Strengths*: [List the strengths]
      -*Areas of Improvement*: [List the improvement areas]

      Instructions:
      -Based on the comments and scores, identify strengths and areas of improvement for each skill.
      -DO NOT INCLUDE ADDITIONAL COMMENTARY OR NOTES BEYOND THE OUTPUT FORMAT.
    """
    client = Groq(api_key=api_key)
    llm_response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt_for_skill_wise_assessment}]
    )
    return llm_response.choices[0].message.content

def end_assessment(result, soft_skills_identified, soft_skills_score, candidate_score, soft_skills_reasoning, api_key, model):
    prompt_for_overall_assessment = f"""
    Based on the following input, generate a detailed overall assessment that highlights the strengths and areas of improvement.

    Input:
    	1.Technical skills data: {result}
    		- this contains the skill, total score scored by interviewee in that skill, strengths and weaknesses of that skill
    	2.Soft Skills data:
    		soft skills identified: {soft_skills_identified}
    		soft skills score: {soft_skills_score}
    		soft skills reasoning: {soft_skills_reasoning}
    	3.Candidate total score for technical skills: {candidate_score}

    Consider the input data. Provide a concise and structured response with the following sections:
    - Overall Strengths: A summary of key strengths derived from the provided scores and reasoning.
    - Areas of Improvement: A summary of areas that require attention.
    - Suggestions: Provide actionable suggestions where possible for technical and soft skills.

    Output Format:
    *Strengths*:
    *Areas of Improvement*:

    Instructions:
    - Ensure the assessment is professional and easy to interpret.
    - DO NOT INCLUDE ADDITIONAL COMMENTARY OR NOTES BEYOND THE OUTPUT FORMAT.
    """

    client = Groq(api_key=api_key)
    llm_response = client.chat.completions.create(
        model=model,
        messages=[{"role": "system", "content": prompt_for_overall_assessment}]
    )

    return llm_response.choices[0].message.content