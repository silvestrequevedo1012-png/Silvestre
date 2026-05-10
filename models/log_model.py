"""
models/log_model.py
CRUD operations for the logs table.
"""

from models.database import get_connection


class LogModel:

    @staticmethod
    def create(data: dict):
        sql = """
            INSERT INTO logs (timestamp, id_number, full_name, role, action, status, subject)
            VALUES (:timestamp, :id_number, :full_name, :role, :action, :status, :subject)
        """
        conn = get_connection()
        conn.execute(sql, data)
        conn.commit()
        conn.close()

    @staticmethod
    def get_all() -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM logs ORDER BY id DESC"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def get_by_id_number(id_number: str) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM logs WHERE id_number=? ORDER BY id DESC",
            (id_number,),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]
