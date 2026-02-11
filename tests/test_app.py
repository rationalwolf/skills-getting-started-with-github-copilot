"""
Tests for the Mergington High School Activities API
"""
import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


class TestGetActivities:
    """Test suite for GET /activities endpoint"""
    
    def test_get_activities_returns_200(self, client):
        """Test that get_activities returns a 200 status code"""
        response = client.get("/activities")
        assert response.status_code == 200
    
    def test_get_activities_returns_dict(self, client):
        """Test that get_activities returns a dictionary"""
        response = client.get("/activities")
        assert isinstance(response.json(), dict)
    
    def test_get_activities_contains_expected_activities(self, client):
        """Test that get_activities returns expected activity names"""
        response = client.get("/activities")
        activities = response.json()
        
        expected_activities = ["Basketball", "Tennis Club", "Art Studio", "Drama Club", 
                               "Debate Team", "Science Club", "Chess Club", 
                               "Programming Class", "Gym Class"]
        
        for activity in expected_activities:
            assert activity in activities
    
    def test_activity_has_required_fields(self, client):
        """Test that each activity has required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        required_fields = ["description", "schedule", "max_participants", "participants"]
        
        for activity_name, activity_data in activities.items():
            for field in required_fields:
                assert field in activity_data, f"Activity '{activity_name}' missing field '{field}'"


class TestSignupForActivity:
    """Test suite for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_returns_200_on_success(self, client):
        """Test that signup returns 200 on successful registration"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 200
    
    def test_signup_returns_success_message(self, client):
        """Test that signup returns a success message"""
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": "new-student@mergington.edu"}
        )
        assert response.status_code == 200
        assert "message" in response.json()
        assert "new-student@mergington.edu" in response.json()["message"]
    
    def test_signup_adds_participant_to_activity(self, client):
        """Test that signup actually adds participant to the activity"""
        email = "testuser123@mergington.edu"
        
        # Sign up
        response = client.post(
            "/activities/Tennis Club/signup",
            params={"email": email}
        )
        assert response.status_code == 200
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Tennis Club"]["participants"]
    
    def test_signup_nonexistent_activity_returns_404(self, client):
        """Test that signing up for nonexistent activity returns 404"""
        response = client.post(
            "/activities/Nonexistent Activity/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_signup_duplicate_email_returns_400(self, client):
        """Test that duplicate signup returns 400 error"""
        # Get initial participant
        activities_response = client.get("/activities")
        activities = activities_response.json()
        existing_participant = activities["Basketball"]["participants"][0]
        
        # Try to sign up the same participant again
        response = client.post(
            "/activities/Basketball/signup",
            params={"email": existing_participant}
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"].lower()


class TestUnregisterFromActivity:
    """Test suite for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_returns_200_on_success(self, client):
        """Test that unregister returns 200 on successful removal"""
        # First sign up
        email = "unregister-test@mergington.edu"
        client.post(
            "/activities/Drama Club/signup",
            params={"email": email}
        )
        
        # Then unregister
        response = client.delete(
            "/activities/Drama Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
    
    def test_unregister_returns_success_message(self, client):
        """Test that unregister returns a success message"""
        email = "unregister-test2@mergington.edu"
        client.post(
            "/activities/Science Club/signup",
            params={"email": email}
        )
        
        response = client.delete(
            "/activities/Science Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        assert "message" in response.json()
        assert email in response.json()["message"]
    
    def test_unregister_removes_participant_from_activity(self, client):
        """Test that unregister actually removes participant from activity"""
        email = "unregister-test3@mergington.edu"
        
        # Sign up
        client.post(
            "/activities/Art Studio/signup",
            params={"email": email}
        )
        
        # Verify they're in the list
        activities_response = client.get("/activities")
        assert email in activities_response.json()["Art Studio"]["participants"]
        
        # Unregister
        client.delete(
            "/activities/Art Studio/unregister",
            params={"email": email}
        )
        
        # Verify they're removed
        activities_response = client.get("/activities")
        assert email not in activities_response.json()["Art Studio"]["participants"]
    
    def test_unregister_nonexistent_activity_returns_404(self, client):
        """Test that unregistering from nonexistent activity returns 404"""
        response = client.delete(
            "/activities/Nonexistent Activity/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert "not found" in response.json()["detail"].lower()
    
    def test_unregister_non_participant_returns_400(self, client):
        """Test that unregistering a non-participant returns 400"""
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": "not-a-participant@mergington.edu"}
        )
        assert response.status_code == 400
        assert "not signed up" in response.json()["detail"].lower()


class TestActivityConstraints:
    """Test suite for activity constraints"""
    
    def test_get_activities_respects_max_participants(self, client):
        """Test that activities have max_participants field and it's reasonable"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            max_participants = activity_data["max_participants"]
            actual_participants = len(activity_data["participants"])
            
            # Max should be at least as many as current participants
            assert max_participants >= actual_participants, \
                f"{activity_name} has more participants than max allowed"
