import pytest

from app.extensions import db
from app.models.user import User


@pytest.fixture()
def account():
    return {
        "email": "peter@example.com",
        "display_name": "Peter",
        "password": "Shipyard learning password!",
    }


def register_and_login(client, account):
    registration = client.post("/api/v1/auth/register", json=account)
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": account["email"],
            "password": account["password"],
        },
    )
    assert login.status_code == 200

    return login.get_json()["data"]["access_token"]


def test_register_creates_account(client, account):
    response = client.post("/api/v1/auth/register", json=account)
    data = response.get_json()["data"]

    assert response.status_code == 201
    assert data["email"] == account["email"]
    assert data["display_name"] == account["display_name"]
    assert "password" not in data
    assert "password_hash" not in data


def test_registration_hashes_password(client, app, account):
    client.post("/api/v1/auth/register", json=account)

    with app.app_context():
        user = db.session.scalar(
            db.select(User).where(User.email == account["email"])
        )

        assert user is not None
        assert user.password_hash != account["password"]
        assert user.check_password(account["password"])


def test_duplicate_registration_is_rejected(client, account):
    client.post("/api/v1/auth/register", json=account)
    response = client.post("/api/v1/auth/register", json=account)

    assert response.status_code == 409
    assert response.get_json()["error"]["code"] == "CONFLICT"


def test_registration_requires_password(client, account):
    account.pop("password")
    response = client.post("/api/v1/auth/register", json=account)

    assert response.status_code == 400


def test_registration_requires_json_object(client):
    response = client.post(
        "/api/v1/auth/register",
        data="not JSON",
        content_type="text/plain",
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_JSON"


def test_login_returns_token(client, account):
    token = register_and_login(client, account)

    assert isinstance(token, str)
    assert token


def test_wrong_password_is_rejected(client, account):
    client.post("/api/v1/auth/register", json=account)

    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": account["email"],
            "password": "A completely wrong password!",
        },
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["code"] == "INVALID_CREDENTIALS"


def test_unknown_account_is_rejected(client):
    response = client.post(
        "/api/v1/auth/login",
        json={
            "email": "missing@example.com",
            "password": "A completely wrong password!",
        },
    )

    assert response.status_code == 401
    assert response.get_json()["error"]["message"] == "Invalid email or password."


def test_me_returns_authenticated_user(client, account):
    token = register_and_login(client, account)

    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["email"] == account["email"]


def test_me_requires_token(client):
    response = client.get("/api/v1/auth/me")

    assert response.status_code == 401


def test_me_rejects_invalid_token(client):
    response = client.get(
        "/api/v1/auth/me",
        headers={"Authorization": "Bearer not-a-valid-token"},
    )

    assert response.status_code == 401


def test_old_public_user_routes_are_removed(client):
    assert client.get("/api/v1/users").status_code == 404
    assert client.post("/api/v1/users", json={}).status_code == 404