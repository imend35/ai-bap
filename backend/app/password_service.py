
"""I manage secure password hashing and verification for AI BAP."""

from pwdlib import PasswordHash


# I use Argon2id to protect user passwords.
password_hasher = PasswordHash.recommended()


def hash_password(password: str) -> str:
    """I securely hash a plaintext password before storing it."""
    return password_hasher.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    """I verify a plaintext password against its stored hash."""
    return password_hasher.verify(password, password_hash)
