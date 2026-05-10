"""
controllers/register_controller.py
Handles student and faculty registration, including schedule insertion.
"""

from models import StudentModel, FacultyModel, ScheduleModel
from utils import generate_id


class RegisterController:

    @staticmethod
    def register_student(personal: dict, academic: dict,
                         guardian: dict, schedules: list[dict]) -> tuple[bool, str]:
        """
        Returns (success, id_number_or_error_message).
        """
        new_id = generate_id("STU")
        data = {
            "id_number":         new_id,
            "first_name":        personal["first_name"],
            "last_name":         personal["last_name"],
            "middle_name":       personal.get("middle_name", ""),
            "birthdate":         personal.get("birthdate", ""),
            "gender":            personal.get("gender", ""),
            "address":           personal.get("address", ""),
            "phone":             personal.get("phone", ""),
            "email":             personal.get("email", ""),
            "password":          personal["password"],
            "course":            academic.get("course", ""),
            "block":             academic.get("block", ""),
            "year_level":        academic.get("year_level", ""),
            "guardian_name":     guardian.get("guardian_name", ""),
            "guardian_relation": guardian.get("guardian_relation", ""),
            "guardian_phone":    guardian.get("guardian_phone", ""),
        }

        # Check email uniqueness across students and faculty
        if StudentModel.get_by_email(personal["email"]):
            return False, "This email is already registered as a Student."
        if FacultyModel.get_by_email(personal["email"]):
            return False, "This email is already registered as Faculty."

        ok = StudentModel.create(data)
        if not ok:
            return False, "Registration failed. ID may already exist."

        ScheduleModel.create_bulk(new_id, "student", schedules)
        return True, new_id

    @staticmethod
    def register_faculty(personal: dict, employment: dict,
                         schedules: list[dict]) -> tuple[bool, str]:
        new_id = generate_id("FAC")
        data = {
            "id_number":   new_id,
            "first_name":  personal["first_name"],
            "last_name":   personal["last_name"],
            "middle_name": personal.get("middle_name", ""),
            "birthdate":   personal.get("birthdate", ""),
            "gender":      personal.get("gender", ""),
            "address":     personal.get("address", ""),
            "phone":       personal.get("phone", ""),
            "email":       personal.get("email", ""),
            "password":    personal["password"],
            "department":  employment.get("department", ""),
            "position":    employment.get("position", ""),
        }

        # Check email uniqueness across students and faculty
        if StudentModel.get_by_email(personal["email"]):
            return False, "This email is already registered as a Student."
        if FacultyModel.get_by_email(personal["email"]):
            return False, "This email is already registered as Faculty."

        ok = FacultyModel.create(data)
        if not ok:
            return False, "Registration failed. ID may already exist."

        ScheduleModel.create_bulk(new_id, "faculty", schedules)
        return True, new_id