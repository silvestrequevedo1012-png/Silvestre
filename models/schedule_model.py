"""
models/schedule_model.py
CRUD operations for the schedules table.
"""

from models.database import get_connection


class ScheduleModel:

    @staticmethod
    def create_bulk(owner_id: str, owner_type: str, schedules: list[dict]):
        """Insert multiple schedule rows for one person."""
        sql = """
            INSERT INTO schedules (owner_id, owner_type, day, subject, start_time, end_time)
            VALUES (?, ?, ?, ?, ?, ?)
        """
        conn = get_connection()
        for s in schedules:
            if s.get("day") and s.get("subject") and s.get("start") and s.get("end"):
                conn.execute(sql, (
                    owner_id, owner_type,
                    s["day"], s["subject"], s["start"], s["end"],
                ))
        conn.commit()
        conn.close()

    @staticmethod
    def get_for(owner_id: str, owner_type: str) -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            """SELECT * FROM schedules
               WHERE owner_id=? AND owner_type=?
               ORDER BY day, start_time""",
            (owner_id, owner_type),
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def delete_for(owner_id: str, owner_type: str):
        conn = get_connection()
        conn.execute(
            "DELETE FROM schedules WHERE owner_id=? AND owner_type=?",
            (owner_id, owner_type),
        )
        conn.commit()
        conn.close()
