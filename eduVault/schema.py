from pydantic import BaseModel, Field



class SignupRequest(BaseModel):
    name: str = Field(..., min_length=1)
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)
    role: str = Field(default="student")


class LoginRequest(BaseModel):
    email: str = Field(..., min_length=3)
    password: str = Field(..., min_length=6)


class AuthResponse(BaseModel):
    id: int
    name: str
    email: str
    role: str
    message: str
    access_token: str
    token_type: str = "bearer"
    expires_at: str
    
    
class FetchQuestionsRequest(BaseModel):
    subject: str
    year: int
    paper_number: str
    
class OptionResponse(BaseModel):
    id: int
    label: str
    text: str


class QuestionResponse(BaseModel):
    id: int
    question_number: int
    question: str
    options: list[OptionResponse]