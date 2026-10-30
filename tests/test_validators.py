import pytest

from app.validators import (ValidationError, validate_difficulty, validate_email,
                            validate_int, validate_limit, validate_password,
                            validate_username)


@pytest.mark.parametrize("name", ["abc", "Snake_Master", "a" * 20, "user123"])
def test_valid_usernames(name):
    assert validate_username(name) == name


@pytest.mark.parametrize("name", ["ab", "a" * 21, "bad name", "bad-name", "", None, 5, "<script>"])
def test_invalid_usernames(name):
    with pytest.raises(ValidationError):
        validate_username(name)


def test_username_is_stripped():
    assert validate_username("  bob  ") == "bob"


def test_email_normalised():
    assert validate_email("  Bob@Example.COM ") == "bob@example.com"


@pytest.mark.parametrize("email", ["nope", "a@b", "@x.com", "a@.com", "", None, "a b@c.com"])
def test_invalid_emails(email):
    with pytest.raises(ValidationError):
        validate_email(email)


def test_valid_password():
    assert validate_password("Password1") == "Password1"


@pytest.mark.parametrize("pw", ["short1A", "alllowercase1", "ALLUPPERCASE1",
                                "NoDigitsHere", "A1a" + "x" * 80, None, 12345678])
def test_invalid_passwords(pw):
    with pytest.raises(ValidationError):
        validate_password(pw)


def test_validate_int_bounds_and_types():
    assert validate_int(5, "x", 0, 10) == 5
    for bad in (-1, 11, "5", 1.5, True, None):
        with pytest.raises(ValidationError):
            validate_int(bad, "x", 0, 10)


def test_difficulty():
    assert validate_difficulty(" HARD ") == "hard"
    with pytest.raises(ValidationError):
        validate_difficulty("insane")


def test_limit():
    assert validate_limit(None) == 10
    assert validate_limit("5") == 5
    for bad in ("0", "101", "abc"):
        with pytest.raises(ValidationError):
            validate_limit(bad)
