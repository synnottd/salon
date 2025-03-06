from datetime import datetime, timedelta
import pytest
from fastapi import HTTPException
from fastapi.testclient import TestClient
from unittest.mock import Mock, AsyncMock
from app.main import app
from app.services.appointment_service import AppointmentService
from app.models import AppointmentStatus

# Add this at the top of your test file
pytestmark = pytest.mark.asyncio

# Mock the get_db dependency
@pytest.fixture
def mock_db():
    return Mock()

# Mock the AppointmentService
@pytest.fixture
def mock_appointment_service():
    service = Mock(spec=AppointmentService)
    # Convert all methods to AsyncMock since they're async
    service.create_appointment = AsyncMock()
    service.get_customer_appointments = AsyncMock()
    service.get_appointment = AsyncMock()
    service.cancel_appointment = AsyncMock()
    service.check_availability = AsyncMock()
    return service

# Patch the AppointmentService initialization
@pytest.fixture
def client(mock_db, mock_appointment_service, monkeypatch):
    def get_test_db():
        return mock_db
    
    def get_test_appointment_service(db):
        return mock_appointment_service
    
    monkeypatch.setattr("app.api.api_v1.endpoints.appointments.get_db", get_test_db)
    monkeypatch.setattr("app.api.api_v1.endpoints.appointments.AppointmentService", lambda db: mock_appointment_service)
    
    return TestClient(app)

# Test data
@pytest.fixture
def sample_appointment_data():
    return {
        "customer_id": 1,
        "staff_id": 2,
        "service_id": 3,
        "branch_id": 1,
        "appointment_time": "2024-03-10T14:00:00",
        "notes": "Test appointment"
    }

@pytest.fixture
def sample_appointment_response():
    return {
        "id": 1,
        "customer_id": 1,
        "staff_id": 2,
        "service_id": 3,
        "branch_id": 1,
        "appointment_time": "2024-03-10T14:00:00",
        "end_time": "2024-03-10T15:00:00",
        "status": "SCHEDULED",
        "notes": "Test appointment"
    }

# Tests for create_appointment
@pytest.mark.asyncio
async def test_create_appointment_success(client, mock_appointment_service, sample_appointment_data, sample_appointment_response):
    mock_appointment_service.create_appointment.return_value = sample_appointment_response
    
    response = client.post("/api/v1/appointments/", json=sample_appointment_data)
    
    assert response.status_code == 200
    assert response.json() == sample_appointment_response
    
    # Convert the appointment_time to datetime before assertion
    expected_data = dict(sample_appointment_data)
    expected_data['appointment_time'] = datetime.fromisoformat(expected_data['appointment_time'])
    mock_appointment_service.create_appointment.assert_awaited_once_with(**expected_data)

async def test_create_appointment_failure(client, mock_appointment_service, sample_appointment_data):
    mock_appointment_service.create_appointment.side_effect = HTTPException(status_code=400, detail="Appointment time not available")
    
    response = client.post("/api/v1/appointments/", json=sample_appointment_data)
    
    assert response.status_code == 400
    assert "Appointment time not available" in response.json()["detail"]

# Tests for get_appointments
async def test_get_appointments_success(client, mock_appointment_service, sample_appointment_response):
    mock_appointment_service.get_customer_appointments.return_value = [sample_appointment_response]
    
    response = client.get("/api/v1/appointments/", params={"customer_id": "1"})
    
    assert response.status_code == 200
    assert response.json() == [sample_appointment_response]
    mock_appointment_service.get_customer_appointments.assert_awaited_once_with(
        customer_id=1,
        start_date=None,
        end_date=None
    )

async def test_get_appointments_empty(client, mock_appointment_service):
    mock_appointment_service.get_customer_appointments.return_value = []
    
    response = client.get("/api/v1/appointments/")
    
    assert response.status_code == 200
    assert response.json() == []

# Tests for get_appointment
async def test_get_appointment_success(client, mock_appointment_service, sample_appointment_response):
    mock_appointment_service.get_appointment.return_value = sample_appointment_response
    
    response = client.get("/api/v1/appointments/1")
    
    assert response.status_code == 200
    assert response.json() == sample_appointment_response
    mock_appointment_service.get_appointment.assert_awaited_once_with(appointment_id=1)

async def test_get_appointment_not_found(client, mock_appointment_service):
    mock_appointment_service.get_appointment.side_effect = HTTPException(status_code=404, detail="Appointment not found")
    
    response = client.get("/api/v1/appointments/999")
    
    assert response.status_code == 404
    assert "Appointment not found" in response.json()["detail"]

# Tests for cancel_appointment
async def test_cancel_appointment_success(client, mock_appointment_service, sample_appointment_response):
    cancelled_appointment = dict(sample_appointment_response)
    cancelled_appointment["status"] = "CANCELLED"
    mock_appointment_service.cancel_appointment.return_value = cancelled_appointment
    
    response = client.post("/api/v1/appointments/1/cancel")
    
    assert response.status_code == 200
    assert response.json()["status"] == "CANCELLED"
    mock_appointment_service.cancel_appointment.assert_awaited_once_with(appointment_id=1)

async def test_cancel_appointment_not_found(client, mock_appointment_service):
    mock_appointment_service.cancel_appointment.side_effect = HTTPException(status_code=404, detail="Appointment not found")
    
    response = client.post("/api/v1/appointments/999/cancel")
    
    assert response.status_code == 404
    assert "Appointment not found" in response.json()["detail"]

# Tests for check_availability
async def test_check_availability_success(client, mock_appointment_service):
    available_slots = [
        "2024-03-10T14:00:00",  # Keep as strings since that's what the API returns
        "2024-03-10T15:00:00",
        "2024-03-10T16:00:00"
    ]
    mock_appointment_service.check_availability.return_value = available_slots
    
    # Use ISO format for date parameter
    test_date = datetime(2024, 3, 10)
    response = client.get(
        "/api/v1/appointments/availability/",  # Added trailing slash
        params={
            "branch_id": 1,
            "service_id": 1,
            "date": test_date.isoformat(),  # Use date() to get just the date part
            "staff_id": 1
        }
    )
    print(response.json())
    assert response.status_code == 200
    assert response.json() == available_slots
    mock_appointment_service.check_availability.assert_awaited_once_with(
        branch_id=1,
        service_id=1,
        date=test_date,
        staff_id=1
    )

async def test_check_availability_no_slots(client, mock_appointment_service):
    mock_appointment_service.check_availability.return_value = []
    
    # Use ISO format for date parameter
    test_date = datetime(2024, 3, 10)
    response = client.get(
        "/api/v1/appointments/availability/",  # Added trailing slash
        params={
            "branch_id": 1,
            "service_id": 1,
            "date": test_date.isoformat()  # Use date() to get just the date part
        }
    )
    print(response.json())
    
    assert response.status_code == 200
    assert response.json() == [] 