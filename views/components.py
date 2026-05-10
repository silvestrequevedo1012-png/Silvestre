"""
views/components.py
Reusable Flet UI widgets: cards, buttons, text fields, schedule builder, etc.
"""

import flet as ft
from utils import DAYS


# ── Palette ───────────────────────────────────────────────────────────────────
PRIMARY      = "#3F51B5"
PRIMARY_DARK = "#1A237E"
ACCENT       = "#FF6F00"
BG           = "#F0F4FF"
WHITE        = "#FFFFFF"
CARD_SHADOW  = "#18000000"
TEXT_MAIN    = "#212121"
TEXT_SUB     = "#616161"
SUCCESS      = "#2E7D32"
ERROR        = "#C62828"
WARN         = "#E65100"


# ── Typography ────────────────────────────────────────────────────────────────
def heading(text: str, size: int = 22, color: str = PRIMARY_DARK) -> ft.Text:
    return ft.Text(text, size=size, color=color, weight=ft.FontWeight.BOLD)


def subtext(text: str, size: int = 13, color: str = TEXT_SUB) -> ft.Text:
    return ft.Text(text, size=size, color=color)


def label_text(text: str) -> ft.Text:
    return ft.Text(text, size=14, weight=ft.FontWeight.W_600, color=TEXT_MAIN)


# ── Card ──────────────────────────────────────────────────────────────────────
def card(content: ft.Control, padding: int = 20,
         bgcolor: str = WHITE, width=None) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=bgcolor,
        border_radius=16,
        padding=padding,
        width=width,
        shadow=ft.BoxShadow(
            blur_radius=16, color=CARD_SHADOW, offset=ft.Offset(0, 4)
        ),
    )


# ── Buttons ───────────────────────────────────────────────────────────────────
def primary_btn(label: str, on_click, width: int = 280,
                bgcolor: str = PRIMARY, icon=None) -> ft.ElevatedButton:
    return ft.ElevatedButton(
        label, on_click=on_click, width=width, icon=icon,
        style=ft.ButtonStyle(
            bgcolor=bgcolor,
            color=WHITE,
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding.symmetric(vertical=14),
        ),
    )


def danger_btn(label: str, on_click, width: int = 140) -> ft.ElevatedButton:
    return primary_btn(label, on_click, width=width, bgcolor="#B71C1C")


def back_btn(on_click) -> ft.IconButton:
    return ft.IconButton(ft.Icons.ARROW_BACK, on_click=on_click,
                         icon_color=PRIMARY)


# ── Text Fields ───────────────────────────────────────────────────────────────
def text_field(label: str, password: bool = False,
               width: int = 280, hint: str = "") -> ft.TextField:
    return ft.TextField(
        label=label,
        password=password,
        can_reveal_password=password,
        hint_text=hint,
        width=width,
        border_radius=10,
        border_color=PRIMARY,
        focused_border_color=PRIMARY_DARK,
        bgcolor=WHITE,
        text_size=14,
    )


# ── Dropdown ──────────────────────────────────────────────────────────────────
def dropdown(label: str, options: list[str], width: int = 200,
             on_select=None) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        width=width,
        border_radius=10,
        options=[ft.dropdown.Option(o) for o in options],
        on_select=on_select,
    )


# ── Snackbar ─────────────────────────────────────────────────────────────────
def show_snack(page: ft.Page, message: str, color: str = "#323232"):
    sb = ft.SnackBar(
        ft.Text(message, color=WHITE),
        bgcolor=color,
        duration=ft.Duration(milliseconds=3500),
        open=True,
    )
    page.overlay.append(sb)
    page.update()


# ── Section divider with label ────────────────────────────────────────────────
def section_header(title: str) -> ft.Column:
    return ft.Column([
        ft.Divider(height=8, color="transparent"),
        ft.Container(
            ft.Text(title, size=13, weight=ft.FontWeight.W_700,
                    color=PRIMARY_DARK),
            bgcolor="#E8EAF6",
            padding=ft.Padding.symmetric(horizontal=12, vertical=6),
            border_radius=8,
        ),
    ], spacing=0)


# ── Schedule Builder ──────────────────────────────────────────────────────────
def schedule_builder(page: ft.Page, store: list, label: str = "Schedule") -> ft.Column:
    """
    Inline schedule row builder.
    Each row writes into a dict inside `store`.
    store is mutated in-place so the caller can read it on submit.
    """
    rows_col = ft.Column(spacing=6)

    def add_row(e=None):
        entry: dict = {"day": "", "subject": "", "start": "", "end": ""}
        store.append(entry)

        day_dd   = dropdown("Day", DAYS, width=120)
        subj_tf  = ft.TextField(label="Subject",      width=145, border_radius=8,
                                border_color=PRIMARY)
        start_tf = ft.TextField(label="Start HH:MM",  width=112, border_radius=8,
                                border_color=PRIMARY, hint_text="08:00")
        end_tf   = ft.TextField(label="End HH:MM",    width=112, border_radius=8,
                                border_color=PRIMARY, hint_text="10:00")

        def sync(_=None):
            entry["day"]     = day_dd.value   or ""
            entry["subject"] = subj_tf.value  or ""
            entry["start"]   = start_tf.value or ""
            entry["end"]     = end_tf.value   or ""

        day_dd.on_select    = sync
        subj_tf.on_change   = sync
        start_tf.on_change  = sync
        end_tf.on_change    = sync

        def remove(_):
            rows_col.controls.remove(row)
            store.remove(entry)
            page.update()

        row = ft.Row(
            [day_dd, subj_tf, start_tf, end_tf,
             ft.IconButton(ft.Icons.DELETE_OUTLINE,
                           on_click=remove, icon_color=ERROR)],
            wrap=True, spacing=6,
        )
        rows_col.controls.append(row)
        page.update()

    add_btn = ft.TextButton(
        f"＋ Add {label}",
        on_click=add_row,
        style=ft.ButtonStyle(color=PRIMARY),
    )
    return ft.Column([
        label_text(label),
        rows_col,
        add_btn,
    ], spacing=6)


# ── Data table helper ─────────────────────────────────────────────────────────
def data_table(columns: list[str], rows: list[ft.DataRow]) -> ft.DataTable:
    return ft.DataTable(
        columns=[
            ft.DataColumn(ft.Text(c, weight=ft.FontWeight.W_600, size=12))
            for c in columns
        ],
        rows=rows,
        border=ft.Border.all(1, "#E0E0E0"),
        border_radius=8,
        column_spacing=16,
        data_row_min_height=36,
    )


# ── Colored status chip ───────────────────────────────────────────────────────
def status_chip(text: str, color: str) -> ft.Container:
    return ft.Container(
        ft.Text(text, size=11, color=WHITE, weight=ft.FontWeight.W_600),
        bgcolor=color,
        border_radius=20,
        padding=ft.Padding.symmetric(horizontal=10, vertical=3),
    )


# ── Top app bar ───────────────────────────────────────────────────────────────
def app_bar(title: str, on_logout, icon=ft.Icons.SCHOOL) -> ft.Container:
    return ft.Container(
        ft.Row([
            ft.Icon(icon, color=WHITE, size=24),
            ft.Text(title, color=WHITE, size=17,
                    weight=ft.FontWeight.BOLD, expand=True),
            ft.TextButton("Logout", on_click=on_logout,
                          style=ft.ButtonStyle(color=WHITE)),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=PRIMARY,
        padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        shadow=ft.BoxShadow(blur_radius=6, color=CARD_SHADOW),
    )