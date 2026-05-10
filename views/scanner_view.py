"""
views/scanner_view.py
Entry/Exit scanner terminal with manual ID input + live camera QR scanner.

Camera scanning uses OpenCV's built-in QRCodeDetector in a background thread.
Install dependencies if not already present:
    pip install opencv-python
"""

import threading
import time
import flet as ft
from controllers import ScannerController
from models import LogModel
from views.theme import *


# ─────────────────────────────────────────────────────────────────────────────
# Camera QR scanner — runs in a daemon thread, opens an OpenCV window
# ─────────────────────────────────────────────────────────────────────────────

class CameraScanner:
    """
    Opens the default webcam in a background thread, decodes QR codes with
    cv2.QRCodeDetector (no extra DLLs needed on Windows), and calls on_result(id_str).

    A per-code cooldown prevents the same ID from firing repeatedly while the
    card stays in frame.

    on_close() is called whenever the camera thread exits — whether the user
    pressed Q/ESC or a QR scan triggered an auto-close.
    """
    COOLDOWN = 3.0  # seconds before the same code can trigger again

    def __init__(self, on_result, on_close=None):
        self.on_result   = on_result
        self.on_close    = on_close or (lambda: None)
        self._thread     = None
        self._stop_event = threading.Event()
        self._last_seen  = {}   # code -> timestamp of last fire
        self.running     = False
        self.error: str  = ""

    # ── Public API ────────────────────────────────────────────────────────────

    def start(self):
        if self._thread and self._thread.is_alive():
            return
        self._stop_event.clear()
        self.error   = ""
        self.running = True
        self._thread = threading.Thread(target=self._run, daemon=True)
        self._thread.start()

    def stop(self):
        self._stop_event.set()
        # running is set to False inside _run when it exits

    # ── Internal ──────────────────────────────────────────────────────────────

    def _run(self):
        try:
            import cv2
            import numpy as np
        except ImportError as exc:
            self.error   = str(exc)
            self.running = False
            return

        cap = cv2.VideoCapture(0)
        if not cap.isOpened():
            self.error   = "Could not open camera (index 0)."
            self.running = False
            return

        # Prefer WeChatQRCode (bundled in opencv-contrib) — far more reliable
        # than QRCodeDetector for real-world, low-light, angled QR codes.
        try:
            qr_detector  = cv2.wechat_qrcode_WeChatQRCode()
            use_wechat   = True
        except Exception:
            qr_detector  = cv2.QRCodeDetector()
            use_wechat   = False

        win_name = "Campus SIS — QR Scanner  |  press Q or ESC to close"
        cv2.namedWindow(win_name, cv2.WINDOW_NORMAL)
        cv2.resizeWindow(win_name, 640, 480)

        def _try_decode(img):
            """Return decoded string or '' — tries full frame then 2× upscale."""
            if use_wechat:
                texts, _ = qr_detector.detectAndDecode(img)
                if texts:
                    return texts[0].strip()
            else:
                decoded, _, _ = qr_detector.detectAndDecode(img)
                if decoded:
                    return decoded.strip()
            # Retry on a sharper, upscaled copy (helps with small / blurry QR codes)
            big = cv2.resize(img, (img.shape[1] * 2, img.shape[0] * 2),
                             interpolation=cv2.INTER_LINEAR)
            if use_wechat:
                texts, _ = qr_detector.detectAndDecode(big)
                if texts:
                    return texts[0].strip()
            else:
                decoded, _, _ = qr_detector.detectAndDecode(big)
                if decoded:
                    return decoded.strip()
            return ""

        while not self._stop_event.is_set():
            ret, frame = cap.read()
            if not ret:
                break

            now  = time.time()
            data = _try_decode(frame)

            if data:
                if now - self._last_seen.get(data, 0) >= self.COOLDOWN:
                    self._last_seen[data] = now
                    self.on_result(data)

                # Green border flash so the operator sees a successful read
                h, w = frame.shape[:2]
                cv2.rectangle(frame, (0, 0), (w - 1, h - 1), (0, 230, 118), 6)
                cv2.putText(frame, f"READ: {data[:30]}", (12, 38),
                            cv2.FONT_HERSHEY_SIMPLEX, 0.9, (0, 230, 118), 2)

            # Overlay hint text
            cv2.putText(
                frame, "Point QR code at camera  |  Q / ESC = close",
                (10, frame.shape[0] - 12),
                cv2.FONT_HERSHEY_SIMPLEX, 0.5, (200, 200, 200), 1,
            )

            cv2.imshow(win_name, frame)

            key = cv2.waitKey(1) & 0xFF
            if key in (27, ord("q"), ord("Q")):
                break

        cap.release()
        cv2.destroyAllWindows()
        self.running = False
        self.on_close()   # notify UI the camera window has closed



# ─────────────────────────────────────────────────────────────────────────────
# Main scanner view
# ─────────────────────────────────────────────────────────────────────────────

def scanner_view(page: ft.Page, nav: dict):
    page.clean()
    page.bgcolor = PRIMARY
    page.padding = 0
    page.scroll  = None

    camera      = CameraScanner(on_result=_noop, on_close=_noop)   # real callbacks set below
    log_entries = []

    def _rebuild_log(new_entries):
        """Apply new log entries to the sidebar. Must be called from main thread."""
        log_entries.clear()
        log_entries.extend(new_entries)
        if log_col.current:
            if log_entries:
                log_col.current.controls = [_log_item(e) for e in log_entries]
            else:
                log_col.current.controls = [
                    ft.Container(
                        content=ft.Text(
                            "No scans yet", size=12,
                            color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
                            text_align=ft.TextAlign.CENTER,
                        ),
                        alignment=ft.Alignment(0, 0),
                        padding=ft.Padding.symmetric(vertical=24),
                    )
                ]

    # Flet refs
    result_card    = ft.Ref[ft.Container]()
    log_col        = ft.Ref[ft.Column]()
    cam_btn        = ft.Ref[ft.Button]()
    cam_status_row = ft.Ref[ft.Row]()

    # ── Helpers ───────────────────────────────────────────────────────────────

    def _time_fmt(ts: str) -> str:
        import datetime as _dt
        try:
            return _dt.datetime.strptime(ts, "%Y-%m-%d %H:%M:%S").strftime("%I:%M %p")
        except Exception:
            return ts

    def _role_label(role: str) -> str:
        return "Teacher" if role == "faculty" else "Student"

    def _info_row(icon, label, value, value_color=None):
        return ft.Row([
            ft.Icon(icon, size=16, color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE)),
            ft.Text(label + ":", size=13,
                    color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE), width=80),
            ft.Text(value, size=13, weight=ft.FontWeight.W_600,
                    color=value_color or ft.Colors.WHITE, expand=True),
        ], spacing=8, vertical_alignment=ft.CrossAxisAlignment.CENTER)

    def _log_item(entry: dict) -> ft.Container:
        action = entry["action"]
        badge  = entry["badge"]
        name   = entry["name"]
        ts     = entry["time"]
        accent = (WARNING if badge == "LATE" else SUCCESS) if action == "ENTRY" else PRIMARY_LIGHT
        icon_n = ft.Icons.LOGIN if action == "ENTRY" else ft.Icons.LOGOUT

        return ft.Container(
            content=ft.Row([
                ft.Container(
                    content=ft.Icon(icon_n, size=14, color=accent),
                    width=28, height=28, border_radius=14,
                    bgcolor=ft.Colors.with_opacity(0.18, accent),
                    alignment=ft.Alignment(0, 0),
                ),
                ft.Column([
                    ft.Text(name, size=11, weight=ft.FontWeight.W_600,
                            color=ft.Colors.WHITE, no_wrap=True),
                    ft.Text(_time_fmt(ts), size=10,
                            color=ft.Colors.with_opacity(0.45, ft.Colors.WHITE)),
                ], spacing=1, expand=True),
                ft.Container(
                    content=ft.Text(badge, size=9, color=ft.Colors.WHITE,
                                    weight=ft.FontWeight.W_700),
                    bgcolor=accent, border_radius=10,
                    padding=ft.Padding.symmetric(horizontal=6, vertical=2),
                ),
            ], spacing=6, vertical_alignment=ft.CrossAxisAlignment.CENTER),
            bgcolor=ft.Colors.with_opacity(0.07, ft.Colors.WHITE),
            border_radius=10,
            padding=ft.Padding.symmetric(horizontal=8, vertical=6),
            border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
        )

    # ── Core scan processor ───────────────────────────────────────────────────

    def _process_scan(id_val: str):
        """Calls ScannerController, updates result card and session log."""
        if not id_val:
            return

        result = ScannerController.scan(id_val)

        if result["success"]:
            action = result["action"]
            status = result["status"]
            name   = result.get("name", "")
            role   = result.get("role", "")
            ts     = result.get("time", "")
            subj   = result.get("subject", "")

            if action == "ENTRY":
                if status == "LATE":
                    color, title, status_label = WARNING, "ACCESS GRANTED", "LATE"
                elif status == "PRESENT":
                    color, title, status_label = SUCCESS, "ACCESS GRANTED", "PRESENT"
                else:
                    color, title, status_label = SUCCESS, "ACCESS GRANTED", "ON TIME"
                time_label  = "Time In"
                sched_label = subj or "No Schedule Today"
                action_icon = ft.Icons.LOGIN
            else:
                color, title, status_label = PRIMARY_LIGHT, "EXIT RECORDED", "OK"
                time_label  = "Time Out"
                sched_label = ""
                action_icon = ft.Icons.LOGOUT

            rows = [
                _info_row(ft.Icons.PERSON,       "Name",     name),
                _info_row(ft.Icons.BADGE,         "Role",     _role_label(role)),
                _info_row(ft.Icons.ACCESS_TIME,   time_label, _time_fmt(ts)),
            ]
            if action == "ENTRY":
                rows.append(_info_row(
                    ft.Icons.BOOK_OUTLINED, "Schedule", sched_label,
                    value_color=WARNING if status == "LATE" else None,
                ))

            card_content = ft.Column([
                ft.Row([
                    ft.Icon(action_icon, size=22, color=color),
                    ft.Text(title, size=20, weight=ft.FontWeight.BOLD, color=color),
                    ft.Container(expand=True),
                    ft.Container(
                        content=ft.Text(status_label, size=11,
                                        color=ft.Colors.WHITE, weight=ft.FontWeight.W_700),
                        bgcolor=color, border_radius=20,
                        padding=ft.Padding.symmetric(horizontal=12, vertical=4),
                    ),
                ], vertical_alignment=ft.CrossAxisAlignment.CENTER),
                ft.Divider(color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE), height=20),
                *rows,
            ], spacing=10)

            log_entries.insert(0, {
                "action": action, "badge": status_label, "name": name, "time": ts,
            })
            if log_col.current:
                log_col.current.controls = [_log_item(e) for e in log_entries]

        else:
            color = ERROR_COLOR
            card_content = ft.Column([
                ft.Row([
                    ft.Icon(ft.Icons.BLOCK, size=22, color=color),
                    ft.Text("ACCESS DENIED", size=20,
                            weight=ft.FontWeight.BOLD, color=color),
                ], spacing=8),
                ft.Divider(color=ft.Colors.with_opacity(0.15, ft.Colors.WHITE), height=20),
                ft.Text(result["message"], size=14, color=ft.Colors.WHITE,
                        text_align=ft.TextAlign.CENTER),
            ], spacing=10, horizontal_alignment=ft.CrossAxisAlignment.CENTER)

        result_card.current.bgcolor = ft.Colors.with_opacity(0.12, color)
        result_card.current.border  = ft.Border.all(2, ft.Colors.with_opacity(0.5, color))
        result_card.current.content = card_content
        page.update()

    # ── Manual submit ─────────────────────────────────────────────────────────

    id_field = ft.TextField(
        hint_text="Scan or type ID number...",
        text_align=ft.TextAlign.CENTER,
        text_size=22,
        border_radius=14,
        border_color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
        focused_border_color=ACCENT,
        bgcolor=ft.Colors.with_opacity(0.1, ft.Colors.WHITE),
        color=ft.Colors.WHITE,
        hint_style=ft.TextStyle(color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
        cursor_color=ACCENT,
        autofocus=True,
        width=380,
    )

    def do_scan(e=None):
        id_val = id_field.value.strip()
        id_field.value = ""
        page.update()
        _process_scan(id_val)

    id_field.on_submit = do_scan

    # ── Camera callbacks (called from background thread) ─────────────────────

    def _on_camera_qr(code: str):
        """QR decoded — runs on the camera background thread.
        Sequence: stop camera → process scan (writes DB) → reload logs → repaint.
        Everything in order so the log always reflects the completed scan."""
        camera.stop()

        # 1. Process the scan (saves to DB)
        _process_scan(code)

        # 2. Reload all logs from DB now that the scan is committed
        try:
            db_logs = LogModel.get_all()
        except Exception as exc:
            print(f"[_on_camera_qr] DB error: {exc}")
            db_logs = []

        new_entries = []
        for row in db_logs[:50]:
            action = row.get("action", "")
            status = row.get("status", "OK")
            if action == "EXIT":
                badge = "EXIT"
            elif status == "LATE":
                badge = "LATE"
            elif status == "PRESENT":
                badge = "PRESENT"
            else:
                badge = status or "OK"
            new_entries.append({
                "action": action,
                "badge":  badge,
                "name":   row.get("full_name", ""),
                "time":   row.get("timestamp", ""),
            })

        # 3. Update UI — result card + log sidebar + button state — single repaint
        _refresh_cam_ui()
        _rebuild_log(new_entries)
        page.update()

    def _on_camera_close():
        """Camera closed by Q/ESC (no scan). Just reset the button UI."""
        _refresh_cam_ui()
        page.update()

    camera.on_result = _on_camera_qr    # wire up now that closures exist
    camera.on_close  = _on_camera_close

    # ── Camera toggle ─────────────────────────────────────────────────────────

    _CAM_BTN_ON = ft.ButtonStyle(
        bgcolor=ERROR_COLOR,
        color=ft.Colors.WHITE,
        shape=ft.RoundedRectangleBorder(radius=12),
        padding=ft.Padding.symmetric(vertical=14),
        elevation=4,
    )
    _CAM_BTN_OFF = ft.ButtonStyle(
        bgcolor=ft.Colors.with_opacity(0.15, ft.Colors.WHITE),
        color=ft.Colors.WHITE,
        shape=ft.RoundedRectangleBorder(radius=12),
        padding=ft.Padding.symmetric(vertical=14),
        elevation=0,
        side=ft.BorderSide(1.5, ft.Colors.with_opacity(0.35, ft.Colors.WHITE)),
    )

    def _refresh_cam_ui():
        if cam_btn.current is None:
            return
        if camera.running:
            cam_btn.current.content = "Stop Camera"
            cam_btn.current.icon  = ft.Icons.VIDEOCAM_OFF
            cam_btn.current.style = _CAM_BTN_ON
            if cam_status_row.current:
                cam_status_row.current.visible = True
        else:
            cam_btn.current.content = "Open Camera Scanner"
            cam_btn.current.icon  = ft.Icons.VIDEOCAM
            cam_btn.current.style = _CAM_BTN_OFF
            if cam_status_row.current:
                cam_status_row.current.visible = False
        page.update()

    def _toggle_camera(e):
        if camera.running:
            camera.stop()
            time.sleep(0.2)
            _refresh_cam_ui()
        else:
            camera.start()
            time.sleep(0.45)          # wait for startup errors to surface
            if camera.error:
                _show_cam_error(camera.error)
                camera.running = False
            _refresh_cam_ui()

    def _show_cam_error(msg: str):
        if "No module named" in msg or "ImportError" in msg:
            friendly = "Missing package. Run:  pip install opencv-python"
        elif "Could not open camera" in msg:
            friendly = "Camera not found. Make sure a webcam is connected."
        else:
            friendly = f"Camera error: {msg}"
        sb = ft.SnackBar(
            content=ft.Text(friendly, color=ft.Colors.WHITE),
            bgcolor=ERROR_COLOR, duration=6000, open=True,
        )
        page.overlay.append(sb)
        page.update()

    page.on_close = lambda _: camera.stop()

    # ── Camera button widgets ─────────────────────────────────────────────────

    camera_btn = ft.Button(
        ref=cam_btn,
        content="Open Camera Scanner",
        icon=ft.Icons.VIDEOCAM,
        on_click=_toggle_camera,
        width=230,
        style=_CAM_BTN_OFF,
    )

    cam_active_row = ft.Row(
        ref=cam_status_row,
        controls=[
            ft.Icon(ft.Icons.FIBER_MANUAL_RECORD, size=10, color=SUCCESS),
            ft.Text(
                "Camera active — hold QR code up to the camera window",
                size=11,
                color=ft.Colors.with_opacity(0.72, ft.Colors.WHITE),
            ),
        ],
        spacing=6,
        visible=False,
        vertical_alignment=ft.CrossAxisAlignment.CENTER,
    )

    # ── Right sidebar: session log ────────────────────────────────────────────

    log_panel = ft.Container(
        content=ft.Column([
            ft.Row([
                ft.Icon(ft.Icons.HISTORY, size=15,
                        color=ft.Colors.with_opacity(0.55, ft.Colors.WHITE)),
                ft.Text("Session Log", size=13, weight=ft.FontWeight.W_600,
                        color=ft.Colors.with_opacity(0.65, ft.Colors.WHITE)),
            ], spacing=6),
            ft.Container(
                content=ft.Divider(color=ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
                padding=ft.Padding.symmetric(vertical=6),
            ),
            ft.Column(
                ref=log_col,
                controls=[
                    ft.Container(
                        content=ft.Text("No scans yet", size=12,
                                        color=ft.Colors.with_opacity(0.3, ft.Colors.WHITE),
                                        text_align=ft.TextAlign.CENTER),
                        alignment=ft.Alignment(0, 0),
                        padding=ft.Padding.symmetric(vertical=24),
                    )
                ],
                spacing=6,
                scroll=ft.ScrollMode.AUTO,
                expand=True,
            ),
        ], spacing=0, expand=True),
        bgcolor=ft.Colors.with_opacity(0.07, ft.Colors.WHITE),
        border_radius=16,
        border=ft.Border.all(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE)),
        padding=ft.Padding.symmetric(horizontal=12, vertical=14),
        width=210,
    )

    # ── Full layout ───────────────────────────────────────────────────────────

    page.add(
        ft.Column([

            # ── Top bar ───────────────────────────────────────────────────────
            ft.Container(
                content=ft.Row([
                    ft.IconButton(
                        icon=ft.Icons.ARROW_BACK_IOS_NEW,
                        icon_color=ft.Colors.with_opacity(0.7, ft.Colors.WHITE),
                        on_click=lambda _: (camera.stop(), nav["login"]()),
                        tooltip="Back",
                    ),
                    ft.Column([
                        ft.Text("Campus Entry Terminal", size=20,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text("Type your ID or use the camera QR scanner", size=13,
                                color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE)),
                    ], spacing=2, expand=True),
                    ft.Icon(ft.Icons.QR_CODE_SCANNER, size=32, color=ACCENT),
                ], alignment=ft.MainAxisAlignment.START,
                   vertical_alignment=ft.CrossAxisAlignment.CENTER),
                padding=ft.Padding.symmetric(horizontal=32, vertical=20),
                border=ft.Border(
                    bottom=ft.BorderSide(1, ft.Colors.with_opacity(0.1, ft.Colors.WHITE))
                ),
            ),

            # ── Body ──────────────────────────────────────────────────────────
            ft.Row([

                # Centre — scanner UI
                ft.Container(
                    content=ft.Column([
                        ft.Container(height=20),

                        # Icon
                        ft.Container(
                            content=ft.Icon(ft.Icons.QR_CODE_SCANNER, size=64, color=ACCENT),
                            width=110, height=110, border_radius=55,
                            bgcolor=ft.Colors.with_opacity(0.1, ACCENT),
                            alignment=ft.Alignment(0, 0),
                            border=ft.Border.all(2, ft.Colors.with_opacity(0.3, ACCENT)),
                        ),
                        ft.Container(height=16),

                        ft.Text("Present Your ID", size=26,
                                weight=ft.FontWeight.BOLD, color=ft.Colors.WHITE),
                        ft.Text(
                            "Enter your ID manually, use a barcode scanner, or open the camera",
                            size=13, color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
                            text_align=ft.TextAlign.CENTER,
                        ),
                        ft.Container(height=20),

                        # ── Manual input ──────────────────────────────────────
                        ft.Row([
                            id_field,
                            ft.Button(
                                "SUBMIT",
                                icon=ft.Icons.SEND,
                                on_click=do_scan,
                                style=ft.ButtonStyle(
                                    bgcolor=ACCENT,
                                    color=PRIMARY,
                                    shape=ft.RoundedRectangleBorder(radius=12),
                                    padding=ft.Padding.symmetric(
                                        vertical=16, horizontal=20,
                                    ),
                                    elevation=4,
                                ),
                            ),
                        ], spacing=10, alignment=ft.MainAxisAlignment.CENTER),

                        ft.Container(height=14),

                        # ── Divider ───────────────────────────────────────────
                        ft.Row([
                            ft.Container(
                                content=ft.Divider(
                                    color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)
                                ),
                                expand=True,
                            ),
                            ft.Text("  or  ", size=12,
                                    color=ft.Colors.with_opacity(0.4, ft.Colors.WHITE)),
                            ft.Container(
                                content=ft.Divider(
                                    color=ft.Colors.with_opacity(0.2, ft.Colors.WHITE)
                                ),
                                expand=True,
                            ),
                        ], vertical_alignment=ft.CrossAxisAlignment.CENTER, width=460),

                        ft.Container(height=14),

                        # ── Camera button ─────────────────────────────────────
                        ft.Column([
                            camera_btn,
                            ft.Container(height=6),
                            cam_active_row,
                        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=0),

                        ft.Container(height=24),

                        # ── Result card ───────────────────────────────────────
                        ft.Container(
                            ref=result_card,
                            content=ft.Column([
                                ft.Icon(ft.Icons.INFO_OUTLINE, size=36, color=TEXT_MUTED),
                                ft.Text("Awaiting scan...", size=18,
                                        weight=ft.FontWeight.BOLD,
                                        color=TEXT_MUTED,
                                        text_align=ft.TextAlign.CENTER),
                                ft.Text("Scan an ID to see the result here", size=13,
                                        color=ft.Colors.with_opacity(0.6, ft.Colors.WHITE),
                                        text_align=ft.TextAlign.CENTER),
                            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=8),
                            bgcolor=ft.Colors.with_opacity(0.06, ft.Colors.WHITE),
                            border_radius=16,
                            padding=ft.Padding.symmetric(horizontal=40, vertical=24),
                            border=ft.Border.all(
                                1, ft.Colors.with_opacity(0.15, ft.Colors.WHITE)
                            ),
                            width=500,
                            animate=ft.Animation(300, ft.AnimationCurve.EASE_OUT),
                        ),
                        ft.Container(height=24),
                    ],
                    horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                    alignment=ft.MainAxisAlignment.START,
                    scroll=ft.ScrollMode.AUTO,
                    ),
                    expand=True,
                    alignment=ft.Alignment(0, 0),
                ),

                # Right — session log
                ft.Container(
                    content=log_panel,
                    padding=ft.Padding.only(right=24, top=20, bottom=20),
                ),

            ], expand=True, spacing=0,
               vertical_alignment=ft.CrossAxisAlignment.STRETCH),

        ], expand=True, spacing=0),
    )


# Placeholder so CameraScanner can be constructed before the closure is ready
def _noop(*args):
    pass