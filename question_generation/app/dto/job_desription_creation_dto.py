from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Union

class UserLoginDTO(BaseModel):
    username: str = Field(..., description="Username of the user", max_length=50)
    password: str = Field(..., description="Password of the user", min_length=8)

class JobDescriptionInputDTO(BaseModel):
    job_summary: str

class JobDescriptionOutputDTO(BaseModel):
    status: str
    job_description: str = None
    message: str = None




