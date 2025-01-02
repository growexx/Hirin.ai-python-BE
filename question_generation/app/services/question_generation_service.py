import os
from app.logger_config import logger
from app.utils.hepler import Helper
from app.services.llmClientService import LLMClient
import asyncio
from app.services.aws_service import AWSService
from app.services.getTextService import GetText

class QuestionGenerationService:

    @classmethod
    async def questionGeneration(cls, groq_client, lmodel, jobDescription,jobDescriptionUrl,isText,skills,totalTime):
        try:

            jd_summary_prompt_template = await Helper.read_prompt("app/static/job_summary_prompt.txt")
            jd_prompt = ''

            if isText:
                jd_prompt = jd_summary_prompt_template.format(job_description=jobDescription)
            else:
                path = await AWSService.download_file_from_s3('your-bucket-name', jobDescriptionUrl, '/path/to/save/your/file.txt')
                job_Description = GetText.getText(path)

                if not job_Description:
                    logger.info("Error: Unable to parse job description")
                    return None
                
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

            jdSummary = LLMClient.GroqLLM(groq_client, jd_prompt, lmodel)

            if not jdSummary:
                logger.info("Error: Unable to summarized job description.")
                return None

          
            skillName = []
            skillLevel = []
            noOfQuestion = []

            print(f"skills:{skills}")
         
            for skill in skills:
                print(f"skill:{skill}")
                skillName.append(skill.name)
                skillLevel.append(skill.level)
                noOfQuestion.append(skill.totalQuestions)


            if not skillName or not (len(skillName) == len(skillLevel) == len(noOfQuestion)):
                logger.info("Inconsistent list lengths in the response.")
                return None
            
            
            
            print(f"skillLevel")
            
            
            questionGenerationPrompt = ''

            if int(totalTime) == 0:
                questionGenerationPromptTemplate = await Helper.read_prompt("app/static/question_generation_withouttime_prompt.txt")
                questionGenerationPrompt = questionGenerationPromptTemplate.format(SJD=jdSummary,keySkills=skillName,proficiencyLevel=skillLevel,questionsPerSkill=noOfQuestion) 
            else:
                questionGenerationPromptTemplate = await Helper.read_prompt("app/static/question_generation_prompt.txt")
                questionGenerationPrompt = questionGenerationPromptTemplate.format(SJD=jdSummary,keySkills=skillName,proficiencyLevel=skillLevel,questionsPerSkill=noOfQuestion,interview_duration=totalTime) 
            
            questions = LLMClient.GroqLLM(groq_client, questionGenerationPrompt, lmodel)

            
            questions_json = Helper.format_question_json(questions)

            print(f"questions_json:{questions_json}")

            if not questions_json:
                logger.error("Failed to convert question into the json formate")
                return None
            
            return questions_json

        except Exception as e:
            logger.error(f"Failed to generate skill level for question: {str(e)}")
            return None