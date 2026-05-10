"""
views/theme.py
Shared design tokens and reusable UI components for Campus SIS.
"""

import flet as ft

# ── Palette ───────────────────────────────────────────────────────────────────
PRIMARY       = "#1E3A5F"      # deep navy
PRIMARY_LIGHT = "#2A5298"      # medium blue
ACCENT        = "#E8A020"      # gold/amber
ACCENT_LIGHT  = "#F5C842"
SURFACE       = "#FFFFFF"
SURFACE_ALT   = "#F4F7FC"
BORDER        = "#D0D9E8"
TEXT_DARK     = "#1A1A2E"
TEXT_MUTED    = "#6B7A99"
SUCCESS       = "#27AE60"
ERROR_COLOR   = "#E74C3C"
WARNING       = "#F39C12"
SIDEBAR_BG    = "#1E3A5F"
SIDEBAR_HOVER = "#2A5298"


def page_bg(page: ft.Page):
    page.bgcolor = SURFACE_ALT


# ── Reusable widgets ──────────────────────────────────────────────────────────

def heading(text: str, size: int = 22, color: str = TEXT_DARK) -> ft.Text:
    return ft.Text(text, size=size, weight=ft.FontWeight.BOLD, color=color)


def subheading(text: str, size: int = 14, color: str = TEXT_MUTED) -> ft.Text:
    return ft.Text(text, size=size, color=color)


def card(content, padding: int = 24, shadow: bool = True) -> ft.Container:
    return ft.Container(
        content=content,
        bgcolor=SURFACE,
        border_radius=16,
        padding=padding,
        shadow=ft.BoxShadow(
            spread_radius=0,
            blur_radius=16,
            color=ft.Colors.with_opacity(0.08, ft.Colors.BLACK),
            offset=ft.Offset(0, 4),
        ) if shadow else None,
    )


def primary_btn(text: str, on_click=None, icon=None, width: int = None,
                bgcolor: str = PRIMARY, color: str = SURFACE) -> ft.Button:
    return ft.Button(
        content=text,
        icon=icon,
        on_click=on_click,
        width=width,
        bgcolor=bgcolor,
        color=color,
        style=ft.ButtonStyle(
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding.symmetric(horizontal=24, vertical=14),
            elevation=2,
            overlay_color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        ),
    )


def outline_btn(text: str, on_click=None, icon=None, color: str = PRIMARY) -> ft.OutlinedButton:
    return ft.OutlinedButton(
        content=text,
        icon=icon,
        on_click=on_click,
        style=ft.ButtonStyle(
            color=color,
            side=ft.BorderSide(color=color, width=1.5),
            shape=ft.RoundedRectangleBorder(radius=10),
            padding=ft.Padding.symmetric(horizontal=20, vertical=12),
        ),
    )


def text_field(label: str, hint: str = "", password: bool = False,
               can_reveal: bool = False, icon=None, width: int = None,
               multiline: bool = False, expand: bool = False) -> ft.TextField:
    return ft.TextField(
        label=label,
        hint_text=hint,
        password=password,
        can_reveal_password=can_reveal,
        prefix_icon=icon,
        width=width,
        expand=expand,
        multiline=multiline,
        min_lines=1 if not multiline else 3,
        max_lines=1 if not multiline else 5,
        border_radius=10,
        border_color=BORDER,
        focused_border_color=PRIMARY_LIGHT,
        label_style=ft.TextStyle(color=TEXT_MUTED, size=13),
        text_style=ft.TextStyle(color=TEXT_DARK, size=14),
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=14),
        filled=True,
        fill_color=SURFACE_ALT,
    )


def dropdown(label: str, options: list[str], width: int = None) -> ft.Dropdown:
    return ft.Dropdown(
        label=label,
        options=[ft.dropdown.Option(o) for o in options],
        width=width,
        border_radius=10,
        border_color=BORDER,
        focused_border_color=PRIMARY_LIGHT,
        label_style=ft.TextStyle(color=TEXT_MUTED, size=13),
        text_style=ft.TextStyle(color=TEXT_DARK, size=14),
        filled=True,
        fill_color=SURFACE_ALT,
        content_padding=ft.Padding.symmetric(horizontal=16, vertical=4),
    )


def divider(label: str = None) -> ft.Control:
    if label:
        return ft.Row([
            ft.Container(ft.Divider(color=BORDER), expand=True),
            ft.Text(f"  {label}  ", color=TEXT_MUTED, size=12),
            ft.Container(ft.Divider(color=BORDER), expand=True),
        ], vertical_alignment=ft.CrossAxisAlignment.CENTER)
    return ft.Divider(color=BORDER, height=1)


def snack(page: ft.Page, msg: str, error: bool = False):
    sb = ft.SnackBar(
        content=ft.Text(msg, color=ft.Colors.WHITE),
        bgcolor=ERROR_COLOR if error else SUCCESS,
        duration=3000,
        open=True,
    )
    page.overlay.append(sb)
    page.update()


def avatar_circle(photo: str, size: int = 80) -> ft.Container:
    """Display a circular avatar from file path or initials fallback."""
    if photo and __import__("os").path.exists(photo):
        content = ft.Image(
            src=photo,
            width=size, height=size,
            fit=ft.BoxFit.COVER,
            border_radius=ft.BorderRadius.all(size // 2),
        )
    else:
        content = ft.Icon(ft.Icons.PERSON, size=size * 0.55, color=ft.Colors.WHITE)

    return ft.Container(
        content=content,
        width=size, height=size,
        border_radius=ft.BorderRadius.all(size // 2),
        bgcolor=PRIMARY_LIGHT,
        clip_behavior=ft.ClipBehavior.HARD_EDGE,
        border=ft.Border.all(3, ACCENT),
    )


def sidebar_item(icon, label: str, on_click=None, active: bool = False) -> ft.Container:
    return ft.Container(
        content=ft.Row([
            ft.Icon(icon, size=20,
                    color=ACCENT if active else ft.Colors.with_opacity(0.7, ft.Colors.WHITE)),
            ft.Text(label, size=14,
                    color=ACCENT if active else ft.Colors.with_opacity(0.85, ft.Colors.WHITE),
                    weight=ft.FontWeight.W_600 if active else ft.FontWeight.NORMAL),
        ], spacing=12),
        padding=ft.Padding.symmetric(horizontal=20, vertical=14),
        border_radius=10,
        ink=True,
        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE) if active else ft.Colors.TRANSPARENT,
        on_click=on_click,
        on_hover=lambda e: setattr(e.control, "bgcolor",
            ft.Colors.with_opacity(0.1, ft.Colors.WHITE) if e.data == "true" and not active
            else (ft.Colors.with_opacity(0.15, ft.Colors.WHITE) if active else ft.Colors.TRANSPARENT))
        if not active else None,
        animate=ft.Animation(150, ft.AnimationCurve.EASE_OUT),
    )


def stat_card(icon, label: str, value: str, color: str = PRIMARY) -> ft.Container:
    return ft.Container(
        content=ft.Column([
            ft.Container(
                content=ft.Icon(icon, size=28, color=color),
                width=52, height=52,
                border_radius=14,
                bgcolor=ft.Colors.with_opacity(0.1, color),
                alignment=ft.Alignment(0, 0),
            ),
            ft.Text(value, size=26, weight=ft.FontWeight.BOLD, color=TEXT_DARK),
            ft.Text(label, size=12, color=TEXT_MUTED),
        ], spacing=8, horizontal_alignment=ft.CrossAxisAlignment.START),
        bgcolor=SURFACE,
        border_radius=16,
        padding=20,
        expand=True,
        shadow=ft.BoxShadow(
            blur_radius=12,
            color=ft.Colors.with_opacity(0.07, ft.Colors.BLACK),
            offset=ft.Offset(0, 3),
        ),
    )