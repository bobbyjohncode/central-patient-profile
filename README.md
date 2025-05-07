# Central Patient Profile API

A FastAPI-based REST API for managing patient profiles, built with FastAPI, SQLAlchemy, and PostgreSQL (Neon).

## Features

- Create and manage patient profiles
- RESTful API endpoints
- PostgreSQL database integration
- Pydantic data validation
- Swagger/OpenAPI documentation

## Setup

1. Clone the repository:
```bash
git clone <your-repo-url>
cd central-patient-profile
```

2. Create and activate a virtual environment:
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
Create a `.env` file in the root directory with:
```
DATABASE_URL=your_neon_database_url
```

5. Run the application:
```bash
uvicorn app.main:app --reload
```

## API Documentation

Once the server is running, you can access:
- Swagger UI: http://localhost:8001/docs
- ReDoc: http://localhost:8001/redoc

## API Endpoints

- `GET /` - Health check
- `POST /patients/` - Create a new patient
- `GET /patients/` - List all patients
- `GET /patients/{patient_id}` - Get a specific patient

## Development

The project structure:
```
central-patient-profile/
├── app/
│   ├── api/
│   │   └── routes/
│   │       └── patients.py
│   ├── db/
│   │   ├── base_class.py
│   │   ├── init_db.py
│   │   └── session.py
│   ├── models/
│   │   └── patient.py
│   ├── schemas/
│   │   └── patient.py
│   └── main.py
├── requirements.txt
└── README.md
``` 