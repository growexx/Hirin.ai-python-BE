from pydantic import BaseModel, HttpUrl, Field
from typing import Optional, Union
from typing import List,Dict


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


class Question(BaseModel):
    question: str
    time: int

class QuestionGenerationOutputDTO(BaseModel):
    questions: Dict[str, List[Question]]
    message: str
    status: str
