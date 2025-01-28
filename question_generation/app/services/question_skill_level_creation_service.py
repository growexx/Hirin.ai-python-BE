from app.logger_config import logger
from app.utils.hepler import Helper
from app.services.llmClientService import LLMClient
import asyncio
from app.services.aws_service import AWSService
from app.services.getTextService import GetText
import os

class QuestionSkillLevelCreationService:

    @classmethod
    async def questionskillcreation(cls,client, Bdmodel, jobDescription,totalQuestion,interviewDuration,job_title, job_description_type):
        try:
            totalQuestionByTwo = int(totalQuestion // 2)
            prompt_template = await Helper.read_prompt("app/static/question_skill_level_creation_prompt.txt")
            prompt = ''
            if job_description_type == 'text':
                prompt = prompt_template.format(job_description=jobDescription,interview_duration=interviewDuration,total_questions=totalQuestion,totalQuestionByTwo=totalQuestionByTwo)
                validation_prompt = await Helper.read_prompt("app/static/jd_validation_prompt.txt")
                vd_prompt = validation_prompt.format(text_from_file=jobDescription)
                validation_status, reason = Helper.validate_job_description_llm(client, Bdmodel, vd_prompt)
                logger.info(f"Validation Status: {validation_status}")

                if validation_status == "Invalid":
                    return {
                        "status": 0,
                        "message": f"Please provide a relevant Job Description",
                        "data": {}
                    }

                v_prompt_template = await Helper.read_prompt("app/static/job_description_validation_prompt.txt")
                v_prompt = v_prompt_template.format(input_text=jobDescription,input_title=job_title)
                check = LLMClient.BedRockLLM(client, v_prompt, Bdmodel)

                if check.strip().lower() == "irrelevant":
                    return {
                        "status": 0,
                        "message": f"Please provide a relevant Job Description",
                        "data": {}
                    }

                logger.info(f"PROMPT: {prompt}")
            elif job_description_type == 'url':

                path = await AWSService.download_file_from_s3(jobDescription,'app/static/JD/')
                job_Description = GetText.getText(path)

                validation_prompt = await Helper.read_prompt("app/static/jd_validation_prompt.txt")
                vd_prompt = validation_prompt.format(text_from_file=job_Description)
                validation_status, reason = Helper.validate_job_description_llm(client, Bdmodel, vd_prompt)
                logger.info(f"Validation Status: {validation_status}")
                if validation_status == "Invalid":
                    return {
                        "status": 0,
                        "message": f"Please provide a relevant Job Description in the file",
                        "data": {}
                    }

                v_prompt_template = await Helper.read_prompt("app/static/job_description_validation_prompt.txt")
                v_prompt = v_prompt_template.format(input_text=job_Description,input_title=job_title)
                check = LLMClient.BedRockLLM(client, v_prompt, Bdmodel)

                if check.strip().lower() == "irrelevant":
                    return {
                        "status": 0,
                        "message": f"Please provide a relevant Job Description",
                        "data": {}
                    }
                logger.info(f"RAW FILE JOB DESCRIPITON:{job_Description}")


                if not job_Description:
                    logger.info("Error: Unable to parse job description")
                    return None

                prompt = prompt_template.format(job_description=job_Description,interview_duration=interviewDuration,total_questions=totalQuestion,totalQuestionByTwo=totalQuestionByTwo)
                logger.info(f"PROMPT: {prompt}")
                try:
                     os.remove(path)
                     logger.info(f"The file {path} has been deleted.")
                except FileNotFoundError:
                     logger.error(f"The file {path} was not found.")
                except PermissionError:
                     print(f"Permission denied to delete the file {path}.")
                except Exception as e:
                    print(f"An error occurred: {e}")

            skill_retry_count = 0
            max_retries = 3
            while skill_retry_count < max_retries:

                questionSkill = LLMClient.BedRockLLM(client, prompt, Bdmodel)
                logger.info(f"Raw QuestionSkill: {questionSkill}")

                questionSkill = Helper.standardize_llm_response(questionSkill)
                logger.info(f"Standardized QuestionSkill: {questionSkill}")

                if  Helper.check_list_sizes(questionSkill):
                    logger.info(f"Validated QuestionSkill: {questionSkill}")
                    return questionSkill
                else:
                    logger.warning(f"Validation failed. Retrying... ({skill_retry_count + 1}/{max_retries})")
                    skill_retry_count += 1

            logger.error("Skill Array Validation failed after maximum retries.")

            if not questionSkill:
                logger.info("Error: No skill level generated for question generated.")
                return None

            return questionSkill

        except Exception as e:
            logger.error(f"Failed to generate skill level for question: {str(e)}")
            return None