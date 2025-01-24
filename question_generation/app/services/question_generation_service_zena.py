import os
import asyncio
from app.logger_config import logger
from app.utils.hepler import Helper
from app.services.llmClientService import LLMClient
from app.services.aws_service import AWSService
from app.services.getTextService import GetText

class QuestionGenerationServiceZena:

    @classmethod
    async def questionGenerationZena(cls,bdClient, lmodel, jobDescription, jobDescriptionUrl, isText, skills, totalTime, previous_questions,region):
        try:

            jd_summary_prompt_template = await Helper.read_prompt("app/static/job_summary_prompt.txt")

            if isText:
                jd_prompt = jd_summary_prompt_template.format(job_description=jobDescription)
            else:
                path = await AWSService.download_file_from_s3(jobDescriptionUrl,'app/static/JD/')
                job_Description = GetText.getText(path)

                if not job_Description:
                    logger.info("Error: Unable to parse job description")
                    return None

                await Helper.delete_file(path)
                jd_prompt = jd_summary_prompt_template.format(job_description=job_Description)

                try:
                     os.remove(path)
                     logger.info(f"The file {path} has been deleted.")
                except FileNotFoundError:
                     logger.error(f"The file {path} was not found.")
                except PermissionError:
                     print(f"Permission denied to delete the file {path}.")
                except Exception as e:
                    print(f"An error occurred: {e}")

            jdSummary = LLMClient.BedRockLLM(bdClient, jd_prompt, lmodel)

            if not jdSummary:
                logger.info("Error: Unable to summarized job description.")
                return None

            # Extract skill information
            skillName, skillLevel, noOfQuestion = [], [], []
            for skill in skills:
                skillName.append(skill.name)
                skillLevel.append(skill.level)
                noOfQuestion.append(skill.totalQuestions)

            previous_questions_list = [
            previous_questions
            ]

            previous_questions_json = {
                "previous_questions": [question.question for question in previous_questions_list[0]]
            }

            if not skillName or not (len(skillName) == len(skillLevel) == len(noOfQuestion)):
                logger.info("Inconsistent list lengths in the response.")
                return None

            question_prompt_template = await Helper.read_prompt("app/static/question_generation_prompt_zena.txt")

            prompt = question_prompt_template.format(
                SJD=jdSummary,
                keySkills=skillName,
                proficiencyLevel=skillLevel,
                questionsPerSkill=noOfQuestion,
                previously_generated_questions=previous_questions_json
            )
            logger.info(prompt)
            responses = LLMClient.BedRockLLM(bdClient, prompt, lmodel)
            logger.info(responses)

            if responses:
                logger.info("All skills have the correct number of questions by ZENA.")
                questions_json = Helper.format_question_json(responses)
                logger.info(f"Questions JSON: {questions_json}")

                if not questions_json:
                    logger.error("Failed to convert question into the json format by ZENA")
                    return None
                return questions_json

        except Exception as e:
            logger.error(f"Failed to generate skill level for question by ZENA: {str(e)}")
            return None
