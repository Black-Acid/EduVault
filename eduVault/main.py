from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, status
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session

from eduVault.database import check_db_connection, get_db
from eduVault.schema import AuthResponse, LoginRequest, SignupRequest
import eduVault.services as sv
import eduVault.schema as sma

@asynccontextmanager
async def lifespan(app: FastAPI):
    check_db_connection()
    yield


app = FastAPI(lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["https://pastquestionsandtutorials.vercel.app"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
async def health_check() -> dict[str, str]:
    return {"status": "ok"}


@app.post("/auth/signup", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def signup(payload: SignupRequest, db: Session = Depends(get_db)) -> AuthResponse:
    return sv.AuthService.signup(db, payload)


@app.post("/auth/login", response_model=AuthResponse)
def login(payload: LoginRequest, db: Session = Depends(get_db)) -> AuthResponse:
    return sv.AuthService.login(db, payload)


@app.post(
    "/ai/explain",
    response_model=sma.WrongAnswerExplanation
)
def explain_wrong_answer(
    payload: sma.ExplainWrongAnswerRequest,
    db: Session = Depends(get_db),
    current_user = Depends(sv.get_current_user)
):
    return sv.explain_wrong_answer(
        db=db,
        attempt_id=payload.attempt_id,
        question_id=payload.question_id,
        user=current_user
    )

#task for today 
# Build the endpoint for the dashboard for both students and tutors
# build the endpoint for the zoom class  
# Setup redis to keep the questions so we have our database free from hits all the time
@app.get("/subjects")
def subjects(db: Session = Depends(get_db)):
    return sv.get_available_subjects(db)

@app.post("/questions")
def get_questions(
    payload: sma.FetchQuestionsRequest,
    db: Session = Depends(get_db)
):
    return sv.fetch_questions(
        db=db,
        payload=payload
    )
    

@app.post(
    "/papers/submit",
    response_model=sma.SubmitPaperResponse
)
def submit_questions(
    payload: sma.SubmitPaperRequest,
    db: Session = Depends(get_db),
    current_user = Depends(sv.get_current_user)
):
    return sv.submit_paper(
        db=db,
        payload=payload,
        user=current_user
    )
    
@app.get("/dashboard", response_model=sma.UserDashboardResponse)
def dashboard(
    
    year: int,
    month: int,
    current_user = Depends(sv.get_current_user),
    db: Session = Depends(get_db)
):
    return sv.get_dashboard(
        db=db,
        user_id=current_user.id,
        year=year,
        month=month
    )