import pytest


def account_headers(client, email):
    password = "Shipyard project password!"

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
        json={"email": email, "password": password},
    )
    assert login.status_code == 200

    token = login.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def team(client):
    owner = account_headers(client, "owner@example.com")
    member = account_headers(client, "member@example.com")
    outsider = account_headers(client, "outsider@example.com")

    organization = client.post(
        "/api/v1/organizations",
        headers=owner,
        json={"name": "Project Team"},
    )
    assert organization.status_code == 201

    organization_id = organization.get_json()["data"]["id"]

    membership = client.post(
        f"/api/v1/organizations/{organization_id}/members",
        headers=owner,
        json={"email": "member@example.com"},
    )
    assert membership.status_code == 201

    return {
        "id": organization_id,
        "owner": owner,
        "member": member,
        "outsider": outsider,
    }


def create_test_project(client, team):
    response = client.post(
        f"/api/v1/organizations/{team['id']}/projects",
        headers=team["owner"],
        json={
            "name": "Backend API",
            "description": "Build the Shipyard API.",
        },
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def test_owner_can_create_project(client, team):
    project = create_test_project(client, team)

    assert project["name"] == "Backend API"
    assert project["organization_id"] == team["id"]


def test_member_can_list_and_view_projects(client, team):
    project = create_test_project(client, team)
    base = f"/api/v1/organizations/{team['id']}/projects"

    listing = client.get(base, headers=team["member"])
    detail = client.get(
        f"{base}/{project['id']}",
        headers=team["member"],
    )

    assert listing.status_code == 200
    assert listing.get_json()["data"][0]["id"] == project["id"]
    assert detail.status_code == 200


def test_member_cannot_create_project(client, team):
    base = f"/api/v1/organizations/{team['id']}/projects"

    response = client.post(
        base,
        headers=team["member"],
        json={"name": "Unauthorized project"},
    )

    assert response.status_code == 403

    listing = client.get(base, headers=team["owner"])
    assert listing.get_json()["data"] == []


def test_admin_can_create_project(client, team):
    admin = account_headers(client, "admin@example.com")

    added = client.post(
        f"/api/v1/organizations/{team['id']}/members",
        headers=team["owner"],
        json={"email": "admin@example.com", "role": "admin"},
    )
    assert added.status_code == 201

    response = client.post(
        f"/api/v1/organizations/{team['id']}/projects",
        headers=admin,
        json={"name": "Admin project"},
    )

    assert response.status_code == 201


def test_outsider_cannot_access_projects(client, team):
    project = create_test_project(client, team)
    base = f"/api/v1/organizations/{team['id']}/projects"

    assert client.get(
        base,
        headers=team["outsider"],
    ).status_code == 404

    assert client.get(
        f"{base}/{project['id']}",
        headers=team["outsider"],
    ).status_code == 404

    assert client.post(
        base,
        headers=team["outsider"],
        json={"name": "Unauthorized project"},
    ).status_code == 404


def test_project_cannot_be_read_under_wrong_organization(client, team):
    project = create_test_project(client, team)

    second = client.post(
        "/api/v1/organizations",
        headers=team["owner"],
        json={"name": "Second Team"},
    )
    assert second.status_code == 201
    second_id = second.get_json()["data"]["id"]

    response = client.get(
        f"/api/v1/organizations/{second_id}/projects/{project['id']}",
        headers=team["owner"],
    )

    assert response.status_code == 404


@pytest.mark.parametrize("name", ["", "   ", None, "x" * 101])
def test_invalid_project_names_are_rejected(client, team, name):
    response = client.post(
        f"/api/v1/organizations/{team['id']}/projects",
        headers=team["owner"],
        json={"name": name},
    )

    assert response.status_code == 400


def test_body_cannot_override_organization(client, team):
    response = client.post(
        f"/api/v1/organizations/{team['id']}/projects",
        headers=team["owner"],
        json={
            "name": "Correctly scoped",
            "organization_id": 999999,
        },
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["organization_id"] == team["id"]


def test_project_routes_require_authentication(client, team):
    project = create_test_project(client, team)
    base = f"/api/v1/organizations/{team['id']}/projects"

    assert client.get(base).status_code == 401
    assert client.post(base, json={"name": "No access"}).status_code == 401
    assert client.get(f"{base}/{project['id']}").status_code == 401