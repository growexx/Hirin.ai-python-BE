from flask import Blueprint, jsonify,after_this_request
from app import auth
from app.utils.config_loader import Config
from pydantic import BaseModel, Field, ValidationError
from app.dto.dto import UserLoginDTO, ProtectedRouteResponseDTO, PublicRouteResponseDTO
from app.services.putQueueMessageService import PutMessageQueue
import threading

api_blueprint = Blueprint('api', __name__)

username = Config.get('Auth','username')
password = Config.get('Auth','password')

users = {
    username : password  
}

@auth.verify_password
def verify_password(username, password):
    if users.get(username) == password:
        return username

@api_blueprint.route('/protected')
@auth.login_required
def protected():
    response_dto = ProtectedRouteResponseDTO(message="This is a protected route")
    print("Inside protected method")
    thread = threading.Thread(target=PutMessageQueue.putMessage)
    thread.daemon = True 
    thread.start()
    print("Complete protected method")
    return jsonify(response_dto.dict())

@api_blueprint.route('/public')
def public():
    response_dto = PublicRouteResponseDTO(message="This is a public route")
    print("Inside public method")
    thread = threading.Thread(target=PutMessageQueue.putMessage)
    thread.daemon = True 
    thread.start()
    print("Complete public method")
    return jsonify(response_dto.dict()), 200



