import asyncio
import aioboto3
import json
from app.services.GetSQSMessage import SQSMessage
from app.utils.config_loader import Config
from app.utils.logger_config import logger
from app.services.BucketService import BucketReadService
from app.services.getTextService import GetText
from app.services.llmClientService import LLMClient
from app.utils.hepler import Helper
from groq import Groq
from openai import OpenAI
from datetime import datetime
from app.services.SNSService import SNSSender
import boto3


class ResumeRelevanceScorProcessor:

    def __init__(self):
        try:
            self.GROQ_KEY = Config.get('GROQ','api_key')
            self.GROQ_MODEL = Config.get('GROQ','lModel')
            self.OPENAI_KEY = Config.get('OPENAI','api_key')
            self.OPENAI_MODEL = Config.get('OPENAI','model')
            self.SNS_ARN = Config.get('SNS','sns_arn')
            self.AWS_REGION = Config.get('AWS','region')
            self.bdModel = Config.get('BEDROCK','model'),
            
        except Exception as e:
            logger.error(f"Error occured while reading the configuration")
        try:
            self.groqClient = Groq(api_key=self.GROQ_KEY)
            self.openAIClient = OpenAI(api_key=self.OPENAI_KEY)
            self.bd_client = boto3.client("bedrock-runtime",region_name = self.AWS_REGION)
        except Exception as e:
            logger.info(f"Exception occured while creating LLM client : {e}")


    async def getCVScore(self, task_queue,sqsUrl):
        try:
            resume = ''
            resumePath = ''
            lammaRelevanceSummary = ''
            path = ''
            jobDescriptionPromptTemplate = ''
            todayDate = datetime.now().date()

            while True:
                message= await task_queue.get()
                if message is None:
                    break
                
                message_body = message['Body']

                try:
                    messageData = json.loads(message_body)
                    logger.info(f"Decoded message body: {messageData}")
                except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON: {e}")
                        
                actualMessageBody = messageData['Message']

                try:
                    message_data = json.loads(actualMessageBody)
                    logger.info(f"Decoded message data: {message_data}")
                except json.JSONDecodeError as e:
                        logger.error(f"Error decoding JSON: {e}")

                jobDescriptionPromptTemplate = await Helper.read_prompt('app/static/JobSummaryPrompt.txt')

                resumePath = await BucketReadService.download_file_from_s3(message_data['resume_url'],'app/static/Resume/')

                if resumePath:
                    resume = GetText.getText(resumePath)
                else:
                    logger.info(f"Error: Unable to pasred resume")
                
                if resume:
                    await Helper.delete_file(resumePath)

                if message_data['job_description_type'].lower() == 'url':
                    path = await BucketReadService.download_file_from_s3(message_data['job_description_url'],'app/static/JD/') 
                    job_Description = GetText.getText(path)
                    
                    if not job_Description:
                        logger.info("Error: Unable to parse job description")
                        return None
                    
                    prompt = jobDescriptionPromptTemplate.format(job_description=job_Description)
                    lammaJDSummary = LLMClient.BedRockLLM(self.bd_client,prompt,self.bdModel)

                    if lammaJDSummary != "" and resume != "":
                        relevance_prompt_template = await Helper.read_prompt('app/static/ResumeRelevancePrompt.txt')
                        prompt = relevance_prompt_template.format(job_description=lammaJDSummary,resume=resume,date=todayDate)
                        lammaRelevanceSummary = LLMClient.BedRockLLM(self.bd_client,prompt,self.bdModel)
                        logger.info(f"lammaRelevanceSummary: {lammaRelevanceSummary}")
                    

                    if lammaRelevanceSummary:
                        relevanceSummary = Helper.output_formatter(lammaRelevanceSummary,message_data['metadata'])
                        subject = "CV - screening"
                        response = await SNSSender.send_message_to_sns_async(relevanceSummary,subject,self.AWS_REGION,self.SNS_ARN)
                        if response:
                            print(f"response:{response}")
                            await SQSMessage.delete_message(message,sqsUrl,self.AWS_REGION)
                        
                            
                    else:
                        error = f"unable to process the cv for {message_data['metadata']}"
                        subject = "CV - screening"
                        await SNSSender.send_message_to_sns_async(relevanceSummary,subject,self.AWS_REGION,self.SNS_ARN)

                        
                    # openAIJDSummary=LLMClient.OpenAILLM(self.OPENAI_KEYClient,prompt,self.OPENAI_MODEL)

                    # if openAIJDSummary != "" and resume != "":
                    #     relevance_prompt_template = await Helper.read_prompt('app/static/ResumeRelevancePrompt.txt')
                    #     prompt = relevance_prompt_template.format(job_description=openAIJDSummary,resume=resume)
                    #     LLMClient.OpenAILLM(self.openAIClient,prompt,self.OPENAI_MODEL)

                    # gemmaJDSummary = LLMClient.GemmaLLM(gClient,prompt,gmodel)
                    # if gemmaJDSummary != "" and resume != "":
                    #     relevance_prompt_template = await Helper.read_prompt('app/static/ResumeRelevancePrompt.txt')
                    #     prompt = relevance_prompt_template.format(job_description=openAIJDSummary,resume=resume)
                    #     LLMClient.GemmaLLM(gClient,prompt,gmodel)
                
                elif message_data['job_description_type'].lower() == 'text':

                    # prompt = jobDescriptionPromptTemplate.format(job_description=message_data['job_description'])
                    # lammaJDSummary = LLMClient.GroqLLM(self.groqClient,prompt,self.GROQ_MODEL)

                    lammaJDSummary = message_data['job_description'] 
                    if lammaJDSummary != "" and resume != "":
                        relevance_prompt_template = await Helper.read_prompt('app/static/ResumeRelevancePrompt.txt')
                        prompt = relevance_prompt_template.format(job_description=lammaJDSummary,resume=resume,date=todayDate)
                        lammaRelevanceSummary = LLMClient.BedRockLLM(self.bd_client,prompt,self.bdModel)
                        logger.info(f"lammaRelevanceSummary: {lammaRelevanceSummary}")
                    
                    if lammaRelevanceSummary:
                        relevanceSummary = Helper.output_formatter(lammaRelevanceSummary,message_data['metadata'])
                        subject = "CV - screening"
                        response = await SNSSender.send_message_to_sns_async(relevanceSummary,subject,self.AWS_REGION,self.SNS_ARN)
                        if response:
                            print(f"response:{response}")
                            await SQSMessage.delete_message(message,sqsUrl,self.AWS_REGION)
                        
                            
                    else:
                        error = f"unable to process the cv for {message_data['metadata']}"
                        subject = "CV - screening"
                        await SNSSender.send_message_to_sns_async(relevanceSummary,subject,self.AWS_REGION,self.SNS_ARN)
                    

                    # openAIJDSummary=LLMClient.OpenAILLM(self.OPENAI_KEYClient,prompt,self.OPENAI_MODEL)

                    # if openAIJDSummary != "" and resume != "":
                    #     relevance_prompt_template = await Helper.read_prompt('app/static/ResumeRelevancePrompt.txt')
                    #     prompt = relevance_prompt_template.format(job_description=openAIJDSummary,resume=resume)
                    #     LLMClient.OpenAILLM(self.openAIClient,prompt,self.OPENAI_MODEL)

                    # gemmaJDSummary = LLMClient.GemmaLLM(gClient,prompt,gmodel)
                    # if gemmaJDSummary != "" and resume != "":
                    #     relevance_prompt_template = await Helper.read_prompt('app/static/ResumeRelevancePrompt.txt')
                    #     prompt = relevance_prompt_template.format(job_description=openAIJDSummary,resume=resume)
                    #     LLMClient.GemmaLLM(gClient,prompt,gmodel)

                task_queue.task_done()
        except Exception as e:
            logger.error(f"{e} error occured while evaluating cv score.")
        finally:
            task_queue.task_done()
