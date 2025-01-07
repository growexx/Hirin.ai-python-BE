from flask import Blueprint, jsonify, request
import asyncio
from app import auth
from app.utils.config_loader import Config
from openai import OpenAI
from groq import Groq
from app.logger_config import logger, listener
from app.services.job_description_creation_service import JobDescriptionCreationService
from app.services.question_skill_level_creation_service import QuestionSkillLevelCreationService
from app.services.question_generation_service import QuestionGenerationService
from app.dto.job_desription_creation_dto import JobDescriptionInputDTO,JobDescriptionOutputDTO
from app.dto.question_skill_creation_dto import QuestionSkillCreationInputDTO,QuestionSkillCreationOutputDTO
from app.dto.question_generation_dto import QuestionGenerationInputDTO
from app.dto.job_summary_dto import JobSummaryRequestDTO, JobSummaryResponseDTO
from app.services.job_summary_service import JobSummaryCreationService


api_blueprint = Blueprint('api', __name__)

try:
    username = Config.get('Auth','username')
    password = Config.get('Auth','password')
except Exception as e:
    logger.error(f"Failed to load API keys: {e}")
    raise


try:
    API_KEYS = {
        "OPENAI_API_KEY": Config.get('Openapi','api_key'),
        "GROQ_API_KEY": Config.get('Groq','api_key')
    }
    Models = {
        "OPENAI_MODLE": Config.get('Openapi','model'),
        "GROQ_MODLE" : Config.get('Groq','lModel')
    }
except Exception as e:
    logger.error(f"Failed to load API keys: {e}")
    raise

try:
    openai_client = OpenAI(api_key=API_KEYS["OPENAI_API_KEY"])
    groq_client = Groq(api_key=API_KEYS["GROQ_API_KEY"])
except Exception as e:
    logger.error(f"Failed to initialize API clients: {e}")
    raise

try:
   openai_client = OpenAI(api_key=API_KEYS["OPENAI_API_KEY"])
   groq_client = Groq(api_key=API_KEYS["GROQ_API_KEY"])
except Exception as e:
   logger.error(f"Failed to initialize API clients: {e}")
   raise



users = {
    username : password
}

@auth.verify_password
def verify_password(username, password):
    if users.get(username) == password:
        return username
    

@api_blueprint.route('/create-job-description',methods=['POST'])
@auth.login_required

async def job_description_creation():
     try:
          job_summary = JobDescriptionInputDTO(**request.get_json())
          if not job_summary:
            return jsonify({
                "status": "error",
                "message": "Please provide the missing field."
            }), 400
          
          job_description = await JobDescriptionCreationService.createJobDescription(groq_client,Models['GROQ_MODLE'],job_summary) 
          response = JobDescriptionOutputDTO(
            status="success",
            job_description=job_description
        )
          return jsonify(response.model_dump()), 200
     
               
     except Exception as e:
          return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500
     

@api_blueprint.route('/create-complexity-skills',methods= ['POST'])
@auth.login_required
async def skills_no_questions_creation():
    try:
        data = QuestionSkillCreationInputDTO(**request.json)
        if not data:
             return jsonify({
                "status": "error",
                "message": "Please provide the missing field."
            }), 400
        
        questionSkillLevel = await QuestionSkillLevelCreationService.questionskillcreation(groq_client,Models['GROQ_MODLE'],data.job_description,data.total_questions,data.interview_duration,data.job_description_type)
        response = QuestionSkillCreationOutputDTO(
        status="success",
        key_skills=questionSkillLevel['keySkills'],
        proficiency_level=questionSkillLevel['proficiencyLevel'],
        questions_per_skill=questionSkillLevel['questionsPerSkill'],
        message="Data successfully processed.")

        return jsonify(response.model_dump()), 200 

    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500


@api_blueprint.route('/question-generation', methods = ['POST'])
@auth.login_required
async def question_generation():
    try:
        data = QuestionGenerationInputDTO(**request.json)
        if not data:
             return jsonify({
                "status": "error",
                "message": "Please provide the missing field."
            }), 400
        
        questions = await QuestionGenerationService.questionGeneration(groq_client,Models['GROQ_MODLE'],data.job_description,data.job_description_url,data.is_text,data.skills,data.total_time)

        return jsonify({
            "status": "success",
            "message": "question generated successfully...",
            "question":questions

        }), 200
        
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500
    

@api_blueprint.route('/job-summarization', methods = ['POST'])
@auth.login_required
async def job_summarizattion():
    try:

        data = JobSummaryRequestDTO(**request.json)
        if not data:
             return jsonify({
                "status": "error",
                "message": "Please provide the missing field."
            }), 400
        
        jobSummary = await JobSummaryCreationService.createJobSummary(groq_client,Models['GROQ_MODLE'],data)
        return jsonify({
            "status": "success",
            "message": "summary generated successfully...",
            "job_summary":jobSummary

        }), 200
        
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"An error occurred: {str(e)}"
        }), 500



