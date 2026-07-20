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
    subjects_taught: Mapped[list["Subject"]] = relationship(
        "Subject",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    quizzes: Mapped[list["Quiz"]] = relationship(
        "Quiz",
        back_populates="creator",
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
    progress_tracking: Mapped[list["ProgressTracking"]] = relationship(
        "ProgressTracking",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    ai_explanations: Mapped[list["AIExplanation"]] = relationship(
        "AIExplanation",
        back_populates="user",
        cascade="all, delete-orphan",
    )
    bookings_as_student: Mapped[list["Booking"]] = relationship(
        "Booking",
        foreign_keys="[Booking.student_id]",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    bookings_as_teacher: Mapped[list["Booking"]] = relationship(
        "Booking",
        foreign_keys="[Booking.teacher_id]",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    availability: Mapped[list["TeacherAvailability"]] = relationship(
        "TeacherAvailability",
        back_populates="teacher",
        cascade="all, delete-orphan",
    )
    tutoring_sessions_as_student: Mapped[list["TutoringSession"]] = relationship(
        "TutoringSession",
        foreign_keys="[TutoringSession.student_id]",
        back_populates="student",
        cascade="all, delete-orphan",
    )
    tutoring_sessions_as_teacher: Mapped[list["TutoringSession"]] = relationship(
        "TutoringSession",
        foreign_keys="[TutoringSession.teacher_id]",
        back_populates="teacher",
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

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    teacher: Mapped["User"] = relationship("User", back_populates="subjects_taught")
    levels: Mapped[list["Level"]] = relationship(
        "Level",
        back_populates="subject",
        cascade="all, delete-orphan",
    )
    quizzes: Mapped[list["Quiz"]] = relationship(
        "Quiz",
        back_populates="subject",
        cascade="all, delete-orphan",
    )
    progress_tracking: Mapped[list["ProgressTracking"]] = relationship(
        "ProgressTracking",
        back_populates="subject",
        cascade="all, delete-orphan",
    )
    bookings: Mapped[list["Booking"]] = relationship(
        "Booking",
        back_populates="subject",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Subject(id={self.id}, title={self.title!r})>"


class Level(Base):
    __tablename__ = "Levels"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Subjects.id"),
        nullable=False,
        index=True,
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    subject: Mapped["Subject"] = relationship("Subject", back_populates="levels")
    quizzes: Mapped[list["Quiz"]] = relationship(
        "Quiz",
        back_populates="level",
        cascade="all, delete-orphan",
    )
    progress_tracking: Mapped[list["ProgressTracking"]] = relationship(
        "ProgressTracking",
        back_populates="level",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Level(id={self.id}, name={self.name!r})>"


class Quiz(Base):
    __tablename__ = "Quizzes"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    subject_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Subjects.id"),
        nullable=False,
        index=True,
    )
    level_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("Levels.id"), index=True)
    creator_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        index=True,
    )
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    subject: Mapped["Subject"] = relationship("Subject", back_populates="quizzes")
    level: Mapped[Optional["Level"]] = relationship("Level", back_populates="quizzes")
    creator: Mapped["User"] = relationship("User", back_populates="quizzes")
    questions: Mapped[list["Question"]] = relationship(
        "Question",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )
    quiz_attempts: Mapped[list["QuizAttempt"]] = relationship(
        "QuizAttempt",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )
    ai_explanations: Mapped[list["AIExplanation"]] = relationship(
        "AIExplanation",
        back_populates="quiz",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Quiz(id={self.id}, title={self.title!r})>"


class Question(Base):
    __tablename__ = "Questions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quiz_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Quizzes.id"),
        nullable=False,
        index=True,
    )
    question_text: Mapped[str] = mapped_column(Text, nullable=False)
    options: Mapped[Optional[str]] = mapped_column(Text)
    correct_answer: Mapped[str] = mapped_column(Text, nullable=False)
    explanation: Mapped[Optional[str]] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="questions")
    student_answers: Mapped[list["StudentAnswer"]] = relationship(
        "StudentAnswer",
        back_populates="question",
        cascade="all, delete-orphan",
    )
    ai_explanations: Mapped[list["AIExplanation"]] = relationship(
        "AIExplanation",
        back_populates="question",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Question(id={self.id}, quiz_id={self.quiz_id})>"


class QuizAttempt(Base):
    __tablename__ = "Quiz_Attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        index=True,
    )
    quiz_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Quizzes.id"),
        nullable=False,
        index=True,
    )
    score: Mapped[Optional[int]] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="in_progress")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="quiz_attempts")
    quiz: Mapped["Quiz"] = relationship("Quiz", back_populates="quiz_attempts")
    student_answers: Mapped[list["StudentAnswer"]] = relationship(
        "StudentAnswer",
        back_populates="quiz_attempt",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<QuizAttempt(id={self.id}, quiz_id={self.quiz_id}, user_id={self.user_id})>"


class StudentAnswer(Base):
    __tablename__ = "Student_Answers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quiz_attempt_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Quiz_Attempts.id"),
        nullable=False,
        index=True,
    )
    question_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Questions.id"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        index=True,
    )
    answer_text: Mapped[str] = mapped_column(Text, nullable=False)
    is_correct: Mapped[bool] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    quiz_attempt: Mapped["QuizAttempt"] = relationship("QuizAttempt", back_populates="student_answers")
    question: Mapped["Question"] = relationship("Question", back_populates="student_answers")
    user: Mapped["User"] = relationship("User", back_populates="student_answers")

    def __repr__(self) -> str:
        return f"<StudentAnswer(id={self.id}, question_id={self.question_id})>"


class ProgressTracking(Base):
    __tablename__ = "Progress_Tracking"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("Subjects.id"), index=True)
    level_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("Levels.id"), index=True)
    completed_lessons: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    completion_percentage: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    user: Mapped["User"] = relationship("User", back_populates="progress_tracking")
    subject: Mapped[Optional["Subject"]] = relationship("Subject", back_populates="progress_tracking")
    level: Mapped[Optional["Level"]] = relationship("Level", back_populates="progress_tracking")

    def __repr__(self) -> str:
        return f"<ProgressTracking(id={self.id}, user_id={self.user_id})>"


class AIExplanation(Base):
    __tablename__ = "AI_Explanations"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    quiz_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("Quizzes.id"), index=True)
    question_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("Questions.id"), index=True)
    user_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        index=True,
    )
    explanation_text: Mapped[str] = mapped_column(Text, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    quiz: Mapped[Optional["Quiz"]] = relationship("Quiz", back_populates="ai_explanations")
    question: Mapped[Optional["Question"]] = relationship("Question", back_populates="ai_explanations")
    user: Mapped["User"] = relationship("User", back_populates="ai_explanations")

    def __repr__(self) -> str:
        return f"<AIExplanation(id={self.id}, user_id={self.user_id})>"


class Booking(Base):
    __tablename__ = "Bookings"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        index=True,
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        index=True,
    )
    subject_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("Subjects.id"), index=True)
    scheduled_for: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="pending")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    student: Mapped["User"] = relationship(
        "User",
        foreign_keys="[Booking.student_id]",
        back_populates="bookings_as_student",
    )
    teacher: Mapped["User"] = relationship(
        "User",
        foreign_keys="[Booking.teacher_id]",
        back_populates="bookings_as_teacher",
    )
    subject: Mapped[Optional["Subject"]] = relationship("Subject", back_populates="bookings")
    tutoring_session: Mapped[Optional["TutoringSession"]] = relationship(
        "TutoringSession",
        back_populates="booking",
        uselist=False,
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Booking(id={self.id}, student_id={self.student_id}, teacher_id={self.teacher_id})>"


class TeacherAvailability(Base):
    __tablename__ = "Teacher_Availability"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        index=True,
    )
    day_of_week: Mapped[str] = mapped_column(String(50), nullable=False)
    start_time: Mapped[str] = mapped_column(String(10), nullable=False)
    end_time: Mapped[str] = mapped_column(String(10), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    teacher: Mapped["User"] = relationship("User", back_populates="availability")

    def __repr__(self) -> str:
        return f"<TeacherAvailability(id={self.id}, teacher_id={self.teacher_id})>"


class TutoringSession(Base):
    __tablename__ = "Tutoring_Sessions"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    booking_id: Mapped[Optional[int]] = mapped_column(Integer, ForeignKey("Bookings.id"), index=True)
    student_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        index=True,
    )
    teacher_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("Users.id"),
        nullable=False,
        index=True,
    )
    started_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    ended_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True))
    status: Mapped[str] = mapped_column(String(50), nullable=False, default="scheduled")
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now()
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), nullable=False, server_default=func.now(), onupdate=func.now()
    )

    booking: Mapped[Optional["Booking"]] = relationship("Booking", back_populates="tutoring_session")
    student: Mapped["User"] = relationship(
        "User",
        foreign_keys="[TutoringSession.student_id]",
        back_populates="tutoring_sessions_as_student",
    )
    teacher: Mapped["User"] = relationship(
        "User",
        foreign_keys="[TutoringSession.teacher_id]",
        back_populates="tutoring_sessions_as_teacher",
    )

    def __repr__(self) -> str:
        return f"<TutoringSession(id={self.id}, status={self.status!r})>"
