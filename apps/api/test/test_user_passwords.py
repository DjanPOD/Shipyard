import pytest

from app.models.user import User


def make_user() -> User:
    """Build an unsaved user for password-method tests."""

    return User(
        email="peter@example.com",
        display_name="Peter",
    )


def test_password_is_stored_as_hash():
    user = make_user()
    password = "Shipyard learning password!"

    user.set_password(password)

    assert user.password_hash is not None
    assert user.password_hash != password
    assert user.check_password(password) is True


def test_wrong_password_is_rejected():
    user = make_user()
    user.set_password("Shipyard learning password!")

    assert user.check_password("A different password!") is False


def test_user_without_password_cannot_authenticate():
    user = make_user()

    assert user.check_password("Shipyard learning password!") is False


@pytest.mark.parametrize(
    "password",
    [
        "",
        "too-short",
        "x" * 129,
        None,
    ],
)
def test_invalid_password_is_rejected(password):
    user = make_user()

    with pytest.raises(ValueError):
        user.set_password(password)


def test_password_hash_is_not_in_public_user_data():
    user = make_user()
    user.set_password("Shipyard learning password!")

    data = user.to_dict()

    assert "password" not in data
    assert "password_hash" not in data
    assert user.password_hash not in data.values()