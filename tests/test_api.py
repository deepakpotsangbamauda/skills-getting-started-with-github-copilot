"""
Tests for the Mergington High School API endpoints
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities to initial state before each test"""
    # Store original state
    original_activities = {
        "Chess Club": {
            "description": "Learn strategies and compete in chess tournaments",
            "schedule": "Fridays, 3:30 PM - 5:00 PM",
            "max_participants": 12,
            "participants": ["michael@mergington.edu", "daniel@mergington.edu"]
        },
        "Programming Class": {
            "description": "Learn programming fundamentals and build software projects",
            "schedule": "Tuesdays and Thursdays, 3:30 PM - 4:30 PM",
            "max_participants": 20,
            "participants": ["emma@mergington.edu", "sophia@mergington.edu"]
        },
        "Gym Class": {
            "description": "Physical education and sports activities",
            "schedule": "Mondays, Wednesdays, Fridays, 2:00 PM - 3:00 PM",
            "max_participants": 30,
            "participants": ["john@mergington.edu", "olivia@mergington.edu"]
        },
        "Basketball Team": {
            "description": "Competitive basketball training and interschool games",
            "schedule": "Tuesdays and Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Swimming Club": {
            "description": "Swimming lessons and competitive swimming events",
            "schedule": "Mondays and Wednesdays, 3:00 PM - 4:30 PM",
            "max_participants": 20,
            "participants": []
        },
        "Art Studio": {
            "description": "Explore painting, drawing, and mixed media art projects",
            "schedule": "Wednesdays, 3:30 PM - 5:00 PM",
            "max_participants": 15,
            "participants": []
        },
        "Drama Club": {
            "description": "Acting, theater production, and performance skills",
            "schedule": "Thursdays, 4:00 PM - 6:00 PM",
            "max_participants": 25,
            "participants": []
        },
        "Debate Team": {
            "description": "Develop critical thinking and public speaking through competitive debates",
            "schedule": "Tuesdays, 3:30 PM - 5:00 PM",
            "max_participants": 16,
            "participants": []
        },
        "Science Olympiad": {
            "description": "Prepare for science competitions and conduct experiments",
            "schedule": "Fridays, 3:00 PM - 5:00 PM",
            "max_participants": 18,
            "participants": []
        }
    }
    
    # Reset activities
    activities.clear()
    activities.update(original_activities)
    
    yield


class TestRootEndpoint:
    """Tests for the root endpoint"""
    
    def test_root_redirects_to_index(self, client):
        """Test that root redirects to static index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestGetActivities:
    """Tests for GET /activities endpoint"""
    
    def test_get_activities_success(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) == 9
        assert "Chess Club" in data
        assert "Programming Class" in data
        assert "Basketball Team" in data
        
    def test_get_activities_structure(self, client):
        """Test that activities have the correct structure"""
        response = client.get("/activities")
        data = response.json()
        
        chess_club = data["Chess Club"]
        assert "description" in chess_club
        assert "schedule" in chess_club
        assert "max_participants" in chess_club
        assert "participants" in chess_club
        
        assert chess_club["max_participants"] == 12
        assert len(chess_club["participants"]) == 2


class TestSignupForActivity:
    """Tests for POST /activities/{activity_name}/signup endpoint"""
    
    def test_signup_success(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == "Signed up test@mergington.edu for Basketball Team"
        
        # Verify participant was added
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert "test@mergington.edu" in activities_data["Basketball Team"]["participants"]
    
    def test_signup_duplicate(self, client):
        """Test that duplicate signup is rejected"""
        # First signup
        client.post(
            "/activities/Basketball Team/signup",
            params={"email": "test@mergington.edu"}
        )
        
        # Second signup with same email
        response = client.post(
            "/activities/Basketball Team/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up for this activity"
    
    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Club/signup",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_signup_with_existing_participants(self, client):
        """Test signup for activity that already has participants"""
        response = client.post(
            "/activities/Chess Club/signup",
            params={"email": "new.student@mergington.edu"}
        )
        assert response.status_code == 200
        
        # Verify participant was added to existing list
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        participants = activities_data["Chess Club"]["participants"]
        
        assert "new.student@mergington.edu" in participants
        assert len(participants) == 3  # 2 original + 1 new
    
    def test_signup_url_encoding(self, client):
        """Test signup with activity name that requires URL encoding"""
        response = client.post(
            "/activities/Programming Class/signup",
            params={"email": "coder@mergington.edu"}
        )
        assert response.status_code == 200


class TestUnregisterFromActivity:
    """Tests for DELETE /activities/{activity_name}/unregister endpoint"""
    
    def test_unregister_success(self, client):
        """Test successful unregistration from an activity"""
        # First, ensure participant is registered
        email = "michael@mergington.edu"
        
        # Unregister
        response = client.delete(
            "/activities/Chess Club/unregister",
            params={"email": email}
        )
        assert response.status_code == 200
        
        data = response.json()
        assert data["message"] == f"Unregistered {email} from Chess Club"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert email not in activities_data["Chess Club"]["participants"]
    
    def test_unregister_not_registered(self, client):
        """Test unregistration when participant is not registered"""
        response = client.delete(
            "/activities/Basketball Team/unregister",
            params={"email": "notregistered@mergington.edu"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student is not registered for this activity"
    
    def test_unregister_nonexistent_activity(self, client):
        """Test unregistration from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Club/unregister",
            params={"email": "test@mergington.edu"}
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"
    
    def test_unregister_all_participants(self, client):
        """Test unregistering all participants from an activity"""
        # Unregister both participants from Chess Club
        client.delete("/activities/Chess Club/unregister", params={"email": "michael@mergington.edu"})
        client.delete("/activities/Chess Club/unregister", params={"email": "daniel@mergington.edu"})
        
        # Verify activity has no participants
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        assert len(activities_data["Chess Club"]["participants"]) == 0


class TestIntegrationScenarios:
    """Integration tests for complete user workflows"""
    
    def test_signup_and_unregister_workflow(self, client):
        """Test complete signup and unregister workflow"""
        email = "workflow.test@mergington.edu"
        activity = "Swimming Club"
        
        # Sign up
        signup_response = client.post(
            f"/activities/{activity}/signup",
            params={"email": email}
        )
        assert signup_response.status_code == 200
        
        # Verify signup
        activities_response = client.get("/activities")
        assert email in activities_response.json()[activity]["participants"]
        
        # Unregister
        unregister_response = client.delete(
            f"/activities/{activity}/unregister",
            params={"email": email}
        )
        assert unregister_response.status_code == 200
        
        # Verify unregistration
        activities_response = client.get("/activities")
        assert email not in activities_response.json()[activity]["participants"]
    
    def test_multiple_signups_different_activities(self, client):
        """Test signing up for multiple activities"""
        email = "multisport@mergington.edu"
        
        # Sign up for multiple activities
        activities_to_join = ["Basketball Team", "Swimming Club", "Drama Club"]
        
        for activity in activities_to_join:
            response = client.post(
                f"/activities/{activity}/signup",
                params={"email": email}
            )
            assert response.status_code == 200
        
        # Verify all signups
        activities_response = client.get("/activities")
        activities_data = activities_response.json()
        
        for activity in activities_to_join:
            assert email in activities_data[activity]["participants"]
