# Salon Assistant

A voice-enabled salon booking assistant that helps customers schedule appointments and check service availability.

## Prerequisites

- Python 3.8 or higher
- PostgreSQL 12 or higher
- psql command-line tool

## Installation

1. Clone the repository:
```bash
git clone <repository-url>
cd salon
```

2. Create and activate a virtual environment:
```bash
python -m venv venv
# On Windows:
venv\Scripts\activate
# On macOS/Linux:
source venv/bin/activate
```

3. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Database Setup

1. Start PostgreSQL service:
```bash
# On macOS
brew services start postgresql

# On Ubuntu/Debian
sudo service postgresql start

# On Windows
# Start PostgreSQL service from Services application
```

2. Create the database:
```bash
psql -U postgres
CREATE DATABASE salon;
\q
```

3. Seed the database with initial data:
```bash
# From project root
python scripts/seed_database.py
```

## Configuration

1. Create a `.env` file in the root directory or copy from .env.example:

```env
# Database Settings
DATABASE_URL=postgresql://{username}:{password}@localhost:5432/salon

# Voice Service Settingsa
WHISPER_MODEL=tiny  # Options: tiny, base, small, medium, large
TTS_LANGUAGE=en
TTS_PROVIDER=gtts  # Options: gtts, google_cloud
STT_PROVIDER=whisper  # Options: whisper, google_cloud

# Optional Google Cloud Settings
GOOGLE_CLOUD_CREDENTIALS=path/to/credentials.json  # Only if using Google Cloud services
```

## Running the Application

You'll need to run three components: the FastAPI server, the Rasa server, and the Rasa Action server.

1. Ensure PostgreSQL is running:
```bash
# Check PostgreSQL status
# On macOS
brew services list | grep postgresql

# On Ubuntu/Debian
sudo service postgresql status

# On Windows
# Check Services application
```

2. Start the FastAPI server:
```bash
# From the project root
uvicorn app.main:app --reload --port 8000
```

3. Start the Rasa server:
```bash
# From the rasa directory
rasa run --enable-api --cors "*" --port 5005 --model stable-model.tar.gz
```

4. Start the Rasa Action server (in a new terminal):
```bash
# From the rasa directory
rasa run actions --port 5055
```
## Training a new model
After making changes to the rasa config files you will need to re-train
```bash
# From the rasa directory
rasa train
```

You can then start the model
```bash
# From the rasa directory
rasa run --enable-api --cors "*" --port 5005 --model route/to/model
```

## Testing the Application

1. Run the test suite:
```bash
# From the project root
pytest
```

2. Access the voice interface:
- Open your browser and navigate to: `http://localhost:8000/static/voice.html`
- Click "Start Recording" and allow microphone access
- Speak your request (e.g., "I want to book a haircut")
- Click "Stop Recording" to process your request

## Available Services

The assistant can help with:
- Booking appointments for:
  - Haircuts
  - Massages
  - Facials
  - Manicures
  - Pedicures
  - Hair coloring
  - Styling
- Checking service availability
- Canceling appointments

## Development

### Project Structure

```
salon/
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

## License

MIT License 