import os
import requests
from urllib.parse import urlparse, unquote
from app.logger_config import logger
import aiohttp

class AWSService:

    @classmethod
    async def download_file_from_s3(url,save_dir):
       try:
        parsed_url = urlparse(url)
        path = parsed_url.path
        file_name = unquote(os.path.basename(path)).replace("'", "")
        os.makedirs(save_dir, exist_ok=True)
        save_path = os.path.join(save_dir, file_name)
        response = requests.get(url)
        
        async with aiohttp.ClientSession() as session:
            async with session.get(url) as response:
                if response.status == 200:
                    with open(save_path, 'wb') as f:
                        f.write(await response.read())
                    print(f"File downloaded successfully: {save_path}")
                    return save_path
                else:
                    print(f"Failed to download file. Status code: {response.status}")
                    return None
       except Exception as e:
        logger.error(f"Failed to download job_description from s3: {str(e)}")
        return None


