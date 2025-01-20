from app.utils.logger_config import logger
from app.services.llmClientService import LLMClient
import aiofiles
import json
import re
import os


class Helper:

    @classmethod
    async def read_prompt(cls, file_name):
        try:
            async with aiofiles.open(file_name, 'r') as file:
                content = await file.read()
                logger.info(f"Successfully read prompt file: {file_name}")
                return content
        except Exception as e:
            logger.info(f"Failed to read prompt file {file_name}: {e}")
            return ""
    
    @classmethod
    async def delete_file(cls,file_path):
        if os.path.exists(file_path):
            try:
                async with aiofiles.open(file_path, 'r'):
                    pass
                os.remove(file_path)
                logger.info(f"File {file_path} has been deleted.")
            except Exception as e:
                logger.info(f"Error deleting file {file_path}: {e}")
        else:
            logger.info(f"File {file_path} does not exist.")

    @classmethod
    def extract_list(cls,pattern, text):
        try:
            match = re.search(pattern, text, re.DOTALL | re.IGNORECASE)
            if match:
                items = match.group(1).strip().split("\n")
                return [item.strip().lstrip("- ") for item in items]
            return []
        except Exception as e:
            logger.error(f"Error while extrcating the list : {e}")

    
    @classmethod
    def output_formatter(cls, inputstring, metadata):

        try:
            technical_skills = {
            "must_have_skills": {
                "match": Helper.extract_list(r"must-have\s*match\s*skills:\n(.*?)\n\n", inputstring),
                "unmatch": Helper.extract_list(r"must-have\s*missing\s*skills:\n(.*?)\n\n", inputstring),
            },
            "good_to_have_skills": {
                "match": Helper.extract_list(r"good-to-have\s*match\s*skills:\n(.*?)\n\n", inputstring),
                "unmatch": Helper.extract_list(r"good-to-have\s*missing\s*skills:\n(.*?)\n\n", inputstring),
            },
            "job_description_experience": re.search(r"relevant\s*expericence\s*:\s*\n-\s*jd:\s*(.*?)\n", inputstring,re.IGNORECASE).group(1),
            "resume_experience": re.search(r"-\s*resume:\s*(.*?)\n", inputstring, re.IGNORECASE).group(1),
                "score": float(re.search(r"score:\s*(\d+(\.\d+)?)\n\neducation", inputstring, re.IGNORECASE).group(1)) * 10,
            }

            
            education = {
                "mentioned_jd": re.search(r"relevant\s*education\s*degree:\s*\n-\s*jd:\s*(.*?)\s*\n", inputstring, re.IGNORECASE).group(1),
                "mentioned_resume": re.search(r"-\s*resume\s*:\s*(.*?)\s*\n", inputstring, re.IGNORECASE).group(1),
                "score": float(re.search(r"score\s*:\s*(\d+(\.\d+)?)\n\nSoft\s*skills", inputstring, re.IGNORECASE).group(1)) * 10,
            }

            soft_skills = {
                "must_have_skills": {
                    "match": Helper.extract_list(r"must-have\s*match\s*skills\s*:\s*\n(.*?)\n\n", inputstring),
                    "unmatch": Helper.extract_list(r"must-have\s*Missing\s*skills\s*:\s*\n(.*?)\n\n", inputstring),
                },
                "good_to_have_skills": {
                    "match": Helper.extract_list(r"good-to-have\s*match\s*skills\s*:\s*\n(.*?)\n\n", inputstring),
                    "unmatch": Helper.extract_list(r"good-to-have\s*missing\s*skills\s*:\s*\n(.*?)\n\n", inputstring),
                },
                "score": float(re.search(r"score\s*:\s*(\d+(\.\d+)?)\n\naddtional\s*factor", inputstring,re.IGNORECASE).group(1))*10,
            }

        
            additional_factor = {
                "factor": [re.search(r"factor\s*:\s*(.*?)\n", inputstring, re.IGNORECASE).group(1)],
                "score": float(re.search(r"score\s*:\s*(\d+(\.\d+)?)\n\ntotal\s*score", inputstring, re.IGNORECASE).group(1))*10,
            }

            output_json = {
                "metadata": metadata,
                "event": "cvScreeningEnded",
                "job_description_summary": "",
                "cv_score": float(re.search(r"total\s*score\s*:\s*(\d+(\.\d+)?)", inputstring, re.IGNORECASE).group(1))*10,
                "technical_skills_and_experience": technical_skills,
                "education": education,
                "soft_skills": soft_skills,
                "additional_factor": additional_factor,
            }

            return json.dumps(output_json, indent=4)
        except Exception as e:
            logger.error(f"Error occured while formating the output : {e}")
            return None

    @classmethod
    def validate_output(cls, output):
        try:
            data = json.loads(output)
            required_keys = ["cv_score", "technical_skills_and_experience", "education", "soft_skills", "additional_factor"]
            for key in required_keys:
                if key not in data:
                    return False
            return True
        except (json.JSONDecodeError, KeyError):
            return False
        
    @classmethod
    def json_output_formatter(cls, inputstring, jdSummary, metadata):
        try:
            if inputstring != '' and inputstring is not None:
                json_data = json.loads(inputstring)
                json_data["metadata"] = metadata
                json_data["job_description_summary"] = jdSummary
                json_data["event"] = "cvScreeningEnded"

                return json.dumps(json_data, indent=4)
            
            return None
        except Exception as e:
            logger.error(f"Error occured while formating the output : {e}")
            return None
        
    @classmethod
    def get_response_with_retry(self,prompt,bd_client, bdModel, max_retries=3):
        try:
            for attempt in range(max_retries):
                print(f"bd_client: {bd_client}")
                print(f"prompt:{prompt}")
                print(f"model: {bdModel}")
                response = LLMClient.BedRockLLM(bd_client,prompt,bdModel)
                print(response)
                response = response.replace("```json\n", "").replace("\n```", "")

                print(response)

                if Helper.validate_output(response):
                    return response
                else:
                    print(f"Attempt {attempt + 1} failed: Invalid format. Retrying...")
                    prompt = f"The previous response was invalid. Please adhere strictly to the specified output format:\n {prompt}"

            return None
        except Exception as e:
            logger.error(f"Uanble to generate valid response : {e}")
            return None
        



    
        
    

    
