"""
views/faculty_view.py
Faculty dashboard with schedule, logs, profile and photo editing.
"""

import os, shutil
import flet as ft
from models import FacultyModel, ScheduleModel, LogModel
from views.theme import *
from views.student_view import _sched_item, _log_row, _info_tile, _photo_widget

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


def faculty_view(page: ft.Page, user: dict, nav: dict, active_tab: int = 0):
    page.clean()
    page.bgcolor = SURFACE_ALT
    page.padding = 0
    page.scroll  = None

    user = FacultyModel.get_by_id(user["id_number"]) or user

    def go_tab(idx):
        faculty_view(page, user, nav, active_tab=idx)

    avatar = avatar_circle(user.get("photo"), size=72)

    nav_items = [
        (ft.Icons.DASHBOARD_OUTLINED, "Dashboard",  0),
        (ft.Icons.CALENDAR_MONTH,     "My Schedule", 1),
        (ft.Icons.HISTORY,            "Attendance",  2),
        (ft.Icons.PERSON_OUTLINED,    "Profile",     3),
    ]

    sidebar = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    avatar,
                    ft.Container(height=10),
                    ft.Text(f"{user['first_name']} {user['last_name']}",
                            size=14, weight=ft.FontWeight.W_600,
                            color=ft.Colors.WHITE, text_align=ft.TextAlign.CENTER),
                    ft.Text(user.get("id_number", ""), size=11,
                            color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE),
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Text("Faculty", size=11, color=ACCENT_LIGHT,
                                        weight=ft.FontWeight.W_600),
                        bgcolor=ft.Colors.with_opacity(0.15, ACCENT),
                        border_radius=20, padding=ft.Padding.symmetric(horizontal=12, vertical=4),
                    ),
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                padding=ft.Padding.symmetric(vertical=24),
                border=ft.Border(bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE))),
            ),
            ft.Container(height=8),
            *[sidebar_item(icon, label, on_click=lambda _, i=idx: go_tab(i),
                           active=(active_tab == idx))
              for icon, label, idx in nav_items],
            ft.Container(expand=True),
            ft.Divider(color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
            sidebar_item(ft.Icons.LOGOUT, "Sign Out",
                         on_click=lambda _: _logout()),
            ft.Container(height=12),
        ], spacing=4, expand=True),
        bgcolor=SIDEBAR_BG,
        width=220,
        padding=ft.Padding.symmetric(horizontal=12, vertical=12),
    )

    def _logout():
        FacultyModel.set_logged_in(user["id_number"], False)
        nav["login"]()

    topbar_titles = ["Dashboard", "My Schedule", "Attendance Log", "My Profile"]
    topbar = ft.Container(
        content=ft.Row([
            heading(topbar_titles[active_tab], size=20),
            ft.Text(f"📅 {__import__('datetime').datetime.now().strftime('%B %d, %Y')}",
                    size=13, color=TEXT_MUTED),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
           vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE, padding=ft.Padding.symmetric(horizontal=24, vertical=16),
        shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                             offset=ft.Offset(0, 2)),
    )

    # In Flet 0.85+, FilePicker is a Service — it self-registers with the page.
    # Do NOT add it to page.overlay; doing so causes "Unknown control: FilePicker".
    file_picker = ft.FilePicker()

    tabs = [
        _dashboard(user),
        _schedule(user),
        _attendance(user),
        _profile(page, user, nav, file_picker),
    ]

    content_area = ft.Container(
        content=ft.Column([
            topbar,
            ft.Container(content=tabs[active_tab], expand=True, padding=24),
        ], expand=True, spacing=0),
        expand=True,
        bgcolor=SURFACE_ALT,
    )

    page.add(ft.Row([sidebar, content_area], expand=True, spacing=0))


def _dashboard(user: dict) -> ft.Control:
    schedules = ScheduleModel.get_for(user["id_number"], "faculty")
    logs = LogModel.get_by_id_number(user["id_number"])
    entries = [l for l in logs if l["action"] == "ENTRY"]
    late    = [l for l in entries if l["status"] == "LATE"]

    import datetime
    today = datetime.datetime.now().strftime("%A")
    today_scheds = [s for s in schedules if s.get("day","").lower() == today.lower()]

    return ft.Column([
        ft.Row([
            ft.Column([
                heading(f"Hello, {user.get('position','Prof.')} {user['last_name']}! 👋", size=20),
                subheading(f"ID: {user['id_number']} • {user.get('department','')} Department"),
            ], spacing=4, expand=True),
            ft.Container(
                content=ft.Text(
                    "✅ Active" if user.get("logged_in") else "🔴 Offline",
                    size=13, weight=ft.FontWeight.W_600,
                    color=SUCCESS if user.get("logged_in") else TEXT_MUTED,
                ),
                bgcolor=ft.Colors.with_opacity(0.08, SUCCESS if user.get("logged_in") else ft.Colors.GREY),
                border_radius=20, padding=ft.Padding.symmetric(horizontal=14, vertical=6),
            ),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Container(height=16),
        ft.Row([
            stat_card(ft.Icons.LOGIN, "Total Sessions", str(len(entries)), PRIMARY_LIGHT),
            stat_card(ft.Icons.WARNING_AMBER_OUTLINED, "Late Sessions", str(len(late)), WARNING),
            stat_card(ft.Icons.CLASS_OUTLINED, "Subjects", str(len(schedules)), SUCCESS),
        ], spacing=16),
        ft.Container(height=16),
        ft.Row([
            ft.Container(
                content=card(ft.Column([
                    ft.Row([ft.Icon(ft.Icons.TODAY, color=PRIMARY),
                            heading(f"Today — {today}", size=15)], spacing=8),
                    ft.Container(height=12),
                    *([_sched_chip_f(s) for s in today_scheds]
                      if today_scheds else [subheading("No classes today. 🎉")]),
                ], spacing=8)),
                expand=2,
            ),
            ft.Container(
                content=card(ft.Column([
                    heading("Recent Activity", size=15),
                    ft.Container(height=8),
                    *([_log_row(l) for l in logs[:5]] if logs else [subheading("No activity yet.")]),
                ], spacing=6)),
                expand=3,
            ),
        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
    ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)


def _schedule(user: dict) -> ft.Control:
    schedules = ScheduleModel.get_for(user["id_number"], "faculty")
    days_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday"]
    by_day = {d: [] for d in days_order}
    for s in schedules:
        by_day.get(s.get("day"), []).append(s)

    day_cols = []
    for day in days_order:
        scheds = by_day[day]
        if not scheds:
            continue
        day_cols.append(ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Text(day, size=13, weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                    bgcolor=PRIMARY, border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                ),
                *[_sched_item(s) for s in scheds],
            ], spacing=8),
            bgcolor=SURFACE, border_radius=14, padding=16,
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK)),
        ))

    return ft.Column([
        card(ft.Row([
            ft.Icon(ft.Icons.CALENDAR_MONTH, color=PRIMARY),
            ft.Column([
                heading("Teaching Schedule", size=18),
                subheading(f"Department: {user.get('department','')} | Position: {user.get('position','')}"),
            ], spacing=2),
        ], spacing=10)),
        ft.Container(height=16),
        ft.GridView(controls=day_cols, runs_count=3, max_extent=300, spacing=16, run_spacing=16, expand=True)
        if day_cols else card(subheading("No schedules found.")),
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)


def _attendance(user: dict) -> ft.Control:
    logs = LogModel.get_by_id_number(user["id_number"])
    rows = []
    for l in logs[:50]:
        status_color = (SUCCESS if l["status"] in ("ON TIME","OK")
                        else (WARNING if l["status"]=="LATE" else ERROR_COLOR))
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(l["timestamp"], size=13)),
            ft.DataCell(ft.Container(
                content=ft.Text(l["action"], size=12, color=ft.Colors.WHITE, weight=ft.FontWeight.W_600),
                bgcolor=SUCCESS if l["action"]=="ENTRY" else TEXT_MUTED,
                border_radius=6, padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            )),
            ft.DataCell(ft.Text(l["status"], size=13, color=status_color, weight=ft.FontWeight.W_600)),
            ft.DataCell(ft.Text(l.get("subject","—"), size=13)),
        ]))

    return ft.Column([
        card(ft.Row([ft.Icon(ft.Icons.HISTORY, color=PRIMARY),
                     heading("Attendance History", size=18)], spacing=8)),
        ft.Container(height=16),
        card(ft.DataTable(
            columns=[ft.DataColumn(ft.Text(h, color=TEXT_MUTED, weight=ft.FontWeight.BOLD, size=12))
                     for h in ["Date/Time","Action","Status","Subject"]],
            rows=rows,
            column_spacing=20, data_row_min_height=44,
            horizontal_lines=ft.BorderSide(1, BORDER),
        ) if rows else subheading("No attendance records yet.")),
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)


def _profile(page: ft.Page, user: dict, nav: dict, file_picker: ft.FilePicker) -> ft.Control:
    photo_container = ft.Container(
        content=_photo_widget(user.get("photo")),
        width=120, height=120, border_radius=60,
        bgcolor=PRIMARY_LIGHT,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        border=ft.Border.all(4, ACCENT),
        alignment=ft.Alignment(0, 0),
    )

    async def _on_photo_async(_, picker, page, user, nav, container):
        files = await picker.pick_files(
            file_type=ft.FilePickerFileType.CUSTOM,
            allowed_extensions=["jpg", "jpeg", "png", "webp"],
            dialog_title="Select Profile Photo",
        )
        _on_photo(files, page, user, nav, container)

    def _on_photo(files, page, user, nav, container):
        if files and files[0].path:
            src = files[0].path
            if os.path.exists(src):
                ext = os.path.splitext(src)[1] or ".jpg"
                dst = os.path.join(UPLOADS_DIR, f"{user['id_number']}{ext}")
                shutil.copy2(src, dst)
                FacultyModel.update_photo(user["id_number"], dst)
                snack(page, "Photo updated successfully!")
                page.update()
                import time; time.sleep(0.8)
                faculty_view(page, user, nav)

    info_fields = [
        ("Faculty ID",  user.get("id_number",""),   ft.Icons.BADGE),
        ("Full Name",   f"{user.get('first_name','')} {user.get('middle_name','')} {user.get('last_name','')}".strip(), ft.Icons.PERSON),
        ("Birthdate",   user.get("birthdate","—"),  ft.Icons.CAKE),
        ("Gender",      user.get("gender","—"),     ft.Icons.PEOPLE),
        ("Address",     user.get("address","—"),    ft.Icons.HOME),
        ("Phone",       user.get("phone","—"),      ft.Icons.PHONE),
        ("Email",       user.get("email","—"),      ft.Icons.EMAIL),
        ("Department",  user.get("department","—"), ft.Icons.BUSINESS),
        ("Position",    user.get("position","—"),   ft.Icons.WORK),
    ]

    return ft.Column([
        ft.Row([
            card(ft.Column([
                photo_container,
                ft.Container(height=16),
                heading(f"{user.get('first_name','')} {user.get('last_name','')}", size=18),
                subheading(user.get("position",""), size=13),
                subheading(user.get("id_number",""), size=12),
                ft.Container(height=12),
                primary_btn("Change Photo", icon=ft.Icons.CAMERA_ALT_OUTLINED,
                            on_click=lambda _: _on_photo_async(_, file_picker, page, user, nav, photo_container)),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)),
            ft.Container(
                content=ft.Column([
                    heading("Profile Information", size=18),
                    ft.Container(height=12),
                    ft.GridView(
                        controls=[_info_tile(l, v, i) for l, v, i in info_fields],
                        runs_count=2, max_extent=260, spacing=12, run_spacing=12,
                    ),
                ], spacing=0),
                expand=True,
                bgcolor=SURFACE, border_radius=16, padding=24,
                shadow=ft.BoxShadow(blur_radius=12,
                    color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK),
                    offset=ft.Offset(0, 3)),
            ),
        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)


def _sched_chip_f(s: dict) -> ft.Container:
    return ft.Container(
        content=ft.Row([
            ft.Icon(ft.Icons.CLASS_OUTLINED, size=14, color=PRIMARY),
            ft.Text(f"{s.get('subject','')}  {s.get('start_time','')}–{s.get('end_time','')}",
                    size=13, color=TEXT_DARK),
        ], spacing=8),
        bgcolor=SURFACE_ALT, border_radius=8,
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        border=ft.Border.all(1, BORDER),
    )