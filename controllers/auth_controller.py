"""
controllers/auth_controller.py
Handles authentication for Admin, Student, and Faculty.
"""

from models import AdminModel, StudentModel, FacultyModel


class AuthController:

    @staticmethod
    def login(role: str, identifier: str, password: str) -> tuple[str | None, dict | None]:
        """
        Returns (role_string, user_dict) on success, or (None, None) on failure.
        role: 'Admin' | 'Student' | 'Faculty'
        """
        if role == "Admin":
            user = AdminModel.authenticate(identifier, password)
            if user:
                return "admin", user

        elif role == "Student":
            user = StudentModel.authenticate(identifier, password)
            if user:
                return "student", user

        elif role == "Faculty":
            user = FacultyModel.authenticate(identifier, password)
            if user:
                return "faculty", user

        return None, None
