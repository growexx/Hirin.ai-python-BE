from flask import Flask
from flask_httpauth import HTTPBasicAuth
from flask_swagger_ui import get_swaggerui_blueprint
from flask_cors import CORS
import os
from app.utils.config_loader import Config

# Initialize the basic auth
auth = HTTPBasicAuth()

# Initialize the Swagger UI
SWAGGER_URL = '/swagger'
API_URL = os.path.join('/static', 'swagger.json')
swaggerui_blueprint = get_swaggerui_blueprint(
    SWAGGER_URL, API_URL, config={'app_name': "CV Screening"}
)

def create_app():
    app = Flask(__name__)

    confPath =  os.path.join('app/utils', 'config.ini') 
    Config.load_config(confPath)
    CORS(app, resources={r"/*": {"origins": "*"}})
    app.register_blueprint(swaggerui_blueprint, url_prefix=SWAGGER_URL)

    from app.api.routes import api_blueprint
    app.register_blueprint(api_blueprint)

    return app




