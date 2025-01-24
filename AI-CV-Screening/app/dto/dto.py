from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Union

class UserLoginDTO(BaseModel):
    username: str = Field(..., description="Username of the user", max_length=50)
    password: str = Field(..., description="Password of the user", min_length=8)

class Metadata(BaseModel):
    candidateId: str
    other_field: Optional[str] = None

class JobRequestDTO(BaseModel):
    metadata: Metadata
    resume: str
    jobDescriptionType: str
    jobDescription: Union[str, HttpUrl]
# Response DTO
class JobResponseDTO(BaseModel):
    candidateId: str
    resumeLink: str
    jobDescriptionType: str
    jobDescription: Union[str, HttpUrl]
    message: str




