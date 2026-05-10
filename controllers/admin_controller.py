"""
controllers/admin_controller.py
Admin-facing operations: view logs, list/remove students & faculty.
"""

from models import StudentModel, FacultyModel, LogModel, ScheduleModel


class AdminController:

    # ── Logs ──────────────────────────────────────────────────────────────────
    @staticmethod
    def get_all_logs() -> list[dict]:
        return LogModel.get_all()

    # ── Students ──────────────────────────────────────────────────────────────
    @staticmethod
    def get_all_students() -> list[dict]:
        students = StudentModel.get_all()
        for s in students:
            s["schedules"] = ScheduleModel.get_for(s["id_number"], "student")
        return students

    @staticmethod
    def remove_student(id_number: str):
        StudentModel.delete(id_number)

    # ── Faculty ───────────────────────────────────────────────────────────────
    @staticmethod
    def get_all_faculty() -> list[dict]:
        faculty = FacultyModel.get_all()
        for f in faculty:
            f["schedules"] = ScheduleModel.get_for(f["id_number"], "faculty")
        return faculty

    @staticmethod
    def remove_faculty(id_number: str):
        FacultyModel.delete(id_number)
