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
from app.services.question_generation_service_zena import QuestionGenerationServiceZena
from app.dto.job_desription_creation_dto import JobDescriptionInputDTO,JobDescriptionOutputDTO
from app.dto.question_skill_creation_dto import QuestionSkillCreationInputDTO,QuestionSkillCreationOutputDTO
from app.dto.question_generation_dto import QuestionGenerationInputDTO, SingleSkillQuestionGenerationInputDTO
from app.dto.job_summary_dto import JobSummaryRequestDTO, JobSummaryResponseDTO
from app.services.job_summary_service import JobSummaryCreationService
from groq import AsyncGroq
import boto3


api_blueprint = Blueprint('api', __name__)

try:
    username = Config.get('Auth','username')
    password = Config.get('Auth','password')
except Exception as e:
    logger.error(f"Failed to load API keys: {e}")
    raise


try:
    region = Config.get('BEDROCK','region')
    # API_KEYS = {
    #     "GROQ_API_KEY": Config.get('Groq','api_key')
    # }
    Models = {
        "BEDROCK_MODEL": Config.get('BEDROCK','model'),
        # "GROQ_MODLE" : Config.get('Groq','lModel')
    }
except Exception as e:
    logger.error(f"Failed to load API keys: {e}")
    raise

try:
    # groq_client = Groq(api_key=API_KEYS["GROQ_API_KEY"])
    # async_groq_client = AsyncGroq(api_key=API_KEYS["GROQ_API_KEY"])

    bd_client = boto3.client("bedrock-runtime",
        region_name = region)


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
          job_title, job_summary = JobDescriptionInputDTO(**request.get_json())
          if not job_summary:
            return jsonify({
                "status": "error",
                "message": "Please provide the missing field."
            }), 400

          job_description = await JobDescriptionCreationService.createJobDescription(bd_client,Models['BEDROCK_MODEL'],job_title, job_summary)
          if job_description.strip().lower() == "not valid":
            return {
                "status": 0,
                "message": "Please provide a relevant Job Summary",
                "data": job_description
            }, 200
          elif job_description.strip().lower() == "irrelevant":
            return {
                "status": 0,
                "message": "Please provide a relevant Job Summary",
                "data": job_description
            }, 200
          else:
            return {
                    "status": 1,
                    "message": "Job Description successfully generated",
                    "data": job_description
                }, 200

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

        questionSkillLevel = await QuestionSkillLevelCreationService.questionskillcreation(bd_client,Models['BEDROCK_MODEL'],data.job_description,data.total_questions,data.interview_duration,data.job_title,data.job_description_type)

        if 'status' in questionSkillLevel and questionSkillLevel['status'] == 0:
            return jsonify(questionSkillLevel), 200
        else:
            return {
                "status": 1,
                "message": f"Skills successfully Generated",
                "data": questionSkillLevel
            }, 200

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

        questions = await QuestionGenerationService.questionGeneration(bd_client, Models['BEDROCK_MODEL'],data.job_description,data.job_description_url,data.is_text,data.skills,data.total_time,region)

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

@api_blueprint.route('/question-generation-zena', methods = ['POST'])
@auth.login_required
async def question_generation_zena():
    try:
        data = SingleSkillQuestionGenerationInputDTO(**request.json)
        if not data:
             return jsonify({
                "status": "error",
                "message": "Please provide the missing field."
            }), 400

        questions = await QuestionGenerationServiceZena.questionGenerationZena(bd_client, Models['BEDROCK_MODEL'],data.job_description,data.job_description_url,data.is_text,data.skills,data.total_time,data.previous_questions,region)

        return jsonify({
            "status": "success",
            "message": "question generated successfully...",
            "questions":questions

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

        jobSummary = await JobSummaryCreationService.createJobSummary(bd_client,Models['BEDROCK_MODEL'],data)
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



