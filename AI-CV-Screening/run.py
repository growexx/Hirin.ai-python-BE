import asyncio
from app.services.SQSProcessor import QueueProcessor
from app.utils.config_loader import Config
import os
from app.utils.logger_config import logger

async def main():
    try:
        cvprocessor = QueueProcessor(batch_size=10, num_workers=5)
        await cvprocessor.process_queue_message_in_batches()
    except Exception as e:
        logger.error(f"Error occured while processing relevance summary: {e}")

if __name__ == "__main__":
    try:  
        confPath =  os.path.join('app/utils', 'config.ini') 
        Config.load_config(confPath)
        asyncio.run(main())
    except Exception as e:
        logger.info(f"Exception occured: {e}")
        
