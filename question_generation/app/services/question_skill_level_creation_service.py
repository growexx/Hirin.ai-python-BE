from app.logger_config import logger
from app.utils.hepler import Helper
from app.services.llmClientService import LLMClient
import asyncio
from app.services.aws_service import AWSService
from app.services.getTextService import GetText
import os

class QuestionSkillLevelCreationService:

    @classmethod
    async def questionskillcreation(cls,client, Bdmodel, jobDescription,totalQuestion,interviewDuration,job_description_type):
        try:

            totalQuestionByTwo = int(totalQuestion // 2)
            prompt_template = await Helper.read_prompt("app/static/question_skill_level_creation_prompt.txt")
            prompt = ''
            if job_description_type == 'text':
                prompt = prompt_template.format(job_description=jobDescription,interview_duration=interviewDuration,total_questions=totalQuestion,totalQuestionByTwo=totalQuestionByTwo)
                logger.info(f"PROMPT: {prompt}")
            elif job_description_type == 'url':

                path = await AWSService.download_file_from_s3(jobDescription,'app/static/JD/')
                job_Description = GetText.getText(path)

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


            questionSkill = LLMClient.BedRockLLM(client,prompt, Bdmodel)
            logger.info(f"QuestionSkill1: {questionSkill}")
            questionSkill = Helper.standardize_llm_response(questionSkill)
            logger.info(f"QuestionSkill2: {questionSkill}")

            if not questionSkill:
                logger.info("Error: No skill level generated for question generated.")
                return None

            return questionSkill

        except Exception as e:
            logger.error(f"Failed to generate skill level for question: {str(e)}")
            return None