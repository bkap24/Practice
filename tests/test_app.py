from copy import deepcopy

import pytest
from fastapi.testclient import TestClient

from src import app as app_module


client = TestClient(app_module.app)


@pytest.fixture(autouse=True)
def restore_activities():
    original_activities = deepcopy(app_module.activities)

    yield

    app_module.activities.clear()
    app_module.activities.update(original_activities)


def test_root_redirects_to_static_index():
    # Arrange
    request_options = {"follow_redirects": False}

    # Act
    response = client.get("/", **request_options)

    # Assert
    assert response.status_code == 307
    assert response.headers["location"] == "/static/index.html"


def test_get_activities_returns_configured_activities():
    # Arrange
    expected_activity_names = set(app_module.activities)

    # Act
    response = client.get("/activities")

    # Assert
    assert response.status_code == 200
    assert set(response.json()) == expected_activity_names
    assert response.json()["Soccer Club"]["participants"] == []


def test_signup_adds_participant_to_activity():
    # Arrange
    activity_name = "Soccer Club"
    email = "student@example.com"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Signed up {email} for {activity_name}"}
    assert email in app_module.activities[activity_name]["participants"]


def test_signup_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": "student@example.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_signup_rejects_duplicate_participant():
    # Arrange
    activity_name = "Soccer Club"
    email = "student@example.com"
    app_module.activities[activity_name]["participants"].append(email)

    # Act
    response = client.post(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 400
    assert response.json() == {"detail": "Student already signed up"}


def test_unregister_removes_participant_from_activity():
    # Arrange
    activity_name = "Soccer Club"
    email = "student@example.com"
    app_module.activities[activity_name]["participants"].append(email)

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": email}
    )

    # Assert
    assert response.status_code == 200
    assert response.json() == {"message": f"Unregistered {email} from {activity_name}"}
    assert email not in app_module.activities[activity_name]["participants"]


def test_unregister_rejects_unknown_activity():
    # Arrange
    activity_name = "Unknown Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": "student@example.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Activity not found"}


def test_unregister_rejects_student_not_signed_up():
    # Arrange
    activity_name = "Soccer Club"

    # Act
    response = client.delete(
        f"/activities/{activity_name}/signup", params={"email": "student@example.com"}
    )

    # Assert
    assert response.status_code == 404
    assert response.json() == {"detail": "Student is not signed up"}