import pytest


def register_account(client, email):
    password = "Shipyard membership password!"

    registration = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": email.split("@")[0],
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


@pytest.fixture()
def team(client):
    owner_headers = register_account(client, "owner@example.com")
    member_headers = register_account(client, "member@example.com")
    outsider_headers = register_account(client, "outsider@example.com")

    response = client.post(
        "/api/v1/organizations",
        headers=owner_headers,
        json={"name": "Membership Test Team"},
    )
    assert response.status_code == 201

    return {
        "id": response.get_json()["data"]["id"],
        "owner": owner_headers,
        "member": member_headers,
        "outsider": outsider_headers,
    }


def add_test_member(client, team, role="member"):
    return client.post(
        f"/api/v1/organizations/{team['id']}/members",
        headers=team["owner"],
        json={
            "email": "member@example.com",
            "role": role,
        },
    )


def test_owner_can_add_existing_user(client, team):
    response = add_test_member(client, team)

    assert response.status_code == 201
    assert response.get_json()["data"]["email"] == "member@example.com"
    assert response.get_json()["data"]["role"] == "member"

    # Membership grants access to the organization itself.
    detail = client.get(
        f"/api/v1/organizations/{team['id']}",
        headers=team["member"],
    )

    assert detail.status_code == 200
    assert detail.get_json()["data"]["role"] == "member"


def test_member_can_view_team_members(client, team):
    assert add_test_member(client, team).status_code == 201

    response = client.get(
        f"/api/v1/organizations/{team['id']}/members",
        headers=team["member"],
    )

    assert response.status_code == 200

    emails = {
        item["email"]
        for item in response.get_json()["data"]
    }

    assert emails == {"owner@example.com", "member@example.com"}


@pytest.mark.parametrize("role", ["member", "admin"])
def test_nonowner_cannot_add_members(client, team, role):
    assert add_test_member(client, team, role).status_code == 201

    response = client.post(
        f"/api/v1/organizations/{team['id']}/members",
        headers=team["member"],
        json={"email": "outsider@example.com"},
    )

    assert response.status_code == 403

    # A denied request must not create the membership.
    detail = client.get(
        f"/api/v1/organizations/{team['id']}",
        headers=team["outsider"],
    )
    assert detail.status_code == 404


def test_outsider_cannot_read_or_modify_members(client, team):
    path = f"/api/v1/organizations/{team['id']}/members"

    assert client.get(
        path,
        headers=team["outsider"],
    ).status_code == 404

    assert client.post(
        path,
        headers=team["outsider"],
        json={"email": "outsider@example.com"},
    ).status_code == 404


def test_duplicate_add_does_not_change_role(client, team):
    assert add_test_member(client, team).status_code == 201

    duplicate = add_test_member(client, team, role="admin")
    assert duplicate.status_code == 409

    detail = client.get(
        f"/api/v1/organizations/{team['id']}",
        headers=team["member"],
    )

    assert detail.get_json()["data"]["role"] == "member"


@pytest.mark.parametrize("role", ["owner", "super-admin", None, []])
def test_invalid_roles_are_rejected(client, team, role):
    response = add_test_member(client, team, role)

    assert response.status_code == 400


def test_unknown_email_is_rejected(client, team):
    response = client.post(
        f"/api/v1/organizations/{team['id']}/members",
        headers=team["owner"],
        json={"email": "missing@example.com"},
    )

    assert response.status_code == 404
    assert response.get_json()["error"]["code"] == "USER_NOT_FOUND"


def test_member_routes_require_authentication(client, team):
    path = f"/api/v1/organizations/{team['id']}/members"

    assert client.get(path).status_code == 401

    assert client.post(
        path,
        json={"email": "member@example.com"},
    ).status_code == 401