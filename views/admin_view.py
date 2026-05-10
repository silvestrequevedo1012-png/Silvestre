"""
views/admin_view.py
Admin dashboard: manage students, faculty (with photo), logs.
"""

import os
import datetime
import flet as ft
from controllers import AdminController
from models import StudentModel, FacultyModel
from views.theme import *
from views.student_view import _sched_item, _photo_widget


def admin_view(page: ft.Page, user: dict, nav: dict, active_tab: int = 0):
    page.clean()
    page.bgcolor = SURFACE_ALT
    page.padding = 0
    page.scroll  = None

    def go_tab(idx):
        admin_view(page, user, nav, active_tab=idx)

    nav_items = [
        (ft.Icons.DASHBOARD_OUTLINED, "Dashboard",  0),
        (ft.Icons.SCHOOL,             "Students",   1),
        (ft.Icons.PEOPLE,             "Faculty",    2),
        (ft.Icons.HISTORY,            "Logs",       3),
    ]

    sidebar = ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Column([
                    ft.Container(
                        content=ft.Icon(ft.Icons.ADMIN_PANEL_SETTINGS, size=42, color=ACCENT),
                        width=72, height=72, border_radius=36,
                        bgcolor=ft.Colors.with_opacity(0.15, ACCENT),
                        alignment=ft.Alignment(0, 0),
                        border=ft.Border.all(3, ACCENT),
                    ),
                    ft.Container(height=10),
                    ft.Text(user.get("name","Administrator"), size=14,
                            weight=ft.FontWeight.W_600, color=ft.Colors.WHITE,
                            text_align=ft.TextAlign.CENTER),
                    ft.Container(height=4),
                    ft.Container(
                        content=ft.Text("System Admin", size=11, color=ACCENT,
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
            sidebar_item(ft.Icons.LOGOUT, "Sign Out", on_click=lambda _: nav["login"]()),
            ft.Container(height=12),
        ], spacing=4, expand=True),
        bgcolor=SIDEBAR_BG, width=220,
        padding=ft.Padding.symmetric(horizontal=12, vertical=12),
    )

    tab_titles = ["Dashboard", "Student Management", "Faculty Management", "Entry/Exit Logs"]
    topbar = ft.Container(
        content=ft.Row([
            heading(tab_titles[active_tab], size=20),
            ft.Text(f"📅 {datetime.datetime.now().strftime('%B %d, %Y')}",
                    size=13, color=TEXT_MUTED),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
           vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE, padding=ft.Padding.symmetric(horizontal=24, vertical=16),
        shadow=ft.BoxShadow(blur_radius=6, color=ft.Colors.with_opacity(0.05, ft.Colors.BLACK),
                             offset=ft.Offset(0, 2)),
    )

    tabs_content = [
        _dashboard(page, nav, go_tab),
        _students_tab(page, nav, user),
        _faculty_tab(page, nav, user),
        _logs_tab(page),
    ]

    content_area = ft.Container(
        content=ft.Column([
            topbar,
            ft.Container(content=tabs_content[active_tab], expand=True, padding=24),
        ], expand=True, spacing=0),
        expand=True, bgcolor=SURFACE_ALT,
    )

    page.add(ft.Row([sidebar, content_area], expand=True, spacing=0))


# ── Dashboard ─────────────────────────────────────────────────────────────────
def _dashboard(page: ft.Page, nav: dict, go_tab=None) -> ft.Control:
    students = AdminController.get_all_students()
    faculty  = AdminController.get_all_faculty()
    logs     = AdminController.get_all_logs()
    entries  = [l for l in logs if l["action"] == "ENTRY"]
    late     = [l for l in entries if l["status"] == "LATE"]
    active_s = [s for s in students if s.get("logged_in")]
    active_f = [f for f in faculty  if f.get("logged_in")]

    return ft.Column([
        ft.Row([
            heading("System Overview", size=22),
            primary_btn("Scanner Terminal", icon=ft.Icons.QR_CODE_SCANNER,
                        on_click=lambda _: nav["scanner"]()),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN,
           vertical_alignment=ft.CrossAxisAlignment.CENTER),
        ft.Container(height=16),
        ft.Row([
            stat_card(ft.Icons.SCHOOL,      "Total Students",  str(len(students)), PRIMARY),
            stat_card(ft.Icons.PEOPLE,      "Total Faculty",   str(len(faculty)),  PRIMARY_LIGHT),
            stat_card(ft.Icons.LOGIN,       "Total Entries",   str(len(entries)),  SUCCESS),
            stat_card(ft.Icons.WARNING_AMBER_OUTLINED, "Late Entries", str(len(late)), WARNING),
        ], spacing=16),
        ft.Container(height=16),
        ft.Row([
            ft.Container(
                content=card(ft.Column([
                    ft.Row([ft.Icon(ft.Icons.WIFI, color=SUCCESS),
                            heading("Currently On Campus", size=15)], spacing=8),
                    ft.Container(height=8),
                    ft.Text(f"Students: {len(active_s)}", size=14, color=TEXT_DARK),
                    ft.Text(f"Faculty:  {len(active_f)}", size=14, color=TEXT_DARK),
                ], spacing=6)),
                expand=1,
            ),
            ft.Container(
                content=card(ft.Column([
                    heading("Recent Logs", size=15),
                    ft.Container(height=8),
                    *([ _mini_log(l) for l in logs[:6]] if logs else [subheading("No logs yet.")]),
                ], spacing=6)),
                expand=3,
            ),
        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
    ], scroll=ft.ScrollMode.AUTO, expand=True, spacing=0)


# ── Students Tab ──────────────────────────────────────────────────────────────
def _students_tab(page: ft.Page, nav: dict, user: dict = None) -> ft.Control:
    students = AdminController.get_all_students()
    search_ref = ft.Ref[ft.TextField]()
    list_ref   = ft.Ref[ft.Column]()

    def build_cards(data):
        cards = []
        for s in data:
            cards.append(_person_card(page, s, "student", nav))
        return cards

    def on_search(e):
        q = search_ref.current.value.lower()
        filtered = [s for s in students
                    if q in s.get("first_name","").lower()
                    or q in s.get("last_name","").lower()
                    or q in s.get("id_number","").lower()
                    or q in s.get("course","").lower()]
        list_ref.current.controls = build_cards(filtered)
        page.update()

    search = ft.TextField(
        ref=search_ref, hint_text="Search by name, ID, or course...",
        prefix_icon=ft.Icons.SEARCH, border_radius=12,
        border_color=BORDER, focused_border_color=PRIMARY_LIGHT,
        filled=True, fill_color=SURFACE,
        on_change=on_search,
    )

    students_col = ft.Column(ref=list_ref, controls=build_cards(students),
                              spacing=10, scroll=ft.ScrollMode.AUTO, height=520)

    return ft.Column([
        ft.Row([
            ft.Container(search, expand=True),
            ft.Container(
                content=ft.Text(f"{len(students)} students", size=13, color=TEXT_MUTED),
                padding=ft.Padding.symmetric(horizontal=12),
            ),
        ], spacing=12),
        ft.Container(height=12),
        students_col,
    ], spacing=0, scroll=ft.ScrollMode.AUTO)


# ── Faculty Tab ───────────────────────────────────────────────────────────────
def _faculty_tab(page: ft.Page, nav: dict, user: dict = None) -> ft.Control:
    faculty  = AdminController.get_all_faculty()
    search_ref = ft.Ref[ft.TextField]()
    list_ref   = ft.Ref[ft.Column]()

    def build_cards(data):
        return [_person_card(page, f, "faculty", nav) for f in data]

    def on_search(e):
        q = search_ref.current.value.lower()
        filtered = [f for f in faculty
                    if q in f.get("first_name","").lower()
                    or q in f.get("last_name","").lower()
                    or q in f.get("id_number","").lower()
                    or q in f.get("department","").lower()]
        list_ref.current.controls = build_cards(filtered)
        page.update()

    search = ft.TextField(
        ref=search_ref, hint_text="Search by name, ID, or department...",
        prefix_icon=ft.Icons.SEARCH, border_radius=12,
        border_color=BORDER, focused_border_color=PRIMARY_LIGHT,
        filled=True, fill_color=SURFACE,
        on_change=on_search,
    )

    faculty_col = ft.Column(ref=list_ref, controls=build_cards(faculty),
                             spacing=10, scroll=ft.ScrollMode.AUTO, height=520)

    return ft.Column([
        ft.Row([
            ft.Container(search, expand=True),
            ft.Container(
                content=ft.Text(f"{len(faculty)} faculty members", size=13, color=TEXT_MUTED),
                padding=ft.Padding.symmetric(horizontal=12),
            ),
        ], spacing=12),
        ft.Container(height=12),
        faculty_col,
    ], spacing=0, scroll=ft.ScrollMode.AUTO)


# ── Logs Tab ──────────────────────────────────────────────────────────────────
def _logs_tab(page: ft.Page = None) -> ft.Control:
    import datetime as _dt

    # Always fetch fresh from DB — never stale
    live_logs  = [AdminController.get_all_logs()]   # mutable wrapper so closures can update it
    active_filter = ["All"]
    entry_col_ref = ft.Ref[ft.Column]()
    exit_col_ref  = ft.Ref[ft.Column]()
    count_ref     = ft.Ref[ft.Text]()

    def _parse_ts(ts_str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return _dt.datetime.strptime(ts_str, fmt)
            except Exception:
                pass
        return None

    def _filter_logs(logs, period):
        if period == "All":
            return logs
        now = _dt.datetime.now()
        result = []
        for l in logs:
            ts = _parse_ts(l.get("timestamp", ""))
            if not ts:
                continue
            if period == "Today" and ts.date() == now.date():
                result.append(l)
            elif period == "This Week":
                week_start = now - _dt.timedelta(days=now.weekday())
                if ts.date() >= week_start.date():
                    result.append(l)
            elif period == "This Month" and ts.year == now.year and ts.month == now.month:
                result.append(l)
            elif period == "This Year" and ts.year == now.year:
                result.append(l)
        return result

    def _fmt_time(ts_str):
        ts = _parse_ts(ts_str)
        return ts.strftime("%b %d, %Y  %I:%M %p") if ts else ts_str

    def _fmt_date(ts_str):
        ts = _parse_ts(ts_str)
        return ts.strftime("%b %d, %Y") if ts else ""

    def _fmt_clock(ts_str):
        ts = _parse_ts(ts_str)
        return ts.strftime("%I:%M %p") if ts else ts_str

    def _status_color(status: str) -> str:
        s = (status or "").upper()
        if s in ("ON TIME", "PRESENT"):
            return SUCCESS
        if s == "LATE":
            return WARNING
        if s in ("OK", "EXIT"):
            return TEXT_MUTED
        if s == "DENIED":
            return ERROR_COLOR
        # anything else
        return ERROR_COLOR

    def _entry_card(l: dict) -> ft.Container:
        status  = l.get("status", "")
        sc      = _status_color(status)
        role_bg = PRIMARY if l.get("role") == "student" else PRIMARY_LIGHT
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.LOGIN, size=13, color=sc),
                        width=26, height=26, border_radius=13,
                        bgcolor=ft.Colors.with_opacity(0.12, sc),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Text(l.get("full_name", "—"), size=13,
                            weight=ft.FontWeight.W_600, color=TEXT_DARK,
                            expand=True, no_wrap=True),
                    ft.Container(
                        content=ft.Text(status or "—", size=10,
                                        color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.W_700),
                        bgcolor=sc, border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                    ),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Container(
                        content=ft.Text(l.get("role", "").upper(), size=10,
                                        color=ft.Colors.WHITE),
                        bgcolor=role_bg, border_radius=6,
                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    ),
                    ft.Text(l.get("id_number", ""), size=11, color=TEXT_MUTED),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=11, color=TEXT_MUTED),
                    ft.Text(_fmt_date(l.get("timestamp", "")), size=11, color=TEXT_MUTED),
                    ft.Container(width=6),
                    ft.Icon(ft.Icons.ACCESS_TIME, size=11, color=sc),
                    ft.Text(_fmt_clock(l.get("timestamp", "")), size=12,
                            color=sc, weight=ft.FontWeight.W_600),
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                *(
                    [ft.Text(f"📚 {l['subject']}", size=11, color=PRIMARY_LIGHT)]
                    if l.get("subject") else []
                ),
            ], spacing=4),
            bgcolor=SURFACE_ALT, border_radius=10,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            border=ft.Border(left=ft.BorderSide(3, sc)),
        )

    def _exit_card(l: dict) -> ft.Container:
        role_bg = PRIMARY if l.get("role") == "student" else PRIMARY_LIGHT
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(ft.Icons.LOGOUT, size=13, color=TEXT_MUTED),
                        width=26, height=26, border_radius=13,
                        bgcolor=ft.Colors.with_opacity(0.1, TEXT_MUTED),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Text(l.get("full_name", "—"), size=13,
                            weight=ft.FontWeight.W_600, color=TEXT_DARK,
                            expand=True, no_wrap=True),
                    ft.Container(
                        content=ft.Text("EXIT", size=10, color=ft.Colors.WHITE,
                                        weight=ft.FontWeight.W_700),
                        bgcolor=TEXT_MUTED, border_radius=8,
                        padding=ft.Padding.symmetric(horizontal=7, vertical=3),
                    ),
                ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Container(
                        content=ft.Text(l.get("role", "").upper(), size=10,
                                        color=ft.Colors.WHITE),
                        bgcolor=role_bg, border_radius=6,
                        padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                    ),
                    ft.Text(l.get("id_number", ""), size=11, color=TEXT_MUTED),
                ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=11, color=TEXT_MUTED),
                    ft.Text(_fmt_date(l.get("timestamp", "")), size=11, color=TEXT_MUTED),
                    ft.Container(width=6),
                    ft.Icon(ft.Icons.ACCESS_TIME, size=11, color=TEXT_MUTED),
                    ft.Text(_fmt_clock(l.get("timestamp", "")), size=12,
                            color=TEXT_MUTED, weight=ft.FontWeight.W_600),
                ], spacing=4, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=4),
            bgcolor=SURFACE_ALT, border_radius=10,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            border=ft.Border(left=ft.BorderSide(3, TEXT_MUTED)),
        )

    def _repaint(filtered):
        entries = [l for l in filtered if l.get("action") == "ENTRY"]
        exits   = [l for l in filtered if l.get("action") == "EXIT"]

        if entry_col_ref.current:
            entry_col_ref.current.controls = (
                [_entry_card(l) for l in entries[:200]]
                if entries else [subheading("No entry records for this period.")]
            )
        if exit_col_ref.current:
            exit_col_ref.current.controls = (
                [_exit_card(l) for l in exits[:200]]
                if exits else [subheading("No exit records for this period.")]
            )
        if count_ref.current:
            count_ref.current.value = (
                f"{len(filtered)} records  •  {len(entries)} IN  •  {len(exits)} OUT"
            )
        # Highlight active filter button
        for ctrl in filter_row.controls:
            if isinstance(ctrl, ft.Container) and hasattr(ctrl.content, "value"):
                is_a = ctrl.content.value == active_filter[0]
                ctrl.bgcolor = PRIMARY if is_a else ft.Colors.with_opacity(0.06, PRIMARY)
                ctrl.border  = ft.Border.all(1.5, PRIMARY if is_a else BORDER)
                ctrl.content.color = PRIMARY if is_a else TEXT_MUTED
        if page:
            page.update()

    def apply_filter(e, period):
        active_filter[0] = period
        _repaint(_filter_logs(live_logs[0], period))

    def do_refresh(e=None):
        # Re-read from database
        live_logs[0] = AdminController.get_all_logs()
        _repaint(_filter_logs(live_logs[0], active_filter[0]))

    def _filter_btn(label):
        is_active = label == active_filter[0]
        return ft.Container(
            content=ft.Text(label, size=12,
                            color=PRIMARY if is_active else TEXT_MUTED,
                            weight=ft.FontWeight.W_600 if is_active else ft.FontWeight.NORMAL),
            bgcolor=PRIMARY if is_active else ft.Colors.with_opacity(0.06, PRIMARY),
            border=ft.Border.all(1.5, PRIMARY if is_active else BORDER),
            border_radius=20,
            padding=ft.Padding.symmetric(horizontal=14, vertical=6),
            ink=True,
            on_click=lambda e, l=label: apply_filter(e, l),
        )

    filter_row = ft.Row(
        controls=[_filter_btn(p) for p in ["All", "Today", "This Week", "This Month", "This Year"]],
        spacing=8, wrap=True,
    )

    initial      = live_logs[0]
    init_entries = [l for l in initial if l.get("action") == "ENTRY"]
    init_exits   = [l for l in initial if l.get("action") == "EXIT"]

    def _col_panel(title, icon, accent, col_ref, init_items, card_fn):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    ft.Container(
                        content=ft.Icon(icon, size=14, color=accent),
                        width=28, height=28, border_radius=14,
                        bgcolor=ft.Colors.with_opacity(0.1, accent),
                        alignment=ft.Alignment(0, 0),
                    ),
                    ft.Text(title, size=14, weight=ft.FontWeight.W_600, color=TEXT_DARK),
                    ft.Container(
                        content=ft.Text(str(len(init_items)), size=12,
                                        color=ft.Colors.WHITE),
                        bgcolor=accent, border_radius=12,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    ),
                ], spacing=8),
                ft.Container(height=8),
                ft.Column(
                    ref=col_ref,
                    controls=(
                        [card_fn(l) for l in init_items[:200]]
                        if init_items else [subheading("No records.")]
                    ),
                    spacing=8,
                    scroll=ft.ScrollMode.ALWAYS,
                    height=420,
                ),
            ], spacing=0),
            bgcolor=SURFACE, border_radius=14,
            padding=16,
            shadow=ft.BoxShadow(blur_radius=8,
                                color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                                offset=ft.Offset(0, 2)),
            border=ft.Border.all(1, BORDER),
            expand=True,
        )

    return ft.Column([
        # Header
        card(ft.Row([
            ft.Icon(ft.Icons.HISTORY, color=PRIMARY),
            heading("Entry / Exit Logs", size=18),
            ft.Container(expand=True),
            ft.Text(
                f"{len(initial)} records  •  {len(init_entries)} IN  •  {len(init_exits)} OUT",
                ref=count_ref, size=13, color=TEXT_MUTED,
            ),
            ft.Container(width=12),
            ft.IconButton(
                icon=ft.Icons.REFRESH,
                icon_color=PRIMARY,
                tooltip="Refresh logs",
                on_click=do_refresh,
            ),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)),
        ft.Container(height=8),
        # Filter buttons
        card(ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.FILTER_LIST, color=TEXT_MUTED, size=18),
                ft.Text("Filter by period:", size=13, color=TEXT_MUTED),
            ], spacing=6),
            ft.Container(height=6),
            filter_row,
        ], spacing=4)),
        ft.Container(height=8),
        # Side-by-side ENTRY | EXIT panels
        ft.Row([
            _col_panel("Entry (Time In)",  ft.Icons.LOGIN,  SUCCESS,
                       entry_col_ref, init_entries, _entry_card),
            _col_panel("Exit (Time Out)",  ft.Icons.LOGOUT, TEXT_MUTED,
                       exit_col_ref,  init_exits,   _exit_card),
        ], spacing=16, vertical_alignment=ft.CrossAxisAlignment.START),
    ], scroll=ft.ScrollMode.AUTO, spacing=0)


# ── Person Card ───────────────────────────────────────────────────────────────
def _person_card(page: ft.Page, person: dict, role: str, nav: dict) -> ft.Container:
    photo = person.get("photo")
    if photo and os.path.exists(photo):
        avatar_w = ft.Container(
            content=ft.Image(src=photo, width=56, height=56, fit=ft.BoxFit.COVER),
            width=56, height=56, border_radius=28,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border=ft.Border.all(2, ACCENT),
        )
    else:
        avatar_w = ft.Container(
            content=ft.Icon(ft.Icons.PERSON, size=28, color=ft.Colors.WHITE),
            width=56, height=56, border_radius=28,
            bgcolor=PRIMARY_LIGHT,
            alignment=ft.Alignment(0, 0),
            border=ft.Border.all(2, BORDER),
        )

    if role == "student":
        subtitle = f"{person.get('course','')} • {person.get('year_level','')} • {person.get('block','')}"
        extra    = f"Email: {person.get('email','—')}"
        tag_color = PRIMARY
    else:
        subtitle = f"{person.get('department','')} • {person.get('position','')}"
        extra    = f"Email: {person.get('email','—')}"
        tag_color = PRIMARY_LIGHT

    status_color = SUCCESS if person.get("logged_in") else TEXT_MUTED
    status_label = "On Campus" if person.get("logged_in") else "Off Campus"

    def confirm_delete(e, pid=person["id_number"]):
        def do_delete(_):
            if role == "student":
                AdminController.remove_student(pid)
            else:
                AdminController.remove_faculty(pid)
            dlg.open = False
            page.update()
            admin_view(page, {"name":"System Administrator"}, nav)

        def cancel(_):
            dlg.open = False
            page.update()

        dlg = ft.AlertDialog(
            modal=True,
            title=ft.Text("Confirm Deletion", color=ERROR_COLOR),
            content=ft.Text(f"Remove {person.get('first_name','')} {person.get('last_name','')}?\nThis cannot be undone."),
            actions=[
                ft.TextButton("Cancel", on_click=cancel),
                ft.ElevatedButton(
                    "Delete",
                    on_click=do_delete,
                    style=ft.ButtonStyle(bgcolor=ERROR_COLOR, color=ft.Colors.WHITE),
                ),
            ],
            actions_alignment=ft.MainAxisAlignment.END,
        )
        page.overlay.append(dlg)
        dlg.open = True
        page.update()

    def view_details(e):
        _show_profile_dialog(page, person, role)

    schedules = person.get("schedules", [])

    return ft.Container(
        content=ft.Row([
            avatar_w,
            ft.Column([
                ft.Row([
                    ft.Text(f"{person.get('first_name','')} {person.get('last_name','')}",
                            size=15, weight=ft.FontWeight.W_600, color=TEXT_DARK),
                    ft.Container(
                        content=ft.Text(person["id_number"], size=11, color=ft.Colors.WHITE),
                        bgcolor=tag_color, border_radius=6,
                        padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    ),
                    ft.Container(
                        content=ft.Text(status_label, size=11, color=status_color),
                        bgcolor=ft.Colors.with_opacity(0.08, status_color),
                        border_radius=10, padding=ft.Padding.symmetric(horizontal=8, vertical=2),
                    ),
                ], spacing=8, wrap=True),
                ft.Text(subtitle, size=12, color=TEXT_MUTED),
                ft.Text(extra,    size=12, color=TEXT_MUTED),
            ], spacing=3, expand=True),
            ft.Row([
                ft.IconButton(ft.Icons.VISIBILITY_OUTLINED, icon_color=PRIMARY,
                              tooltip="View Profile", on_click=view_details),
                ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ERROR_COLOR,
                              tooltip="Remove", on_click=confirm_delete),
            ], spacing=0),
        ], spacing=14, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE, border_radius=14,
        padding=ft.Padding.symmetric(horizontal=16, vertical=12),
        shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                             offset=ft.Offset(0, 2)),
        border=ft.Border.all(1, BORDER),
    )


def _show_profile_dialog(page: ft.Page, person: dict, role: str):
    photo = person.get("photo")
    has_photo = photo and os.path.exists(photo)

    # ── Hero photo / avatar ────────────────────────────────────────────────────
    if has_photo:
        photo_hero = ft.Container(
            content=ft.Image(src=photo, width=140, height=140, fit=ft.BoxFit.COVER),
            width=140, height=140, border_radius=70,
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            border=ft.Border.all(4, ACCENT),
            shadow=ft.BoxShadow(blur_radius=18, spread_radius=2,
                                color=ft.Colors.with_opacity(0.25, ft.Colors.BLACK),
                                offset=ft.Offset(0, 4)),
        )
    else:
        initials = (
            (person.get("first_name", "?")[:1] + person.get("last_name", "")[:1]).upper()
        )
        photo_hero = ft.Container(
            content=ft.Text(initials, size=48, weight=ft.FontWeight.BOLD,
                            color=ft.Colors.WHITE),
            width=140, height=140, border_radius=70,
            bgcolor=PRIMARY_LIGHT,
            alignment=ft.Alignment(0, 0),
            border=ft.Border.all(4, ACCENT),
            shadow=ft.BoxShadow(blur_radius=18, spread_radius=2,
                                color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK),
                                offset=ft.Offset(0, 4)),
        )

    # ── Role badge ─────────────────────────────────────────────────────────────
    role_label = "Student" if role == "student" else "Faculty"
    role_color = PRIMARY if role == "student" else PRIMARY_LIGHT
    status_color = SUCCESS if person.get("logged_in") else TEXT_MUTED
    status_label = "● On Campus" if person.get("logged_in") else "○ Off Campus"

    # ── Info fields ────────────────────────────────────────────────────────────
    def _field(label: str, value: str, icon=None, full_width: bool = False):
        return ft.Container(
            content=ft.Column([
                ft.Row([
                    *([ ft.Icon(icon, size=12, color=TEXT_MUTED)] if icon else []),
                    ft.Text(label, size=10, color=TEXT_MUTED, weight=ft.FontWeight.W_500),
                ], spacing=4),
                ft.Text(value or "—", size=13, color=TEXT_DARK,
                        weight=ft.FontWeight.W_600),
            ], spacing=3),
            bgcolor=SURFACE_ALT, border_radius=10,
            padding=ft.Padding.symmetric(horizontal=12, vertical=10),
            expand=full_width,
        )

    if role == "student":
        section_personal = ft.Row([
            _field("ID Number",   person.get("id_number",""),  ft.Icons.BADGE_OUTLINED),
            _field("Course",      person.get("course","—"),    ft.Icons.SCHOOL_OUTLINED),
            _field("Year Level",  person.get("year_level","—"),ft.Icons.GRADE_OUTLINED),
            _field("Block",       person.get("block","—"),     ft.Icons.GROUP_OUTLINED),
        ], spacing=8, wrap=True)

        section_contact = ft.Row([
            _field("Email",   person.get("email","—"),   ft.Icons.EMAIL_OUTLINED),
            _field("Phone",   person.get("phone","—"),   ft.Icons.PHONE_OUTLINED),
            _field("Gender",  person.get("gender","—"),  ft.Icons.PERSON_OUTLINED),
            _field("Birthdate",person.get("birthdate","—"), ft.Icons.CAKE_OUTLINED),
        ], spacing=8, wrap=True)

        section_address = ft.Row([
            _field("Address", person.get("address","—"), ft.Icons.HOME_OUTLINED, full_width=True),
        ], spacing=8)

        section_guardian = ft.Row([
            _field("Guardian Name",  person.get("guardian_name","—"),  ft.Icons.PEOPLE_OUTLINE),
            _field("Relation",       person.get("guardian_relation","—"), ft.Icons.FAMILY_RESTROOM),
            _field("Guardian Phone", person.get("guardian_phone","—"), ft.Icons.PHONE_OUTLINED),
        ], spacing=8, wrap=True)

        info_sections = [
            ("🎓 Academic",  section_personal),
            ("📞 Contact",   section_contact),
            ("🏠 Address",   section_address),
            ("👨‍👩‍👧 Guardian", section_guardian),
        ]
    else:
        section_employment = ft.Row([
            _field("Faculty ID",  person.get("id_number",""),   ft.Icons.BADGE_OUTLINED),
            _field("Department",  person.get("department","—"), ft.Icons.BUSINESS_OUTLINED),
            _field("Position",    person.get("position","—"),   ft.Icons.WORK_OUTLINE),
        ], spacing=8, wrap=True)

        section_contact = ft.Row([
            _field("Email",    person.get("email","—"),    ft.Icons.EMAIL_OUTLINED),
            _field("Phone",    person.get("phone","—"),    ft.Icons.PHONE_OUTLINED),
            _field("Gender",   person.get("gender","—"),   ft.Icons.PERSON_OUTLINED),
            _field("Birthdate",person.get("birthdate","—"),ft.Icons.CAKE_OUTLINED),
        ], spacing=8, wrap=True)

        section_address = ft.Row([
            _field("Address", person.get("address","—"), ft.Icons.HOME_OUTLINED, full_width=True),
        ], spacing=8)

        info_sections = [
            ("💼 Employment", section_employment),
            ("📞 Contact",    section_contact),
            ("🏠 Address",    section_address),
        ]

    def _section_block(title, content):
        return ft.Column([
            ft.Text(title, size=12, weight=ft.FontWeight.W_700, color=TEXT_MUTED),
            ft.Container(height=6),
            content,
        ], spacing=0)

    schedules = person.get("schedules", [])
    sched_tiles = [_sched_item(s) for s in schedules] if schedules else [subheading("No schedules assigned.")]

    def close(_):
        dlg.open = False
        page.update()

    body_sections = []
    for title, content in info_sections:
        body_sections.append(_section_block(title, content))
        body_sections.append(ft.Container(height=14))
    body_sections.append(_section_block("📅 Schedule", ft.Column(sched_tiles, spacing=6)))

    dlg = ft.AlertDialog(
        modal=True,
        content_padding=ft.Padding.all(0),
        content=ft.Container(
            content=ft.Column([
                # ── Hero header ────────────────────────────────────────────────
                ft.Container(
                    content=ft.Stack([
                        # Background gradient band
                        ft.Container(
                            bgcolor=PRIMARY,
                            height=100,
                            border_radius=ft.BorderRadius(
                                top_left=16, top_right=16,
                                bottom_left=0, bottom_right=0,
                            ),
                        ),
                        # Photo centred, overlapping the band
                        ft.Container(
                            content=ft.Column([
                                ft.Container(height=30),
                                photo_hero,
                                ft.Container(height=10),
                                ft.Text(
                                    f"{person.get('first_name','')} {person.get('last_name','')}",
                                    size=20, weight=ft.FontWeight.BOLD,
                                    color=TEXT_DARK, text_align=ft.TextAlign.CENTER,
                                ),
                                ft.Row([
                                    ft.Container(
                                        content=ft.Text(role_label, size=11,
                                                        color=ft.Colors.WHITE,
                                                        weight=ft.FontWeight.W_600),
                                        bgcolor=role_color, border_radius=12,
                                        padding=ft.Padding.symmetric(horizontal=10, vertical=3),
                                    ),
                                    ft.Text(status_label, size=12, color=status_color,
                                            weight=ft.FontWeight.W_500),
                                ], alignment=ft.MainAxisAlignment.CENTER, spacing=8),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4),
                            alignment=ft.Alignment(0, 0),
                        ),
                    ]),
                    height=280,
                    border=ft.Border(bottom=ft.BorderSide(1, BORDER)),
                ),
                # ── Scrollable body ────────────────────────────────────────────
                ft.Container(
                    content=ft.Column(
                        body_sections,
                        spacing=0,
                        scroll=ft.ScrollMode.AUTO,
                    ),
                    padding=ft.Padding.symmetric(horizontal=20, vertical=16),
                    height=320,
                ),
            ], spacing=0),
            width=560,
            height=620,
            bgcolor=SURFACE,
            border_radius=16,
        ),
        actions=[
            ft.TextButton("Close", on_click=close,
                          style=ft.ButtonStyle(color=PRIMARY)),
        ],
        actions_alignment=ft.MainAxisAlignment.END,
        shape=ft.RoundedRectangleBorder(radius=16),
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()


def _mini_log(l: dict) -> ft.Container:
    import datetime as _dt
    def _parse_ts(ts_str):
        for fmt in ("%Y-%m-%d %H:%M:%S", "%Y-%m-%dT%H:%M:%S"):
            try:
                return _dt.datetime.strptime(ts_str, fmt)
            except Exception:
                pass
        return None
    ts_raw = l.get("timestamp", "")
    ts = _parse_ts(ts_raw)
    date_str  = ts.strftime("%b %d, %Y") if ts else ""
    clock_str = ts.strftime("%I:%M %p")  if ts else ts_raw

    status = l.get("status", "")
    if l["action"] == "EXIT":
        color = TEXT_MUTED
    elif status == "DENIED":
        color = ERROR_COLOR
    elif status == "LATE":
        color = WARNING
    else:
        color = SUCCESS
    return ft.Container(
        content=ft.Row([
            ft.Container(
                content=ft.Icon(ft.Icons.LOGIN if l["action"] == "ENTRY" else ft.Icons.LOGOUT,
                                size=14, color=color),
                width=28, height=28, border_radius=14,
                bgcolor=ft.Colors.with_opacity(0.1, color),
                alignment=ft.Alignment(0, 0),
            ),
            ft.Column([
                ft.Text(f"{l['full_name']} — {l['role'].capitalize()}", size=12, color=TEXT_DARK),
                ft.Row([
                    ft.Icon(ft.Icons.CALENDAR_TODAY, size=10, color=TEXT_MUTED),
                    ft.Text(date_str, size=10, color=TEXT_MUTED),
                    ft.Container(width=4),
                    ft.Icon(ft.Icons.ACCESS_TIME, size=10, color=color),
                    ft.Text(clock_str, size=10, color=color, weight=ft.FontWeight.W_600),
                ], spacing=3, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            ], spacing=1, expand=True),
            ft.Container(
                content=ft.Text(l["status"], size=10, color=ft.Colors.WHITE),
                bgcolor=(SUCCESS if l["status"] in ("ON TIME","OK","PRESENT")
                         else (WARNING if l["status"]=="LATE" else ERROR_COLOR)),
                border_radius=8, padding=ft.Padding.symmetric(horizontal=6, vertical=2),
            ),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE_ALT, border_radius=8,
        padding=ft.Padding.symmetric(horizontal=10, vertical=6),
        border=ft.Border.all(1, BORDER),
    )