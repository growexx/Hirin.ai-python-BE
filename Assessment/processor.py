import json
import logging
from assessment_logic import (
    extract_assessment_data,
    unified_assessment,
    add_skills_to_assessment_result,
    parse_assessment_result,
    calculate_candidate_score,
    calculate_total_possible_score,
    skill_wise_assessment,
    end_assessment
)
from sns_publisher import send_message_to_sns_async

# Configure logging
logging.basicConfig(
    filename='app.log',
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

async def process_data(assessments, sns_topic_arn, api_key, model):
    try:
        logging.info("Starting assessment data processing.")

        # Step 1: Extract assessment data
        try:
            metadata, role, job_description, level_of_seniority, questions_json = extract_assessment_data(assessments)
            logging.info("Successfully extracted assessment data.")
        except Exception as e:
            logging.error(f"Failed to extract assessment data: {e}")
            raise

        # Step 2: Generate unified assessment
        try:
            assessment_result = unified_assessment(
                metadata, role, job_description, level_of_seniority, questions_json, api_key, model
            )
            logging.info("Unified assessment generated successfully.")
        except Exception as e:
            logging.error(f"Failed to generate unified assessment: {e}")
            raise

        # Step 3: Enhance assessment result by adding skills
        try:
            assessment_result = add_skills_to_assessment_result(assessment_result, assessments)
            logging.info("Successfully added skills to assessment result.")
        except Exception as e:
            logging.error(f"Failed to add skills to assessment result: {e}")
            raise

        # Step 4: Parse the assessment result
        try:
            (
                soft_skills_identified,
                soft_skills_score,
                soft_skills_reasoning,
                questions,
                skill_scores
            ) = parse_assessment_result(assessment_result)
            logging.info("Assessment result parsed successfully.")
        except Exception as e:
            logging.error(f"Failed to parse assessment result: {e}")
            raise

        # Step 5: Calculate total and candidate scores
        try:
            candidate_score = calculate_candidate_score(questions)
            total_possible_score = calculate_total_possible_score(questions)
            logging.info(f"Scores calculated successfully: Candidate Score - {candidate_score}, Total Score - {total_possible_score}.")
        except Exception as e:
            logging.error(f"Failed to calculate scores: {e}")
            raise

        # Step 6: Perform skill-wise assessment
        try:
            skill_wise_result = skill_wise_assessment(questions, skill_scores, api_key, model)
            logging.info("Skill-wise assessment completed successfully.")
        except Exception as e:
            logging.error(f"Failed during skill-wise assessment: {e}")
            raise

        # Step 7: Generate overall assessment
        try:
            overall_assessment_result = end_assessment(
                skill_wise_result,
                soft_skills_identified,
                soft_skills_score,
                candidate_score,
                soft_skills_reasoning,
                api_key,
                model
            )
            logging.info("Overall assessment generated successfully.")
        except Exception as e:
            logging.error(f"Failed to generate overall assessment: {e}")
            raise

        # Prepare the final output for SNS
        try:
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
            logging.info("Final assessment output prepared for SNS.")
        except Exception as e:
            logging.error(f"Failed to prepare output for SNS: {e}")
            raise

        # Send the message to SNS
        try:
            await send_message_to_sns_async(
                topic_arn=sns_topic_arn,
                data=sns_message,
                role=role
            )
            logging.info("Assessment result sent to SNS successfully.")
        except Exception as e:
            logging.error(f"Failed to send message to SNS: {e}")
            raise

        return True

    except Exception as e:
        logging.error(f"Error processing data: {e}")
        return False












# from assessment_logic import (
#     extract_assessment_data,
#     unified_assessment,
#     add_skills_to_assessment_result,  # Import the new function
#     parse_assessment_result,
#     calculate_candidate_score,
#     calculate_total_possible_score,
#     skill_wise_assessment,
#     end_assessment
# )
# import json
# from sns_publisher import send_message_to_sns_async

# async def process_data(assessments, sns_topic_arn, api_key, model):
#     try:
#         # Step 1: Extract assessment data
#         metadata, role, job_description, level_of_seniority, questions_json = extract_assessment_data(assessments)

#         # Step 2: Generate unified assessment
#         assessment_result = unified_assessment(
#             metadata, role, job_description, level_of_seniority, questions_json, api_key, model
#         )
#         # print(assessment_result)

#         # Step 3: Enhance assessment result by adding skills
#         assessment_result = add_skills_to_assessment_result(assessment_result, assessments)
#         # print("Enhanced assessment_result:: ", assessment_result)

#         # Step 4: Parse the assessment result
#         (
#             soft_skills_identified,
#             soft_skills_score,
#             soft_skills_reasoning,
#             questions,
#             skill_scores
#         ) = parse_assessment_result(assessment_result)

#         # Step 5: Calculate total and candidate scores
#         candidate_score = calculate_candidate_score(questions)
#         # print('candidate_score:: ', candidate_score)
#         total_possible_score = calculate_total_possible_score(questions)
#         # print('total_possible_score :: ', total_possible_score)

#         # Step 6: Perform skill-wise assessment
#         skill_wise_result = skill_wise_assessment(questions, skill_scores, api_key, model)
#         # print('skill_wise_result:: ', skill_wise_result)

#         # Step 7: Generate overall assessment
#         overall_assessment_result = end_assessment(
#             skill_wise_result,
#             soft_skills_identified,
#             soft_skills_score,
#             candidate_score,
#             soft_skills_reasoning,
#             api_key,
#             model
#         )

#         # print('overall_assessment_result :: ', overall_assessment_result)

#         # Prepare the final output for SNS
#         output = {
#             "metadata": metadata,
#             "Soft Skills Identified": soft_skills_identified,
#             "Soft Skills Score": soft_skills_score,
#             "Soft Skills Reasoning": soft_skills_reasoning,
#             "Question wise assessment": questions,
#             "Skill wise scores": skill_wise_result,
#             "Candidate Technical Score": f"{candidate_score}/{total_possible_score}",
#             "Overall Assessment": overall_assessment_result
#         }

#         # Convert the output to JSON format
#         sns_message = json.dumps(output, indent=2)

#         # Send the message to SNS
#         await send_message_to_sns_async(
#             topic_arn=sns_topic_arn,
#             data=sns_message,
#             role=role
#         )

#         print("Assessment processed and sent to SNS successfully.")
#         return True

#     except Exception as e:
#         print(f"Error processing data: {e}")
#         return False