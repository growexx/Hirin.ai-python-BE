from flask import Blueprint, jsonify,after_this_request
from app import auth
from app.utils.config_loader import Config
from pydantic import BaseModel, Field, ValidationError
#from app.dto.dto import UserLoginDTO, ProtectedRouteResponseDTO, PublicRouteResponseDTO
#from app.services.putQueueMessageService import PutMessageQueue
from flask import Flask, request, jsonify
#from openai import OpenAI
#from groq import Groq
#from app.services.core import process_job_description
import threading

api_blueprint = Blueprint('api', __name__)

username = Config.get('Auth','username')
password = Config.get('Auth','password')


# Load the config.ini file
#try:
#    API_KEYS = {
#        "OPENAI_API_KEY": Config.get('API_KEYS','OPENAI_API_KEY'),
#       "GROQ_API_KEY": Config.get('API_KEYS','GROQ_API_KEY')
#    }
#except Exception as e:
#    logging.error(f"Failed to load API keys: {e}")
#    raise

# Initialize API clients
#try:
#    openai_client = OpenAI(api_key=API_KEYS["OPENAI_API_KEY"])
#    groq_client = Groq(api_key=API_KEYS["GROQ_API_KEY"])
#except Exception as e:
#    logging.error(f"Failed to initialize API clients: {e}")
#    raise

users = {
    username : password
}

@auth.verify_password
def verify_password(username, password):
    if users.get(username) == password:
        return username

# @api_blueprint.route('/process-and-generate/', methods=['POST'])
# @auth.login_required
# def process_and_generate():
#     """
#     Single endpoint to process a job description and return generated questions.
#     """
#     try:
#         # Get the job description from the POST request
#         data = request.get_json()
#         print(data)
#         job_description = data.get('job_description', None)
#         print(job_description)
#         number_of_questions = data.get('no_of_questions',None)
#         print(number_of_questions)
#         # If no job description is provided, return an error
#         if not (job_description or number_of_questions):
#             return jsonify({
#                 "status": "error",
#                 "message": "Job description or Number of Questions not mentioned. Please provide the missing field."
#             }), 400

#         # Process the job description using the function from core_1
#         processed_questions = process_job_description(openai_client, groq_client, job_description=job_description, noq=number_of_questions)

#         return jsonify({
#             "status": "success",
#             "message": "Job description processed and questions generated successfully.",
#             "processed_result": processed_questions
#         })
#     except Exception as e:
#         # Return a detailed error message
#         return jsonify({
#             "status": "error",
#             "message": f"An error occurred: {str(e)}"
#         }), 500


@api_blueprint.route('/test/', methods=['GET'])
@auth.login_required
def test():
	return "message"

