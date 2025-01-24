from app.logger_config import logger
import aiofiles
import json
import re


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
    def standardize_llm_response(cls,raw_response):
        
        default_response = {
            "keySkills": [],
            "proficiencyLevel": [],
            "questionsPerSkill": []
        }
        
        try:
            if isinstance(raw_response, str):
                raw_response = raw_response.replace("json", "", 1)
                raw_response = raw_response.strip('`')
                raw_response = raw_response.strip()
                response = json.loads(raw_response)
                   
            elif isinstance(raw_response, dict):
                response = raw_response
            else:
                raise ValueError("Invalid input format. Expected a JSON string or dictionary.")
            
            
            if "Key Skills" in response and isinstance(response["Key Skills"], list):
                default_response["keySkills"] = response["Key Skills"]
            if "Proficiency Level" in response:
                if isinstance(response["Proficiency Level"], list):
                    default_response["proficiencyLevel"] = response["Proficiency Level"]
                elif isinstance(response["Proficiency Level"], dict):
                    default_response["proficiencyLevel"] = list(response["Proficiency Level"].values())

            if "Questions per skill" in response:
                if isinstance(response["Questions per skill"], list):
                    default_response["questionsPerSkill"] = response["Questions per skill"]
                elif isinstance(response["Questions per skill"], dict):
                    default_response["questionsPerSkill"] = list(response["Questions per skill"].values())
            
            if not (len(default_response["keySkills"]) == len(default_response["proficiencyLevel"]) == len(default_response["questionsPerSkill"])):
                raise ValueError("Inconsistent list lengths in the response.")
        
        except (json.JSONDecodeError, ValueError) as e:
            print(f"Error processing response: {e}")
            return default_response
        
        return default_response
    

    @classmethod
    def format_question_json(cls,inputQuestion):
        pattern = r"Question\s*Number\s*\d*:\s*(.*?)\nEstimated\s*Time:\s*(\d*)\s*minutes\n.*?Key\s*Skill\s*:\s*(.*?)\n"
        questions = {} 
        matches = re.findall(pattern, inputQuestion, re.DOTALL)
        
        for match in matches:

            question, time, skill = match
            time = int(time)  
            
            if skill not in questions:
                questions[skill] = []
            questions[skill].append({
                    "question": question.strip(),
                    "time": int(time)
                    })
            

        final_json = questions
        json_output = json.dumps(final_json, indent=4)
        return final_json

    
