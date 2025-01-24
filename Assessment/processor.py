import json
from assessment_logic import (
    extract_assessment_data,
    question_wise_output_format,
    extract_soft_skills,
    unified_assessment,
    clean_triple_backticks,
    parse_assessment_result,
    calculate_total_scores,
    calculate_soft_skill_scores,
    skill_wise_output_format,
    skill_wise_assessment,
    extractTechnicalAssessment,
    overall_output_format,
    end_assessment,
    extractAssessmentSections
)
from sns_publisher import send_message_to_sns_async
from logger.logger_config import logger

async def process_data(assessments, sns_topic_arn, brt, model_id):
    try:
        # Step 1: Extract assessment data
        metadata, role, job_description, questions_json = extract_assessment_data(assessments)
        
        # Check if any essential data is None
        if any(x is None for x in [metadata, role, job_description, questions_json]):
            logger.error("Missing assessment data.")
            return False

        soft_skills = extract_soft_skills(job_description)

        if not soft_skills:
            logger.error("No soft skills extracted.")
            return False
        
        output_format_for_question_wise = question_wise_output_format()

        # Step 2: Generate unified assessment
        question_wise_assessment = unified_assessment(metadata, role, job_description, questions_json, soft_skills, output_format_for_question_wise, brt, model_id)
        logger.info(f"assessment_result : {question_wise_assessment}")
        
        # Check if assessment result is None
        if question_wise_assessment is None:
            logger.error("Failed to generate unified assessment.")
            return False

        assessment_result = clean_triple_backticks(question_wise_assessment)

        skill_wise_result = json.loads(assessment_result)

        (soft_skills, soft_skill_scores, soft_skill_justifications, soft_skills_data,
        soft_skills_strengths, soft_skills_areas_of_improvement, soft_skills_recommendations, questions, technical_scores, technical_skills, technical_skill_scores, technical_skill_max_scores) = parse_assessment_result(skill_wise_result)

        # Calculate total technical score
        total_technical_score, possible_technical_score = calculate_total_scores(questions)

        # Calculate total soft skill score
        total_soft_skill_score, possible_soft_skill_score = calculate_soft_skill_scores(soft_skill_scores)

        # logger.info results
        logger.info(f"Soft Skills List: {soft_skills}")
        logger.info(f"Soft Skill Scores: {soft_skill_scores}")
        logger.info(f"Soft Skills Justifications: {soft_skill_justifications}")
        logger.info(f"Soft Skills Data: {soft_skills_data}")
        logger.info(f"Strengths: {soft_skills_strengths}")
        logger.info(f"Areas of Improvement: {soft_skills_areas_of_improvement}")
        logger.info(f"Recommendations: {soft_skills_recommendations}")
        logger.info(f"Technical Questions: {questions}")
        logger.info(f"Technical Scores: {technical_scores}")
        logger.info(f"Technical Skills: {technical_skills}")
        logger.info(f"Technical Skill Scores: {technical_skill_scores}")
        logger.info(f"Technical Skill Max Scores: {technical_skill_max_scores}")
        logger.info(f"Candidate Technical Score: {total_technical_score}/{possible_technical_score}")
        logger.info(f"Total Soft Skill Score: {total_soft_skill_score}/{possible_soft_skill_score}")      
        
        if any(x is None for x in [soft_skills, soft_skill_scores, soft_skill_justifications, soft_skills_data,
        soft_skills_strengths, soft_skills_areas_of_improvement, soft_skills_recommendations, questions, technical_scores, technical_skills, technical_skill_scores, technical_skill_max_scores]):
            logger.error("Failed to parse assessment result.")
            return False

        output_format_for_skill_wise = skill_wise_output_format()

        # Step 6: Perform skill-wise assessment
        technical_result_LLM = skill_wise_assessment(questions, technical_skills, technical_skill_scores, total_technical_score, possible_technical_score, output_format_for_skill_wise, brt, model_id)
        
        # Check if skill-wise result is None
        if technical_result_LLM is None:
            logger.error("Failed to complete skill-wise assessment.")
            return False

        logger.info(f"technical_result:: {technical_result_LLM}")
        
        technical_result = clean_triple_backticks(technical_result_LLM)

        technical_skill_strengths, technical_skill_areas_of_improvement, technical_skill_recommendations = extractTechnicalAssessment(technical_result)

        output_format_for_overall_LLM = overall_output_format()
        # Step 7: Generate overall assessment
        overall_assessment_result = end_assessment(technical_result, soft_skills_data, total_technical_score, possible_technical_score, output_format_for_overall_LLM, brt, model_id)

        if overall_assessment_result is None:
            logger.error("Failed to generate overall assessment.")
            return False

        overallStrengthsSection, overallAreasOfImprovementSection, overallRecommendationsSection = extractAssessmentSections(overall_assessment_result)

        if any(x is None for x in [overallStrengthsSection, overallAreasOfImprovementSection, overallRecommendationsSection]):
            logger.error("Failed to extract overall assessment data.")
            return False

        output = {
            "metadata": metadata,
            "questionWiseAssessment": {
                "assessedQuestions": questions,
                "totalTechnicalScoreObtained": total_technical_score,
                "totalPossibleTechnicalScore": possible_technical_score
            },
            "softSkillsAssessment": {
                "softSkillsIdentified": soft_skills,
                "softSkillsScores": soft_skill_scores,
                "softSkillsJustifications": soft_skill_justifications,
                "softSkillsStrengths": soft_skills_strengths,
                "softSkillsAreasOfImprovement": soft_skills_areas_of_improvement,
                "softSkillsRecommendation": soft_skills_recommendations,
                "totalSoftSkillsScoreObtained": total_soft_skill_score,
                "totalPossibleSoftSkillsScore": possible_soft_skill_score
            },
            "technicalSkillWiseAssessment": {
                "technicalSkillsIdentified": technical_skills,
                "technicalSkillsScores": technical_skill_scores,
                "technicalSkillsTotalPossibleScore": technical_skill_max_scores,
                "technicalStrengths": technical_skill_strengths,
                "technicalAreasOfImprovement": technical_skill_areas_of_improvement,
                "technicalRecommendations": technical_skill_recommendations
            },
            "overallAssessment": {
                "overallStrengths": overallStrengthsSection,
                "overallAreasOfImprovement": overallAreasOfImprovementSection,
                "overallRecommendations": overallRecommendationsSection
            }
        }

        logger.info(f"json output ::  output")
        sns_message = json.dumps(output, indent=2)
        logger.info(f"sns_message:: {sns_message}")
        logger.info("Final assessment output prepared for SNS.")

        # Send the message to SNS
        await send_message_to_sns_async(
            topic_arn=sns_topic_arn,
            data=output,
            role=role
        )
        logger.info("Assessment result sent to SNS successfully.")

        return True
    except Exception as e:
        logger.error(f"Error processing data: {e}")
        return False