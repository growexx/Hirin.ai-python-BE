import re
from collections import defaultdict
from logger.logger_config import logger
import json

def extract_assessment_data(assessments):
    try:

        # logger.info(f"type: {type(assessments)}")
        message = assessments.get('Message',None)
        logger.info(f"message: {message}")
        if not message:
            return None, None, None, None, None

        parsed_message = json.loads(message)
        
        metadata = parsed_message['metadata']
        logger.info(f"Metadata: {metadata}")

        role = parsed_message["role"]
        logger.info(f"Role: {role}")

        job_description = parsed_message["job_description"]
        logger.info(f"Job Description: {job_description}")

        questions = parsed_message["questions"]
        logger.info(f"Questions: {questions}")

        questions_json = {"questions": questions}
        logger.info(f"Questions JSON: {questions_json}")

        # Check if any essential data is None
        if any(x is None for x in [metadata, role, job_description, questions_json]):
            logger.error("Missing essential assessment data.")
            return None, None, None, None

        logger.info("Successfully extracted assessment data.")
        return metadata, role, job_description, questions_json
    except Exception as e:
        logger.error(f"Failed to extract assessment data: {e}")
        return None, None, None, None

def question_wise_output_format():
    try:
        output_json_format_question_wise = '''
            {
            "softSkillsAssessment": [
                {
                "softSkill": "[Soft skill name]",
                "score": [0-10],
                "justification": "[Reason for the score]"
                },
            ],
            "overallSoftSkills": {
                "strengths": [LIST OF STRENGTHS],
                "areasOfImprovement": [LIST OF AREAS OF IMPROVEMENT],
                "recommendations": [LIST OF RECOMMENDATIONS]
            },
            "technicalAssessment": [
                {
                "questionID": [Question ID],
                "question": [The question asked],
                "skill": [The skill mentioned for the question],
                "skillType": [Must-have or Good-to-have],
                "technicalScore": [0-10],
                "technicalEvaluationComment": [Evaluation Comment]
                },
            ]
            }
            '''
        return output_json_format_question_wise
    except Exception as e:
        logger.error(f"Failed: {e}")
        return None

def extract_soft_skills(job_description):
    try:
        # Define regex patterns to extract Must-Have and Good-to-Have soft skills
        must_have_pattern = r"Must-Have Soft Skills:\s*(.*?)\n\s*(Good-to-Have|$)"
        good_to_have_pattern = r"Good-to-Have Soft Skills:\s*(.*?)(?:\n|$)"

        # Extract Must-Have Soft Skills
        must_have_match = re.search(must_have_pattern, job_description, re.DOTALL | re.IGNORECASE)
        must_have_soft_skills = (
            [skill.strip() for skill in must_have_match.group(1).split("\n") if skill.strip()]
            if must_have_match
            else []
        )

        # Extract Good-to-Have Soft Skills
        good_to_have_match = re.search(good_to_have_pattern, job_description, re.DOTALL | re.IGNORECASE)
        good_to_have_soft_skills = (
            [skill.strip() for skill in good_to_have_match.group(1).split("\n") if skill.strip()]
            if good_to_have_match
            else []
        )

        # Structure the result
        soft_skills = {
            "must_have": must_have_soft_skills,
            "good_to_have": good_to_have_soft_skills,
        }
        return soft_skills
    except Exception as e:
        return {"error:":e, "must_have": [], "good_to_have": []}

def unified_assessment(metadata, role, job_description, questions_json, soft_skills, output_json_format_question_wise, brt, model_id):
    try:
        # logger.info("inside unified assessment")
        if any(x is None for x in [metadata, role, job_description, questions_json, soft_skills, output_json_format_question_wise]):
            logger.error("inside Missing essential data for unified assessment.")
            return None
        
        # logger.info("after if statement in unified assessment")

        # Construct the prompt for assessment
        prompt_for_assessment = f"""
            You are a seasoned and rigorous evaluator tasked with assessing a candidate's responses during a structured interview.
            Your goal is to evaluate:
            1. Technical skills for each question and soft skills collectively across all responses, considering the job role, description, and level of seniority from the job description and input variables provided.
            2. Identify and assess specific soft skills from the job description and assign individual scores to each identified soft skill.

            ---

            ### Candidate Details:
            - Job Role: {role}
            - Job Description: {job_description}

            Soft Skills from Job Description:
            {soft_skills}

            Questions and Responses:
            {questions_json}

            ---

            ### Evaluation Criteria:

            i] Soft Skills Assessment:
            1. From the {soft_skills} provided, identify the main soft skills and evaluate each soft skill identified.
            2. For each soft skill, provide:
                - Identified Soft Skill: The soft skill in 2 words.
                - Soft Skill Score: Assign a score out of 10 based on the relevance and clarity of the candidate's answers in demonstrating this skill.
                - Justification: Briefly explain why the score was assigned, referring to the responses where applicable. Do not talk about question numbers.

            ii] Overall Soft Skills Evaluation:
            - Strengths: Summarize the candidate's key strengths based on the identified soft skills.
            - Areas of Improvement: Highlight areas where the candidate needs to improve with regard to the identified soft skills.
            - Recommendation: Actionable items for the recruiter to assess the candidate (in the next round or for training purposes).
            Note: Provide 2 points for each section, but allow up to 3 points when necessary to fully address the strengths, areas of improvement, or recommendations.

            iii] Technical Assessment (Per Question):
            For each question, provide the following detailed evaluation:
            - Question: The question asked.
            - Technical Skill: The specific technical skill(s) assessed in the question.
            - Skill Type: Either it is a Must-have skill or Good-to-have skill from Job description.
            - Score: Assign a score out of 10 based on the following dimensions:
                - Relevance: How directly the answer addresses the question.
                - Clarity: How well the answer is articulated and structured.
                - Depth: How comprehensively the candidate demonstrates knowledge and understanding.
                - Accuracy: Whether the answer contains any incorrect or misleading information.
                - Alignment with Seniority: How well the answer matches expectations for the stated level of seniority.
            - Evaluation Comment: Provide a precise, concise, and constructive comment that aligns with the assigned score, highlighting strengths and areas for improvement.

            ---

            ### **Scoring Guidelines**:
            - A score of 10: Exceptional alignment with expectations, clear evidence of mastery, and no significant weaknesses.
            - A score of 7-9: Strong performance with minor gaps or areas for improvement.
            - A score of 4-6: Satisfactory performance, but significant room for improvement.
            - A score of 1-3: Poor performance, lacking key aspects, or significant weaknesses.
            - A score of 0: No demonstration of the required skill or entirely unsatisfactory response.

            ### **Output**:
            - Strictly follow the output format :{output_json_format_question_wise}

            ---

            ### **Reminder**:
            - DO NOT CHANGE THE OUTPUT FORMAT.
            - DO NOT INCLUDE COMMENTARY OR EXTRA NOTES.
            - BE STRICT AND UNBIASED IN YOUR EVALUATION.
        """

        # logger.info("-------------------------------------------------------------------------------------------------")

        # logger.info(f"brt:: {brt}")
        # logger.info(f"model_id::{model_id}")
        # logger.info(f"prompt_for_assessment:: {prompt_for_assessment}")

        conversation = [
            {
                "role": "user",
                "content": [{"text": prompt_for_assessment}],
            }
        ]

        # logger.info("-------------------------------------------------------------------------------------------------")
        # logger.info(f"conversation:: {conversation}")
        

        # Send the message to the model
        response = brt.converse(
            modelId=model_id,
            messages=conversation
        )

        # Extract and logger.info the response text.
        response_text = response["output"]["message"]["content"][0]["text"]
        return response_text
        logger.info("Unified assessment completed successfully.")
    except Exception as e:
        logger.error(f"Failed to generate unified assessment in function: {e}")
        return None

def clean_triple_backticks(input_text):
    if (input_text.startswith("```json") and input_text.endswith("```")):
        return input_text.replace("```json", "", 1).rsplit("```", 1)[0].strip()
    elif (input_text.startswith("```") and input_text.endswith("```")):
        return input_text.replace("```", "", 1).rsplit("```", 1)[0].strip()
    return input_text

def parse_assessment_result(data):
    try:
        soft_skills_list = []
        soft_skills_data = {}

        for skill_data in data["softSkillsAssessment"]:
            skill_name = skill_data["softSkill"]
            score = skill_data["score"]
            justification = skill_data["justification"]
            soft_skills_list.append(skill_name)
            soft_skills_data[skill_name] = {
                "score": score,
                "justification": justification
            }

        # Extract strengths, areas of improvement, and recommendations
        soft_skills_strengths_list = data["overallSoftSkills"]["strengths"]
        soft_skills_areas_of_improvement_list = data["overallSoftSkills"]["areasOfImprovement"]
        soft_skills_recommendations_list = data["overallSoftSkills"]["recommendations"]

        # Extract questions
        questions = []
        technical_scores = defaultdict(lambda: {"total": 0, "max": 0})
        technical_skills = []  # List to hold skill names
        technical_skill_scores = []  # List to hold obtained scores
        technical_skill_max_scores = []  # List to hold max scores

        for question in data["technicalAssessment"]:
            question_id = question["questionID"]
            question_text = question["question"]
            skill = question["skill"]
            skill_type = question["skillType"]
            technical_score = question["technicalScore"]
            evaluation_comment = question["technicalEvaluationComment"]

            questions.append([question_id, question_text, skill, skill_type, technical_score, evaluation_comment])

            # Calculate technical skill-wise scores
            technical_scores[skill]["total"] += technical_score
            technical_scores[skill]["max"] += 10  # Assuming max score per question is 10

        # Prepare lists for technical skills and their respective scores
        for skill, score_data in technical_scores.items():
            technical_skills.append(skill)
            technical_skill_scores.append(score_data["total"])
            technical_skill_max_scores.append(score_data["max"])

        return (
            soft_skills_list,
            [details["score"] for details in soft_skills_data.values()],
            [details["justification"] for details in soft_skills_data.values()],
            soft_skills_data,
            soft_skills_strengths_list,
            soft_skills_areas_of_improvement_list,
            soft_skills_recommendations_list,
            questions,
            technical_scores,
            technical_skills,
            technical_skill_scores,
            technical_skill_max_scores
        )

    except Exception as e:
        logger.error(f"Failed to parse assessment result: {e}")
        return None, None, None, None, None, None, None, None, None, None, None, None


def calculate_total_scores(questions):
    try:
        if not questions:
            logger.error("No questions available to calculate candidate score.")
            return None

        total_score = sum(int(score) for _, _, _, _, score, _ in questions)
        possible_score = len(questions) * 10

        logger.info(f"Candidate score calculated: {total_score}")
        return total_score, possible_score

    except Exception as e:
        logger.error(f"Failed to calculate candidate score: {e}")
        return None

def calculate_soft_skill_scores(soft_skill_scores):
    try:
        if not soft_skill_scores:
            logger.error("No soft skill scores available.")
            return None

        total_soft_skill_score = sum(soft_skill_scores)
        total_possible_soft_skill_score = len(soft_skill_scores) * 10

        logger.info(f"Total soft skill scores calculated: {total_soft_skill_score, total_possible_soft_skill_score}")
        return total_soft_skill_score, total_possible_soft_skill_score
    except Exception as e:
        logger.info(f"Error in calculate_soft_skill_scores: {e}")
        return None

def skill_wise_output_format():
    try:
        output_json_format_skill_wise = '''
            {
            "technicalPerformanceSummary": {
                "strengths": [LIST OF STRENGTHS],
                "areasOfImprovement": [LIST OF AREAS OF IMPROVEMENT],
                "overallRecommendations": [LIST OF RECOMMENDATIONS]
            }
            '''
        return output_json_format_skill_wise
    
    except Exception as e:
        logger.error(f"Failed: {e}")
        return None
        

def skill_wise_assessment(questions, technical_skills, technical_skill_scores, total_technical_score, possible_technical_score, output_json_format_skill_wise, brt, model_id):
    try:
        if not questions or not total_technical_score or not possible_technical_score or not output_json_format_skill_wise:
            logger.error("Missing data for skill-wise assessment.")
            return None

        prompt_for_skill_wise_assessment = f"""
        You are an expert evaluator tasked with assessing the candidate's overall technical performance based on the following data.

            Your goal is to provide:
            1. A summary of the candidate's general strengths across all technical skills.
            2. A summary of the general areas where the candidate needs to improve across all technical skills.
            3. Actionable items for the recruiter to assess the candidate for technical skills.

            ### Technical Skills and Evaluations:
            {questions} (this contains the question, skill, score out of 5, evaluation comment)
            {total_technical_score} out of {possible_technical_score}
            {technical_skills} and their respective scores {technical_skill_scores}

            ### **Output**:
            - Strictly follow the output format :{output_json_format_skill_wise}

            ### Reminder:
            - Based on the comments and scores, provide an overall evaluation of the strengths and areas for improvement across all technical skills.
            - Provide 2 points for each section, but allow up to 3 points when necessary to fully address the strengths, areas of improvement, or recommendations.
            - DO NOT INCLUDE COMMENTARY OR EXTRA NOTES.
            - FOLLOW THE OUTPUT FORMAT STRICTLY.
        """

        response = brt.converse(
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt_for_skill_wise_assessment}]}]
        )
    
        response_text = response["output"]["message"]["content"][0]["text"]
        return response_text
    
    except Exception as e:
        logger.error(f"Failed to complete skill-wise assessment: {e}")
        return None

def extractTechnicalAssessment(data):
    try:
        # Ensure data is a dictionary (convert from JSON string if necessary)
        if isinstance(data, str):
            data = json.loads(data)
        
        # Extract the three lists from the JSON structure with 'technical' prefix and camelCase
        technicalStrengths = data.get('technicalPerformanceSummary', {}).get('strengths', [])
        technicalAreasOfImprovement = data.get('technicalPerformanceSummary', {}).get('areasOfImprovement', [])
        technicalOverallRecommendations = data.get('technicalPerformanceSummary', {}).get('overallRecommendations', [])

    except Exception as e:
        logger.info(f"Error extracting technical summary: {e}")
        return [], [], []

    return technicalStrengths, technicalAreasOfImprovement, technicalOverallRecommendations

def overall_output_format():
    try:
        output_json_format_overall_skills = '''
            {
            "strengths": [LIST OF STRENGTHS],
            "areasOfImprovement": [LIST OF AREAS OF IMPROVEMENT],
            "overallRecommendations": [LIST OF RECOMMENDATIONS]
            }
            '''
    except Exception as e:
        logger.error(f"Failed: {e}")
        return None    
    
    return output_json_format_overall_skills

def end_assessment(technical_result, soft_skills_data, total_technical_score, possible_technical_score, output_json_format_overall_skills, brt, model_id):
    try:
        if any(x is None for x in [technical_result, soft_skills_data, total_technical_score, possible_technical_score, output_json_format_overall_skills]):
            logger.error("Invalid data received for overall assessment.")
            return None

        prompt_for_recruiter_assessment = f"""
        Based on the following input, generate a detailed overall assessment for a recruiter
        that highlights the strengths, areas of improvement, and actionable recommendations for the candidate's evaluation process.

            ### Input:
                1. Technical Skills Summary:
                    - {technical_result}
                    (Includes the candidate's overall performance across technical skills, with strengths and weaknesses for each skill.)
                2. Soft Skills Data:
                    - {soft_skills_data}
                    (Detailed breakdown of the candidate's performance in soft skills, including scores and justifications.)
                3. Candidate's Total Technical Score:
                    - {total_technical_score} out of {possible_technical_score}

            ### Provide a structured response for the recruiter under the following sections:
            Strengths: Summarize the key strengths derived from the input.
            Areas of Improvement: Highlight the areas that require further development.
            Recommendations: Provide actionable items for the next evaluation round or training purposes.

            ### Guidelines:
            - Include 2 points per section, with up to 3 points if necessary to fully address the insights.
            - DO NOT INCLUDE COMMENTARY OR EXTRA NOTES.
            - FOLLOW THE OUTPUT FORMAT STRICTLY.

            ### Output Format:
            - Strictly follow the output format :{output_json_format_overall_skills}
        """

        response = brt.converse(  # Example, change this line to match the API you're using
            modelId=model_id,
            messages=[{"role": "user", "content": [{"text": prompt_for_recruiter_assessment}]}]
        )
    
        # Extract and logger.info the response text
        response_text = response["output"]["message"]["content"][0]["text"]
        return response_text
    except Exception as e:
        logger.error(f"Failed to generate overall assessment: {e}")
        return None

def extractAssessmentSections(endAssessmentResult):
    try:
        # If the input is a string, convert it into a dictionary (JSON)
        if isinstance(endAssessmentResult, str):
            endAssessmentResult = json.loads(endAssessmentResult)

        # Now, endAssessmentResult should be a dictionary
        overallStrengthsSection = endAssessmentResult.get("strengths", [])
        overallAreasOfImprovementSection = endAssessmentResult.get("areasOfImprovement", [])
        overallRecommendationsSection = endAssessmentResult.get("overallRecommendations", [])

    except Exception as e:
        logger.error(f"ERROR: Unable to extract assessment sections. Reason: {e}")
        return None

    # Return the extracted sections
    return overallStrengthsSection, overallAreasOfImprovementSection, overallRecommendationsSection
