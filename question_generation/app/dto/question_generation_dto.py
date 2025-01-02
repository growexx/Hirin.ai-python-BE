from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Union
from typing import List


class Skill(BaseModel):
    name: str
    level: str
    totalQuestions: int

class QuestionGenerationInputDTO(BaseModel):
    job_description: str
    job_description_url: str
    is_text: bool
    skills: List[Skill]
    total_time: int

class QuestionGenerationOutputDTO(BaseModel):
    status : str
    key_skills: List[str]
    proficiency_level: List[str]
    questions_per_skill: List[int]
    message: str = None

