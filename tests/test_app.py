from collections.abc import Iterator

import pytest
from fastapi.testclient import TestClient

from src.app import activities, app


@pytest.fixture
def client() -> Iterator[TestClient]:
    with TestClient(app) as test_client:
        yield test_client


@pytest.fixture
def test_activity() -> Iterator[str]:
    activity_name = "Pytest Activity"
    activities[activity_name] = {
        "description": "Activity used by API tests",
        "schedule": "Test schedule",
        "max_participants": 3,
        "participants": [],
    }

    yield activity_name

    del activities[activity_name]


def test_get_activities_includes_activity_details(
    client: TestClient, test_activity: str
) -> None:
    response = client.get("/activities")

    assert response.status_code == 200
    assert response.json()[test_activity] == {
        "description": "Activity used by API tests",
        "schedule": "Test schedule",
        "max_participants": 3,
        "participants": [],
    }


def test_signup_adds_participant(
    client: TestClient, test_activity: str
) -> None:
    email = "student@example.edu"

    response = client.post(
        f"/activities/{test_activity}/signup", params={"email": email}
    )

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Signed up {email} for {test_activity}"
    }
    assert email in client.get("/activities").json()[test_activity]["participants"]


def test_signup_rejects_duplicate_registration(
    client: TestClient, test_activity: str
) -> None:
    email = "student@example.edu"
    signup_url = f"/activities/{test_activity}/signup"

    assert client.post(signup_url, params={"email": email}).status_code == 200
    response = client.post(signup_url, params={"email": email})

    assert response.status_code == 400
    assert response.json()["detail"] == "Student is already signed up for this activity"
    assert client.get("/activities").json()[test_activity]["participants"] == [email]


def test_signup_returns_404_for_unknown_activity(client: TestClient) -> None:
    response = client.post(
        "/activities/Unknown Activity/signup",
        params={"email": "student@example.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"


def test_unregister_removes_participant(
    client: TestClient, test_activity: str
) -> None:
    email = "student@example.edu"
    signup_url = f"/activities/{test_activity}/signup"
    client.post(signup_url, params={"email": email})

    response = client.delete(signup_url, params={"email": email})

    assert response.status_code == 200
    assert response.json() == {
        "message": f"Unregistered {email} from {test_activity}"
    }
    assert email not in client.get("/activities").json()[test_activity]["participants"]


def test_unregister_returns_404_for_unregistered_participant(
    client: TestClient, test_activity: str
) -> None:
    response = client.delete(
        f"/activities/{test_activity}/signup",
        params={"email": "student@example.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Student is not signed up for this activity"


def test_unregister_returns_404_for_unknown_activity(client: TestClient) -> None:
    response = client.delete(
        "/activities/Unknown Activity/signup",
        params={"email": "student@example.edu"},
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Activity not found"
