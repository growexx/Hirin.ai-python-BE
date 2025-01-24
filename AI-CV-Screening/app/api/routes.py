import threading
from app import auth
from groq import Groq
from openai import OpenAI
from app.utils.config_loader import Config
from pydantic import BaseModel, Field, ValidationError
from flask import Blueprint, jsonify,request
from app.services.putQueueMessageService import PutMessageQueue
from app.dto.dto import UserLoginDTO, JobRequestDTO, JobResponseDTO
from app.services.processScore import ProcessCVScore
from app.logger_config import logger


api_blueprint = Blueprint('api', __name__)



try:
    username = Config.get('Auth','username')
    password = Config.get('Auth','password')
    service_endpoint = Config.get('Queue','service_endpoint')
    queue_id = Config.get('Queue','queue_id')
    mainPath = Config.get('Queue','mainPath')
    confFilePath =  Config.get('Queue','confFilePath')
    gApiKey = Config.get('Groq','api_key')
    lmodel = Config.get('Groq','lModel')
    gmodel = Config.get('Groq','lModel')
    openApiKey = Config.get('Openapi','api_key')
    openModel = Config.get('Openapi','model')
except Exception as e:
    logger.info(f"Exception occured while reading configuration file: {e}")


try:
    gClient = Groq(api_key=gApiKey)
    oClient = OpenAI(api_key=openApiKey)
except Exception as e:
    logger.info(f"Exception occured while creating LLM client : {e}")

users = {
    username : password  
}

@auth.verify_password
def verify_password(username, password):
    if users.get(username) == password:
        return username

@api_blueprint.route('/getResumeScore', methods= ['POST'])
@auth.login_required
def getRelevanceSummary():
    try:

        job_request = JobRequestDTO(**request.get_json())
        print(job_request)

        candidate_id = job_request.metadata.candidateId
        resume = job_request.resume
        job_description_type = job_request.jobDescriptionType
        job_description = job_request.jobDescription

        print(candidate_id)
        print(resume)
        print(job_description_type)
        print(job_description)

        response_data = JobResponseDTO(
            candidateId=candidate_id,
            resumeLink=resume,
            jobDescriptionType=job_description_type,
            jobDescription=job_description,
            message="request process successfully."
        )

        thread = threading.Thread(target=ProcessCVScore.getCVScore, args=(gClient,oClient,lmodel,gmodel,openModel,job_description_type,job_description,resume))
        thread.daemon = True 
        thread.start()

        return jsonify(response_data.dict()), 200

    except ValidationError as e:
        return jsonify({"error": "Invalid request", "details": e.errors()}), 400
