"""
models/faculty_model.py
CRUD operations for the faculty table.
"""

from models.database import get_connection


class FacultyModel:

    @staticmethod
    def create(data: dict) -> bool:
        sql = """
            INSERT INTO faculty
                (id_number, first_name, last_name, middle_name, birthdate,
                 gender, address, phone, email, password,
                 department, position)
            VALUES
                (:id_number, :first_name, :last_name, :middle_name, :birthdate,
                 :gender, :address, :phone, :email, :password,
                 :department, :position)
        """
        try:
            conn = get_connection()
            conn.execute(sql, data)
            conn.commit()
            conn.close()
            return True
        except Exception as e:
            print(f"[FacultyModel.create] ERROR: {e}")
            return False

    @staticmethod
    def authenticate(id_number: str, password: str) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM faculty WHERE id_number=? AND password=?",
            (id_number, password),
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_id(id_number: str) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM faculty WHERE id_number=?", (id_number,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_by_email(email: str) -> dict | None:
        conn = get_connection()
        row = conn.execute(
            "SELECT * FROM faculty WHERE LOWER(email)=LOWER(?)", (email,)
        ).fetchone()
        conn.close()
        return dict(row) if row else None

    @staticmethod
    def get_all() -> list[dict]:
        conn = get_connection()
        rows = conn.execute(
            "SELECT * FROM faculty ORDER BY last_name, first_name"
        ).fetchall()
        conn.close()
        return [dict(r) for r in rows]

    @staticmethod
    def set_logged_in(id_number: str, value: bool):
        conn = get_connection()
        conn.execute(
            "UPDATE faculty SET logged_in=? WHERE id_number=?",
            (1 if value else 0, id_number),
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update(id_number: str, data: dict):
        fields = ", ".join(f"{k}=:{k}" for k in data if k != "id_number")
        data["id_number"] = id_number
        conn = get_connection()
        conn.execute(
            f"UPDATE faculty SET {fields} WHERE id_number=:id_number", data
        )
        conn.commit()
        conn.close()

    @staticmethod
    def update_photo(id_number: str, photo: str):
        conn = get_connection()
        conn.execute(
            "UPDATE faculty SET photo=? WHERE id_number=?", (photo, id_number)
        )
        conn.commit()
        conn.close()

    @staticmethod
    def delete(id_number: str):
        conn = get_connection()
        conn.execute(
            "DELETE FROM schedules WHERE owner_id=? AND owner_type='faculty'",
            (id_number,),
        )
        conn.execute(
            "DELETE FROM faculty WHERE id_number=?", (id_number,)
        )
        conn.commit()
        conn.close()
