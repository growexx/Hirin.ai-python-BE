# import os
# from app.logger_config import logger
# from app.utils.hepler import Helper
# from app.services.llmClientService import LLMClient
# import asyncio
# from app.services.aws_service import AWSService
# from app.services.getTextService import GetText

# class QuestionGenerationService:

#     @classmethod
#     async def questionGeneration(cls, groq_client, lmodel, jobDescription,jobDescriptionUrl,isText,skills,totalTime):
#         try:

#             jd_summary_prompt_template = await Helper.read_prompt("app/static/job_summary_prompt.txt")
#             # questionGenerationPromptTemplate = await Helper.read_prompt("app/static/question_generation_prompt.txt")
#             jd_prompt = ''

#             if isText:
#                 jd_prompt = jd_summary_prompt_template.format(job_description=jobDescription)
#             else:
#                 path = await AWSService.download_file_from_s3(jobDescriptionUrl,'app/static/JD/')
#                 job_Description = GetText.getText(path)

#                 if not job_Description:
#                     logger.info("Error: Unable to parse job description")
#                     return None

#                 await Helper.delete_file(path)
#                 jd_prompt = jd_summary_prompt_template.format(job_description=job_Description)

#                 try:
#                      os.remove(path)
#                      logger.info(f"The file {path} has been deleted.")
#                 except FileNotFoundError:
#                      logger.error(f"The file {path} was not found.")
#                 except PermissionError:
#                      print(f"Permission denied to delete the file {path}.")
#                 except Exception as e:
#                     print(f"An error occurred: {e}")

#             jdSummary = LLMClient.GroqLLM(groq_client, jd_prompt, lmodel)

#             if not jdSummary:
#                 logger.info("Error: Unable to summarized job description.")
#                 return None


#             skillName = []
#             skillLevel = []
#             noOfQuestion = []

#             print(f"skills:{skills}")

#             for skill in skills:
#                 skillName.append(skill.name)
#                 skillLevel.append(skill.level)
#                 noOfQuestion.append(skill.totalQuestions)


#             if not skillName or not (len(skillName) == len(skillLevel) == len(noOfQuestion)):
#                 logger.info("Inconsistent list lengths in the response.")
#                 return None

#             questionGenerationPrompt = ''
#             sumQuestionsPerSkill = sum(noOfQuestion)
#             print(f"sumQuestionsPerSkill:{sumQuestionsPerSkill}")

#             if int(totalTime) == 0:
#                 questionGenerationPromptTemplate = await Helper.read_prompt("app/static/question_generation_withouttime_prompt.txt")
#                 questionGenerationPrompt = questionGenerationPromptTemplate.format(SJD=jdSummary,keySkills=skillName,proficiencyLevel=skillLevel,questionsPerSkill=noOfQuestion,interview_duration="",sumquestionsPerSkill=sumQuestionsPerSkill)
#             else:
#                 questionGenerationPromptTemplate = await Helper.read_prompt("app/static/question_generation_prompt.txt")

#             questionGenerationPrompt = questionGenerationPromptTemplate.format(SJD=jdSummary,keySkills=skillName,proficiencyLevel=skillLevel,questionsPerSkill=noOfQuestion,interview_duration=totalTime,sumquestionsPerSkill=sumQuestionsPerSkill)
#             questionsIntermediate = LLMClient.GroqLLM(groq_client, questionGenerationPrompt, lmodel)

#             while True:
#                 if questionsIntermediate is None:
#                     logger.info("Error: LLM generation failed. Exiting.")
#                     return None

#                 questionsIntermediate, mismatched_skills, expected_questions, mismatched_proficiency = Helper.remove_extra_questions(
#                 questionsIntermediate, skillName, noOfQuestion, skillLevel)

#                 if not mismatched_skills:
#                     logger.info("All skills have the correct number of questions.")
#                     questions_json = Helper.format_question_json(questionsIntermediate)

#                     if not questions_json:
#                         logger.error("Failed to convert question into the json formate")
#                         return None
#                     return questions_json
#                 else:
#                     logger.info(f"Regenerating for mismatched skills: {mismatched_skills}")
#                     sumQuestionsPerSkill = sum(expected_questions)
#                     prompt = questionGenerationPromptTemplate.format(SJD=jdSummary,keySkills=mismatched_skills,proficiencyLevel=mismatched_proficiency,questionsPerSkill=expected_questions,interview_duration=totalTime,sumquestionsPerSkill=sumQuestionsPerSkill)
#                     regenerated_questions = LLMClient.GroqLLM(groq_client, prompt, lmodel)

#                     if regenerated_questions:
#                         questionsIntermediate += "\n" + regenerated_questions

#         except Exception as e:
#             logger.error(f"Failed to generate skill level for question: {str(e)}")
#             return None
import os
import asyncio
from app.logger_config import logger
from app.utils.hepler import Helper
from app.services.llmClientService import LLMClient
from app.services.aws_service import AWSService
from app.services.getTextService import GetText

class QuestionGenerationService:

    @classmethod
    async def questionGeneration(cls, groq_client, async_groq_client, lmodel, jobDescription, jobDescriptionUrl, isText, skills, totalTime):
        try:
            # Job description handling (Blocks 3 and 4)
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

            jdSummary = LLMClient.GroqLLM(groq_client, jd_prompt, lmodel)

            if not jdSummary:
                logger.info("Error: Unable to summarized job description.")
                return None

            # if isText:
            #     jd_prompt = jd_summary_prompt_template.format(job_description=jobDescription)
            # else:
            #     path = await AWSService.download_file_from_s3(jobDescriptionUrl, 'app/static/JD/')
            #     job_Description = GetText.getText(path)

            #     if not job_Description:
            #         logger.info("Error: Unable to parse job description")
            #         return None

            #     await Helper.delete_file(path)
            #     jd_prompt = jd_summary_prompt_template.format(job_description=job_Description)

            #     try:
            #         os.remove(path)
            #     except Exception as e:
            #         logger.error(f"Error while deleting file: {e}")

            # # Summarize job description using LLMClient
            # jdSummary = await LLMClient.call_groq_llm(groq_client, jd_prompt, lmodel)

            # if not jdSummary:
            #     logger.info("Error: Unable to summarize job description.")
            #     return None

            # Extract skill information
            skillName, skillLevel, noOfQuestion = [], [], []
            for skill in skills:
                skillName.append(skill.name)
                skillLevel.append(skill.level)
                noOfQuestion.append(skill.totalQuestions)

            if not skillName or not (len(skillName) == len(skillLevel) == len(noOfQuestion)):
                logger.info("Inconsistent list lengths in the response.")
                return None

            # Chunk inputs
            chunk_size = 2  # Number of skills per chunk
            chunks = list(cls.chunk_inputs(skillName, noOfQuestion, skillLevel, chunk_size))
            # print(chunks)
            # Ensure no data is lost during chunking
            assert sum(len(chunk[0]) for chunk in chunks) == len(skillName), \
                "Chunking error: Mismatch in skillName count."

            # Read the question generation prompt template
            question_prompt_template = await Helper.read_prompt("app/static/question_generation_prompt.txt")

            # Generate prompts dynamically
            prompts = []
            for chunk in chunks:
                print("Current Chunk",chunk)
                prompt = question_prompt_template.format(
                    SJD=jdSummary,
                    keySkills=chunk[0],
                    proficiencyLevel=chunk[2],
                    questionsPerSkill=chunk[1],
                    interview_duration=totalTime if totalTime > 0 else "N/A",
                    sumquestionsPerSkill=sum(chunk[1])
                )
                logger.info(chunk)
                logger.info(prompt)
                prompts.append(prompt)

            # Asynchronous API calls
            tasks = [LLMClient.call_groq_llm(async_groq_client, prompt, lmodel) for prompt in prompts]
            responses = await asyncio.gather(*tasks)

            # Validation and re-run logic
            retries = 2
            for _ in range(retries):
                re_run_indices = []
                for idx, (response, chunk) in enumerate(zip(responses, chunks)):
                    actual_counts = cls.validate_questions(response, chunk[0])
                    if actual_counts != chunk[1]:
                        logger.info(f"Validation failed for chunk {idx + 1}. Expected: {chunk[1]}, Actual: {actual_counts}")
                        re_run_indices.append(idx)

                if not re_run_indices:
                    break

                re_run_prompts = [prompts[i] for i in re_run_indices]
                re_run_tasks = [LLMClient.call_groq_llm(groq_client, prompt, lmodel) for prompt in re_run_prompts]
                re_run_responses = await asyncio.gather(*re_run_tasks)

                for idx, response in zip(re_run_indices, re_run_responses):
                    responses[idx] = response

            # Combine responses and save to file
            combined_responses = "\n".join(responses)
            if combined_responses:
                logger.info("All skills have the correct number of questions.")
                questions_json = Helper.format_question_json(combined_responses)

                if not questions_json:
                    logger.error("Failed to convert question into the json formate")
                    return None
                return questions_json

        except Exception as e:
            logger.error(f"Failed to generate skill level for question: {str(e)}")
            return None

    @staticmethod
    def chunk_inputs(keySkills, questionsPerSkill, proficiencyLevel, chunk_size):
        for i in range(0, len(keySkills), chunk_size):
            yield (
                keySkills[i:i + chunk_size],
                questionsPerSkill[i:i + chunk_size],
                proficiencyLevel[i:i + chunk_size]
            )

    @staticmethod
    def validate_questions(response, keySkills):
        actual_counts = []
        for skill in keySkills:
            skill_count = response.lower().count(f"key skill: {skill.lower()}")
            actual_counts.append(skill_count)
        return actual_counts
