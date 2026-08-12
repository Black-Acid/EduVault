from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status, Depends
from fastapi.security import OAuth2PasswordBearer
from sqlalchemy.orm import Session

from eduVault.models import StudentProfile, TeacherProfile, User
import eduVault.schema as sma
import eduVault.models as mo
from dotenv import load_dotenv
import os
from google import genai
from eduVault.database import get_db

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    raise RuntimeError("GEMINI_API_KEY is not configured")

gemini_client = genai.Client(api_key=GEMINI_API_KEY)

JWT_SECRET = "eduvault-secret-key"
JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = 2 * 60 * 60
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")


def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:

    try:
        payload = jwt.decode(
            token,
            JWT_SECRET,
            algorithms=[JWT_ALGORITHM]
        )

        user_id = payload.get("sub")

        if user_id is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token"
            )

        user_id = int(user_id)

    except (jwt.InvalidTokenError, ValueError):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token"
        )

    user = (
        db.query(User)
        .filter(User.id == user_id)
        .first()
    )

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )

    return user


def _hash_password(password: str) -> str:
    salt = secrets.token_bytes(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
    return (
        "pbkdf2_sha256$100000$"
        + base64.b64encode(salt).decode("ascii")
        + "$"
        + base64.b64encode(derived).decode("ascii")
    )


def _verify_password(password: str, password_hash: str) -> bool:
    if not password_hash.startswith("pbkdf2_sha256$"):
        return False

    _, iterations, salt_b64, expected_b64 = password_hash.split("$", 3)
    salt = base64.b64decode(salt_b64)
    expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
    return secrets.compare_digest(base64.b64encode(expected).decode("ascii"), expected_b64)


def _create_access_token(user_id: int, role: str) -> tuple[str, str]:
    issued_at = datetime.now(timezone.utc)
    expires_at = issued_at + timedelta(seconds=JWT_TTL_SECONDS)
    payload = {
        "sub": str(user_id),
        "role": role,
        "iat": int(issued_at.timestamp()),
        "exp": int(expires_at.timestamp()),
    }
    token = jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)
    return token, expires_at.isoformat()


class AuthService:
    @staticmethod
    def signup(db: Session, payload: sma.SignupRequest) -> sma.AuthResponse:
        normalized_name = payload.name.strip()
        normalized_email = payload.email.strip().lower()
        normalized_role = payload.role.strip().lower() or "student"

        existing_user = db.query(User).filter(User.email == normalized_email).first()
        if existing_user:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Email already registered")

        user = User(
            name=normalized_name,
            email=normalized_email,
            password_hash=_hash_password(payload.password),
            role=normalized_role,
        )
        db.add(user)
        db.flush()

        if normalized_role == "student":
            db.add(StudentProfile(user_id=user.id))
        elif normalized_role == "teacher":
            db.add(TeacherProfile(user_id=user.id))

        db.commit()
        db.refresh(user)

        token, expires_at = _create_access_token(user.id, user.role)
        return sma.AuthResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            message="Signup successful",
            access_token=token,
            expires_at=expires_at,
        )

    @staticmethod
    def login(db: Session, payload: sma.LoginRequest) -> sma.AuthResponse:
        normalized_email = payload.email.strip().lower()
        user = db.query(User).filter(User.email == normalized_email).first()

        if not user or not _verify_password(payload.password, user.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

        token, expires_at = _create_access_token(user.id, user.role)
        return sma.AuthResponse(
            id=user.id,
            name=user.name,
            email=user.email,
            role=user.role,
            message="Login successful",
            access_token=token,
            expires_at=expires_at,
        )



def get_subject(db: Session, subject_name: str) -> mo.Subject:

    subject = (
        db.query(mo.Subject)
        .filter(mo.Subject.name == subject_name)
        .first()
    )

    if not subject:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Subject not found."
        )

    return subject

def get_available_subjects(db: Session):

    subjects = db.query(mo.Subject).all()

    response = []

    for subject in subjects:

        response.append(
            {
                "id": subject.id,
                "name": subject.name,
                "papers": [
                    {
                        "id": paper.id,
                        "year": paper.year,
                        "paper_number": paper.paper_number
                    }
                    for paper in subject.papers
                ]
            }
        )

    return response


def get_paper(
    db: Session,
    subject_id: int,
    year: int,
    paper_number: str
) -> mo.Paper:

    paper = (
        db.query(mo.Paper)
        .filter(
            mo.Paper.subject_id == subject_id,
            mo.Paper.year == year,
            mo.Paper.paper_number == paper_number
        )
        .first()
    )

    if not paper:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Paper not found."
        )

    return paper


def get_questions(
    db: Session,
    paper_id: int
) -> list[mo.Question]:

    questions = (
        db.query(mo.Question)
        .filter(
            mo.Question.paper_id == paper_id
        )
        .all()
    )

    if not questions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No questions found."
        )

    return questions


def build_question_response(
    questions: list[mo.Question]
) -> list[sma.QuestionResponse]:

    response = []

    for question in questions:

        response.append(
            sma.QuestionResponse(
                id=question.id,
                question_number=question.question_number,
                question=question.question_text,
                options=[
                    sma.OptionResponse(
                        id=option.id,
                        label=option.label,
                        text=option.option_text
                    )
                    for option in question.options
                ]
            )
        )

    return response



def fetch_questions(
    db: Session,
    payload: sma.FetchQuestionsRequest
):

    subject = get_subject(
        db,
        payload.subject
    )

    paper = get_paper(
        db,
        subject.id,
        payload.year,
        payload.paper_number
    )

    questions = get_questions(
        db,
        paper.id
    )

    return build_question_response(
        questions
    )
    
    
def submit_paper(
    db: Session,
    payload: sma.SubmitPaperRequest,
    user: mo.User
) -> sma.SubmitPaperResponse:

    # Get the paper
    paper = (
        db.query(mo.Paper)
        .filter(mo.Paper.id == payload.paper_id)
        .first()
    )

    if not paper:
        raise HTTPException(
            status_code=404,
            detail="Paper not found."
        )

    # Get all questions belonging to this paper
    questions = (
        db.query(mo.Question)
        .filter(mo.Question.paper_id == paper.id)
        .all()
    )

    if not questions:
        raise HTTPException(
            status_code=404,
            detail="This paper has no questions."
        )

    total_questions = len(questions)

    # Create an attempt for this specific user
    attempt = mo.QuizAttempt(
        user_id=user.id,
        paper_id=paper.id,
        total_questions=total_questions,
        correct_answers=0,
        score=0,
        percentage=0
    )

    db.add(attempt)
    db.flush()

    score = 0
    wrong_questions = []

    # Mark the submitted answers
    for answer in payload.answers:

        question = (
            db.query(mo.Question)
            .filter(
                mo.Question.id == answer.question_id,
                mo.Question.paper_id == paper.id
            )
            .first()
        )

        if not question:
            continue

        correct_option = (
            db.query(mo.QuestionOption)
            .filter(
                mo.QuestionOption.question_id == question.id,
                mo.QuestionOption.is_correct.is_(True)
            )
            .first()
        )

        if not correct_option:
            continue

        is_correct = (
            answer.selected_option_id == correct_option.id
        )

        if is_correct:
            score += 1
        else:
            wrong_questions.append(
                sma.WrongQuestionResponse(
                    question_id=question.id,
                    # selected_option_id=answer.selected_option_id,
                    # correct_option_id=correct_option.id
                )
            )

        # Save the student's answer
        student_answer = mo.StudentAnswer(
            user_id=user.id,
            attempt_id=attempt.id,
            question_id=question.id,
            selected_option_id=answer.selected_option_id,
            is_correct=is_correct
        )

        db.add(student_answer)

    # Calculate result based on the actual paper
    percentage = (
        (score / total_questions) * 100
        if total_questions > 0
        else 0
    )

    # Update the attempt
    attempt.correct_answers = score
    attempt.score = score
    attempt.percentage = percentage

    db.commit()
    db.refresh(attempt)

    return sma.SubmitPaperResponse(
        attempt_id=attempt.id,
        score=score,
        total_questions=total_questions,
        percentage=percentage,
        correct=score,
        wrong=total_questions - score,
        wrong_questions=wrong_questions
    )
    
    
def explain_wrong_answer(
    db: Session,
    attempt_id: int,
    question_id: int,
    user: mo.User
) -> str:

    # Get the quiz attempt belonging to the logged-in user
    attempt = (
        db.query(mo.QuizAttempt)
        .filter(
            mo.QuizAttempt.id == attempt_id,
            mo.QuizAttempt.user_id == user.id
        )
        .first()
    )

    if not attempt:
        raise HTTPException(
            status_code=404,
            detail="Quiz attempt not found."
        )

    # Get the student's answer for this question
    # within this specific quiz attempt
    student_answer = (
        db.query(mo.StudentAnswer)
        .filter(
            mo.StudentAnswer.attempt_id == attempt.id,
            mo.StudentAnswer.user_id == user.id,
            mo.StudentAnswer.question_id == question_id
        )
        .first()
    )

    if not student_answer:
        raise HTTPException(
            status_code=404,
            detail="Answer not found for this question in this quiz attempt."
        )

    # Make sure the student actually got the question wrong
    if student_answer.is_correct:
        raise HTTPException(
            status_code=400,
            detail="This question was answered correctly."
        )

    # Get the question
    question = (
        db.query(mo.Question)
        .filter(
            mo.Question.id == question_id,
            mo.Question.paper_id == attempt.paper_id
        )
        .first()
    )

    if not question:
        raise HTTPException(
            status_code=404,
            detail="Question not found in this quiz attempt."
        )

    # Get the option selected by the student
    selected_option = (
        db.query(mo.QuestionOption)
        .filter(
            mo.QuestionOption.id == student_answer.selected_option_id,
            mo.QuestionOption.question_id == question.id
        )
        .first()
    )

    if not selected_option:
        raise HTTPException(
            status_code=404,
            detail="Selected option not found."
        )

    # Get the correct option
    correct_option = (
        db.query(mo.QuestionOption)
        .filter(
            mo.QuestionOption.question_id == question.id,
            mo.QuestionOption.is_correct.is_(True)
        )
        .first()
    )

    if not correct_option:
        raise HTTPException(
            status_code=404,
            detail="Correct option not found."
        )

    # Get all options for the question
    options = (
        db.query(mo.QuestionOption)
        .filter(
            mo.QuestionOption.question_id == question.id
        )
        .all()
    )

    options_text = "\n".join(
        f"{option.label}. {option.option_text}"
        for option in options
    )

    # Build the prompt for Gemini
    prompt = f"""
        You are an educational tutor helping a WASSCE student understand
        a question they answered incorrectly.

        Question:
        {question.question_text}

        Options:
        {options_text}

        Student's selected answer:
        {selected_option.label}. {selected_option.option_text}

        Correct answer:
        {correct_option.label}. {correct_option.option_text}

        Your job is to teach the student, not simply give them the answer.

        Requirements:
        - Clearly explain why the correct answer is correct.
        - Explain why the student's selected answer is incorrect.
        - Teach the underlying concept behind the question.
        - If calculations are involved, show the calculation step by step.
        - Use language appropriate for a senior high school student.
        - Be clear, patient, and encouraging.
        - Do not assume the student already understands the concept.
        - Do not be unnecessarily verbose.
        - Do not simply repeat the answer.
    """

    # Send the question to Gemini
    response = gemini_client.interactions.create(
        model="gemini-3.5-flash",
        input=prompt
    )

    return response.output_text

# if __name__ == "__main__":
#     explanation = explain_question(
#         question=(
#             "An electric bulb is rated 120 W and 240 V. "
#             "Determine the current it draws from the mains."
#         ),
#         options=[
#             "A. 0.5 A",
#             "B. 0.6 A",
#             "C. 1.0 A",
#             "D. 2.0 A"
#         ],
#         student_answer="B. 0.6 A",
#         correct_answer="A. 0.5 A"
#     )

#     print("\n--- GEMINI EXPLANATION ---\n")
#     print(explanation)