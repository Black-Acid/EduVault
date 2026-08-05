from __future__ import annotations

import base64
import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from eduVault.models import StudentProfile, TeacherProfile, User
import eduVault.schema as sma
import eduVault.models as mo

JWT_SECRET = "eduvault-secret-key"
JWT_ALGORITHM = "HS256"
JWT_TTL_SECONDS = 2 * 60 * 60





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