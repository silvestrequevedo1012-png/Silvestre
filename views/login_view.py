"""
views/login_view.py
Login page – users can log in with ID number OR email address.
"""

import flet as ft
from controllers import AuthController
from views.theme import *


def login_view(page: ft.Page, nav: dict):
    page.clean()
    page.bgcolor = SURFACE_ALT
    page.padding = 0
    page.scroll = None

    # ── State ─────────────────────────────────────────────────────────────────
    role_ref     = ft.Ref[ft.Dropdown]()
    identifier_f = text_field("ID Number or Email", "Enter your ID or email",
                               icon=ft.Icons.BADGE_OUTLINED)
    password_f   = text_field("Password", password=True, can_reveal=True,
                               icon=ft.Icons.LOCK_OUTLINE)
    error_txt    = ft.Text("", color=ERROR_COLOR, size=13, visible=False)
    loading      = ft.ProgressRing(width=20, height=20, stroke_width=2,
                                    color=SURFACE, visible=False)

    roles = ["Student", "Faculty", "Admin"]
    role_dd = ft.Dropdown(
        ref=role_ref,
        value="Student",
        options=[ft.dropdown.Option(r) for r in roles],
        border_radius=10,
        border_color=BORDER,
        focused_border_color=PRIMARY_LIGHT,
        filled=True,
        fill_color=SURFACE_ALT,
        text_style=ft.TextStyle(color=TEXT_DARK, size=14),
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=4),
    )

    def do_login(e):
        identifier = identifier_f.value.strip()
        password   = password_f.value.strip()
        role       = role_ref.current.value

        if not identifier or not password:
            error_txt.value = "Please fill in all fields."
            error_txt.visible = True
            page.update()
            return

        error_txt.visible = False
        loading.visible   = True
        page.update()

        # For admin, try username. For others, try id_number first, then email.
        user = None
        role_key = None

        if role == "Admin":
            from models import AdminModel
            user = AdminModel.authenticate(identifier, password)
            if user:
                role_key = "admin"
        else:
            from models import StudentModel, FacultyModel
            if role == "Student":
                # Try ID number
                user = StudentModel.authenticate(identifier, password)
                if not user:
                    # Try email
                    from models.database import get_connection
                    with get_connection() as conn:
                        row = conn.execute(
                            "SELECT * FROM students WHERE email=? AND password=?",
                            (identifier, password)
                        ).fetchone()
                        user = dict(row) if row else None
                if user:
                    role_key = "student"
            else:
                user = FacultyModel.authenticate(identifier, password)
                if not user:
                    from models.database import get_connection
                    with get_connection() as conn:
                        row = conn.execute(
                            "SELECT * FROM faculty WHERE email=? AND password=?",
                            (identifier, password)
                        ).fetchone()
                        user = dict(row) if row else None
                if user:
                    role_key = "faculty"

        loading.visible = False

        if not user or not role_key:
            error_txt.value = "Invalid credentials. Please try again."
            error_txt.visible = True
            page.update()
            return

        page.update()
        nav[role_key](user)

    identifier_f.on_submit = do_login
    password_f.on_submit   = do_login

    # ── Left decorative panel ─────────────────────────────────────────────────
    left_panel = ft.Container(
        content=ft.Column([
            ft.Container(height=60),
            ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=72, color=ACCENT),
            ft.Container(height=16),
            ft.Text("Campus SIS", size=32, weight=ft.FontWeight.BOLD,
                    color=ft.Colors.WHITE),
            ft.Text("Student Information System", size=16,
                    color=ft.Colors.with_opacity(0.75, ft.Colors.WHITE)),
            ft.Container(height=40),
            ft.Container(
                content=ft.Column([
                    _feature_item(ft.Icons.FINGERPRINT, "Secure Access Control"),
                    _feature_item(ft.Icons.SCHEDULE,    "Schedule Management"),
                    _feature_item(ft.Icons.ANALYTICS,   "Attendance Analytics"),
                    _feature_item(ft.Icons.BADGE,       "Digital ID System"),
                ], spacing=18),
            ),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
        bgcolor=PRIMARY,
        expand=True,
        padding=ft.Padding.symmetric(horizontal=40, vertical=40),
        alignment=ft.Alignment(0, 0),
    )

    # ── Right login form ──────────────────────────────────────────────────────
    right_panel = ft.Container(
        content=ft.Column([
            ft.Container(height=20),
            ft.Column([
                heading("Welcome Back", size=26),
                subheading("Sign in with your ID number or email", size=14),
            ], spacing=4),
            ft.Container(height=28),
            ft.Text("Sign in as", size=13, color=TEXT_MUTED,
                    weight=ft.FontWeight.W_500),
            ft.Container(height=6),
            role_dd,
            ft.Container(height=16),
            identifier_f,
            ft.Container(height=12),
            password_f,
            ft.Container(height=6),
            error_txt,
            ft.Container(height=20),
            ft.ElevatedButton(
                content=ft.Row([
                    ft.Text("Sign In", size=15, weight=ft.FontWeight.W_600,
                            color=ft.Colors.WHITE),
                    loading,
                ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                on_click=do_login,
                width=340,
                style=ft.ButtonStyle(
                    bgcolor=PRIMARY,
                    shape=ft.RoundedRectangleBorder(radius=12),
                    padding=ft.Padding.symmetric(vertical=16),
                    elevation=3,
                    overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
                ),
            ),
            ft.Container(height=20),
            ft.Row([
                ft.Text("Don't have an account?", size=13, color=TEXT_MUTED),
                ft.TextButton(
                    "Register here",
                    on_click=lambda _: nav["register"](),
                    style=ft.ButtonStyle(
                        color=PRIMARY_LIGHT,
                        padding=ft.Padding.only(left=4),
                    ),
                ),
            ], alignment=ft.MainAxisAlignment.CENTER),
            ft.Container(height=16),
            ft.TextButton(
                "Scanner / Entry Terminal",
                icon=ft.Icons.QR_CODE_SCANNER,
                on_click=lambda _: nav["scanner"](),
                style=ft.ButtonStyle(color=TEXT_MUTED),
            ),
        ],
        horizontal_alignment=ft.CrossAxisAlignment.CENTER,
        scroll=ft.ScrollMode.AUTO,
        spacing=0,
        ),
        expand=True,
        bgcolor=SURFACE,
        padding=ft.Padding.symmetric(horizontal=48, vertical=40),
        alignment=ft.Alignment(0, 0),
    )

    page.add(
        ft.Row([left_panel, right_panel], expand=True, spacing=0)
    )


def _feature_item(icon, text: str) -> ft.Row:
    return ft.Row([
        ft.Container(
            content=ft.Icon(icon, size=18, color=ACCENT),
            width=36, height=36,
            border_radius=10,
            bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
            alignment=ft.Alignment(0, 0),
        ),
        ft.Text(text, size=14, color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE)),
    ], spacing=14)
