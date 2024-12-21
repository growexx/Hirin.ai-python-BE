from flask import Blueprint, jsonify
from app import auth
from app.utils.config_loader import Config
from pydantic import BaseModel, Field, ValidationError
from app.dto.dto import UserLoginDTO, ProtectedRouteResponseDTO, PublicRouteResponseDTO

api_blueprint = Blueprint('api', __name__)

username = Config.get('Auth','username')
password = Config.get('Auth','password')

# Dummy data for authentication
users = {
    username : password  
}

# Define the authentication function
@auth.verify_password
def verify_password(username, password):
    if users.get(username) == password:
        return username

@api_blueprint.route('/protected')
@auth.login_required
def protected():
    response_dto = ProtectedRouteResponseDTO(message="This is a protected route")
    return jsonify(response_dto.dict())

# Public route
@api_blueprint.route('/public')
def public():
    response_dto = PublicRouteResponseDTO(message="This is a public route")
    return jsonify(response_dto.dict())



