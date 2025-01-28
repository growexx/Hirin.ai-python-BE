import json
from app.services.GetSQSMessage import SQSMessage
from app.utils.config_loader import Config
from app.utils.logger_config import logger
from app.services.BucketService import BucketReadService
from app.services.getTextService import GetText
from app.services.llmClientService import LLMClient
from app.utils.hepler import Helper
from datetime import datetime
from app.services.SNSService import SNSSender
import boto3


class ResumeRelevanceScorProcessor:

    def __init__(self):
        try:
            self.SNS_ARN = Config.get('SNS','sns_arn')
            self.AWS_REGION = Config.get('AWS','region')
            self.bdModel = Config.get('BEDROCK','model')
            
        except Exception as e:
            logger.error(f"Error occured while reading the configuration")
        try:
            self.bd_client = boto3.client(
                "bedrock-runtime", 
                region_name = self.AWS_REGION)
        except Exception as e:
            logger.info(f"Exception occured while creating LLM client : {e}")


    async def getCVScore(self, task_queue,sqsUrl):
        try:
            subject = "CV - screening"
            resume = ''
            resumePath = ''
            lammaRelevanceSummary = ''
            path = ''
            jobDescriptionPromptTemplate = ''
            todayDate = datetime.now().date()
            relevanceSummary = ''

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
                        break
                        
                             
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
                    logger.info(f"Error: Unable to dowmload resume")
                    error = "Error:  Unable to download resume"
                    await Helper.delete_file(resumePath)
                    await SNSSender.send_error_message_to_sns_async(error, message_data, subject, '{}', self.AWS_REGION,self.SNS_ARN)
                    await SQSMessage.delete_message(message,sqsUrl,self.AWS_REGION)
                    break

                
                if resume:
                    await Helper.delete_file(resumePath)
                else:
                    logger.info(f"Error: Unable to parse resume")
                    error = "Error while processing CV:  Unable to parse resume"
                    await Helper.delete_file(resumePath)
                    await SNSSender.send_error_message_to_sns_async(error, message_data, subject, '{}', self.AWS_REGION,self.SNS_ARN)
                    await SQSMessage.delete_message(message,sqsUrl,self.AWS_REGION)
                    break


                if message_data['job_description_type'].lower() == 'url':
                    path = await BucketReadService.download_file_from_s3(message_data['job_description_url'],'app/static/JD/') 
                    job_Description = GetText.getText(path)
                    
                    if not job_Description:
                        logger.info("Error: Unable to parse job description")
                        return None
                    
                    prompt = jobDescriptionPromptTemplate.format(job_description=job_Description)
                    lammaJDSummary = LLMClient.BedRockLLM(self.bd_client,prompt,self.bdModel)

                    if lammaJDSummary != "" and resume != "":
                        relevance_prompt_template = await Helper.read_prompt('app/static/ResumeRelevanceJsonFormatPrompt.txt')
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

                    lammaJDSummary = message_data['job_description'] 
                    if lammaJDSummary != "" and resume != "":

                        relevance_prompt_template = await Helper.read_prompt('app/static/ResumeRelevanceJsonFormatPrompt.txt')
                        outJsonFormat = await Helper.read_prompt('app/static/OutputJsonFormat.txt')

                        if relevance_prompt_template != "" and outJsonFormat != "":
                            prompt = relevance_prompt_template.format(job_description=lammaJDSummary,resume=resume,date=todayDate,json_out_format=outJsonFormat)
                            lammaRelevanceSummary = Helper.get_response_with_retry(prompt,self.bd_client,self.bdModel)
                    
                    if lammaRelevanceSummary != '':
                        relevanceSummary = Helper.json_output_formatter(lammaRelevanceSummary,lammaJDSummary,message_data['metadata'])
                       
                        response = await SNSSender.send_message_to_sns_async(relevanceSummary,subject,self.AWS_REGION,self.SNS_ARN)
                        if response:
                            logger.info(f"response:{response}")
                            await SQSMessage.delete_message(message,sqsUrl,self.AWS_REGION)
                         
                    else:   
                        error = f"Error: Unable to process the cv"
                        await SNSSender.send_error_message_to_sns_async(error, message_data, subject, '{}', self.AWS_REGION,self.SNS_ARN)
                        await SQSMessage.delete_message(message,sqsUrl,self.AWS_REGION)
                        break
                    

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
            await SNSSender.send_error_message_to_sns_async(str(e), message_data, subject, '{}', self.AWS_REGION,self.SNS_ARN)
            await SQSMessage.delete_message(message,sqsUrl,self.AWS_REGION)
        finally:
            task_queue.task_done()


    
 
