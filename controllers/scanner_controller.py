"""
controllers/scanner_controller.py
Handles campus entry and exit logic with schedule validation and late-marking.
Everyone is allowed entry regardless of schedule.
- If they have an active schedule now: ON TIME or LATE, shows subject
- If schedule exists today but outside window: PRESENT, shows "No Active Class Right Now"
- If no schedule today at all: PRESENT, shows "No Schedule Today"
Exit is always allowed for anyone currently logged in.
"""

from models import StudentModel, FacultyModel, ScheduleModel, LogModel
from utils import check_schedule, is_late, now_str
import datetime as _dt


class ScannerController:

    @staticmethod
    def scan(id_number: str) -> dict:
        # Identify user
        person = StudentModel.get_by_id(id_number)
        role   = "student"
        if not person:
            person = FacultyModel.get_by_id(id_number)
            role   = "faculty"

        if not person:
            return {"success": False, "action": None,
                    "status": "ERROR", "message": "ID not found.", "subject": "",
                    "name": "", "role": "", "time": ""}

        full_name = f"{person['first_name']} {person['last_name']}"
        ts        = now_str()

        # ── EXIT flow ────────────────────────────────────────────────────────
        if person["logged_in"]:
            if role == "student":
                StudentModel.set_logged_in(id_number, False)
            else:
                FacultyModel.set_logged_in(id_number, False)

            LogModel.create({
                "timestamp": ts,
                "id_number": id_number,
                "full_name": full_name,
                "role":      role,
                "action":    "EXIT",
                "status":    "OK",
                "subject":   "",
            })
            return {
                "success": True, "action": "EXIT", "status": "OK",
                "message": f"EXIT recorded — {ts}", "subject": "",
                "name": full_name, "role": role, "time": ts,
            }

        # ── ENTRY flow — always allowed ───────────────────────────────────────
        if role == "student":
            StudentModel.set_logged_in(id_number, True)
        else:
            FacultyModel.set_logged_in(id_number, True)

        schedules = ScheduleModel.get_for(id_number, role)
        has, sched_start, sched, denial_reason = check_schedule(schedules)

        if has:
            late    = is_late(sched_start)
            status  = "LATE" if late else "ON TIME"
            subject = sched.get("subject", "")
        else:
            status  = "PRESENT"
            if denial_reason == "NO_SCHEDULE_TODAY":
                subject = "No Schedule Today"
            else:
                subject = "No Active Class Right Now"

        LogModel.create({
            "timestamp": ts,
            "id_number": id_number,
            "full_name": full_name,
            "role":      role,
            "action":    "ENTRY",
            "status":    status,
            "subject":   subject,
        })

        return {
            "success": True, "action": "ENTRY", "status": status,
            "message": f"ENTRY recorded — {ts}", "subject": subject,
            "name": full_name, "role": role, "time": ts,
        }
