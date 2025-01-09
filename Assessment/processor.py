import json
from assessment_logic import (
    extract_assessment_data,
    unified_assessment,
    parse_assessment_result,
    calculate_candidate_score,
    calculate_total_possible_score,
    skill_wise_assessment,
    end_assessment
)
from sns_publisher import send_message_to_sns_async
from logger.logger_config import logger

async def process_data(assessments, sns_topic_arn, api_key, model):
    try:
        # Step 1: Extract assessment data
        metadata, role, job_description, level_of_seniority, questions_json = extract_assessment_data(assessments)
        
        # Check if any essential data is None
        if any(x is None for x in [metadata, role, job_description, level_of_seniority, questions_json]):
            logger.error("Missing essential assessment data.")
            return False

        # Step 2: Generate unified assessment
        assessment_result = unified_assessment(
            metadata, role, job_description, level_of_seniority, questions_json, api_key, model
        )
        
        # Check if assessment result is None
        if assessment_result is None:
            logger.error("Failed to generate unified assessment.")
            return False

        # print("before::",assessment_result)
        # # Step 3: Enhance assessment result by adding skills
        # assessment_result = add_skills_to_assessment_result(assessment_result, assessments)

        # print("after:", assessment_result)

        # # Check if the enhanced assessment result is None
        # if assessment_result is None:
        #     logger.error("Failed to add skills to assessment result.")
        #     return False

        # Step 4: Parse the assessment result
        soft_skills_identified, soft_skills_score, soft_skills_reasoning, questions, skill_scores = parse_assessment_result(assessment_result)
        
        # Check if any parsed result is None
        if any(x is None for x in [soft_skills_identified, soft_skills_score, soft_skills_reasoning, questions, skill_scores]):
            logger.error("Failed to parse assessment result.")
            return False

        # Step 5: Calculate total and candidate scores
        candidate_score = calculate_candidate_score(questions)
        total_possible_score = calculate_total_possible_score(questions)
        
        # Check if any score calculation result is None
        if any(x is None for x in [candidate_score, total_possible_score]):
            logger.error("Failed to calculate scores.")
            return False

        # Step 6: Perform skill-wise assessment
        skill_wise_result = skill_wise_assessment(questions, skill_scores, api_key, model)
        
        # Check if skill-wise result is None
        if skill_wise_result is None:
            logger.error("Failed to complete skill-wise assessment.")
            return False

        # Step 7: Generate overall assessment
        overall_assessment_result = end_assessment(
            skill_wise_result,
            soft_skills_identified,
            soft_skills_score,
            candidate_score,
            soft_skills_reasoning,
            api_key,
            model
        )
        
        # Check if overall assessment result is None
        if overall_assessment_result is None:
            logger.error("Failed to generate overall assessment.")
            return False

        # Prepare final output for SNS
        output = {
            "metadata": metadata,
            "Soft Skills Identified": soft_skills_identified,
            "Soft Skills Score": soft_skills_score,
            "Soft Skills Reasoning": soft_skills_reasoning,
            "Question wise assessment": questions,
            "Skill wise scores": skill_wise_result,
            "Candidate Technical Score": f"{candidate_score}/{total_possible_score}",
            "Overall Assessment": overall_assessment_result
        }

        sns_message = json.dumps(output, indent=2)
        logger.info("Final assessment output prepared for SNS.")

        # Send the message to SNS
        await send_message_to_sns_async(
            topic_arn=sns_topic_arn,
            data=sns_message,
            role=role
        )
        logger.info("Assessment result sent to SNS successfully.")

        return True
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return False











# import json
# from assessment_logic import (
#     extract_assessment_data,
#     unified_assessment,
#     add_skills_to_assessment_result,
#     parse_assessment_result,
#     calculate_candidate_score,
#     calculate_total_possible_score,
#     skill_wise_assessment,
#     end_assessment
# )
# from sns_publisher import send_message_to_sns_async
# from logger.logger_config import logger


# async def process_data(assessments, sns_topic_arn, api_key, model):
#     try:
#         logger.info("Starting assessment data processing.")

#         # Step 1: Extract assessment data
#         try:
#             metadata, role, job_description, level_of_seniority, questions_json = extract_assessment_data(assessments)
#             logger.info("Successfully extracted assessment data.")
#         except Exception as e:
#             logger.error(f"Failed to extract assessment data: {e}")
#             raise

#         # Step 2: Generate unified assessment
#         try:
#             assessment_result = unified_assessment(
#                 metadata, role, job_description, level_of_seniority, questions_json, api_key, model
#             )
#             logger.info("Unified assessment generated successfully.")
#         except Exception as e:
#             logger.error(f"Failed to generate unified assessment: {e}")
#             raise

#         # Step 3: Enhance assessment result by adding skills
#         try:
#             assessment_result = add_skills_to_assessment_result(assessment_result, assessments)
#             logger.info("Successfully added skills to assessment result.")
#         except Exception as e:
#             logger.error(f"Failed to add skills to assessment result: {e}")
#             raise

#         # Step 4: Parse the assessment result
#         try:
#             (
#                 soft_skills_identified,
#                 soft_skills_score,
#                 soft_skills_reasoning,
#                 questions,
#                 skill_scores
#             ) = parse_assessment_result(assessment_result)
#             logger.info("Assessment result parsed successfully.")
#         except Exception as e:
#             logger.error(f"Failed to parse assessment result: {e}")
#             raise

#         # Step 5: Calculate total and candidate scores
#         try:
#             candidate_score = calculate_candidate_score(questions)
#             total_possible_score = calculate_total_possible_score(questions)
#             logger.info(f"Scores calculated successfully: Candidate Score - {candidate_score}, Total Score - {total_possible_score}.")
#         except Exception as e:
#             logger.error(f"Failed to calculate scores: {e}")
#             raise

#         # Step 6: Perform skill-wise assessment
#         try:
#             skill_wise_result = skill_wise_assessment(questions, skill_scores, api_key, model)
#             logger.info("Skill-wise assessment completed successfully.")
#         except Exception as e:
#             logger.error(f"Failed during skill-wise assessment: {e}")
#             raise

#         # Step 7: Generate overall assessment
#         try:
#             overall_assessment_result = end_assessment(
#                 skill_wise_result,
#                 soft_skills_identified,
#                 soft_skills_score,
#                 candidate_score,
#                 soft_skills_reasoning,
#                 api_key,
#                 model
#             )
#             logger.info("Overall assessment generated successfully.")
#         except Exception as e:
#             logger.error(f"Failed to generate overall assessment: {e}")
#             raise

#         # Prepare the final output for SNS
#         try:
#             output = {
#                 "metadata": metadata,
#                 "Soft Skills Identified": soft_skills_identified,
#                 "Soft Skills Score": soft_skills_score,
#                 "Soft Skills Reasoning": soft_skills_reasoning,
#                 "Question wise assessment": questions,
#                 "Skill wise scores": skill_wise_result,
#                 "Candidate Technical Score": f"{candidate_score}/{total_possible_score}",
#                 "Overall Assessment": overall_assessment_result
#             }

#             sns_message = json.dumps(output, indent=2)
#             logger.info("Final assessment output prepared for SNS.")
#         except Exception as e:
#             logger.error(f"Failed to prepare output for SNS: {e}")
#             raise

#         # Send the message to SNS
#         try:
#             await send_message_to_sns_async(
#                 topic_arn=sns_topic_arn,
#                 data=sns_message,
#                 role=role
#             )
#             logger.info("Assessment result sent to SNS successfully.")
#         except Exception as e:
#             logger.error(f"Failed to send message to SNS: {e}")
#             raise

#         return True

#     except Exception as e:
#         logger.error(f"Error processing data: {e}")
#         return False