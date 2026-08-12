from pydantic import BaseModel, Field, ConfigDict



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
    
class AnswerSubmission(BaseModel):
    question_id: int
    selected_option_id: int


class SubmitPaperRequest(BaseModel):
    paper_id: int
    answers: list[AnswerSubmission]
    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "paper_id": 1,
                "answers": [
                    {
                        "question_id": 1,
                        "selected_option_id": 2
                    },
                    {
                        "question_id": 2,
                        "selected_option_id": 7
                    },
                    {
                        "question_id": 3,
                        "selected_option_id": 12
                    }
                ]
            }
        }
    )
    
class WrongQuestionResponse(BaseModel):
    question_id: int
    # selected_option_id: int
    # correct_option_id: int


class SubmitPaperResponse(BaseModel):
    attempt_id: int
    score: int
    total_questions: int
    percentage: float
    correct: int
    wrong: int
    wrong_questions: list[WrongQuestionResponse]
    
class ExplainWrongAnswerRequest(BaseModel):
    attempt_id: int
    question_id: int
    
class ExplainWrongAnswerResponse(BaseModel):
    explanation: str