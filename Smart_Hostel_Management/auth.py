import hashlib
import hmac
import secrets
from database import get_db

def _hash_password(password: str, salt: str) -> str:
    return hashlib.pbkdf2_hmac(
        "sha256", password.encode("utf-8"), bytes.fromhex(salt), 200_000
    ).hex()

def create_default_admin():
    with get_db() as conn:
        exists = conn.execute("SELECT user_id FROM users WHERE username='admin'").fetchone()
        if not exists:
            salt = secrets.token_hex(16)
            password_hash = _hash_password("admin123", salt)
            conn.execute(
                "INSERT INTO users(username,password_hash,salt,role) VALUES(?,?,?,'admin')",
                ("admin", password_hash, salt)
            )

def authenticate(username: str, password: str) -> bool:
    with get_db() as conn:
        user = conn.execute(
            "SELECT * FROM users WHERE username=?", (username.strip(),)
        ).fetchone()
    if not user:
        return False
    return hmac.compare_digest(
        user["password_hash"], _hash_password(password, user["salt"])
    )

def change_password(username: str, old_password: str, new_password: str) -> bool:
    if len(new_password) < 8:
        raise ValueError("New password must contain at least 8 characters.")
    with get_db() as conn:
        user = conn.execute("SELECT * FROM users WHERE username=?", (username,)).fetchone()
        if not user or not hmac.compare_digest(
            user["password_hash"], _hash_password(old_password, user["salt"])
        ):
            return False
        salt = secrets.token_hex(16)
        conn.execute(
            "UPDATE users SET password_hash=?, salt=? WHERE username=?",
            (_hash_password(new_password, salt), salt, username)
        )
    return True
