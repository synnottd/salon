# Salon Booking AI Voice Agent

An AI-powered voice agent that handles salon bookings through natural voice commands. This system allows customers to book appointments, check availability, and manage their bookings using voice interactions.

## Features

- Natural voice interface for booking appointments
- Real-time availability checking across multiple branches
- Staff and service management
- Secure payment processing
- Multi-branch coordination
- Natural conversation flow with context awareness

## Tech Stack

- Backend: FastAPI (Python)
- Database: PostgreSQL
- Voice Processing: Google Cloud Speech-to-Text
- NLP: DialogFlow
- Text-to-Speech: Google Cloud TTS
- Payment Processing: Stripe
- Real-time Updates: WebSocket
- Authentication: JWT

## Prerequisites

- Python 3.8+
- PostgreSQL
- Google Cloud Platform account with Speech-to-Text and Text-to-Speech APIs enabled
- DialogFlow account
- Stripe account

## Setup

1. Clone the repository:
```bash
git clone <repository-url>
cd salon-booking-ai
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Set up environment variables:
```bash
cp .env.example .env
# Edit .env with your configuration
```

5. Initialize the database:
```bash
python scripts/init_db.py
```

6. Run the development server:
```bash
uvicorn app.main:app --reload
```

## Project Structure

```
salon-booking-ai/
├── app/
│   ├── api/            # API endpoints
│   ├── core/           # Core functionality
│   ├── db/             # Database models and migrations
│   ├── services/       # Business logic
│   └── utils/          # Utility functions
├── tests/              # Test files
├── scripts/            # Utility scripts
├── .env.example        # Example environment variables
├── requirements.txt    # Project dependencies
└── README.md          # This file
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

Run tests with:
```bash
pytest
```

## License

MIT License 