from app.logger_config import logger
from app.utils.hepler import Helper
from app.services.llmClientService import LLMClient
import asyncio
from app.services.aws_service import AWSService
from app.services.getTextService import GetText

class JobSummaryCreationService:
    
    
    @classmethod
    async def createJobSummary(cls,groqClient, lModel, jobData):
        try:
            job_description = ''
            prompt_template = await Helper.read_prompt("app/static/job_summary_cv_score_prompt.txt")
            
            if jobData.job_description_type.lower() == 'url':
                path = await AWSService.download_file_from_s3(jobData.job_description_url,'app/static/JD/')
                job_description = GetText.getText(path)

                if not job_description:
                    logger.info("Error: Unable to parse job description")
                    return None
                await Helper.delete_file(path)

            else:
                job_description = jobData.job_description

            prompt = prompt_template.format(job_description=job_description) 
            job_description = LLMClient.GroqLLM(groqClient, prompt, lModel)
            
            if not job_description:
                logger.info("Error: No job summary generated.")
                return None
            
            return job_description

        except Exception as e:
            logger.error(f"Failed to generate Job summary: {str(e)}")
            return None