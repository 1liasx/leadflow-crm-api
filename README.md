LeadFlow AI CRM



LeadFlow is a production-oriented lead intake and AI qualification system built with FastAPI, PostgreSQL, n8n, OpenAI, Docker, Alembic, and Pytest.

It receives inbound leads through a production webhook, validates and normalizes the payload, reuses or creates the related company and contact, prevents duplicate lead processing with an external ID, qualifies new opportunities with AI, and persists the enriched result through a documented REST API.

Why This Project

Lead intake often starts with forms, spreadsheets, and disconnected automation steps. That approach becomes fragile when the same request is submitted twice, business data must stay relational, or failures need to be investigated.

LeadFlow provides:

A relational CRM backend instead of a spreadsheet database

Idempotent lead processing with a unique external_id

Company and contact deduplication

AI-based lead scoring and qualification

A production n8n webhook with structured responses

Centralized workflow error handling and safe API retries

Versioned database migrations

Automated tests and Docker image validation in GitHub Actions

System Architecture

flowchart TD
    Form["Website / external system"] --> Webhook["n8n production webhook"]
    Webhook --> Normalize["Normalize and validate"]
    Normalize --> Resolve["Resolve company and contact"]
    Resolve --> Deduplicate["Check external lead ID"]
    Deduplicate -->|Existing| Existing["Return existing lead"]
    Deduplicate -->|New| AI["AI qualification"]
    AI --> API["FastAPI CRM API"]
    API --> DB["PostgreSQL"]

Workflow failures are routed to a separate LF-99 Error Handler workflow, which records structured execution details for diagnosis.

Lead Intake Workflow

The versioned n8n workflow performs the following operations:

Receive a JSON payload through POST /webhook/leadflow-intake.

Validate required fields and normalize email addresses, phone numbers, currency, and source.

Find or create the company.

Find or create the contact.

Search for an existing lead by external_id.

Return the existing lead without calling the AI model when the request was already processed.

Qualify a new lead with an AI scoring rubric.

Parse and validate the AI JSON response.

Create the enriched lead in the CRM API.

Return a consistent JSON response to the caller.

Example response for a new lead:

{
  "success": true,
  "created": true,
  "message": "Lead created successfully",
  "lead_id": 9,
  "external_id": "FORM-PROD-001"
}

Example response for a duplicate request:

{
  "success": true,
  "created": false,
  "message": "Lead already processed",
  "lead_id": 9,
  "external_id": "FORM-PROD-001"
}

AI Qualification

New opportunities receive:

A score from 0 to 100

A priority: low, medium, or high

A CRM status derived from the score

A concise French summary

A concrete recommended action

The parsed response is validated before persistence. The original description and the AI qualification are stored together so the decision remains auditable.

Technology Stack

Technology

Purpose

Python 3.13

Application runtime

FastAPI

REST API and OpenAPI documentation

PostgreSQL 17

Relational persistence

SQLAlchemy 2

ORM and database sessions

Pydantic 2

Request and response validation

Alembic

Versioned database migrations

n8n

Workflow orchestration and production webhook

OpenAI

Lead qualification

Docker Compose

Local multi-container environment

Pytest

Integration tests

GitHub Actions

Migrations, tests, and Docker build validation

Data Model

erDiagram
    COMPANY ||--o{ CONTACT : has
    COMPANY ||--o{ LEAD : owns
    CONTACT o|--o{ LEAD : qualifies

    COMPANY {
        int id PK
        string name UK
        string industry
        string website
        string phone
    }

    CONTACT {
        int id PK
        int company_id FK
        string first_name
        string last_name
        string email UK
        string phone
        string job_title
    }

    LEAD {
        int id PK
        int company_id FK
        int contact_id FK
        string external_id UK
        string title
        text description
        string status
        decimal estimated_value
        string currency
    }

Business Rules

Company names and contact emails are unique.

Every contact belongs to an existing company.

Every lead belongs to a company.

A referenced contact must belong to the selected company.

external_id prevents the same external request from creating multiple leads.

Unsupported lead statuses and negative estimated values are rejected.

Companies with linked records cannot be deleted.

Deleting a contact preserves its leads and sets their contact_id to NULL.

Supported lead statuses:

new → qualified → won
                ↘ lost

API

The application exposes 15 CRUD endpoints plus a health endpoint.

Resource

Operations and filters

Health

GET /health

Companies

Create, list, retrieve, update, delete; exact case-insensitive name filter

Contacts

Create, list, retrieve, update, delete; company_id and exact case-insensitive email filters

Leads

Create, list, retrieve, update, delete; company_id, contact_id, status, and external_id filters

Interactive documentation:

Swagger UI: http://localhost:8001/docs

ReDoc: http://localhost:8001/redoc

Run Locally

Requirements

Git

Docker Desktop

Docker Compose

1. Clone the repository

git clone https://github.com/1liasx/leadflow-crm-api.git
cd leadflow-crm-api

2. Create the environment file

Windows PowerShell:

Copy-Item .env.example .env

Linux or macOS:

cp .env.example .env

Replace the example PostgreSQL password and n8n encryption key before starting the stack. Never commit .env.

Generate a suitable n8n encryption key:

openssl rand -hex 32

3. Start the stack

docker compose up --build -d

Service

Local address

FastAPI

http://localhost:8001

n8n

http://localhost:5678

PostgreSQL

localhost:5432

Test PostgreSQL

localhost:5433

Check container status:

docker compose ps

Check API health:

curl http://localhost:8001/health

Expected response:

{"status":"healthy"}

Import the n8n Workflows

The sanitized exports are stored in n8n/workflows/:

LF-01-lead-intake-ai-qualification.json

LF-99-error-handler.json

After importing them:

Connect an OpenAI credential to the chat model node.

Select LF-99 Error Handler in the main workflow's error workflow setting.

Verify the internal API base URL is http://app:8000.

Publish both workflows.

Production webhook:

POST http://localhost:5678/webhook/leadflow-intake

Test

Start the isolated test database:

docker compose up -d db_test

Run the test suite:

python -m pytest -q

The current suite contains 18 integration tests covering companies, contacts, leads, validation, relational rules, and health checks.

Database Migrations

Apply all migrations:

python -m alembic upgrade head

Show the current revision:

python -m alembic current

Create a new migration after a model change:

python -m alembic revision --autogenerate -m "describe change"

Continuous Integration

Every push and pull request to main runs:

A PostgreSQL 17 service

Dependency installation on Python 3.13

The complete Alembic migration chain

The Pytest suite

A clean Docker image build

The pipeline is defined in .github/workflows/ci.yml.

Security Notes

Secrets are loaded from .env, which is excluded from Git.

The n8n encryption key must be unique and kept outside the repository.

Exported workflows do not contain credentials or local workflow identifiers.

PostgreSQL ports are intended for local development and should not be publicly exposed in production.

Production deployment should terminate TLS through a reverse proxy and restrict API, database, and n8n administration access.

Project Structure

.
├── .github/workflows/ci.yml
├── alembic/
├── app/
│   ├── models/
│   ├── routers/
│   ├── schemas/
│   ├── config.py
│   ├── database.py
│   └── main.py
├── n8n/workflows/
├── tests/
├── .env.example
├── Dockerfile
├── docker-compose.yml
└── requirements.txt

Stop the Stack

Keep persisted data:

docker compose down

Remove local database and n8n volumes:

docker compose down -v

The second command permanently deletes local container data.