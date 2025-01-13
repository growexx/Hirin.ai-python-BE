from app.logger_config import logger
from app.utils.hepler import Helper
from app.services.llmClientService import LLMClient
import asyncio

class JobDescriptionCreationService:
    
    
    @classmethod
    async def createJobDescription(cls,client, bdmodel, jobSummary):
        try:
            prompt_template = await Helper.read_prompt("app/static/job_description_creation_prompt.txt")
            prompt = prompt_template.format(job_summary=jobSummary)
        
            job_description = LLMClient.BedRockLLM(client, prompt, bdmodel)
            
            if not job_description:
                logger.info("Error: No job description generated.")
                return None
            
            return job_description

        except Exception as e:
            logger.error(f"Failed to generate Job description: {str(e)}")
            return None

    