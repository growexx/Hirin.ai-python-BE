import json
from assessment_logic import (
    extract_assessment_data,
    extract_soft_skills,
    unified_assessment,
    parse_assessment_result,
    calculate_total_scores,
    calculate_soft_skill_scores,
    skill_wise_assessment,
    extract_technical_summary,
    end_assessment,
    extract_assessment_sections
)
from sns_publisher import send_message_to_sns_async
from logger.logger_config import logger

async def process_data(assessments, sns_topic_arn, brt, model_id):
    try:
        # Step 1: Extract assessment data
        metadata, role, job_description, level_of_seniority, questions_json = extract_assessment_data(assessments)
        
        # Check if any essential data is None
        if any(x is None for x in [metadata, role, job_description, level_of_seniority, questions_json]):
            logger.error("Missing assessment data.")
            return False

        soft_skills = extract_soft_skills(job_description)

        if not soft_skills:
            logger.error("No soft skills extracted.")
            return False

        # Step 2: Generate unified assessment
        assessment_result = unified_assessment(metadata, role, job_description, questions_json, soft_skills, brt, model_id)
        
        # Check if assessment result is None
        if assessment_result is None:
            logger.error("Failed to generate unified assessment.")
            return False

        (soft_skills, soft_skill_scores, soft_skill_justifications, soft_skills_data, soft_skills_strengths, soft_skills_areas_of_improvement, soft_skills_recommendations, questions, technical_scores) = parse_assessment_result(assessment_result)

        # Calculate total technical score
        total_technical_score, possible_technical_score = calculate_total_scores(questions)

        # Calculate total soft skill score
        total_soft_skill_score, possible_soft_skill_score = calculate_soft_skill_scores(soft_skill_scores)

        # logger.info results
        logger.info("Soft Skills List:", soft_skills)
        logger.info("Soft Skill Scores:", soft_skill_scores)
        logger.info("Soft Skills Justifications:", soft_skill_justifications)
        logger.info("Soft Skills Data:", soft_skills_data)
        logger.info("Strengths:", soft_skills_strengths)
        logger.info("Areas of Improvement:", soft_skills_areas_of_improvement)
        logger.info("Recommendations:", soft_skills_recommendations)
        logger.info("\nTechnical Questions:", questions)
        logger.info(f"\nCandidate Technical Score: {total_technical_score}/{possible_technical_score}")
        logger.info(f"Total Soft Skill Score: {total_soft_skill_score}/{possible_soft_skill_score}")        
        
        if any(x is None for x in [soft_skills, soft_skill_scores, soft_skill_justifications, soft_skills_data, soft_skills_strengths, soft_skills_areas_of_improvement, soft_skills_recommendations, questions, technical_scores]):
            logger.error("Failed to parse assessment result.")
            return False

        # Step 6: Perform skill-wise assessment
        technical_result = skill_wise_assessment(questions, technical_scores, brt, model_id)
        
        # Check if skill-wise result is None
        if technical_result is None:
            logger.error("Failed to complete skill-wise assessment.")
            return False

        logger.info("technical_result:: ",technical_result)
        
        technical_skill_strengths, technical_skill_areas_of_improvement, technical_skill_recommendations = extract_technical_summary(technical_result)

        logger.info("Technical Skill Strengths:", technical_skill_strengths)
        logger.info("Areas of Improvement:", technical_skill_areas_of_improvement)
        logger.info("Recommendations:", technical_skill_recommendations)

        # Step 7: Generate overall assessment
        overall_assessment_result = end_assessment(technical_result, soft_skills_data, total_technical_score, brt, model_id)        
        
        # logger.info("overall_assessment_result:: ",overall_assessment_result)
        # Check if overall assessment result is None
        if overall_assessment_result is None:
            logger.error("Failed to generate overall assessment.")
            return False

        strengths, areas_of_improvement, recommendations = extract_assessment_sections(overall_assessment_result)

        if any(x is None for x in [strengths, areas_of_improvement, recommendations]):
            logger.error("Failed to extract overall assessment data.")
            return False

        total_soft_skills = len(soft_skills_data)  # Get the number of soft skills
        total_possible_soft_skills_score = total_soft_skills 


        # Prepare final output for SNS
        output = {
            "metadata": metadata,
            "QUESTION_WISE_ASSESSMENT": questions,
            "SUMMARY_OF_Soft_SKILLS_AND_SCORES": {
                "Soft Skills Identified": [
                    {"skill": skill, "score": details["score"], "justification": details["justification"]}
                    for skill, details in soft_skills_data.items()
                ],
                "Soft Skills Reasoning": {
                    "Strengths": soft_skills_strengths,
                    "Areas of Improvement":  soft_skills_areas_of_improvement,
                    "Recommendation": soft_skills_recommendations
                }
            },
            "SUMMARY_OF_Technical_SKILLS_AND_SCORES": {
                "Technical Skills Identified": [
                    {"skill": skill, "total": scores["total"], "max": scores["max"]}
                    for skill, scores in technical_scores.items()
                ],
                "Technical Skills Reasoning": {
                    "Strengths": technical_skill_strengths,
                    "Areas of Improvement":technical_skill_areas_of_improvement,
                    "Recommendation": technical_skill_recommendations
                }
            },
            "TECHNICAL_SKILL_WISE_ASSESSMENT": [
                {"skill": skill, "total": scores["total"], "max": scores["max"]}
                for skill, scores in technical_scores.items()
            ],
            "OVERALL_ASSESSMENT": {
                "Candidate Technical Score": f"{total_technical_score}/{possible_technical_score}",
                "Candidate Soft Skill Score": f"{total_soft_skill_score}/{total_possible_soft_skills_score}",
                "End Assessment Result": {
                    "Strengths": strengths,
                    "Areas of Improvement": areas_of_improvement,
                    "Recommendations": recommendations
                }
            }
        }

        logger.info("json output :: ", output)
        sns_message = json.dumps(output, indent=2)
        logger.info("sns_message::", sns_message)
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