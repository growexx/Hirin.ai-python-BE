import asyncio
import aioboto3
from app.services.GetSQSMessage import SQSMessage
from app.utils.config_loader import Config
from app.services.ResumeProcessor import ResumeRelevanceScorProcessor
from app.utils.logger_config import logger

class QueueProcessor:
    def __init__(self,  batch_size=10, num_workers=5):
        try:

            self.queueUrl = Config.get('SQS','queue_url')
            self.AWS_REGION = Config.get('AWS','region')
            self.AWS_ACCESS_KEY_ID = Config.get('AWS','access_key')
            self.AWS_SECRET_ACCESS_KEY = Config.get('AWS','access_secret')           
            self.batch_size = batch_size
            self.num_workers = num_workers

        except Exception as e:
            logger.error(f"Error occured while reading the configuration")
    

    async def process_queue_message_in_batches(self):
        try:
            task_queue = asyncio.Queue()
            print(f"task_queue: {task_queue}")
            workers = []
            resumeProcess = ResumeRelevanceScorProcessor()

            for _ in range(self.num_workers):
                worker_task = asyncio.create_task(resumeProcess.getCVScore(task_queue,self.AWS_REGION,self.AWS_ACCESS_KEY_ID,self.AWS_SECRET_ACCESS_KEY,self.queueUrl))
                workers.append(worker_task)
    
            async with aioboto3.Session().client('sqs',region_name=self.AWS_REGION,
            aws_access_key_id=self.AWS_ACCESS_KEY_ID,
            aws_secret_access_key=self.AWS_SECRET_ACCESS_KEY) as sqs:
                
                while True:
                    messages = await SQSMessage.receive_messages(sqs,self.queueUrl,10,5)
                    
                    if not messages:
                        print("No messages received. Exiting.")
                        break
                
                    for message in messages:
                        await task_queue.put(message)
    
                    await task_queue.join()
            for _ in range(self.num_workers):
                await task_queue.put(None)

            await asyncio.gather(*workers)
        except Exception as e:
            logger.error(f"Exception occured CV Processor: {e}")
        finally:
            for _ in range(self.num_workers):
                await task_queue.put(None)
                
            await asyncio.gather(*workers)
    

            

    
        