"""
views/register_view.py
Multi-step registration for Students and Faculty with photo upload.
"""

import os
import shutil
import flet as ft
from controllers import RegisterController
from views.theme import *


def _generate_qr_image(id_number: str) -> str:
    """
    Generate a scannable QR code PNG for *id_number* and save it next to
    the uploads folder.  Returns the absolute path to the saved PNG, or an
    empty string on failure.
    """
    try:
        import cv2
        import numpy as np

        enc = cv2.QRCodeEncoder.create()
        qr_small = enc.encode(id_number)          # tiny binary matrix

        # Scale up so the QR is crisp and easy to scan (250 × 250 px)
        scale     = max(1, 250 // qr_small.shape[0])
        qr_large  = cv2.resize(
            qr_small,
            (qr_small.shape[1] * scale, qr_small.shape[0] * scale),
            interpolation=cv2.INTER_NEAREST,
        )

        # Add a white border (quiet zone) — required by QR spec
        border    = 20
        h, w      = qr_large.shape[:2]
        canvas    = np.full((h + border * 2, w + border * 2), 255, dtype=np.uint8)
        canvas[border:border + h, border:border + w] = qr_large

        qr_dir  = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads"
        )
        os.makedirs(qr_dir, exist_ok=True)
        qr_path = os.path.join(qr_dir, f"QR-{id_number}.png")
        cv2.imwrite(qr_path, canvas)
        return qr_path
    except Exception as exc:
        print(f"[QR generation] ERROR: {exc}")
        return ""

def _time_options():
    import datetime
    opts = []
    for h in range(6, 23):
        for m in (0, 30):
            t = datetime.time(h, m)
            opts.append(t.strftime("%I:%M %p").lstrip("0"))
    return opts

def time_dropdown(label: str) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        options=[ft.dropdown.Option(t) for t in _time_options()],
        border_radius=10,
        width=160,
        value="8:00 AM",
    )



UPLOADS_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "uploads")
os.makedirs(UPLOADS_DIR, exist_ok=True)


def _show_registration_success(page, nav, id_number: str, role: str):
    """Pop-up dialog showing the new ID with a real scannable QR code and a Done button."""
    role_label = "Student" if role == "student" else "Faculty"

    # Generate an actual scannable QR code image
    qr_path = _generate_qr_image(id_number)

    if qr_path and os.path.exists(qr_path):
        qr_widget = ft.Image(
            src=qr_path,
            width=180, height=180,
            fit=ft.BoxFit.CONTAIN,
        )
    else:
        # Fallback: decorative icon if generation failed
        qr_widget = ft.Icon(ft.Icons.QR_CODE_2, size=80, color=PRIMARY)

    qr_box = ft.Container(
        content=ft.Column([
            qr_widget,
            ft.Text(id_number, size=16, weight=ft.FontWeight.BOLD,
                    color=PRIMARY, text_align=ft.TextAlign.CENTER, selectable=True),
            ft.Text("Scan this QR or copy your ID number", size=11, color=TEXT_MUTED,
                    text_align=ft.TextAlign.CENTER),
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=6),
        width=280, padding=ft.Padding.symmetric(horizontal=20, vertical=20),
        border_radius=16, bgcolor=SURFACE_ALT, border=ft.Border.all(2, PRIMARY),
        alignment=ft.Alignment(0, 0),
    )

    def done(_):
        dlg.open = False
        page.update()
        nav["login"]()

    dlg = ft.AlertDialog(
        modal=True,
        content_padding=ft.Padding.all(0),
        content=ft.Container(
            content=ft.Column([
                ft.Container(
                    content=ft.Column([
                        ft.Icon(ft.Icons.CHECK_CIRCLE, size=52, color=ft.Colors.WHITE),
                        ft.Text("Registration Complete!", size=20,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE,
                                text_align=ft.TextAlign.CENTER),
                        ft.Text(f"{role_label} account created successfully.", size=13,
                                color=ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                                text_align=ft.TextAlign.CENTER),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                    bgcolor=SUCCESS,
                    padding=ft.Padding.symmetric(horizontal=32, vertical=24),
                    border_radius=ft.BorderRadius(top_left=16, top_right=16,
                                                  bottom_left=0, bottom_right=0),
                ),
                ft.Container(
                    content=ft.Column([
                        ft.Text("Your Campus ID Number", size=13,
                                color=TEXT_MUTED, text_align=ft.TextAlign.CENTER),
                        ft.Container(height=12),
                        qr_box,
                        ft.Container(height=16),
                        ft.Text(
                            "Keep this ID safe — you will need it to\nscan in and out of campus.",
                            size=12, color=TEXT_MUTED, text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=20),
                        ft.ElevatedButton(
                            "✓  Done",
                            on_click=done,
                            width=200,
                            style=ft.ButtonStyle(
                                bgcolor=SUCCESS,
                                color=ft.Colors.WHITE,
                                shape=ft.RoundedRectangleBorder(radius=12),
                                padding=ft.Padding.symmetric(vertical=14),
                                elevation=3,
                            ),
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                    padding=ft.Padding.symmetric(horizontal=28, vertical=20),
                ),
            ], spacing=0),
            width=380, bgcolor=SURFACE, border_radius=16,
        ),
        shape=ft.RoundedRectangleBorder(radius=16),
    )
    page.overlay.append(dlg)
    dlg.open = True
    page.update()



def register_view(page: ft.Page, nav: dict):
    page.clean()
    page.bgcolor = SURFACE_ALT
    page.padding = 0
    page.scroll  = None

    reg_type_ref = ft.Ref[ft.Tabs]()
    step_ref     = [0]  # mutable step counter per registration type

    # ── Role tabs ─────────────────────────────────────────────────────────────
    student_form = _StudentForm(page, nav)
    faculty_form = _FacultyForm(page, nav)

    _tab_bar = ft.TabBar(
        tabs=[
            ft.Tab(label="Student Registration", icon=ft.Icons.SCHOOL),
            ft.Tab(label="Faculty Registration", icon=ft.Icons.PERSON_PIN),
        ],
        label_color=PRIMARY,
        unselected_label_color=TEXT_MUTED,
        indicator_color=PRIMARY,
    )
    _tab_view = ft.TabBarView(
        controls=[student_form.build(), faculty_form.build()],
        expand=True,
    )
    tabs = ft.Tabs(
        ref=reg_type_ref,
        content=ft.Column([_tab_bar, _tab_view], expand=True, spacing=0),
        length=2,
        selected_index=0,
        animation_duration=200,
        expand=True,
    )

    header = ft.Container(
        content=ft.Row([
            ft.IconButton(
                icon=ft.Icons.ARROW_BACK_IOS_NEW,
                icon_color=PRIMARY,
                on_click=lambda _: nav["login"](),
                tooltip="Back to Login",
            ),
            ft.Column([
                heading("Registration", size=22),
                subheading("Create your campus account", size=13),
            ], spacing=2, expand=True),
            ft.Icon(ft.Icons.SCHOOL_ROUNDED, size=36, color=PRIMARY),
        ], alignment=ft.MainAxisAlignment.START, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=SURFACE,
        padding=ft.Padding.symmetric(horizontal=24, vertical=16),
        shadow=ft.BoxShadow(blur_radius=8, color=ft.Colors.with_opacity(0.06, ft.Colors.BLACK),
                             offset=ft.Offset(0, 2)),
    )

    page.add(
        ft.Column([header, tabs], expand=True, spacing=0)
    )


# ═══════════════════════════════════════════════════════════════════════════════
#  STUDENT FORM
# ═══════════════════════════════════════════════════════════════════════════════
class _StudentForm:
    def __init__(self, page: ft.Page, nav: dict):
        self.page = page
        self.nav  = nav
        self.step = 0
        self.photo_path = None
        self.photo_preview = ft.Ref[ft.Container]()
        self._build_fields()

    def _build_fields(self):
        tf = text_field
        self.first_name  = tf("First Name *",    icon=ft.Icons.PERSON_OUTLINE)
        self.last_name   = tf("Last Name *",     icon=ft.Icons.PERSON_OUTLINE)
        self.middle_name = tf("Middle Name",     icon=ft.Icons.PERSON_OUTLINE)
        self.birthdate   = tf("Birthdate",       "YYYY-MM-DD", icon=ft.Icons.CAKE_OUTLINED)
        self.gender      = dropdown("Gender", ["Male", "Female", "Other"])
        self.address     = tf("Address",         icon=ft.Icons.HOME_OUTLINED)
        self.phone       = tf("Phone Number",    icon=ft.Icons.PHONE_OUTLINED)
        self.email       = tf("Email Address",   icon=ft.Icons.EMAIL_OUTLINED)
        self.password    = tf("Password *",      password=True, can_reveal=True, icon=ft.Icons.LOCK_OUTLINE)
        self.confirm_pw  = tf("Confirm Password *", password=True, can_reveal=True, icon=ft.Icons.LOCK_OUTLINE)

        self.course      = dropdown("Course", ["BSIT", "BSCS", "BSCE", "BSEd", "BSBA", "BSN", "BSME", "Other"])
        self.block       = tf("Block / Section", icon=ft.Icons.GROUP_OUTLINED)
        self.year_level  = dropdown("Year Level", ["1st Year", "2nd Year", "3rd Year", "4th Year"])

        self.guardian_name     = tf("Guardian Full Name",     icon=ft.Icons.PEOPLE_OUTLINE)
        self.guardian_relation = ft.Dropdown(
            label="Relation to Guardian",
            options=[ft.dropdown.Option(o) for o in [
                "Parent", "Father", "Mother", "Guardian",
                "Grandparent", "Sibling", "Aunt/Uncle", "Other",
            ]],
            leading_icon=ft.Icon(ft.Icons.FAMILY_RESTROOM),
            border_radius=10,
            filled=True,
            fill_color=ft.Colors.with_opacity(1, "white"),
            border_color="#C4C4C4",
            focused_border_color="#5B6EAE",
            expand=True,
        )
        self.guardian_phone    = tf("Guardian Phone",         icon=ft.Icons.PHONE_OUTLINED)

        self.schedules = []
        self.sched_list_ref = ft.Ref[ft.Column]()

    def build(self) -> ft.Control:
        self.steps_container = ft.Ref[ft.Column]()
        self.step_indicator  = ft.Ref[ft.Row]()
        self.step_content    = ft.Ref[ft.Container]()

        return ft.Container(
            content=ft.Column([
                ft.Container(height=16),
                self._step_indicators(),
                ft.Container(height=16),
                ft.Container(
                    ref=self.step_content,
                    content=self._render_step(),
                    expand=True,
                ),
            ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=0),
            padding=ft.Padding.symmetric(horizontal=24, vertical=8),
            expand=True,
        )

    def _step_indicators(self) -> ft.Row:
        steps = ["Personal Info", "Photo", "Academic", "Guardian", "Schedule"]
        items = []
        for i, s in enumerate(steps):
            active  = i == self.step
            done    = i < self.step
            color   = ACCENT if done else (PRIMARY if active else BORDER)
            bgcolor = color if (active or done) else SURFACE
            items.append(ft.Column([
                ft.Container(
                    content=ft.Icon(ft.Icons.CHECK, size=14, color=ft.Colors.WHITE)
                             if done else ft.Text(str(i+1), size=12,
                             color=ft.Colors.WHITE if active else TEXT_MUTED,
                             weight=ft.FontWeight.BOLD),
                    width=30, height=30,
                    border_radius=15,
                    bgcolor=bgcolor,
                    border=ft.Border.all(2, color),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Text(s, size=10, color=PRIMARY if active else TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4))
            if i < len(steps) - 1:
                items.append(ft.Container(
                    ft.Divider(color=ACCENT if done else BORDER, height=2),
                    expand=True, margin=ft.Margin(bottom=16),
                ))
        return ft.Row(items, alignment=ft.MainAxisAlignment.CENTER,
                      vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _render_step(self) -> ft.Control:
        if self.step == 0:
            return self._step_personal()
        elif self.step == 1:
            return self._step_photo()
        elif self.step == 2:
            return self._step_academic()
        elif self.step == 3:
            return self._step_guardian()
        elif self.step == 4:
            return self._step_schedule()
        return ft.Container()

    def _nav_row(self, on_back=None, on_next=None, next_label="Next",
                 next_icon=ft.Icons.ARROW_FORWARD_IOS) -> ft.Row:
        return ft.Row([
            outline_btn("Back", on_click=on_back, icon=ft.Icons.ARROW_BACK_IOS_NEW)
            if on_back else ft.Container(),
            primary_btn(next_label, on_click=on_next, icon=next_icon),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    # ── Step 0: Personal Info ─────────────────────────────────────────────────
    def _step_personal(self) -> ft.Control:
        def next_step(e):
            if not self.first_name.value or not self.last_name.value:
                snack(self.page, "First and last name are required.", error=True)
                return
            if not self.password.value:
                snack(self.page, "Password is required.", error=True)
                return
            if self.password.value != self.confirm_pw.value:
                snack(self.page, "Passwords do not match.", error=True)
                return
            self._go_step(1)

        return ft.Column([
            card(ft.Column([
                heading("Personal Information", size=18),
                ft.Container(height=16),
                ft.Row([self.first_name, self.last_name], spacing=12, expand=True),
                self.middle_name,
                ft.Row([self.birthdate, self.gender], spacing=12),
                self.address,
                ft.Row([self.phone, self.email], spacing=12),
                ft.Container(height=8),
                divider("Account Credentials"),
                ft.Container(height=8),
                ft.Row([self.password, self.confirm_pw], spacing=12),
            ], spacing=12)),
            ft.Container(height=16),
            self._nav_row(
                on_back=lambda _: self.nav["login"](),
                on_next=next_step,
            ),
            ft.Container(height=24),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

    # ── Step 1: Photo Upload ──────────────────────────────────────────────────
    def _step_photo(self) -> ft.Control:
        preview_container = ft.Container(
            ref=self.photo_preview,
            content=_photo_placeholder(),
            width=160, height=160,
            border_radius=80,
            bgcolor=SURFACE_ALT,
            border=ft.Border.all(3, BORDER),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.Alignment(0, 0),
        )

        async def pick_photo(_):
            files = await ft.FilePicker().pick_files(
                allowed_extensions=["jpg", "jpeg", "png", "webp"],
                dialog_title="Select Profile Photo",
            )
            if files:
                self._on_photo_picked(files, preview_container)

        def next_step(e):
            self._go_step(2)

        return ft.Column([
            card(ft.Column([
                heading("Profile Photo", size=18),
                subheading("Upload a clear photo (optional but recommended)", size=13),
                ft.Container(height=24),
                ft.Row([
                    ft.Column([
                        preview_container,
                        ft.Container(height=16),
                        primary_btn(
                            "Choose Photo",
                            icon=ft.Icons.UPLOAD_FILE,
                            on_click=pick_photo,
                        ),
                        ft.Container(height=8),
                        ft.TextButton(
                            "Remove",
                            icon=ft.Icons.DELETE_OUTLINE,
                            on_click=lambda e: self._clear_photo(preview_container),
                            style=ft.ButtonStyle(color=ERROR_COLOR),
                        ) if self.photo_path else ft.Container(),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                    ft.Container(width=32),
                    ft.Column([
                        ft.Text("Photo Guidelines:", size=14,
                                weight=ft.FontWeight.W_600, color=TEXT_DARK),
                        ft.Container(height=8),
                        *[_guideline(t) for t in [
                            "Use a recent, clear photo",
                            "Face must be visible and centered",
                            "Plain or simple background preferred",
                            "Accepted: JPG, PNG, WEBP",
                            "Max recommended size: 5MB",
                        ]],
                    ], spacing=6, expand=True),
                ], vertical_alignment=ft.CrossAxisAlignment.START, spacing=0),
            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)),
            ft.Container(height=16),
            self._nav_row(on_back=lambda _: self._go_step(0), on_next=next_step),
            ft.Container(height=24),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

    def _on_photo_picked(self, files, container: ft.Container):
        if files and len(files) > 0:
            src = files[0].path
            if src and os.path.exists(src):
                self.photo_path = src
                container.content = ft.Image(
                    src=src, width=160, height=160,
                    fit=ft.BoxFit.COVER,
                )
                self.page.update()

    def _clear_photo(self, container: ft.Container):
        self.photo_path = None
        container.content = _photo_placeholder()
        self.page.update()

    # ── Step 2: Academic Info ─────────────────────────────────────────────────
    def _step_academic(self) -> ft.Control:
        def next_step(e):
            self._go_step(3)

        return ft.Column([
            card(ft.Column([
                heading("Academic Information", size=18),
                ft.Container(height=16),
                self.course,
                ft.Row([self.block, self.year_level], spacing=12),
            ], spacing=12)),
            ft.Container(height=16),
            self._nav_row(on_back=lambda _: self._go_step(1), on_next=next_step),
            ft.Container(height=24),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

    # ── Step 3: Guardian Info ─────────────────────────────────────────────────
    def _step_guardian(self) -> ft.Control:
        def next_step(e):
            self._go_step(4)

        return ft.Column([
            card(ft.Column([
                heading("Guardian Information", size=18),
                ft.Container(height=16),
                self.guardian_name,
                self.guardian_relation,
                self.guardian_phone,
            ], spacing=12)),
            ft.Container(height=16),
            self._nav_row(on_back=lambda _: self._go_step(2), on_next=next_step),
            ft.Container(height=24),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

    # ── Step 4: Schedule ─────────────────────────────────────────────────────
    def _step_schedule(self) -> ft.Control:
        sched_list = ft.Column(ref=self.sched_list_ref, spacing=8)

        def add_row(e=None):
            day   = dropdown("Day", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
            subj  = text_field("Subject")
            start = time_dropdown("Start Time")
            end   = time_dropdown("End Time")
            end.value = "9:00 AM"
            row_data = {"day_dd": day, "subj": subj, "start": start, "end": end}
            self.schedules.append(row_data)

            def remove(e, rd=row_data):
                self.schedules.remove(rd)
                sched_list.controls.remove(row_ctrl)
                self.page.update()

            row_ctrl = ft.Container(
                content=ft.Column([
                    ft.Row([day, subj], spacing=8),
                    ft.Row([start, end,
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ERROR_COLOR,
                                          on_click=remove, tooltip="Remove")],
                           spacing=8, alignment=ft.MainAxisAlignment.START),
                ], spacing=6),
                bgcolor=SURFACE_ALT,
                border_radius=12,
                padding=12,
                border=ft.Border.all(1, BORDER),
            )
            sched_list.controls.append(row_ctrl)
            self.page.update()

        add_row()

        def submit(e):
            scheds = []
            for rd in self.schedules:
                scheds.append({
                    "day":     rd["day_dd"].value,
                    "subject": rd["subj"].value,
                    "start":   rd["start"].value,
                    "end":     rd["end"].value,
                })

            personal = {
                "first_name": self.first_name.value,
                "last_name":  self.last_name.value,
                "middle_name":self.middle_name.value,
                "birthdate":  self.birthdate.value,
                "gender":     self.gender.value,
                "address":    self.address.value,
                "phone":      self.phone.value,
                "email":      self.email.value,
                "password":   self.password.value,
            }
            academic = {
                "course":     self.course.value,
                "block":      self.block.value,
                "year_level": self.year_level.value,
            }
            guardian = {
                "guardian_name":     self.guardian_name.value,
                "guardian_relation": self.guardian_relation.value,
                "guardian_phone":    self.guardian_phone.value,
            }

            ok, result = RegisterController.register_student(personal, academic, guardian, scheds)
            if not ok:
                snack(self.page, result, error=True)
                return

            # Save photo
            if self.photo_path and os.path.exists(self.photo_path):
                from models import StudentModel
                ext = os.path.splitext(self.photo_path)[1] or ".jpg"
                dst = os.path.join(UPLOADS_DIR, f"{result}{ext}")
                shutil.copy2(self.photo_path, dst)
                StudentModel.update_photo(result, dst)

            _show_registration_success(self.page, self.nav, result, "student")

        return ft.Column([
            card(ft.Column([
                ft.Row([
                    heading("Class Schedule", size=18),
                    primary_btn("+ Add Row", on_click=add_row,
                                icon=ft.Icons.ADD),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                subheading("Add your subjects and class times", size=13),
                ft.Container(height=12),
                sched_list,
            ], spacing=8)),
            ft.Container(height=16),
            self._nav_row(
                on_back=lambda _: self._go_step(3),
                on_next=submit,
                next_label="Submit Registration",
                next_icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
            ),
            ft.Container(height=24),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

    def _go_step(self, step: int):
        self.step = step
        if self.step_content.current:
            self.step_content.current.content = self._render_step()
            self.step_content.current.update()
        if self.step_indicator.current:
            self.step_indicator.current.controls = self._step_indicators().controls
            self.step_indicator.current.update()


# ═══════════════════════════════════════════════════════════════════════════════
#  FACULTY FORM
# ═══════════════════════════════════════════════════════════════════════════════
class _FacultyForm:
    def __init__(self, page: ft.Page, nav: dict):
        self.page = page
        self.nav  = nav
        self.step = 0
        self.photo_path = None
        self._build_fields()

    def _build_fields(self):
        tf = text_field
        self.first_name  = tf("First Name *",  icon=ft.Icons.PERSON_OUTLINE)
        self.last_name   = tf("Last Name *",   icon=ft.Icons.PERSON_OUTLINE)
        self.middle_name = tf("Middle Name",   icon=ft.Icons.PERSON_OUTLINE)
        self.birthdate   = tf("Birthdate",     "YYYY-MM-DD", icon=ft.Icons.CAKE_OUTLINED)
        self.gender      = dropdown("Gender", ["Male", "Female", "Other"])
        self.address     = tf("Address",       icon=ft.Icons.HOME_OUTLINED)
        self.phone       = tf("Phone Number",  icon=ft.Icons.PHONE_OUTLINED)
        self.email       = tf("Email Address", icon=ft.Icons.EMAIL_OUTLINED)
        self.password    = tf("Password *",    password=True, can_reveal=True, icon=ft.Icons.LOCK_OUTLINE)
        self.confirm_pw  = tf("Confirm Password *", password=True, can_reveal=True, icon=ft.Icons.LOCK_OUTLINE)
        self.department  = dropdown("Department", ["CCS", "CEA", "CBA", "CTE", "CN", "CAS", "Other"])
        self.position    = dropdown("Position", ["Professor", "Associate Professor", "Assistant Professor",
                                                  "Instructor", "Lecturer", "Department Head", "Other"])
        self.schedules = []

    def build(self) -> ft.Control:
        self.step_indicator = ft.Ref[ft.Row]()
        self.step_content   = ft.Ref[ft.Container]()

        return ft.Container(
            content=ft.Column([
                ft.Container(height=16),
                self._step_indicators(),
                ft.Container(height=16),
                ft.Container(
                    ref=self.step_content,
                    content=self._render_step(),
                    expand=True,
                ),
            ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=0),
            padding=ft.Padding.symmetric(horizontal=24, vertical=8),
            expand=True,
        )

    def _render_steps(self) -> ft.Control:
        return ft.Column([
            ft.Container(height=16),
            self._step_indicators(),
            ft.Container(height=16),
            self._render_step(),
        ], expand=True, scroll=ft.ScrollMode.AUTO, spacing=0)

    def _step_indicators(self) -> ft.Row:
        steps = ["Personal Info", "Photo", "Employment", "Schedule"]
        items = []
        for i, s in enumerate(steps):
            active  = i == self.step
            done    = i < self.step
            color   = ACCENT if done else (PRIMARY if active else BORDER)
            bgcolor = color if (active or done) else SURFACE
            items.append(ft.Column([
                ft.Container(
                    content=ft.Icon(ft.Icons.CHECK, size=14, color=ft.Colors.WHITE)
                             if done else ft.Text(str(i+1), size=12,
                             color=ft.Colors.WHITE if active else TEXT_MUTED,
                             weight=ft.FontWeight.BOLD),
                    width=30, height=30, border_radius=15,
                    bgcolor=bgcolor, border=ft.Border.all(2, color),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Text(s, size=10, color=PRIMARY if active else TEXT_MUTED,
                        text_align=ft.TextAlign.CENTER),
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=4))
            if i < len(steps) - 1:
                items.append(ft.Container(
                    ft.Divider(color=ACCENT if done else BORDER, height=2),
                    expand=True, margin=ft.Margin(bottom=16),
                ))
        return ft.Row(items, alignment=ft.MainAxisAlignment.CENTER,
                      vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _render_step(self) -> ft.Control:
        if self.step == 0:
            return self._step_personal()
        elif self.step == 1:
            return self._step_photo()
        elif self.step == 2:
            return self._step_employment()
        elif self.step == 3:
            return self._step_schedule()
        return ft.Container()

    def _nav_row(self, on_back=None, on_next=None, next_label="Next",
                 next_icon=ft.Icons.ARROW_FORWARD_IOS) -> ft.Row:
        return ft.Row([
            outline_btn("Back", on_click=on_back, icon=ft.Icons.ARROW_BACK_IOS_NEW)
            if on_back else ft.Container(),
            primary_btn(next_label, on_click=on_next, icon=next_icon),
        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN)

    def _step_personal(self) -> ft.Control:
        def next_step(e):
            if not self.first_name.value or not self.last_name.value:
                snack(self.page, "First and last name are required.", error=True)
                return
            if not self.password.value:
                snack(self.page, "Password is required.", error=True)
                return
            if self.password.value != self.confirm_pw.value:
                snack(self.page, "Passwords do not match.", error=True)
                return
            self._go_step(1)

        return ft.Column([
            card(ft.Column([
                heading("Personal Information", size=18),
                ft.Container(height=16),
                ft.Row([self.first_name, self.last_name], spacing=12),
                self.middle_name,
                ft.Row([self.birthdate, self.gender], spacing=12),
                self.address,
                ft.Row([self.phone, self.email], spacing=12),
                ft.Container(height=8),
                divider("Account Credentials"),
                ft.Container(height=8),
                ft.Row([self.password, self.confirm_pw], spacing=12),
            ], spacing=12)),
            ft.Container(height=16),
            self._nav_row(on_back=lambda _: self.nav["login"](), on_next=next_step),
            ft.Container(height=24),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

    def _step_photo(self) -> ft.Control:
        preview_container = ft.Container(
            content=_photo_placeholder(),
            width=160, height=160,
            border_radius=80,
            bgcolor=SURFACE_ALT,
            border=ft.Border.all(3, BORDER),
            clip_behavior=ft.ClipBehavior.HARD_EDGE,
            alignment=ft.Alignment(0, 0),
        )

        async def pick_photo(_):
            files = await ft.FilePicker().pick_files(
                allowed_extensions=["jpg", "jpeg", "png", "webp"],
                dialog_title="Select Profile Photo",
            )
            if files:
                self._on_photo_picked(files, preview_container)

        def next_step(e):
            self._go_step(2)

        return ft.Column([
            card(ft.Column([
                heading("Profile Photo", size=18),
                subheading("Upload a clear faculty ID photo (optional)", size=13),
                ft.Container(height=24),
                ft.Row([
                    ft.Column([
                        preview_container,
                        ft.Container(height=16),
                        primary_btn(
                            "Choose Photo",
                            icon=ft.Icons.UPLOAD_FILE,
                            on_click=pick_photo,
                        ),
                    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),
                    ft.Container(width=32),
                    ft.Column([
                        ft.Text("Photo Guidelines:", size=14,
                                weight=ft.FontWeight.W_600, color=TEXT_DARK),
                        ft.Container(height=8),
                        *[_guideline(t) for t in [
                            "Use a recent, clear photo",
                            "Face must be visible",
                            "Accepted: JPG, PNG, WEBP",
                        ]],
                    ], spacing=6, expand=True),
                ], vertical_alignment=ft.CrossAxisAlignment.START),
            ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.CENTER)),
            ft.Container(height=16),
            self._nav_row(on_back=lambda _: self._go_step(0), on_next=next_step),
            ft.Container(height=24),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

    def _on_photo_picked(self, files, container: ft.Container):
        if files and len(files) > 0:
            src = files[0].path
            if src and os.path.exists(src):
                self.photo_path = src
                container.content = ft.Image(src=src, width=160, height=160, fit=ft.BoxFit.COVER)
                self.page.update()

    def _step_employment(self) -> ft.Control:
        def next_step(e):
            self._go_step(3)
        return ft.Column([
            card(ft.Column([
                heading("Employment Information", size=18),
                ft.Container(height=16),
                self.department,
                self.position,
            ], spacing=12)),
            ft.Container(height=16),
            self._nav_row(on_back=lambda _: self._go_step(1), on_next=next_step),
            ft.Container(height=24),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

    def _step_schedule(self) -> ft.Control:
        sched_list = ft.Column(spacing=8)

        def add_row(e=None):
            day   = dropdown("Day", ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"])
            subj  = text_field("Subject")
            start = time_dropdown("Start Time")
            end   = time_dropdown("End Time")
            end.value = "9:00 AM"
            room  = text_field("Room")
            rd    = {"day_dd": day, "subj": subj, "start": start, "end": end, "room": room}
            self.schedules.append(rd)

            def remove(e, r=rd, rc=None):
                self.schedules.remove(r)
                sched_list.controls.remove(row_ctrl)
                self.page.update()

            row_ctrl = ft.Container(
                content=ft.Column([
                    ft.Row([day, subj, room], spacing=8),
                    ft.Row([start, end,
                            ft.IconButton(ft.Icons.DELETE_OUTLINE, icon_color=ERROR_COLOR,
                                          on_click=remove, tooltip="Remove")],
                           spacing=8),
                ], spacing=6),
                bgcolor=SURFACE_ALT, border_radius=12, padding=12,
                border=ft.Border.all(1, BORDER),
            )
            sched_list.controls.append(row_ctrl)
            self.page.update()

        add_row()

        def submit(e):
            scheds = [{"day": rd["day_dd"].value, "subject": rd["subj"].value,
                       "start": rd["start"].value, "end": rd["end"].value}
                      for rd in self.schedules]
            personal = {
                "first_name": self.first_name.value, "last_name": self.last_name.value,
                "middle_name": self.middle_name.value, "birthdate": self.birthdate.value,
                "gender": self.gender.value, "address": self.address.value,
                "phone": self.phone.value, "email": self.email.value,
                "password": self.password.value,
            }
            employment = {"department": self.department.value, "position": self.position.value}

            ok, result = RegisterController.register_faculty(personal, employment, scheds)
            if not ok:
                snack(self.page, result, error=True)
                return

            if self.photo_path and os.path.exists(self.photo_path):
                from models import FacultyModel
                ext = os.path.splitext(self.photo_path)[1] or ".jpg"
                dst = os.path.join(UPLOADS_DIR, f"{result}{ext}")
                shutil.copy2(self.photo_path, dst)
                FacultyModel.update_photo(result, dst)

            _show_registration_success(self.page, self.nav, result, "faculty")

        return ft.Column([
            card(ft.Column([
                ft.Row([
                    heading("Teaching Schedule", size=18),
                    primary_btn("+ Add Row", on_click=add_row, icon=ft.Icons.ADD),
                ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN),
                subheading("Add your subjects and class times", size=13),
                ft.Container(height=12),
                sched_list,
            ], spacing=8)),
            ft.Container(height=16),
            self._nav_row(
                on_back=lambda _: self._go_step(2),
                on_next=submit,
                next_label="Submit Registration",
                next_icon=ft.Icons.CHECK_CIRCLE_OUTLINE,
            ),
            ft.Container(height=24),
        ], spacing=0, scroll=ft.ScrollMode.AUTO)

    def _go_step(self, step: int):
        self.step = step
        if self.step_content.current:
            self.step_content.current.content = self._render_step()
            self.step_content.current.update()
        if self.step_indicator.current:
            self.step_indicator.current.controls = self._step_indicators().controls
            self.step_indicator.current.update()


# ── Helpers ───────────────────────────────────────────────────────────────────
def _photo_placeholder() -> ft.Column:
    return ft.Column([
        ft.Icon(ft.Icons.ADD_A_PHOTO_OUTLINED, size=40, color=TEXT_MUTED),
        ft.Text("No photo", size=12, color=TEXT_MUTED),
    ], horizontal_alignment=ft.CrossAxisAlignment.CENTER,
       alignment=ft.MainAxisAlignment.CENTER, spacing=8)


def _guideline(text: str) -> ft.Row:
    return ft.Row([
        ft.Icon(ft.Icons.CHECK_CIRCLE_OUTLINE, size=14, color=SUCCESS),
        ft.Text(text, size=13, color=TEXT_MUTED, expand=True),
    ], spacing=8)