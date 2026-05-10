"""
views/student_view.py
Student dashboard with schedule, logs, profile, and photo editing.
"""

import os, shutil
import flet as ft
from models import StudentModel, ScheduleModel, LogModel
from views.theme import *

UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


def student_view(page: ft.Page, user: dict, nav: dict, active_tab: int = 0):
    page.clean()
    page.bgcolor = SURFACE_ALT
    page.padding = 0
    page.scroll  = None

    # Refresh user data
    user = StudentModel.get_by_id(user["id_number"]) or user

    def go_tab(idx):
        student_view(page, user, nav, active_tab=idx)

    avatar = avatar_circle(user.get("photo"), size=72)

    nav_items = [
        (ft.Icons.DASHBOARD_OUTLINED,   "Dashboard",  0),
        (ft.Icons.CALENDAR_MONTH,       "My Schedule",1),
        (ft.Icons.HISTORY,              "Attendance", 2),
        (ft.Icons.PERSON_OUTLINED,      "Profile",    3),
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
                        content=ft.Text("Student", size=11, color=ACCENT,
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
        StudentModel.set_logged_in(user["id_number"], False)
        nav["login"]()

    # ── Main content ──────────────────────────────────────────────────────────
    # In Flet 0.85+, FilePicker is a Service — it self-registers with the page.
    # Do NOT add it to page.overlay; doing so causes "Unknown control: FilePicker".
    file_picker = ft.FilePicker()

    tabs = [_dashboard(user), _schedule(user), _attendance(user),
            _profile(page, user, nav, file_picker)]
    content_area = ft.Container(
        content=ft.Column([
            _topbar(active_tab),
            ft.Container(
                content=tabs[active_tab],
                expand=True,
                padding=24,
            ),
        ], expand=True, spacing=0),
        expand=True,
        bgcolor=SURFACE_ALT,
    )

    page.add(ft.Row([sidebar, content_area], expand=True, spacing=0))


def _topbar(tab_idx: int) -> ft.Container:
    titles = ["Dashboard", "My Schedule", "Attendance Log", "My Profile"]
    return ft.Container(
        content=ft.Row([
            heading(titles[tab_idx], size=20),
            ft.Text(f"📅 {__import__('datetime').datetime.now().strftime('%B %d, %Y')}",
                    size=13, color=TEXT_MUTED),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
           vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE,
        padding=ft.Padding.symmetric(horizontal=24, vertical=16),
        shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                             offset=ft.Offset(0, 2)),
    )


def _dashboard(user: dict) -> ft.Control:
    schedules = ScheduleModel.get_for(user["id_number"], "student")
    logs = LogModel.get_by_id_number(user["id_number"])
    entries = [l for l in logs if l["action"] == "ENTRY"]
    late    = [l for l in entries if l["status"] == "LATE"]

    import datetime
    today = datetime.datetime.now().strftime("%A")
    today_scheds = [s for s in schedules if s.get("day", "").lower() == today.lower()]

    today_card = card(ft.Column([
        ft.Row([
            ft.Icon(ft.Icons.TODAY, color=PRIMARY),
            heading(f"Today — {today}", size=15),
        ], spacing=8),
        ft.Container(height=12),
        *([_sched_chip(s) for s in today_scheds]
          if today_scheds else [subheading("No classes today. Enjoy your day! 🎉")]),
    ], spacing=8))

    stats_row = ft.Row([
        stat_card(ft.Icons.LOGIN,  "Total Entries",  str(len(entries)), PRIMARY_LIGHT),
        stat_card(ft.Icons.WARNING_AMBER_OUTLINED, "Late Entries", str(len(late)), WARNING),
        stat_card(ft.Icons.CALENDAR_TODAY, "Subjects", str(len(schedules)), SUCCESS),
    ], spacing=16)

    recent_items = [_log_row(l) for l in logs[:5]] if logs else [subheading("No activity yet.")]
    recent = ft.Column([
        heading("Recent Activity", size=15),
        ft.Container(height=8),
        *recent_items,
    ], spacing=6)

    return ft.Column([
        ft.Row([
            ft.Column([
                heading(f"Hello, {user['first_name']}! 👋", size=22),
                subheading(f"ID: {user['id_number']} • {user.get('course','')} {user.get('year_level','')}"),
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
        stats_row,
        ft.Container(height=16),
        ft.Row([
            ft.Container(today_card, expand=2),
            ft.Container(card(recent), expand=3),
        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
    ], spacing=0, scroll=ft.ScrollMode.AUTO, expand=True)


def _schedule(user: dict) -> ft.Control:
    schedules = ScheduleModel.get_for(user["id_number"], "student")
    days_order = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
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
                    content=ft.Text(day, size=13, weight=ft.FontWeight.BOLD,
                                    color=ft.Colors.WHITE),
                    bgcolor=PRIMARY, border_radius=8,
                    padding=ft.Padding.symmetric(horizontal=12, vertical=6),
                ),
                *[_sched_item(s) for s in scheds],
            ], spacing=8),
            bgcolor=SURFACE, border_radius=14, padding=16,
            shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK)),
        ))

    return ft.Column([
        card(ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.CALENDAR_MONTH, color=PRIMARY),
                heading("Weekly Schedule", size=18),
            ], spacing=8),
            subheading(f"Course: {user.get('course','')} | Year: {user.get('year_level','')} | Block: {user.get('block','')}"),
        ], spacing=4)),
        ft.Container(height=16),
        ft.GridView(
            controls=day_cols,
            runs_count=3,
            max_extent=300,
            spacing=16,
            run_spacing=16,
            expand=True,
        ) if day_cols else card(subheading("No schedules found.")),
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)


def _attendance(user: dict) -> ft.Control:
    logs = LogModel.get_by_id_number(user["id_number"])

    header = ft.DataRow(cells=[
        ft.DataCell(ft.Text("Date/Time", weight=ft.FontWeight.BOLD, color=TEXT_MUTED, size=12)),
        ft.DataCell(ft.Text("Action",    weight=ft.FontWeight.BOLD, color=TEXT_MUTED, size=12)),
        ft.DataCell(ft.Text("Status",    weight=ft.FontWeight.BOLD, color=TEXT_MUTED, size=12)),
        ft.DataCell(ft.Text("Subject",   weight=ft.FontWeight.BOLD, color=TEXT_MUTED, size=12)),
    ])

    rows = []
    for l in logs[:50]:
        status_color = (SUCCESS if l["status"] in ("ON TIME","OK")
                        else (WARNING if l["status"]=="LATE" else ERROR_COLOR))
        rows.append(ft.DataRow(cells=[
            ft.DataCell(ft.Text(l["timestamp"], size=13)),
            ft.DataCell(ft.Container(
                content=ft.Text(l["action"], size=12, color=ft.Colors.WHITE,
                                weight=ft.FontWeight.W_600),
                bgcolor=SUCCESS if l["action"]=="ENTRY" else TEXT_MUTED,
                border_radius=6, padding=ft.Padding.symmetric(horizontal=8, vertical=3),
            )),
            ft.DataCell(ft.Text(l["status"], size=13, color=status_color,
                                weight=ft.FontWeight.W_600)),
            ft.DataCell(ft.Text(l.get("subject","—"), size=13)),
        ]))

    return ft.Column([
        card(ft.Row([
            ft.Icon(ft.Icons.HISTORY, color=PRIMARY),
            heading("Attendance History", size=18),
        ], spacing=8)),
        ft.Container(height=16),
        card(ft.Column([
            ft.DataTable(
                columns=[
                    ft.DataColumn(ft.Text("")),
                    ft.DataColumn(ft.Text("")),
                    ft.DataColumn(ft.Text("")),
                    ft.DataColumn(ft.Text("")),
                ],
                rows=[header] + rows,
                column_spacing=20,
                data_row_min_height=44,
                heading_row_height=0,
                border_radius=10,
                horizontal_lines=ft.BorderSide(1, BORDER),
            ) if rows else subheading("No attendance records yet."),
        ], scroll=ft.ScrollMode.AUTO)),
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
            dialog_title="Select New Profile Photo",
        )
        _on_photo(files, page, user, nav, container)

    def _on_photo(files, page, user, nav, container):
        if files and files[0].path:
            src = files[0].path
            if os.path.exists(src):
                ext = os.path.splitext(src)[1] or ".jpg"
                dst = os.path.join(UPLOADS_DIR, f"{user['id_number']}{ext}")
                shutil.copy2(src, dst)
                StudentModel.update_photo(user["id_number"], dst)
                snack(page, "Photo updated successfully!")
                page.update()
                import time; time.sleep(0.8)
                student_view(page, user, nav)

    fields_info = [
        ("ID Number",    user.get("id_number",""),    ft.Icons.BADGE),
        ("Full Name",    f"{user.get('first_name','')} {user.get('middle_name','')} {user.get('last_name','')}".strip(), ft.Icons.PERSON),
        ("Birthdate",    user.get("birthdate","—"),   ft.Icons.CAKE),
        ("Gender",       user.get("gender","—"),      ft.Icons.PEOPLE),
        ("Address",      user.get("address","—"),     ft.Icons.HOME),
        ("Phone",        user.get("phone","—"),       ft.Icons.PHONE),
        ("Email",        user.get("email","—"),       ft.Icons.EMAIL),
        ("Course",       user.get("course","—"),      ft.Icons.SCHOOL),
        ("Year Level",   user.get("year_level","—"),  ft.Icons.STAIRS),
        ("Block",        user.get("block","—"),       ft.Icons.GROUP),
        ("Guardian",     user.get("guardian_name","—"), ft.Icons.FAMILY_RESTROOM),
    ]

    return ft.Column([
        ft.Row([
            card(ft.Column([
                photo_container,
                ft.Container(height=16),
                heading(f"{user.get('first_name','')} {user.get('last_name','')}", size=20),
                subheading(user.get("id_number",""), size=13),
                ft.Container(height=12),
                primary_btn(
                    "Change Photo",
                    icon=ft.Icons.CAMERA_ALT_OUTLINED,
                    on_click=lambda _: _on_photo_async(_, file_picker, page, user, nav, photo_container),
                ),
                ft.Container(height=16),
                # ── Scannable QR code ──────────────────────────────────────
                _qr_code_widget(user.get("id_number", "")),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)),
            ft.Container(
                content=ft.Column([
                    heading("Account Information", size=18),
                    ft.Container(height=12),
                    ft.GridView(
                        controls=[_info_tile(label, value, icon)
                                  for label, value, icon in fields_info],
                        runs_count=2, max_extent=260,
                        spacing=12, run_spacing=12,
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


# ── Helpers ───────────────────────────────────────────────────────────────────
def _qr_code_widget(id_number: str) -> ft.Control:
    """Return a real scannable QR image for this student's ID, or a fallback icon."""
    if not id_number:
        return ft.Container()
    try:
        import cv2, numpy as np, os
        # Check for cached QR image
        uploads_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
        qr_path     = os.path.join(uploads_dir, f"QR-{id_number}.png")
        if not os.path.exists(qr_path):
            # Generate it on the fly
            os.makedirs(uploads_dir, exist_ok=True)
            enc      = cv2.QRCodeEncoder.create()
            qr_small = enc.encode(id_number)
            scale    = max(1, 200 // qr_small.shape[0])
            qr_large = cv2.resize(qr_small, (qr_small.shape[1] * scale, qr_small.shape[0] * scale),
                                  interpolation=cv2.INTER_NEAREST)
            border = 16
            h, w   = qr_large.shape[:2]
            canvas = np.full((h + border * 2, w + border * 2), 255, dtype=np.uint8)
            canvas[border:border + h, border:border + w] = qr_large
            cv2.imwrite(qr_path, canvas)
        return ft.Column([
            ft.Image(src=qr_path, width=160, height=160, fit=ft.BoxFit.CONTAIN),
            ft.Text("Scan at campus entry/exit", size=10,
                    color=ft.Colors.with_opacity(0.55, ft.Colors.BLACK),
                    text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4)
    except Exception as exc:
        print(f"[_qr_code_widget] {exc}")
        return ft.Icon(ft.Icons.QR_CODE_2, size=60)


def _photo_widget(photo: str) -> ft.Control:
    if photo and os.path.exists(photo):
        return ft.Image(src=photo, width=120, height=120, fit=ft.BoxFit.COVER)
    return ft.Icon(ft.Icons.PERSON, size=64, color=ft.Colors.WHITE)


def _sched_chip(s: dict) -> ft.Container:
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


def _sched_item(s: dict) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Text(s.get("subject",""), size=14, weight=ft.FontWeight.W_600, color=TEXT_DARK),
            ft.Text(f"{s.get('start_time','')} – {s.get('end_time','')}", size=12, color=TEXT_MUTED),
        ], spacing=2),
        bgcolor=SURFACE_ALT, border_radius=8,
        padding=ft.Padding.symmetric(horizontal=12, vertical=8),
        border=ft.Border.all(1, BORDER),
    )


def _log_row(l: dict) -> ft.Container:
    color = SUCCESS if l["action"] == "ENTRY" else TEXT_MUTED
    return ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Icon(
                    ft.Icons.LOGIN if l["action"] == "ENTRY" else ft.Icons.LOGOUT,
                    size=16, color=color,
                ),
                width=32, height=32, border_radius=16,
                bgcolor=ft.Colors.with_opacity(0.1, color),
                alignment=ft.Alignment(0, 0),
            ),
            ft.Column([
                ft.Text(f"{l['action']} — {l.get('subject','')}", size=13, color=TEXT_DARK),
                ft.Text(l["timestamp"], size=11, color=TEXT_MUTED),
            ], spacing=2, expand=True),
            ft.Container(
                content=ft.Text(l["status"], size=11, color=ft.Colors.WHITE),
                bgcolor=(SUCCESS if l["status"] in ("ON TIME","OK")
                         else (WARNING if l["status"]=="LATE" else ERROR_COLOR)),
                border_radius=10, padding=ft.Padding.symmetric(horizontal=8, vertical=2),
            ),
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE_ALT, border_radius=10, padding=12,
        border=ft.Border.all(1, BORDER),
    )


def _info_tile(label: str, value: str, icon) -> ft.Container:
    return ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Icon(icon, size=16, color=PRIMARY),
                width=32, height=32, border_radius=8,
                bgcolor=ft.Colors.with_opacity(0.08, PRIMARY),
                alignment=ft.Alignment(0, 0),
            ),
            ft.Column([
                ft.Text(label, size=11, color=TEXT_MUTED),
                ft.Text(value or "—", size=13, color=TEXT_DARK, weight=ft.FontWeight.W_500),
            ], spacing=1, expand=True),
        ], spacing=10, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE_ALT, border_radius=10,
        padding=ft.Padding.symmetric(horizontal=12, vertical=10),
        border=ft.Border.all(1, BORDER),
    )