def test_list_users_returns_empty_list_inititially(client):
    response = client.get("/api/v1/users")

    assert response.status_code == 200
    assert response.get_json() == {"data": []}

def test_create_user_returns_created_user(client):
    response = client.post(
            "/api/v1/users",
            json={
                "email": "peter@example.com",
                "displayName": "Peter",
            },
        )

    body = response.get_json()

    assert response.status_code == 201
    assert body["data"]["id"] == 1
    assert body["data"]["email"] == "peter@example.com" 
    assert body["data"]["display_name"] == "Peter"
    assert body["data"]["created_at"] is not None
    assert body["data"]["updated"] is not None

def test_create_user_normalizes_email(client):
    response = client.post(
        "/api/v1/users",
        json={
            "email": "  PETER@EXAMPLE.COM  ",
            "displayName": "Peter",
        },
    )

    assert response.status_code == 201
    assert response.get_json()["data"]["email"] == "peter@example.com"


def test_create_user_rejects_duplicate_email(client):
    payload = {
        "email": "peter@example.com",
        "displayName": "Peter",
    }

    first_response = client.post("/api/v1/users", json=payload)
    second_response = client.post("/api/v1/users", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.get_json()["error"]["code"] == "CONFLICT"


def test_create_user_requires_email(client):
    response = client.post(
        "/api/v1/users",
        json={
            "displayName": "Peter",
        },
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "VALIDATION_ERROR"


def test_create_user_requires_json_object(client):
    response = client.post(
        "/api/v1/users",
        data="this is not JSON",
        content_type="text/plain",
    )

    assert response.status_code == 400
    assert response.get_json()["error"]["code"] == "INVALID_JSON"