import re
from collections import defaultdict
from groq import Groq
from logger.logger_config import logger
import json

def extract_assessment_data(assessments):
    try:

        print(f"type: {type(assessments)}")
        message = assessments.get('Message',None)
        print(f"message: {message}")
        if not message:
            return None, None, None, None, None

        parsed_message = json.loads(message)
        
        metadata = parsed_message['metadata']

        # print("Metadata:", metadata)

        role = parsed_message["role"]
        # print("Role:", role)

        job_description = parsed_message["job_description"]
        # print("Job Description:", job_description)

        level_of_seniority = parsed_message["level_of_seniority"]
        # print("Level of Seniority:", level_of_seniority)

        questions = parsed_message["questions"]
        # print("Questions:", questions)

        questions_json = {"questions": questions}
        # print("Questions JSON:", questions_json)


        # Check if any essential data is None
        if any(x is None for x in [metadata, role, job_description, level_of_seniority, questions_json]):
            logger.error("Missing essential assessment data.")
            return None, None, None, None, None

        logger.info("Successfully extracted assessment data.")
        return metadata, role, job_description, level_of_seniority, questions_json
    except Exception as e:
        logger.error(f"Failed to extract assessment data: {e}")
        return None, None, None, None, None


def unified_assessment(metadata, role, job_description, level_of_seniority, questions_json, api_key, model):
    try:
        if any(x is None for x in [metadata, role, job_description, level_of_seniority, questions_json]):
            logger.error("Missing essential data for unified assessment.")
            return None

        print("Metadata:", metadata)
        print("Role:", role)
        print("Job Description:", job_description)
        print("Level of Seniority:", level_of_seniority)
        print("Questions JSON:", questions_json)

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
            *Skill*: [The skill mentioned for the question]
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
        # logger.info("Unified assessment completed successfully.")
        return llm_response.choices[0].message.content if llm_response else None
    except Exception as e:
        logger.error(f"Failed to generate unified assessment: {e}")
        return None


# def add_skills_to_assessment_result(assessment_result, assessments):
#     try:
#         assessment_result = assessment_result
#         assessments = assessments

#         if assessment_result is None or assessments is None:
#             logger.error("Invalid data received for skill addition.")
#             return None

#         print("inside add skills to assessment result, assessment_result :: ",assessment_result)
#         print("inside add skills to assessment result, assessments :: ", assessments)
#         result_lines = assessment_result.split("\n")
#         questions_by_text = {q["question"]: q for q in assessments["questions"]}

#         updated_result_lines = []
#         current_question_text = None

#         for line in result_lines:
#             if line.startswith("*Question*:"):
#                 current_question_text = line.split(":")[1].strip().strip("*")
#                 updated_result_lines.append(line)
#             elif current_question_text and line.startswith("*Technical Score*:"):
#                 skill = questions_by_text.get(current_question_text, {}).get("skill", "Unknown Skill")
#                 updated_result_lines.append(f"*Skill*: {skill}")
#                 updated_result_lines.append(line)
#             else:
#                 updated_result_lines.append(line)

#         return "\n".join(updated_result_lines)
#     except Exception as e:
#         logger.error(f"Failed to add skills to assessment result: {e}")
#         return None


def parse_assessment_result(data):
    try:
        if data is None:
            logger.error("No assessment result data to parse.")
            return None, None, None, None, None

        soft_skills_match = re.search(
            r"\*Soft Skills Identified\*: (.+?)\n\*Soft Skills Score\*: (\d+)\n\*Soft Skills Reasoning\*: (.+)", data
        )
        soft_skills_identified = soft_skills_match.group(1) if soft_skills_match else "N/A"
        soft_skills_score = int(soft_skills_match.group(2)) if soft_skills_match else 0
        soft_skills_reasoning = soft_skills_match.group(3) if soft_skills_match else "N/A"

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

        logger.info("Assessment result parsed successfully.")
        return soft_skills_identified, soft_skills_score, soft_skills_reasoning, questions, skill_summary
    except Exception as e:
        logger.error(f"Failed to parse assessment result: {e}")
        return None, None, None, None, None


def calculate_candidate_score(questions):
    try:
        if not questions:
            logger.error("No questions available to calculate candidate score.")
            return None

        score = sum(int(score) for _, _, score, _ in questions)
        logger.info(f"Candidate score calculated: {score}")
        return score
    except Exception as e:
        logger.error(f"Failed to calculate candidate score: {e}")
        return None


def calculate_total_possible_score(questions):
    try:
        if not questions:
            logger.error("No questions available to calculate total possible score.")
            return None

        total_score = len(questions) * 5
        logger.info(f"Total possible score calculated: {total_score}")
        return total_score
    except Exception as e:
        logger.error(f"Failed to calculate total possible score: {e}")
        return None


def skill_wise_assessment(questions, skill_scores, api_key, model):
    try:
        if not questions or not skill_scores:
            logger.error("Missing questions or skill scores for skill-wise assessment.")
            return None

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
        logger.info("Skill-wise assessment completed successfully.")
        return llm_response.choices[0].message.content if llm_response else None
    except Exception as e:
        logger.error(f"Failed to complete skill-wise assessment: {e}")
        return None


def end_assessment(result, soft_skills_identified, soft_skills_score, candidate_score, soft_skills_reasoning, api_key, model):
    try:
        if any(x is None for x in [result, soft_skills_identified, soft_skills_score, candidate_score, soft_skills_reasoning]):
            logger.error("Invalid data received for overall assessment.")
            return None

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
        logger.info("Overall assessment generated successfully.")
        return llm_response.choices[0].message.content if llm_response else None
    except Exception as e:
        logger.error(f"Failed to generate overall assessment: {e}")
        return None














# import re
# from collections import defaultdict
# from groq import Groq
# from logger.logger_config import logger

# def extract_assessment_data(assessments):
#     try:
#         metadata = assessments.get("metadata", {})
#         role = assessments.get("role", "")
#         job_description = assessments.get("job_description", "")
#         level_of_seniority = assessments.get("level_of_seniority", "")
#         questions = assessments.get("questions", [])
#         questions_json = {"questions": questions}

#         logger.info("Successfully extracted assessment data.")
#         return metadata, role, job_description, level_of_seniority, questions_json
#     except Exception as e:
#         logger.error(f"Failed to extract assessment data: {e}")
#         raise

# def unified_assessment(metadata, role, job_description, level_of_seniority, questions_json, api_key, model):
#     try:
#         prompt_for_assessment = f"""
#             You are a seasoned and rigorous evaluator tasked with assessing a candidate's responses during a structured interview.
#             Your goal is to evaluate technical skills for each question and soft skills collectively across all responses, considering the job role, description, and level of seniority provided.

#             Candidate Details:
#             - Job Role: {role}
#             - Level of Seniority: {level_of_seniority}
#             - Job Description: {job_description}

#             Questions and Responses:
#             {questions_json}

#             Evaluation Criteria:

#             1. Soft Skills Assessment:
#             Consider all the answers and evaluate the soft skills of the interviewee.
#             - Soft Skills Identified: List the key soft skills demonstrated or implied across all responses.
#             - Soft Skills Score: Assign a collective score out of 5 based on relevance, clarity, and effectiveness shown across all answers.
#             - Reasoning: Briefly explain why the soft skills were identified and justify the score assigned.

#             2. Technical Assessment (Per Question):
#             For each question, provide the following detailed evaluation:
#             - Question: The question asked.
#             - Technical Skill: The specific technical skill(s) assessed in the question.
#             - Score: Assign a score out of 5 based on the following dimensions:
#                 - Relevance: How directly the answer addresses the question.
#                 - Clarity: How well the answer is articulated and structured.
#                 - Depth: How comprehensively the candidate demonstrates knowledge and understanding.
#                 - Accuracy: Whether the answer contains any incorrect or misleading information.
#                 - Alignment with Seniority: How well the answer matches expectations for the stated level of seniority.
#             - Evaluation Comment: Provide a precise, concise, and constructive comment highlighting strengths and areas for improvement.

#             Scoring Guidance:
#             - A score of 5 reflects exceptional alignment with expectations for the given criterion and seniority level.
#             - A score of 3 reflects satisfactory performance with room for improvement.
#             - A score of 0 reflects significant shortcomings.

#             Output Format:
#             For Soft Skills:
#             *Soft Skills Identified*: [List soft skills]
#             *Soft Skills Score*: [0-5]
#             *Soft Skills Reasoning*: [Reason for score]

#             For each question:
#             *Question ID*:
#             *Question*: [The question asked]
#             *Technical Score*: [0-5]
#             *Technical Evaluation Comment*: [Comment]

#             Instructions:
#             - Be strict and unbiased in your evaluation.
#             - Provide concise yet thorough reasoning for all scores.
#             - DO NOT INCLUDE ADDITIONAL COMMENTARY OR NOTES BEYOND THE OUTPUT FORMAT.
#             """ # For brevity, prompt content is the same as before.

#         client = Groq(api_key=api_key)
#         llm_response = client.chat.completions.create(
#             model=model,
#             messages=[{"role": "system", "content": prompt_for_assessment}]
#         )
#         logger.info("Unified assessment completed successfully.")
#         return llm_response.choices[0].message.content
#     except Exception as e:
#         logger.error(f"Failed to generate unified assessment: {e}")
#         raise

# def add_skills_to_assessment_result(assessment_result, assessments):
#     try:
#         result_lines = assessment_result.split("\n")
#         questions_by_text = {q["question"]: q for q in assessments["questions"]}

#         updated_result_lines = []
#         current_question_text = None

#         for line in result_lines:
#             if line.startswith("*Question*:"):
#                 current_question_text = line.split(":")[1].strip().strip("*")
#                 updated_result_lines.append(line)
#             elif current_question_text and line.startswith("*Technical Score*:"):
#                 skill = questions_by_text.get(current_question_text, {}).get("skill", "Unknown Skill")
#                 updated_result_lines.append(f"*Skill*: {skill}")
#                 updated_result_lines.append(line)
#             else:
#                 updated_result_lines.append(line)

#         logger.info("Skills successfully added to assessment result.")
#         return "\n".join(updated_result_lines)
#     except Exception as e:
#         logger.error(f"Failed to add skills to assessment result: {e}")
#         raise

# def parse_assessment_result(data):
#     try:
#         soft_skills_match = re.search(
#             r"\*Soft Skills Identified\*: (.+?)\n\*Soft Skills Score\*: (\d+)\n\*Soft Skills Reasoning\*: (.+)", data
#         )
#         soft_skills_identified = soft_skills_match.group(1) if soft_skills_match else "N/A"
#         soft_skills_score = int(soft_skills_match.group(2)) if soft_skills_match else 0
#         soft_skills_reasoning = soft_skills_match.group(3) if soft_skills_match else "N/A"

#         questions = re.findall(
#             r"\*Question\*: (.+?)\n\*Skill\*: (.+?)\n\*Technical Score\*: (\d+)\n\*Technical Evaluation Comment\*: (.+?)(?:\n|$)",
#             data
#         )

#         skills_scores = defaultdict(lambda: {"total": 0, "count": 0, "max": 0})
#         for _, skill, score, _ in questions:
#             score = int(score)
#             skills_scores[skill]["total"] += score
#             skills_scores[skill]["count"] += 1
#             skills_scores[skill]["max"] += 5

#         skill_summary = {skill: {"total": scores["total"], "max": scores["max"]} for skill, scores in skills_scores.items()}

#         logger.info("Assessment result parsed successfully.")
#         return soft_skills_identified, soft_skills_score, soft_skills_reasoning, questions, skill_summary
#     except Exception as e:
#         logger.error(f"Failed to parse assessment result: {e}")
#         raise

# def calculate_candidate_score(questions):
#     try:
#         score = sum(int(score) for _, _, score, _ in questions)
#         logger.info(f"Candidate score calculated: {score}")
#         return score
#     except Exception as e:
#         logger.error(f"Failed to calculate candidate score: {e}")
#         raise

# def calculate_total_possible_score(questions):
#     try:
#         total_score = len(questions) * 5
#         logger.info(f"Total possible score calculated: {total_score}")
#         return total_score
#     except Exception as e:
#         logger.error(f"Failed to calculate total possible score: {e}")
#         raise

# def skill_wise_assessment(questions, skill_scores, api_key, model):
#     try:
#         prompt_for_skill_wise_assessment = f"""
#             You are an expert evaluator tasked with assessing the candidate's performance based on the following data.

#             Your goal is to provide:
#             1. Skill-wise scores: Evaluate each skill based on the scores provided.
#             2. Strengths: Highlight the candidate's general strengths for each skill.
#             3. Areas of Improvement: Identify the general areas where the candidate needs to improve for each skill.

#             Technical Skills and Evaluations:
#             {questions} (this contains the question, skill, score out of 5, evaluation comment)
#             {skill_scores} (these contain the total score for each skill and the max possible score)

#             Output Format:
#             For each skill:
#             -*Skill*: [Skill Name]
#             -*Total Score*: [Total score for the skill]
#             -*Strengths*: [List the strengths]
#             -*Areas of Improvement*: [List the improvement areas]

#             Instructions:
#             -Based on the comments and scores, identify strengths and areas of improvement for each skill.
#             -DO NOT INCLUDE ADDITIONAL COMMENTARY OR NOTES BEYOND THE OUTPUT FORMAT.
#             """

#         client = Groq(api_key=api_key)
#         llm_response = client.chat.completions.create(
#             model=model,
#             messages=[{"role": "system", "content": prompt_for_skill_wise_assessment}]
#         )
#         logger.info("Skill-wise assessment completed successfully.")
#         return llm_response.choices[0].message.content
#     except Exception as e:
#         logger.error(f"Failed to complete skill-wise assessment: {e}")
#         raise

# def end_assessment(result, soft_skills_identified, soft_skills_score, candidate_score, soft_skills_reasoning, api_key, model):
#     try:
#         prompt_for_overall_assessment = f"""
#             Based on the following input, generate a detailed overall assessment that highlights the strengths and areas of improvement.

#             Input:
#                 1.Technical skills data: {result}
#                     - this contains the skill, total score scored by interviewee in that skill, strengths and weaknesses of that skill
#                 2.Soft Skills data:
#                     soft skills identified: {soft_skills_identified}
#                     soft skills score: {soft_skills_score}
#                     soft skills reasoning: {soft_skills_reasoning}
#                 3.Candidate total score for technical skills: {candidate_score}

#             Consider the input data. Provide a concise and structured response with the following sections:
#             - Overall Strengths: A summary of key strengths derived from the provided scores and reasoning.
#             - Areas of Improvement: A summary of areas that require attention.
#             - Suggestions: Provide actionable suggestions where possible for technical and soft skills.

#             Output Format:
#             *Strengths*:
#             *Areas of Improvement*:

#             Instructions:
#             - Ensure the assessment is professional and easy to interpret.
#             - DO NOT INCLUDE ADDITIONAL COMMENTARY OR NOTES BEYOND THE OUTPUT FORMAT.
#             """

#         client = Groq(api_key=api_key)
#         llm_response = client.chat.completions.create(
#             model=model,
#             messages=[{"role": "system", "content": prompt_for_overall_assessment}]
#         )
#         logger.info("Overall assessment generated successfully.")
#         return llm_response.choices[0].message.content
#     except Exception as e:
#         logger.error(f"Failed to generate overall assessment: {e}")
#         raise