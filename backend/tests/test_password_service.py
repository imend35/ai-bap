
"""I test secure password hashing and verification for AI BAP."""

from app.password_service import hash_password, verify_password


def test_password_hash_is_not_plaintext():
    """I verify that passwords are never stored as plaintext."""
    password = "TestPassword123!"

    password_hash = hash_password(password)

    assert password_hash != password
    assert password_hash.startswith("$argon2id$")


def test_correct_password_is_verified():
    """I verify that the correct password matches its stored hash."""
    password = "TestPassword123!"

    password_hash = hash_password(password)

    assert verify_password(password, password_hash) is True


def test_incorrect_password_is_rejected():
    """I verify that an incorrect password is rejected."""
    password_hash = hash_password("TestPassword123!")

    assert verify_password("WrongPassword123!", password_hash) is False


def test_same_password_generates_different_hashes():
    """I verify that password hashing uses a unique random salt."""
    password = "TestPassword123!"

    first_hash = hash_password(password)
    second_hash = hash_password(password)

    assert first_hash != second_hash
    assert verify_password(password, first_hash) is True
    assert verify_password(password, second_hash) is True
