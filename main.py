"""
main.py
Entry point — initialises the database and wires all MVC layers together.
"""

import sys
import os

# ── Pin the DB to sit next to main.py, regardless of launch directory ─────────
_HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, _HERE)

# Set DB path BEFORE any model imports so every module sees the same file
os.environ["SIS_DB_PATH"] = os.path.join(_HERE, "sis.db")

import flet as ft

from models import init_db
from models.database import migrate_db
from views import (
    login_view, register_view, scanner_view,
    student_view, faculty_view, admin_view,
)


def main(page: ft.Page):
    page.title         = "Campus SIS"
    page.theme_mode    = ft.ThemeMode.LIGHT
    page.window_width  = 1100
    page.window_height = 740
    page.padding       = 0

    nav: dict = {}

    nav["login"]    = lambda:      login_view(page, nav)
    nav["register"] = lambda:      register_view(page, nav)
    nav["scanner"]  = lambda:      scanner_view(page, nav)
    nav["admin"]    = lambda user: admin_view(page, user, nav)
    nav["student"]  = lambda user: student_view(page, user, nav)
    nav["faculty"]  = lambda user: faculty_view(page, user, nav)

    nav["login"]()


if __name__ == "__main__":
    init_db()
    migrate_db()
    ft.run(main)
