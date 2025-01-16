import re
from collections import defaultdict
from logger.logger_config import logger
import json

def extract_assessment_data(assessments):
    try:

        logger.info(f"type: {type(assessments)}")
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

        level_of_seniority = parsed_message["level_of_seniority"]
        logger.info(f"Level of Seniority: {level_of_seniority}")

        questions = parsed_message["questions"]
        logger.info(f"Questions: {questions}")

        questions_json = {"questions": questions}
        logger.info(f"Questions JSON: {questions_json}")

        # Check if any essential data is None
        if any(x is None for x in [metadata, role, job_description, level_of_seniority, questions_json]):
            logger.error("Missing essential assessment data.")
            return None, None, None, None, None

        logger.info("Successfully extracted assessment data.")
        return metadata, role, job_description, level_of_seniority, questions_json
    except Exception as e:
        logger.error(f"Failed to extract assessment data: {e}")
        return None, None, None, None, None

def extract_soft_skills(job_description):
    try:
        # Define regex patterns to extract Must-Have and Good-to-Have soft skills
        must_have_pattern = r"Must-Have Soft Skills:\s*(.*?)\n\s*(Good-to-Have|$)"
        good_to_have_pattern = r"Good-to-Have Soft Skills:\s*(.*?)(?:\n|$)"

        # Extract Must-Have Soft Skills
        must_have_match = re.search(must_have_pattern, job_description, re.DOTALL)
        must_have_soft_skills = (
            [skill.strip() for skill in must_have_match.group(1).split("\n") if skill.strip()]
            if must_have_match
            else []
        )

        # Extract Good-to-Have Soft Skills
        good_to_have_match = re.search(good_to_have_pattern, job_description, re.DOTALL)
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

def unified_assessment(metadata, role, job_description, questions_json, soft_skills, brt, model_id):
    try:
        if any(x is None for x in [metadata, role, job_description, questions_json, soft_skills]):
            # logger.error("Missing essential data for unified assessment.")
            return None

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
                - Justification: Briefly explain why the score was assigned, referring to the responses where applicable.

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

            ### **Output Format**:
            For Soft Skills:
            Soft Skill: [Soft skill name]
            Score: [Soft skill score (0-10)]
            Justification: [Reason for the score]

            For Overall Soft Skills:
            1.Strengths: [Key strengths related to soft skills]
            2.Areas of Improvement: [Key improvement areas related to soft skills]
            3.Recommendations: [Key actionable items for recruiter]

            For each question:
            Question ID: [The Question ID]
            Question: [The question asked]
            Skill: [The skill mentioned for the question]
            Skill Type: [The skill type this skill falls under in Job Description]
            Technical Score: [0-10]
            Technical Evaluation Comment: [Comment]

            ---

            ### **Reminder**:
            - DO NOT INCLUDE COMMENTARY OR EXTRA NOTES.
            - FOLLOW THE OUTPUT FORMAT STRICTLY.
            - Be strict and unbiased in your evaluation.
        """

        conversation = [
            {
                "role": "user",
                "content": [{"text": prompt_for_assessment}],
            }
        ]

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
        logger.error(f"Failed to generate unified assessment: {e}")
        return None

def parse_assessment_result(data):
    try:
        print(f"data:{data}")
        soft_skill_matches = re.findall(r"(\d+)\.\s(.+?)\nScore:\s(\d+)\nJustification:\s(.+?)\n", data)
        soft_skills_list = []
        soft_skills_data = {}

        for _, skill, score, justification in soft_skill_matches:
            soft_skills_list.append(skill)
            soft_skills_data[skill] = {
                "score": int(score),
                "justification": justification.strip()
            }

        # Extract strengths, areas of improvement, and recommendations
        strengths = re.search(r"Strengths:\s*((?:- .+\n?)+)", data)
        areas_of_improvement = re.search(r"Areas of Improvement:\s*((?:- .+\n?)+)", data)
        recommendations = re.search(r"Recommendations:\s*((?:- .+\n?)+)", data)

        # Process each section into lists of points
        strengths_list = [point.strip("- ").strip() for point in strengths.group(1).strip().split("\n") if point.strip()] if strengths else []
        areas_of_improvement_list = [point.strip("- ").strip() for point in areas_of_improvement.group(1).strip().split("\n") if point.strip()] if areas_of_improvement else []
        recommendations_list = [point.strip("- ").strip() for point in recommendations.group(1).strip().split("\n") if point.strip()] if recommendations else []

        # Extract questions
        questions = re.findall(
            r"Question\s*ID:\s(\w+)\nQuestion:\s(.+?)\nSkill:\s(.+?)\nSkill\s*Type:\s(.+?)\nTechnical\s*Score:\s(\d+)\nTechnical\s*Evaluation\s*Comment:\s(.+?)(?:\n|$)",
            data,
            re.DOTALL | re.IGNORECASE # To handle multiline comments
        )

        # Calculate technical skill-wise scores
        technical_scores = defaultdict(lambda: {"total": 0, "max": 0})
        for _, _, skill, _, score, _ in questions:
            score = int(score)
            technical_scores[skill]["total"] += score
            technical_scores[skill]["max"] += 10  # Assuming max score per question is 10

        return (
            soft_skills_list,
            [details["score"] for details in soft_skills_data.values()],
            [details["justification"] for details in soft_skills_data.values()],
            soft_skills_data,
            strengths_list,
            areas_of_improvement_list,
            recommendations_list,
            questions,
            technical_scores,
        )

    except Exception as e:
        logger.error(f"Failed to parse assessment result: {e}")
        return None, None, None, None, None


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

def skill_wise_assessment(questions, skill_scores, brt, model_id):
    try:
        if not questions or not skill_scores:
            logger.error("Missing questions or skill scores for skill-wise assessment.")
            return None

        prompt_for_skill_wise_assessment = f"""
        You are an expert evaluator tasked with assessing the candidate's overall technical performance based on the following data.

            Your goal is to provide:
            1. A summary of the candidate's general strengths across all technical skills.
            2. A summary of the general areas where the candidate needs to improve across all technical skills.
            3. Actionable items for the recruiter to assess the candidate for technical skills.

            ### Technical Skills and Evaluations:
            {questions} (this contains the question, skill, score out of 5, evaluation comment)
            {skill_scores} (these contain the total score for each skill and the max possible score)

            ### Output Format:
            Technical Performance Summary:
            1.Strengths: [List the general strengths across all technical skills]
            2.Areas of Improvement: [List the general improvement areas across all technical skills]

            Overall Recommendations:
            -Provide recommendations or actionable items for the recruiter to assess the candidate (in the next round or for training purposes).

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

def extract_technical_summary(technical_result):
    try:
        # Regular expressions to extract the different parts of the result
        strengths_pattern = r"Strengths:\s*([\s\S]+?)\s*2"
        areas_of_improvement_pattern = r"Areas of Improvement:\s*([\s\S]+?)\s*Overall Recommendations:"
        recommendations_pattern = r"Overall Recommendations:\s*([\s\S]+)"

        # Extract strengths, areas of improvement, and recommendations using the regular expressions
        strengths = re.search(strengths_pattern, technical_result)
        areas_of_improvement = re.search(areas_of_improvement_pattern, technical_result)
        recommendations = re.search(recommendations_pattern, technical_result)

        # Initialize the individual variables
        technical_skill_strengths = []
        areas_of_improvement_list = []
        recommendations_list = []

        if strengths:
            # Clean and split the strengths section into lines, ignoring extra spaces
            technical_skill_strengths = [line.strip() for line in strengths.group(1).split('\n') if line.strip()]

        if areas_of_improvement:
            # Clean and split the areas of improvement section into lines
            areas_of_improvement_list = [line.strip() for line in areas_of_improvement.group(1).split('\n') if line.strip()]

        if recommendations:
            # Clean and split the recommendations section into lines
            recommendations_list = [line.strip() for line in recommendations.group(1).split('\n') if line.strip()]

        # Return the variables as a tuple or a dictionary of individual variables
        return technical_skill_strengths, areas_of_improvement_list, recommendations_list

    except Exception as e:
        logger.info(f"Error extracting technical summary: {e}")
        return [], [], []


def end_assessment(technical_result, soft_skills_data, candidate_score, brt, model_id):
    try:
        if any(x is None for x in [technical_result, soft_skills_data, candidate_score]):
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
                    - {candidate_score}

            ### Provide a structured response for the recruiter under the following sections:
            Strengths: Summarize the key strengths derived from the input.
            Areas of Improvement: Highlight the areas that require further development.
            Recommendations: Provide actionable items for the next evaluation round or training purposes.

            ### Guidelines:
            - Include 2 points per section, with up to 3 points if necessary to fully address the insights.
            - DO NOT INCLUDE COMMENTARY OR EXTRA NOTES.
            - FOLLOW THE OUTPUT FORMAT STRICTLY.

            ### Output Format:
            1.Strengths:
            - [List key strengths]
            2.Areas of Improvement:
            - [List areas requiring improvement]
            3.Recommendations:
            - [List actionable recommendations]
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

def extract_assessment_sections(end_assessment_result):
    try:
        # Split the assessment result by the section headings
        strengths_section = end_assessment_result.split("Strengths:")[1].split("2")[0].strip()
    except IndexError:
        strengths_section = "No strengths section found."

    try:
        areas_of_improvement_section = end_assessment_result.split("Areas of Improvement:")[1].split("3")[0].strip()
    except IndexError:
        areas_of_improvement_section = "No areas of improvement section found."

    try:
        recommendations_section = end_assessment_result.split("Recommendations:")[1].strip()
    except IndexError:
        recommendations_section = "No recommendations section found."
    
    logger.info("extracted overall assessment sections successfully.")
    # Return the extracted sections
    return strengths_section, areas_of_improvement_section, recommendations_section