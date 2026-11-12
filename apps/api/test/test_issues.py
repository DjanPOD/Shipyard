import pytest


def register_headers(client, email):
    password = "Shipyard issue password!"

    response = client.post(
        "/api/v1/auth/register",
        json={
            "email": email,
            "display_name": "Test User",
            "password": password,
        },
    )
    assert response.status_code == 201

    response = client.post(
        "/api/v1/auth/login",
        json={"email": email, "password": password},
    )
    assert response.status_code == 200

    token = response.get_json()["data"]["access_token"]
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture()
def workspace(client):
    owner = register_headers(client, "owner@example.com")
    member = register_headers(client, "member@example.com")
    outsider = register_headers(client, "outsider@example.com")

    organization = client.post(
        "/api/v1/organizations",
        headers=owner,
        json={"name": "Issue Team"},
    )
    assert organization.status_code == 201
    organization_id = organization.get_json()["data"]["id"]

    added = client.post(
        f"/api/v1/organizations/{organization_id}/members",
        headers=owner,
        json={"email": "member@example.com", "role": "member"},
    )
    assert added.status_code == 201

    project = client.post(
        f"/api/v1/organizations/{organization_id}/projects",
        headers=owner,
        json={"name": "Backend API"},
    )
    assert project.status_code == 201
    project_id = project.get_json()["data"]["id"]

    return {
        "owner": owner,
        "member": member,
        "outsider": outsider,
        "organization_id": organization_id,
        "project_id": project_id,
        "base": (
            f"/api/v1/organizations/{organization_id}"
            f"/projects/{project_id}/issues"
        ),
    }


def make_issue(client, workspace):
    response = client.post(
        workspace["base"],
        headers=workspace["owner"],
        json={"title": "Implement issue tracking"},
    )
    assert response.status_code == 201
    return response.get_json()["data"]


def test_member_can_create_list_view_and_update_issue(client, workspace):
    headers = workspace["member"]

    created = client.post(
        workspace["base"],
        headers=headers,
        json={"title": "  Fix login  "},
    )
    assert created.status_code == 201

    issue = created.get_json()["data"]
    assert issue["title"] == "Fix login"
    assert issue["status"] == "backlog"
    assert issue["priority"] == "medium"
    assert issue["description"] == ""

    url = f"{workspace['base']}/{issue['id']}"

    listing = client.get(workspace["base"], headers=headers)
    assert listing.status_code == 200
    assert listing.get_json()["data"][0]["id"] == issue["id"]

    detail = client.get(url, headers=headers)
    assert detail.status_code == 200

    updated = client.patch(
        url,
        headers=headers,
        json={"status": "in_progress", "priority": "high"},
    )
    assert updated.status_code == 200

    data = updated.get_json()["data"]
    assert data["status"] == "in_progress"
    assert data["priority"] == "high"
    assert data["title"] == "Fix login"

    persisted = client.get(url, headers=headers).get_json()["data"]
    assert persisted["status"] == "in_progress"


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"title": ""},
        {"title": "   "},
        {"title": None},
        {"title": "x" * 201},
        {"title": "Valid", "description": None},
        {"title": "Valid", "description": "x" * 10001},
        {"title": "Valid", "status": "invalid"},
        {"title": "Valid", "status": []},
        {"title": "Valid", "priority": None},
        {"title": "Valid", "project_id": 999},
    ],
)
def test_invalid_creation_is_rejected(client, workspace, payload):
    response = client.post(
        workspace["base"],
        headers=workspace["owner"],
        json=payload,
    )

    assert response.status_code == 400

    listing = client.get(
        workspace["base"],
        headers=workspace["owner"],
    )
    assert listing.get_json()["data"] == []


@pytest.mark.parametrize(
    "payload",
    [
        {},
        {"status": None},
        {"priority": ["high"]},
        {"project_id": 999},
        {"title": "Changed", "priority": "invalid"},
    ],
)
def test_invalid_update_does_not_change_issue(client, workspace, payload):
    issue = make_issue(client, workspace)
    url = f"{workspace['base']}/{issue['id']}"

    response = client.patch(
        url,
        headers=workspace["owner"],
        json=payload,
    )
    assert response.status_code == 400

    persisted = client.get(
        url,
        headers=workspace["owner"],
    ).get_json()["data"]

    assert persisted["title"] == issue["title"]
    assert persisted["priority"] == issue["priority"]
    assert persisted["status"] == issue["status"]


def test_outsider_cannot_access_any_issue_endpoint(client, workspace):
    issue = make_issue(client, workspace)
    base = workspace["base"]
    url = f"{base}/{issue['id']}"
    headers = workspace["outsider"]

    assert client.get(base, headers=headers).status_code == 404
    assert client.get(url, headers=headers).status_code == 404

    assert client.post(
        base,
        headers=headers,
        json={"title": "Unauthorized"},
    ).status_code == 404

    assert client.patch(
        url,
        headers=headers,
        json={"status": "done"},
    ).status_code == 404

    persisted = client.get(
        url,
        headers=workspace["owner"],
    ).get_json()["data"]

    assert persisted["status"] == "backlog"


def test_issue_cannot_be_accessed_under_another_project(client, workspace):
    issue = make_issue(client, workspace)
    organization_id = workspace["organization_id"]
    headers = workspace["owner"]

    second = client.post(
        f"/api/v1/organizations/{organization_id}/projects",
        headers=headers,
        json={"name": "Second project"},
    )
    assert second.status_code == 201
    second_id = second.get_json()["data"]["id"]

    url = (
        f"/api/v1/organizations/{organization_id}"
        f"/projects/{second_id}/issues/{issue['id']}"
    )

    assert client.get(url, headers=headers).status_code == 404

    assert client.patch(
        url,
        headers=headers,
        json={"status": "done"},
    ).status_code == 404


def test_project_cannot_be_accessed_under_another_organization(
    client,
    workspace,
):
    issue = make_issue(client, workspace)
    headers = workspace["owner"]

    second = client.post(
        "/api/v1/organizations",
        headers=headers,
        json={"name": "Second organization"},
    )
    assert second.status_code == 201
    second_id = second.get_json()["data"]["id"]

    base = (
        f"/api/v1/organizations/{second_id}"
        f"/projects/{workspace['project_id']}/issues"
    )
    url = f"{base}/{issue['id']}"

    assert client.get(base, headers=headers).status_code == 404
    assert client.get(url, headers=headers).status_code == 404

    assert client.post(
        base,
        headers=headers,
        json={"title": "Wrong scope"},
    ).status_code == 404

    assert client.patch(
        url,
        headers=headers,
        json={"status": "done"},
    ).status_code == 404


def test_issue_endpoints_require_authentication(client, workspace):
    issue = make_issue(client, workspace)
    base = workspace["base"]
    url = f"{base}/{issue['id']}"

    assert client.get(base).status_code == 401
    assert client.get(url).status_code == 401

    assert client.post(
        base,
        json={"title": "Unauthorized"},
    ).status_code == 401

    assert client.patch(
        url,
        json={"status": "done"},
    ).status_code == 401


@pytest.mark.parametrize("method", ["post", "patch"])
@pytest.mark.parametrize("body", [None, [], "invalid"])
def test_non_object_json_is_rejected(client, workspace, method, body):
    issue = make_issue(client, workspace)

    url = workspace["base"]
    if method == "patch":
        url += f"/{issue['id']}"

    import json

    response = getattr(client, method)(
        url,
        headers=workspace["owner"],
        data=json.dumps(body),
        content_type="application/json",
    )

    assert response.status_code == 400