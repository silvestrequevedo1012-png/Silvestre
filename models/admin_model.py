"""
models/admin_model.py
CRUD operations for the admins table.
"""

from models.database import get_connection


class AdminModel:

    @staticmethod
    def authenticate(username: str, password: str) -> dict | None:
        with get_connection() as conn:
            row = conn.execute(
                "SELECT * FROM admins WHERE username=? AND password=?",
                (username, password),
            ).fetchone()
        return dict(row) if row else None
