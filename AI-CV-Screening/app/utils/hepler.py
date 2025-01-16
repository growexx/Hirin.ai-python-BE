from app.utils.logger_config import logger
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
            print(f"metadata: {metadata}")
            print(f"inputstring : {inputstring}")
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



    
        
    

    
