"# EduVault

EduVault is a FastAPI-based backend for managing exam-style question papers, student quiz attempts, subject performance tracking, and AI-powered explanations for incorrect answers. The project is built around a PostgreSQL database and uses SQLAlchemy ORM models plus Alembic migrations to manage schema changes.

This repository is the server-side implementation for an educational assessment platform focused on WASSCE-style past questions and student learning analytics.

## What this project does

The application currently supports the following behaviors, based directly on the code in this repository:

- User registration and login for students and teachers
- JWT-based authentication for protected endpoints
- Retrieval of available subjects and their associated papers
- Fetching exam questions for a selected subject, year, and paper
- Submitting a paper attempt and computing a score, percentage, and incorrect-question list
- Explaining a wrong answer using the Google Gemini API
- Returning a user dashboard with overview stats, subject mastery summaries, and monthly activity data

The app is not a full general-purpose web app framework; it is a backend service that exposes structured API routes for these educational workflows.

## Architecture

The application follows a simple layered backend structure:

- API layer: FastAPI routes in [eduVault/main.py](eduVault/main.py)
- Business logic: service functions in [eduVault/services.py](eduVault/services.py)
- Data models: SQLAlchemy models in [eduVault/models.py](eduVault/models.py)
- Request/response validation: Pydantic schemas in [eduVault/schema.py](eduVault/schema.py)
- Database access: SQLAlchemy engine/session config in [eduVault/database.py](eduVault/database.py)
- Schema migrations: Alembic scripts in [alembic](alembic)

At runtime, the app:

1. Loads environment variables from the project root `.env` file.
2. Opens a PostgreSQL connection via SQLAlchemy.
3. Validates the database connection on startup.
4. Serves API routes over FastAPI.
5. Uses JWT auth for protected operations.
6. Uses Google GenAI for AI explanation of missing or incorrect answers.

## Technologies used

The repository uses the following technologies directly in code and dependencies:

- Python 3.12
- FastAPI
- Uvicorn
- SQLAlchemy 2.0
- PostgreSQL
- Alembic
- Pydantic
- Python dotenv
- JWT (PyJWT)
- Google GenAI SDK
- Python standard library hashing and security helpers

The dependency list is in [requirements.txt](requirements.txt).

## Project structure

```text
FinalYear/
├── .env                          # Required runtime configuration
├── .gitignore
├── README.md                    # Project documentation
├── requirements.txt             # Python dependencies
├── alembic.ini                  # Alembic configuration
├── alembic/                     # Database migration scripts
│   ├── env.py
│   ├── README
│   ├── script.py.mako
│   └── versions/
├── eduVault/
│   ├── __init__.py              # package marker (if present in the package folder)
│   ├── database.py              # DB connection and session setup
│   ├── main.py                  # FastAPI app and routes
│   ├── models.py                # SQLAlchemy ORM models
│   ├── schema.py                # Pydantic request/response models
│   ├── services.py              # Auth, question, submission, AI and dashboard logic
│   └── ...
├── scripts.py                   # Seed script for sample Physics paper data
└── acid/                        # Local Python virtual environment
```

## Environment variables

The application requires environment variables to be present before startup.

### Required variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `DATABASE_URL` | Yes | PostgreSQL connection string used by SQLAlchemy and Alembic. |
| `GEMINI_API_KEY` | Yes | API key used to initialize the Google GenAI client in [eduVault/services.py](eduVault/services.py). |

### Hardcoded values in the code

These values are not loaded from the environment, but are set directly inside the code:

- `JWT_SECRET = "eduvault-secret-key"`
- `JWT_ALGORITHM = "HS256"`
- `JWT_TTL_SECONDS = 2 * 60 * 60`

The app loads environment variables using `python-dotenv`:

- [eduVault/database.py](eduVault/database.py)
- [alembic/env.py](alembic/env.py)
- [eduVault/services.py](eduVault/services.py)

Example `.env` content, matching the repository’s current setup:

```env
DATABASE_URL='postgresql://<user>:<password>@<host>:<port>/<database>?sslmode=require&channel_binding=require'
GEMINI_API_KEY=your_google_gemini_api_key
```

## Database setup

The backend uses PostgreSQL, and the connection string comes from `DATABASE_URL`.

The project includes Alembic migrations for schema creation:

- [alembic.ini](alembic.ini)
- [alembic/env.py](alembic/env.py)
- [alembic/versions/18189ac62018_initial_schema.py](alembic/versions/18189ac62018_initial_schema.py)
- [alembic/versions/e53446217281_add_quiz_attempts_and_student_answers.py](alembic/versions/e53446217281_add_quiz_attempts_and_student_answers.py)

The schema currently includes these main tables:

- `Users`
- `Student_Profiles`
- `Teacher_Profiles`
- `Subjects`
- `Papers`
- `Questions`
- `Question_Options`
- `Quiz_Attempts`
- `Student_Answers`

The ORM models for these tables are defined in [eduVault/models.py](eduVault/models.py).

### Applying migrations

From the project root:

```bash
alembic upgrade head
```

This matches the Alembic configuration in [alembic.ini](alembic.ini).

## Local setup

### Prerequisites

- Python 3.12
- A PostgreSQL database accessible via `DATABASE_URL`
- A valid `GEMINI_API_KEY`
- Access to a terminal in the project root

### Install dependencies

```bash
python -m venv .venv
# On Windows
.venv\Scripts\activate
pip install -r requirements.txt
```

Alternatively, this repository already contains a local virtual environment under [acid](acid), but the code is configured to run from a standard Python environment as well.

### Create the environment file

Create a `.env` file in the repository root with the required values:

```env
DATABASE_URL=postgresql://user:password@host:5432/eduvaultdb
GEMINI_API_KEY=your_key_here
```

### Start the app

Run the API locally with:

```bash
uvicorn eduVault.main:app --reload --host 0.0.0.0 --port 8000
```

This starts the FastAPI application defined in [eduVault/main.py](eduVault/main.py).

The app also has CORS enabled to allow requests from:

- `https://pastquestionsandtutorials.vercel.app`

## How the app works

The main backend flow is:

1. A user signs up or logs in.
2. The app issues a JWT token with the user id and role.
3. A client can fetch subject and paper data.
4. The client requests questions for a selected paper.
5. The student submits answers for a paper.
6. The backend calculates the score and stores a `Quiz_Attempts` record plus individual `Student_Answers` rows.
7. For wrong answers, a client can request an explanation using Gemini.
8. The dashboard aggregates the student’s quiz activity and performance metrics.

## API endpoints

The backend exposes the following routes in [eduVault/main.py](eduVault/main.py).

### Health check

#### GET /

Returns the basic service health status.

Example response:

```json
{
  "status": "ok"
}
```

### Authentication

#### POST /auth/signup

Creates a new user.

Request body:

```json
{
  "name": "Jane Doe",
  "email": "jane@example.com",
  "password": "secret123",
  "role": "student"
}
```

Fields:

- `name`: required string
- `email`: required string
- `password`: required string, minimum length 6
- `role`: optional string, defaults to `student`

Response model: `AuthResponse`

Example response:

```json
{
  "id": 1,
  "name": "Jane Doe",
  "email": "jane@example.com",
  "role": "student",
  "message": "Signup successful",
  "access_token": "<jwt>",
  "token_type": "bearer",
  "expires_at": "2026-09-03T12:00:00+00:00"
}
```

#### POST /auth/login

Authenticates an existing user.

Request body:

```json
{
  "email": "jane@example.com",
  "password": "secret123"
}
```

Response model: same as signup response.

### AI explanation

#### POST /ai/explain

Requires authentication using a bearer token.

Request body:

```json
{
  "attempt_id": 12,
  "question_id": 45
}
```

Response model:

```json
{
  "explanation": "..."
}
```

Behavior in code:

- Validates that the quiz attempt belongs to the authenticated user.
- Validates that the answer exists for that question in that attempt.
- Confirms the question was answered incorrectly.
- Builds a tutoring prompt.
- Sends the prompt to the Gemini model using `gemini_client.interactions.create(...)`.
- Returns the generated explanation as plain text.

### Subjects and paper data

#### GET /subjects

Returns subjects and their associated papers.

Example response:

```json
[
  {
    "id": 1,
    "name": "Physics",
    "papers": [
      {
        "id": 10,
        "year": 2020,
        "paper_number": "Paper 1"
      }
    ]
  }
]
```

#### POST /questions

Fetches all questions for a specific subject, year, and paper.

Request body:

```json
{
  "subject": "Physics",
  "year": 2020,
  "paper_number": "Paper 1"
}
```

Response shape:

```json
[
  {
    "id": 101,
    "question_number": 1,
    "question": "In a collision between two objects, kinetic energy is conserved only if",
    "options": [
      {"id": 201, "label": "A", "text": "one of the objects is initially at rest."},
      {"id": 202, "label": "B", "text": "potential energy is converted to work."}
    ]
  }
]
```

### Submitting papers

#### POST /papers/submit

Requires authentication using a bearer token.

Request body:

```json
{
  "paper_id": 1,
  "answers": [
    {"question_id": 10, "selected_option_id": 24},
    {"question_id": 11, "selected_option_id": 33}
  ]
}
```

Response model:

```json
{
  "attempt_id": 7,
  "score": 2,
  "total_questions": 20,
  "percentage": 10.0,
  "correct": 2,
  "wrong": 18,
  "wrong_questions": [
    {"question_id": 11}
  ]
}
```

Behavior in code:

- Finds the target paper.
- Loads all paper questions.
- Creates a new `Quiz_Attempts` row.
- Stores each answer in `Student_Answers`.
- Calculates the score and percentage based on which selected option matches the correct option.
- Returns both the score summary and a list of incorrect question ids.

### Dashboard

#### GET /dashboard

Query parameters:

- `user_id` (required int)
- `year` (required int)
- `month` (required int)

Example:

```http
GET /dashboard?user_id=1&year=2026&month=9
```

Response model:

```json
{
  "user": {
    "name": "Jane Doe"
  },
  "overview": {
    "current_streak": 3,
    "average_score": 72.5,
    "accuracy": 75.0,
    "total_questions_solved": 120,
    "total_duration_minutes": null
  },
  "subject_mastery": [
    {
      "subject_name": "Physics",
      "mastery_percentage": 84.0,
      "strongest_topic": null
    }
  ],
  "areas_to_improve": [
    {
      "subject_name": "Chemistry",
      "mastery_percentage": 48.0
    }
  ],
  "unfinished_quizzes": [],
  "monthly_activity": {
    "year": 2026,
    "month": 9,
    "days": [
      {"date": "2026-09-01", "quiz_count": 1},
      {"date": "2026-09-02", "quiz_count": 0}
    ]
  }
}
```

The dashboard logic calculates:

- current streak from quiz activity dates
- average score from submitted attempt percentages
- accuracy from total correct answers divided by total attempted questions
- subject mastery from `Student_Answers` by subject
- monthly activity counts by date

## Data model summary

The database schema in [eduVault/models.py](eduVault/models.py) centers on these entities:

- `User`: account record with `name`, `email`, `password_hash`, `role`, timestamps
- `StudentProfile`: student-specific profile row
- `TeacherProfile`: teacher-specific profile row
- `Subject`: academic subject, such as Physics
- `Paper`: subject-specific exam paper metadata such as year and paper number
- `Question`: question text and metadata for a paper
- `QuestionOption`: each option and whether it is correct
- `QuizAttempt`: a user’s submission for a paper
- `StudentAnswer`: the selected option for a question in a quiz attempt

## Notes and implementation details

- The app validates the database connection on startup with `check_db_connection()`.
- The JWT secret is currently hard-coded as `eduvault-secret-key` rather than loaded from environment variables.
- The app allows all HTTP methods from the configured CORS origin and includes all headers.
- The `dashboard` endpoint is not protected by a bearer token in the route definition and accepts `user_id`, `year`, and `month` as query parameters.
- `GET /subjects` and `POST /questions` are open endpoints, while signup/login and protected features use authentication.
- FastAPI auto-generates API documentation at `/docs` and `/redoc` when the server is running.

## Running the app in development

```bash
uvicorn eduVault.main:app --reload
```

Then open the API in a browser:

- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Important caveat

This repository does not include an admin panel, a Redis cache layer, or a complete Zoom integration. The comments in [eduVault/main.py](eduVault/main.py) mention planned future work such as dashboard endpoints, Zoom class support, and Redis caching, but those features are not implemented in the code currently present in this repository.

The README above reflects only the features actually present in the current codebase.
" 
