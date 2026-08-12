from __future__ import annotations

from datetime import datetime
from typing import Optional

from sqlalchemy import (
    DateTime,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Boolean,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from eduVault.database import Base


class User(Base):
    __tablename__ = "Users"
    __table_args__ = (UniqueConstraint("email", name="uq_users_email"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column(String(255), nullable=False)
    role: Mapped[str] = mapped_column(String(50), nullable=False, default="student")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    student_profile: Mapped[Optional["StudentProfile"]] = relationship(
        "StudentProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    teacher_profile: Mapped[Optional["TeacherProfile"]] = relationship(
        "TeacherProfile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="user",
        cascade="all, delete-orphan",
    )

    student_answers: Mapped[list["StudentAnswer"]] = relationship(
        "StudentAnswer",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    

    def __repr__(self) -> str:
        return f"<User(id={self.id}, email={self.email!r}, name={self.name!r})>"


class StudentProfile(Base):
    __tablename__ = "Student_Profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_student_profiles_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    bio: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="student_profile")

    def __repr__(self) -> str:
        return f"<StudentProfile(id={self.id}, user_id={self.user_id})>"


class TeacherProfile(Base):
    __tablename__ = "Teacher_Profiles"
    __table_args__ = (UniqueConstraint("user_id", name="uq_teacher_profiles_user_id"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        unique=True,
        index=True,
    )
    bio: Mapped[Optional[str]] = mapped_column(Text)
    specialization: Mapped[Optional[str]] = mapped_column(String(100))
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="teacher_profile")

    def __repr__(self) -> str:
        return f"<TeacherProfile(id={self.id}, user_id={self.user_id})>"


class Subject(Base):
    __tablename__ = "Subjects"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        unique=True
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    papers: Mapped[list["Paper"]] = relationship(
        "Paper",
        back_populates="subject",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Subject(id={self.id}, name={self.name})>"

class Paper(Base):
    __tablename__ = "Papers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    subject_id: Mapped[int] = mapped_column(
        ForeignKey("Subjects.id"),
        nullable=False,
        index=True
    )

    year: Mapped[int] = mapped_column(
        String(20),
        nullable=False
    )

    paper_number: Mapped[str] = mapped_column(
        Integer(),
        nullable=False
    )

    total_marks: Mapped[Optional[int]] = mapped_column(
        Integer
    )

    duration: Mapped[Optional[str]] = mapped_column(
        String(50)
    )

    subject: Mapped["Subject"] = relationship(
        "Subject",
        back_populates="papers"
    )

    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="paper",
        cascade="all, delete-orphan"
    )
    
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="paper",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<Paper(id={self.id}, year={self.year}, paper={self.paper_number})>"
    
class Question(Base):
    __tablename__ = "Questions"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    paper_id: Mapped[int] = mapped_column(
        ForeignKey("Papers.id"),
        nullable=False,
        index=True
    )

    question_number: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    question_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="WASSCE"
    )

    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="questions"
    )

    options: Mapped[list["QuestionOption"]] = relationship(
        "QuestionOption",
        back_populates="question",
        cascade="all, delete-orphan"
    )
    
    student_answers: Mapped[list["StudentAnswer"]] = relationship(
        "StudentAnswer",
        back_populates="question"
    )

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, number={self.question_number})>"
    
    
class QuestionOption(Base):
    __tablename__ = "Question_Options"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("Questions.id"),
        nullable=False,
        index=True
    )

    label: Mapped[str] = mapped_column(
        String(5),
        nullable=False
    )

    option_text: Mapped[str] = mapped_column(
        Text,
        nullable=False
    )

    is_correct: Mapped[bool] = mapped_column(
        nullable=False,
        default=False
    )

    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="options"
    )

    def __repr__(self) -> str:
        return f"<QuestionOption(id={self.id}, label={self.label})>"
    
    student_answers: Mapped[list["StudentAnswer"]] = relationship(
        "StudentAnswer",
        back_populates="selected_option"
    )

class QuizAttempt(Base):
    __tablename__ = "Quiz_Attempts"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("Users.id"),
        nullable=False,
        index=True
    )

    paper_id: Mapped[int] = mapped_column(
        ForeignKey("Papers.id"),
        nullable=False,
        index=True
    )

    total_questions: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    correct_answers: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    score: Mapped[int] = mapped_column(
        Integer,
        nullable=False
    )

    percentage: Mapped[float] = mapped_column(
        nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now()
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="quiz_attempts"
    )

    paper: Mapped["Paper"] = relationship(
        "Paper",
        back_populates="quiz_attempts"
    )

    answers: Mapped[list["StudentAnswer"]] = relationship(
        "StudentAnswer",
        back_populates="attempt",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<QuizAttempt(id={self.id}, user_id={self.user_id}, paper_id={self.paper_id})>"
    
    
class StudentAnswer(Base):
    __tablename__ = "Student_Answers"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True
    )

    user_id: Mapped[int] = mapped_column(
        ForeignKey("Users.id"),
        nullable=False,
        index=True
    )

    attempt_id: Mapped[int] = mapped_column(
        ForeignKey("Quiz_Attempts.id"),
        nullable=False,
        index=True
    )

    question_id: Mapped[int] = mapped_column(
        ForeignKey("Questions.id"),
        nullable=False,
        index=True
    )

    selected_option_id: Mapped[int] = mapped_column(
        ForeignKey("Question_Options.id"),
        nullable=False
    )

    is_correct: Mapped[bool] = mapped_column(
        nullable=False
    )

    user: Mapped["User"] = relationship(
        "User",
        back_populates="student_answers"
    )

    attempt: Mapped["QuizAttempt"] = relationship(
        "QuizAttempt",
        back_populates="answers"
    )

    question: Mapped["Question"] = relationship(
        "Question",
        back_populates="student_answers"
    )

    selected_option: Mapped["QuestionOption"] = relationship(
        "QuestionOption",
        back_populates="student_answers"
    )

    def __repr__(self) -> str:
        return f"<StudentAnswer(id={self.id}, question_id={self.question_id}, is_correct={self.is_correct})>"