from pydantic import BaseModel, Field

class UserLoginDTO(BaseModel):
    username: str = Field(..., description="Username of the user", max_length=50)
    password: str = Field(..., description="Password of the user", min_length=8)

class ProtectedRouteResponseDTO(BaseModel):
    message: str = Field(..., description="Message indicating access to the protected route")

class PublicRouteResponseDTO(BaseModel):
    message: str = Field(..., description="Message indicating access to the public route")
