import pytest


@pytest.fixture()
def owner_headers(client):
    return account_headers(client, "owner@example.com")


@pytest.fixture()
def outsider_headers(client):
    return account_headers(client, "outsider@example.com")


def account_headers(client, email):
    password = "Shipyard organization password!"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": "Test User",
            "password": password,
        },
    )
    assert registration.status_code == 201

    login = client.post(
        "/api/v1/auth/login",
        json={
            "email": email,
            "password": password,
        },
    )
    assert login.status_code == 200

    token = login.get_json()["data"]["access_token"]

    return {"Authorization": f"Bearer {token}"}


def create_team(client, headers):
    response = client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": "Shipyard Team"},
    )

    assert response.status_code == 201
    return response.get_json()["data"]


def test_create_organization_assigns_owner(client, owner_headers):
    organization = create_team(client, owner_headers)

    assert organization["name"] == "Shipyard Team"
    assert organization["role"] == "owner"


def test_created_organization_appears_in_owners_list(client, owner_headers):
    organization = create_team(client, owner_headers)

    response = client.get(
        "/api/v1/organizations",
        headers=owner_headers,
    )

    assert response.status_code == 200

    data = response.get_json()["data"]
    assert len(data) == 1
    assert data[0]["id"] == organization["id"]


def test_owner_can_view_organization(client, owner_headers):
    organization = create_team(client, owner_headers)

    response = client.get(
        f"/api/v1/organizations/{organization['id']}",
        headers=owner_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["data"]["role"] == "owner"


def test_outsider_cannot_list_another_users_organization(
    client, owner_headers, outsider_headers
):
    create_team(client, owner_headers)

    response = client.get(
        "/api/v1/organizations",
        headers=outsider_headers,
    )

    assert response.status_code == 200
    assert response.get_json()["data"] == []


def test_outsider_cannot_view_organization(
    client, owner_headers, outsider_headers
):
    organization = create_team(client, owner_headers)

    response = client.get(
        f"/api/v1/organizations/{organization['id']}",
        headers=outsider_headers,
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "NOT_FOUND"


@pytest.mark.parametrize("name", ["", "   ", "x" * 101, None])
def test_invalid_organization_name_is_rejected(
    client, owner_headers, name
):
    response = client.post(
        "/api/v1/organizations",
        headers=owner_headers,
        json={"name": name},
    )

    assert response.status_code == 400


def test_create_organization_requires_json_object(client, owner_headers):
    response = client.post(
        "/api/v1/organizations",
        headers=owner_headers,
        json=[],
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_JSON"


def test_client_cannot_override_creator_or_role(
    client, owner_headers, outsider_headers
):
    response = client.post(
        "/api/v1/organizations",
        headers=owner_headers,
        json={
            "name": "My Team",
            "role": "member",
            "user_id": 999999,
        },
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["role"] == "owner"

    outsiders_list = client.get(
        "/api/v1/organizations",
        headers=outsider_headers,
    )
    assert outsiders_list.get_json()["data"] == []


def test_organization_routes_require_authentication(client):
    assert client.get("/api/v1/organizations").status_code == 401

    assert client.post(
        "/api/v1/organizations",
        json={"name": "No Access"},
    ).status_code == 401

    assert client.get("/api/v1/organizations/1").status_code == 401