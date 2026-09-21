import datetime
import math
import os
import random
import sys
import threading
import time
import tkinter as tk
from tkinter import ttk, messagebox
import urllib.parse
import webbrowser as wb

try:
    import psutil
except ImportError:
    psutil = None

# Add current Jarvis directory to module path
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))
if CURRENT_DIR not in sys.path:
    sys.path.insert(0, CURRENT_DIR)

import jarvis

# =============================================================================
# STARK INDUSTRIES & S.H.I.E.L.D. HOLOGRAPHIC PALETTE (Iron Man Tactical HUD)
# =============================================================================
BG_DEEP = "#03060c"          # Deep space obsidian
BG_PANEL = "#070e1b"         # Tactical glass panel
BG_CARD = "#0a1426"          # Widget card surface
BG_INPUT = "#0d1b33"         # Command entry surface
BG_HOVER = "#14284d"         # Button hover

ACCENT_CYAN = "#00f0ff"      # Arc Reactor electric cyan
ACCENT_ORANGE = "#ff8800"    # Stark tactical orange / HUD radar
ACCENT_GREEN = "#00ff9d"     # Active speaking / nominal
ACCENT_AMBER = "#ffaa00"     # Listening / warning
ACCENT_GOLD = "#ffd166"      # User speech highlight
ACCENT_RED = "#ff3355"       # Critical alert / shutdown
TEXT_WHITE = "#f0f6fc"       # Primary text
TEXT_MUTED = "#527196"       # Secondary telemetry text
BORDER_COLOR = "#0f233f"     # Panel contour
BORDER_CYAN = "#00a2b8"      # Glowing border


class JarvisStarkHUD:
    def __init__(self, root: tk.Tk):
        self.root = root
        self.root.title("J.A.R.V.I.S. // STARK INDUSTRIES MARK VII - TACTICAL HUD")
        
        # Center window on screen
        win_w, win_h = 1180, 860
        screen_w = self.root.winfo_screenwidth()
        screen_h = self.root.winfo_screenheight()
        pos_x = max(10, (screen_w - win_w) // 2)
        pos_y = max(10, (screen_h - win_h) // 2)
        self.root.geometry(f"{win_w}x{win_h}+{pos_x}+{pos_y}")
        self.root.minsize(980, 720)
        self.root.configure(bg=BG_DEEP)

        # Style TTK progress bars
        self._init_ttk_styles()

        # State flags & animation phases
        self.is_listening = False
        self.is_speaking = False
        self.angle_cw = 0
        self.angle_ccw = 360
        self.pulse_phase = 0
        self.radar_sweep = 0
        self.selected_device_index = None

        # Connect GUI transcript logging to Jarvis speak engine
        jarvis.gui_callback = self._log

        # Build UI
        self._build_ui()
        self._populate_audio_devices()
        self._start_hud_animation()
        self._start_clock_and_telemetry_updater()

        # Startup greeting in daemon thread
        threading.Thread(target=self._initial_greeting, daemon=True).start()

    def _init_ttk_styles(self):
        style = ttk.Style()
        try:
            style.theme_use('clam')
        except Exception:
            pass
        style.configure("Cyan.Horizontal.TProgressbar", foreground=ACCENT_CYAN, background=ACCENT_CYAN, troughcolor="#081426", bordercolor=BORDER_COLOR)
        style.configure("Orange.Horizontal.TProgressbar", foreground=ACCENT_ORANGE, background=ACCENT_ORANGE, troughcolor="#081426", bordercolor=BORDER_COLOR)
        style.configure("Green.Horizontal.TProgressbar", foreground=ACCENT_GREEN, background=ACCENT_GREEN, troughcolor="#081426", bordercolor=BORDER_COLOR)

    def _build_ui(self):
        # =====================================================================
        # 1. TOP S.H.I.E.L.D. & STARK BAR
        # =====================================================================
        top_bar = tk.Frame(self.root, bg=BG_PANEL, bd=1, highlightbackground=BORDER_COLOR, highlightthickness=1)
        top_bar.pack(side="top", fill="x", padx=10, pady=(8, 3))

        top_inner = tk.Frame(top_bar, bg=BG_PANEL)
        top_inner.pack(fill="x", padx=10, pady=5)

        # Left: S.H.I.E.L.D. Emblem & Title
        title_box = tk.Frame(top_inner, bg=BG_PANEL)
        title_box.pack(side="left")

        logo_canvas = tk.Canvas(title_box, width=38, height=38, bg=BG_PANEL, highlightthickness=0)
        logo_canvas.pack(side="left", padx=(0, 8))
        # Outer ring & eagle wings emblem
        logo_canvas.create_oval(3, 3, 35, 35, outline=ACCENT_ORANGE, width=2)
        logo_canvas.create_polygon(8, 19, 19, 7, 30, 19, 19, 28, fill=ACCENT_ORANGE)
        logo_canvas.create_oval(16, 16, 22, 22, fill=BG_PANEL, outline=ACCENT_ORANGE)

        t_sub_box = tk.Frame(title_box, bg=BG_PANEL)
        t_sub_box.pack(side="left")

        title_lbl = tk.Label(
            t_sub_box,
            text="J . A . R . V . I . S",
            font=("Segoe UI", 16, "bold"),
            fg=ACCENT_CYAN,
            bg=BG_PANEL
        )
        title_lbl.pack(anchor="w")

        sub_lbl = tk.Label(
            t_sub_box,
            text="IRONMAN J.A.R.V.I.S. + S.H.I.E.L.D. OS",
            font=("Consolas", 8, "bold"),
            fg=ACCENT_ORANGE,
            bg=BG_PANEL
        )
        sub_lbl.pack(anchor="w")

        # Center: Interactive Search & Query Prompt
        center_prompt_box = tk.Frame(top_inner, bg=BG_PANEL)
        center_prompt_box.pack(side="left", expand=True, padx=15)

        prompt_title = tk.Label(
            center_prompt_box,
            text="J . A . R . V . I . S . // What Can I Search For You, Sir?",
            font=("Consolas", 9, "bold"),
            fg=TEXT_WHITE,
            bg=BG_PANEL
        )
        prompt_title.pack(anchor="center")

        # Quick Web Search Chips
        web_chips_frame = tk.Frame(center_prompt_box, bg=BG_PANEL)
        web_chips_frame.pack(anchor="center", pady=(2, 0))

        web_links = [
            ("GOOGLE", "https://www.google.com"),
            ("YOUTUBE", "https://www.youtube.com"),
            ("WIKIPEDIA", "https://www.wikipedia.org"),
            ("MAPS", "https://maps.google.com"),
            ("GMAIL", "https://mail.google.com"),
        ]
        for name, url in web_links:
            btn = tk.Button(
                web_chips_frame,
                text=name,
                font=("Consolas", 7, "bold"),
                fg=ACCENT_CYAN,
                bg=BG_CARD,
                activebackground=ACCENT_CYAN,
                activeforeground="#000000",
                relief="flat",
                bd=0,
                padx=6,
                pady=1,
                cursor="hand2",
                command=lambda u=url: wb.open(u)
            )
            btn.pack(side="left", padx=2)

        # Right: System Power Quick Controls & Large Calendar Box
        right_top_box = tk.Frame(top_inner, bg=BG_PANEL)
        right_top_box.pack(side="right")

        # Power actions
        power_box = tk.Frame(right_top_box, bg=BG_PANEL)
        power_box.pack(side="left", padx=(0, 12))

        power_actions = [
            ("🔒 LOCK", lambda: jarvis.window_control("lock")),
            ("💤 SLEEP", lambda: jarvis.execute_command("sleep pc")),
            ("⚡ RESTART", lambda: jarvis.execute_command("restart system")),
            ("❌ SHUTDOWN", lambda: jarvis.execute_command("shutdown system"))
        ]
        for p_lbl, p_cmd in power_actions:
            btn = tk.Button(
                power_box,
                text=p_lbl,
                font=("Segoe UI", 7, "bold"),
                fg=TEXT_WHITE,
                bg=BG_CARD,
                activebackground=ACCENT_ORANGE,
                activeforeground="#000000",
                relief="flat",
                bd=0,
                padx=6,
                pady=3,
                cursor="hand2",
                command=p_cmd
            )
            btn.pack(side="left", padx=2)

        # Big Calendar Day Widget (Matching Reference Image)
        cal_box = tk.Frame(right_top_box, bg=BG_CARD, bd=1, highlightbackground=BORDER_COLOR, highlightthickness=1)
        cal_box.pack(side="right", padx=(4, 0))

        cal_inner = tk.Frame(cal_box, bg=BG_CARD)
        cal_inner.pack(padx=8, pady=2)

        self.cal_day_num = tk.Label(
            cal_inner,
            text="21",
            font=("Consolas", 18, "bold"),
            fg=TEXT_WHITE,
            bg=BG_CARD
        )
        self.cal_day_num.pack(side="left", padx=(0, 6))

        cal_text_box = tk.Frame(cal_inner, bg=BG_CARD)
        cal_text_box.pack(side="left")

        self.cal_month = tk.Label(
            cal_text_box,
            text="SEPTEMBER",
            font=("Consolas", 8, "bold"),
            fg=ACCENT_ORANGE,
            bg=BG_CARD
        )
        self.cal_month.pack(anchor="w")

        self.cal_weekday = tk.Label(
            cal_text_box,
            text="MONDAY",
            font=("Consolas", 7),
            fg=TEXT_MUTED,
            bg=BG_CARD
        )
        self.cal_weekday.pack(anchor="w")

        # =====================================================================
        # 2. AUDIO INPUT & DIAGNOSTIC STRIP
        # =====================================================================
        tool_bar = tk.Frame(self.root, bg=BG_DEEP)
        tool_bar.pack(side="top", fill="x", padx=12, pady=(2, 4))

        src_lbl = tk.Label(
            tool_bar,
            text="🎙️ AUDIO SOURCE:",
            font=("Consolas", 8, "bold"),
            fg=TEXT_MUTED,
            bg=BG_DEEP
        )
        src_lbl.pack(side="left", padx=(2, 6))

        self.device_combo = ttk.Combobox(tool_bar, state="readonly", width=38)
        self.device_combo.pack(side="left", padx=(0, 8))
        self.device_combo.bind("<<ComboboxSelected>>", self._on_device_selected)

        test_mic_btn = tk.Button(
            tool_bar,
            text="⚡ Test Mic Signal",
            font=("Segoe UI", 8, "bold"),
            fg=ACCENT_CYAN,
            bg=BG_CARD,
            activebackground=BG_HOVER,
            activeforeground=TEXT_WHITE,
            relief="flat",
            bd=0,
            padx=10,
            pady=2,
            cursor="hand2",
            command=self._test_microphone_stream
        )
        test_mic_btn.pack(side="left")

        self.mic_feedback_lbl = tk.Label(
            tool_bar,
            text="Ready // Stark Audio Drivers Active",
            font=("Segoe UI", 8, "italic"),
            fg=TEXT_MUTED,
            bg=BG_DEEP
        )
        self.mic_feedback_lbl.pack(side="left", padx=10)

        # =====================================================================
        # 3. PINNED BOTTOM INTERFACE (Command Bar, Quick Chips, Feed)
        # =====================================================================
        input_card = tk.Frame(self.root, bg=BG_PANEL, bd=1, highlightbackground=BORDER_COLOR, highlightthickness=1)
        input_card.pack(side="bottom", fill="x", padx=10, pady=(0, 8))

        input_inner = tk.Frame(input_card, bg=BG_PANEL)
        input_inner.pack(fill="x", padx=8, pady=8)

        # Voice Trigger Button
        self.mic_btn = tk.Button(
            input_inner,
            text="🎙️ ACTIVATE VOICE PROTOCOL",
            font=("Segoe UI", 10, "bold"),
            fg="#03060c",
            bg=ACCENT_CYAN,
            activebackground="#4ff3ff",
            activeforeground="#03060c",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._start_voice_thread
        )
        self.mic_btn.pack(side="left", padx=(0, 8))

        # Command Text Entry
        self.entry = tk.Entry(
            input_inner,
            font=("Consolas", 11),
            bg=BG_INPUT,
            fg=TEXT_WHITE,
            insertbackground=ACCENT_CYAN,
            relief="flat",
            bd=0
        )
        self.entry.pack(side="left", fill="x", expand=True, ipady=6, padx=(0, 8))
        self.entry.bind("<Return>", lambda event: self._on_text_submit())

        # Send Button
        send_btn = tk.Button(
            input_inner,
            text="EXECUTE ➤",
            font=("Segoe UI", 10, "bold"),
            fg=TEXT_WHITE,
            bg="#006bb3",
            activebackground=ACCENT_CYAN,
            activeforeground="#000000",
            relief="flat",
            bd=0,
            padx=18,
            pady=8,
            cursor="hand2",
            command=self._on_text_submit
        )
        send_btn.pack(side="right")

        # Quick Action Chips (Above command bar)
        quick_frame = tk.Frame(self.root, bg=BG_DEEP)
        quick_frame.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

        quick_actions = [
            ("🕒 Time", "what is the time"),
            ("📅 Date", "what is today's date"),
            ("🎵 Music", "play a music"),
            ("📝 Read Notes", "read my notes"),
            ("🗑️ Clear Notes", "clear all notes"),
            ("📸 Screenshot", "screenshot"),
            ("🔊 Vol +", "volume up"),
            ("🔉 Vol -", "volume down"),
            ("🌐 Wikipedia", "wikipedia"),
            ("🔍 Google", "search google"),
            ("🗑️ Trash", "empty recycle bin"),
            ("😄 Joke", "tell me a joke")
        ]

        for label, cmd in quick_actions:
            btn = tk.Button(
                quick_frame,
                text=label,
                font=("Segoe UI", 8, "bold"),
                fg=TEXT_WHITE,
                bg=BG_CARD,
                activebackground=ACCENT_ORANGE,
                activeforeground="#000000",
                relief="flat",
                bd=1,
                padx=7,
                pady=2,
                cursor="hand2",
                command=lambda c=cmd: self._send_command(c)
            )
            btn.pack(side="left", padx=2)

        # Quantum Interaction Feed (Compact terminal transcript)
        feed_card = tk.Frame(self.root, bg=BG_PANEL, bd=1, highlightbackground=BORDER_COLOR, highlightthickness=1)
        feed_card.pack(side="bottom", fill="x", padx=10, pady=(0, 5))

        feed_hdr = tk.Frame(feed_card, bg=BG_PANEL)
        feed_hdr.pack(fill="x", padx=10, pady=(5, 2))

        f_title = tk.Label(
            feed_hdr,
            text="// QUANTUM INTERACTION FEED",
            font=("Consolas", 8, "bold"),
            fg=ACCENT_CYAN,
            bg=BG_PANEL
        )
        f_title.pack(side="left")

        # Digital Clock in feed header
        self.feed_clock_lbl = tk.Label(
            feed_hdr,
            text="00:00:00",
            font=("Consolas", 9, "bold"),
            fg=ACCENT_ORANGE,
            bg=BG_PANEL
        )
        self.feed_clock_lbl.pack(side="left", padx=15)

        # Battery / Year Telemetry
        self.feed_telemetry_lbl = tk.Label(
            feed_hdr,
            text="BATTERY: 100% [ AC LINE ] // DAYS LEFT: 101",
            font=("Consolas", 7),
            fg=TEXT_MUTED,
            bg=BG_PANEL
        )
        self.feed_telemetry_lbl.pack(side="left")

        purge_btn = tk.Button(
            feed_hdr,
            text="PURGE",
            font=("Consolas", 7),
            fg=TEXT_MUTED,
            bg=BG_PANEL,
            activebackground=BG_INPUT,
            activeforeground=TEXT_WHITE,
            relief="flat",
            bd=0,
            cursor="hand2",
            command=self._clear_feed
        )
        purge_btn.pack(side="right")

        f_text_frame = tk.Frame(feed_card, bg=BG_PANEL)
        f_text_frame.pack(fill="x", padx=10, pady=(0, 6))

        self.feed = tk.Text(
            f_text_frame,
            height=4,
            bg=BG_INPUT,
            fg=TEXT_WHITE,
            insertbackground=ACCENT_CYAN,
            font=("Consolas", 9),
            wrap="word",
            relief="flat",
            bd=0,
            padx=8,
            pady=3
        )
        self.feed.pack(side="left", fill="x", expand=True)

        scrollbar = ttk.Scrollbar(f_text_frame, command=self.feed.yview)
        scrollbar.pack(side="right", fill="y")
        self.feed.config(yscrollcommand=scrollbar.set)

        self.feed.tag_config("jarvis", foreground=ACCENT_CYAN, font=("Consolas", 9, "bold"))
        self.feed.tag_config("user", foreground=ACCENT_GOLD, font=("Consolas", 9, "bold"))
        self.feed.tag_config("system", foreground=TEXT_MUTED, font=("Consolas", 8, "italic"))
        self.feed.tag_config("body", foreground=TEXT_WHITE, font=("Consolas", 9))
        self.feed.config(state="disabled")

        # =====================================================================
        # 4. MAIN SCI-FI DASHBOARD (Left Rail + Central Canvas + Right Rail)
        # =====================================================================
        main_dash = tk.Frame(self.root, bg=BG_DEEP)
        main_dash.pack(side="top", fill="both", expand=True, padx=10, pady=(0, 4))

        # --- LEFT COLUMN: Cyber App Launcher Rail ("BRIDGE CONTROL") ---
        left_rail = tk.Frame(main_dash, bg=BG_PANEL, width=175, bd=1, highlightbackground=BORDER_COLOR, highlightthickness=1)
        left_rail.pack(side="left", fill="y", padx=(0, 6))
        left_rail.pack_propagate(False)

        l_hdr = tk.Frame(left_rail, bg=BG_PANEL)
        l_hdr.pack(fill="x", pady=6)
        tk.Label(
            l_hdr,
            text="[ BRIDGE CONTROL ]",
            font=("Consolas", 8, "bold"),
            fg=ACCENT_ORANGE,
            bg=BG_PANEL
        ).pack()

        # Vertical cyber launcher buttons with orange indicator marks
        launchers = [
            ("Chrome", lambda: wb.open("https://www.google.com")),
            ("Control Panel", lambda: os.system("control")),
            ("Steam", lambda: jarvis.execute_command("open steam")),
            ("WhatsApp", lambda: wb.open("https://web.whatsapp.com")),
            ("YouTube", lambda: wb.open("https://www.youtube.com")),
            ("VS Code", lambda: jarvis.execute_command("open vs code")),
            ("Task Manager", lambda: jarvis.execute_command("open task manager")),
            ("Settings", lambda: jarvis.execute_command("open settings")),
            ("Explorer", lambda: jarvis.execute_command("open explorer")),
            ("Calculator", lambda: jarvis.execute_command("open calculator")),
            ("Record Audio", lambda: jarvis.execute_command("record audio")),
        ]

        # Inner frame with vertical meter scale + buttons
        rail_body = tk.Frame(left_rail, bg=BG_PANEL)
        rail_body.pack(fill="both", expand=True, padx=4)

        # Scale markings on the left edge
        scale_canvas = tk.Canvas(rail_body, width=18, bg=BG_PANEL, highlightthickness=0)
        scale_canvas.pack(side="left", fill="y", padx=(0, 2))
        scale_canvas.create_line(14, 10, 14, 300, fill="#123050", width=1)
        for i, val in enumerate(["100", "80", "60", "40", "20", "10"]):
            y_pos = 15 + i * 50
            scale_canvas.create_line(8, y_pos, 14, y_pos, fill=ACCENT_ORANGE, width=1.5)
            scale_canvas.create_text(6, y_pos, text=val, fill=TEXT_MUTED, font=("Consolas", 6), anchor="e")

        btn_column = tk.Frame(rail_body, bg=BG_PANEL)
        btn_column.pack(side="left", fill="both", expand=True)

        for text, cmd in launchers:
            b_frame = tk.Frame(btn_column, bg=BG_CARD)
            b_frame.pack(fill="x", pady=2)

            # Left orange indicator bar
            tk.Frame(b_frame, bg=ACCENT_ORANGE, width=3).pack(side="left", fill="y")

            b = tk.Button(
                b_frame,
                text=f" {text}",
                font=("Consolas", 8, "bold"),
                fg=TEXT_WHITE,
                bg=BG_CARD,
                activebackground=BG_HOVER,
                activeforeground=ACCENT_CYAN,
                anchor="w",
                relief="flat",
                bd=0,
                padx=6,
                pady=4,
                cursor="hand2",
                command=cmd
            )
            b.pack(side="left", fill="x", expand=True)

        # --- RIGHT COLUMN: System Telemetry Cards ---
        right_rail = tk.Frame(main_dash, bg=BG_PANEL, width=195, bd=1, highlightbackground=BORDER_COLOR, highlightthickness=1)
        right_rail.pack(side="right", fill="y", padx=(6, 0))
        right_rail.pack_propagate(False)

        r_hdr = tk.Label(
            right_rail,
            text="[ SYSTEM TELEMETRY ]",
            font=("Consolas", 8, "bold"),
            fg=ACCENT_CYAN,
            bg=BG_PANEL
        )
        r_hdr.pack(pady=6)

        # CPU Card
        self.cpu_card_val = tk.Label(right_rail, text="CPU: 0%", font=("Consolas", 8, "bold"), fg=ACCENT_CYAN, bg=BG_PANEL)
        self.cpu_card_val.pack(anchor="w", padx=10, pady=(2, 0))
        self.cpu_bar = ttk.Progressbar(right_rail, style="Cyan.Horizontal.TProgressbar", length=170, mode="determinate")
        self.cpu_bar.pack(padx=10, pady=(0, 4))

        # RAM Card
        self.ram_card_val = tk.Label(right_rail, text="RAM: 0%", font=("Consolas", 8, "bold"), fg=ACCENT_ORANGE, bg=BG_PANEL)
        self.ram_card_val.pack(anchor="w", padx=10, pady=(2, 0))
        self.ram_bar = ttk.Progressbar(right_rail, style="Orange.Horizontal.TProgressbar", length=170, mode="determinate")
        self.ram_bar.pack(padx=10, pady=(0, 4))

        # DISK (C:) Card
        self.disk_card_val = tk.Label(right_rail, text="DISK (C:): 0%", font=("Consolas", 8, "bold"), fg=ACCENT_GREEN, bg=BG_PANEL)
        self.disk_card_val.pack(anchor="w", padx=10, pady=(2, 0))
        self.disk_bar = ttk.Progressbar(right_rail, style="Green.Horizontal.TProgressbar", length=170, mode="determinate")
        self.disk_bar.pack(padx=10, pady=(0, 6))

        # System UpTime Card
        up_box = tk.Frame(right_rail, bg=BG_CARD)
        up_box.pack(fill="x", padx=8, pady=2)
        tk.Label(up_box, text="SYSTEM UPTIME", font=("Consolas", 7), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", padx=6, pady=(2, 0))
        self.uptime_lbl = tk.Label(up_box, text="0h 00m 00s", font=("Consolas", 8, "bold"), fg=ACCENT_CYAN, bg=BG_CARD)
        self.uptime_lbl.pack(anchor="w", padx=6, pady=(0, 2))

        # Status Cards
        telemetry_items = [
            ("ARMOR STATUS", "MARK VII (100%)", ACCENT_CYAN),
            ("AUDIO ENGINE", "ACTIVE // SAPI5", ACCENT_GREEN),
            ("JARVIS AI", "NOMINAL", ACCENT_GREEN),
        ]
        for title, val, color in telemetry_items:
            box = tk.Frame(right_rail, bg=BG_CARD)
            box.pack(fill="x", padx=8, pady=2)
            tk.Label(box, text=title, font=("Consolas", 7), fg=TEXT_MUTED, bg=BG_CARD).pack(anchor="w", padx=6, pady=(2, 0))
            tk.Label(box, text=val, font=("Consolas", 8, "bold"), fg=color, bg=BG_CARD).pack(anchor="w", padx=6, pady=(0, 2))

        # Media Player Control Card (Matching bottom right tunes widget in reference image)
        media_card = tk.Frame(right_rail, bg=BG_CARD, bd=1, highlightbackground=BORDER_COLOR, highlightthickness=1)
        media_card.pack(fill="x", padx=8, pady=(8, 2))

        m_hdr = tk.Label(media_card, text="🎵 STARK TUNES", font=("Consolas", 7, "bold"), fg=ACCENT_ORANGE, bg=BG_CARD)
        m_hdr.pack(anchor="w", padx=6, pady=(4, 1))

        self.media_track_lbl = tk.Label(
            media_card,
            text="OneRepublic - Love Runs...",
            font=("Consolas", 7),
            fg=TEXT_WHITE,
            bg=BG_CARD
        )
        self.media_track_lbl.pack(anchor="w", padx=6, pady=(0, 4))

        m_btns_box = tk.Frame(media_card, bg=BG_CARD)
        m_btns_box.pack(fill="x", padx=4, pady=(0, 4))

        media_btns = [
            ("⏮", lambda: jarvis.media_control("prev")),
            ("⏯", lambda: jarvis.media_control("play")),
            ("⏭", lambda: jarvis.media_control("next")),
            ("🔇", lambda: jarvis.volume_control("mute")),
        ]
        for icon, cmd in media_btns:
            mb = tk.Button(
                m_btns_box,
                text=icon,
                font=("Segoe UI", 9, "bold"),
                fg=TEXT_WHITE,
                bg=BG_INPUT,
                activebackground=ACCENT_CYAN,
                activeforeground="#000000",
                relief="flat",
                bd=0,
                padx=6,
                pady=1,
                cursor="hand2",
                command=cmd
            )
            mb.pack(side="left", padx=2, expand=True)

        # --- CENTER COLUMN: Holographic Iron Man Vector Canvas ---
        canvas_card = tk.Frame(main_dash, bg=BG_PANEL, bd=1, highlightbackground=BORDER_COLOR, highlightthickness=1)
        canvas_card.pack(side="left", fill="both", expand=True)

        self.canvas = tk.Canvas(
            canvas_card,
            bg=BG_DEEP,
            highlightthickness=0,
            cursor="hand2"
        )
        self.canvas.pack(fill="both", expand=True, padx=2, pady=2)
        # Clicking canvas / Arc Reactor triggers voice listening
        self.canvas.bind("<Button-1>", lambda e: self._start_voice_thread())

    def _start_clock_and_telemetry_updater(self):
        """Updates clock, calendar, CPU %, RAM %, Disk %, and Uptime dynamically."""
        now = datetime.datetime.now()
        time_str = now.strftime("%H:%M:%S")
        self.feed_clock_lbl.config(text=time_str)

        # Update Top Calendar Box
        self.cal_day_num.config(text=now.strftime("%d"))
        self.cal_month.config(text=now.strftime("%B").upper())
        self.cal_weekday.config(text=now.strftime("%A").upper())

        # Year telemetry
        end_of_year = datetime.date(now.year, 12, 31)
        days_left = (end_of_year - now.date()).days
        months_left = 12 - now.month
        self.feed_telemetry_lbl.config(
            text=f"POWER: 100% [ AC LINE ] // DAYS LEFT: {days_left} // MONTHS LEFT: {months_left}"
        )

        if psutil:
            try:
                cpu = psutil.cpu_percent()
                ram = psutil.virtual_memory().percent
                self.cpu_card_val.config(text=f"CPU: {cpu:.1f}%")
                self.cpu_bar['value'] = cpu
                self.ram_card_val.config(text=f"RAM: {ram:.1f}%")
                self.ram_bar['value'] = ram

                # Disk telemetry
                if hasattr(psutil, 'disk_usage'):
                    d = psutil.disk_usage('C:')
                    used_gb = d.used / (1024**3)
                    total_gb = d.total / (1024**3)
                    self.disk_card_val.config(text=f"DISK (C:): {d.percent:.1f}% ({used_gb:.0f}/{total_gb:.0f} GB)")
                    self.disk_bar['value'] = d.percent

                # Uptime telemetry
                if hasattr(psutil, 'boot_time'):
                    up_sec = int(time.time() - psutil.boot_time())
                    up_h, r = divmod(up_sec, 3600)
                    up_m, up_s = divmod(r, 60)
                    self.uptime_lbl.config(text=f"{up_h}h {up_m:02d}m {up_s:02d}s")
            except Exception:
                pass

        self.root.after(1000, self._start_clock_and_telemetry_updater)

    def _start_hud_animation(self):
        """Draws the animated holographic Iron Man wireframe HUD with rotating tech dials."""
        w = self.canvas.winfo_width()
        h = self.canvas.winfo_height()
        if w < 100 or h < 100:
            w, h = 760, 420
        cx, cy = w // 2, h // 2

        self.canvas.delete("all")

        # Color shift based on listening / speaking
        is_actively_speaking = self.is_speaking or (hasattr(jarvis, "tts_manager") and jarvis.tts_manager.is_busy)
        if self.is_listening:
            core_color = ACCENT_AMBER
            status_text = "LISTENING... PLEASE SPEAK NOW"
            eye_glow = "#ffe680"
        elif is_actively_speaking:
            core_color = ACCENT_GREEN
            status_text = "TRANSMITTING SPEECH RESPONSE"
            eye_glow = "#80ffc0"
        else:
            core_color = ACCENT_CYAN
            status_text = "CURRENT POWER LEVEL: 100% AND HOLDING STEADY"
            eye_glow = "#d0ffff"

        # 1. Tech Coordinate Grid & Corner Brackets
        self._draw_hud_grid_and_brackets(w, h)

        # Update animation angles
        self.angle_cw = (self.angle_cw + 2.2) % 360
        self.angle_ccw = (self.angle_ccw - 1.8) % 360
        self.pulse_phase = (self.pulse_phase + 0.09) % (2 * math.pi)
        self.radar_sweep = (self.radar_sweep + 3.0) % 360
        pulse = math.sin(self.pulse_phase) * 3.5

        # 2. Left JARVIS Rotary Dial (Matching reference image)
        dial_offset_x = max(180, min(240, cx - 130))
        lx, ly = cx - dial_offset_x, cy + 40
        self._draw_jarvis_dial(lx, ly, pulse, core_color)

        # 3. Right System Radar Dial (Matching reference image)
        rx, ry = cx + dial_offset_x, cy + 40
        self._draw_radar_dial(rx, ry, pulse, core_color)

        # 4. Iron Man Wireframe Helmet & Chest
        hcx, hcy = cx, cy - 25
        self._draw_ironman_helmet(hcx, hcy, eye_glow, core_color)

        # 5. Chest Arc Reactor (Centered & Pulsing)
        rcx, rcy = hcx, hcy + 92
        self._draw_arc_reactor(rcx, rcy, pulse, core_color)

        # 6. Floating Telemetry Overlays on Center Canvas
        self._draw_canvas_telemetry(cx, cy, w, h, status_text, core_color)

        self.root.after(35, self._start_hud_animation)

    def _draw_hud_grid_and_brackets(self, w: int, h: int):
        """Draws subtle sci-fi coordinate grid and corner brackets."""
        grid_step = 60
        for gx in range(grid_step, w, grid_step):
            self.canvas.create_line(gx, 0, gx, h, fill="#051220", width=1)
        for gy in range(grid_step, h, grid_step):
            self.canvas.create_line(0, gy, w, gy, fill="#051220", width=1)

        # Corner brackets
        c = "#0f2c4c"
        l = 20
        # Top-left
        self.canvas.create_line(10, 10, 10 + l, 10, fill=c, width=2)
        self.canvas.create_line(10, 10, 10, 10 + l, fill=c, width=2)
        # Top-right
        self.canvas.create_line(w - 10, 10, w - 10 - l, 10, fill=c, width=2)
        self.canvas.create_line(w - 10, 10, w - 10, 10 + l, fill=c, width=2)
        # Bottom-left
        self.canvas.create_line(10, h - 10, 10 + l, h - 10, fill=c, width=2)
        self.canvas.create_line(10, h - 10, 10, h - 10 - l, fill=c, width=2)
        # Bottom-right
        self.canvas.create_line(w - 10, h - 10, w - 10 - l, h - 10, fill=c, width=2)
        self.canvas.create_line(w - 10, h - 10, w - 10, h - 10 - l, fill=c, width=2)

    def _draw_jarvis_dial(self, lx: int, ly: int, pulse: float, core_color: str):
        """Draws the left circular JARVIS HUD dial matching the reference image."""
        # Outer tick ring
        self.canvas.create_oval(lx - 58, ly - 58, lx + 58, ly + 58, outline="#0b243d", width=1)
        # Middle glowing cyan circle
        self.canvas.create_oval(lx - 44, ly - 44, lx + 44, ly + 44, outline=ACCENT_CYAN, width=2)
        # Rotating orange arc
        self.canvas.create_arc(
            lx - 50, ly - 50, lx + 50, ly + 50,
            start=self.angle_cw, extent=100,
            outline=ACCENT_ORANGE, width=3, style="arc"
        )
        # Counter-rotating segmented arc
        self.canvas.create_arc(
            lx - 36, ly - 36, lx + 36, ly + 36,
            start=self.angle_ccw, extent=60,
            outline=ACCENT_CYAN, width=2, style="arc"
        )
        # Center "JARVIS" text
        self.canvas.create_text(lx, ly, text="JARVIS", fill=ACCENT_CYAN, font=("Segoe UI", 11, "bold"))
        self.canvas.create_text(lx, ly + 68, text="BRIDGE CONTROL", fill=TEXT_MUTED, font=("Consolas", 7, "bold"))

    def _draw_radar_dial(self, rx: int, ry: int, pulse: float, core_color: str):
        """Draws the right circular Radar HUD dial matching the reference image."""
        # Outer telemetry circle
        self.canvas.create_oval(rx - 58, ry - 58, rx + 58, ry + 58, outline="#0b243d", width=1)
        # Inner cyan circle
        self.canvas.create_oval(rx - 44, ry - 44, rx + 44, ry + 44, outline=ACCENT_CYAN, width=2)
        # Rotating orange arc
        self.canvas.create_arc(
            rx - 50, ry - 50, rx + 50, ry + 50,
            start=self.angle_ccw, extent=120,
            outline=ACCENT_ORANGE, width=4, style="arc"
        )
        # Rotating radar sweep line
        rad = math.radians(self.radar_sweep)
        sw_x = rx + math.cos(rad) * 42
        sw_y = ry + math.sin(rad) * 42
        self.canvas.create_line(rx, ry, sw_x, sw_y, fill=ACCENT_GREEN, width=1.5)
        # Crosshair lines
        self.canvas.create_line(rx - 42, ry, rx + 42, ry, fill="#12365a", width=1)
        self.canvas.create_line(rx, ry - 42, rx, ry + 42, fill="#12365a", width=1)

        # Center label
        self.canvas.create_text(rx, ry, text="RADAR", fill=ACCENT_CYAN, font=("Segoe UI", 9, "bold"))
        self.canvas.create_text(rx, ry + 68, text="TARGET TELEMETRY", fill=TEXT_MUTED, font=("Consolas", 7, "bold"))

    def _draw_ironman_helmet(self, hcx: int, hcy: int, eye_glow: str, core_color: str):
        """Draws the detailed Iron Man wireframe helmet silhouette and chest contour."""
        # Helmet Silhouette Outline Polygon
        head_poly = [
            hcx - 26, hcy - 80,
            hcx, hcy - 88,
            hcx + 26, hcy - 80,
            hcx + 40, hcy - 58,
            hcx + 42, hcy - 28,
            hcx + 32, hcy - 4,
            hcx + 24, hcy + 18,
            hcx + 14, hcy + 28,
            hcx - 14, hcy + 28,
            hcx - 24, hcy + 18,
            hcx - 32, hcy - 4,
            hcx - 42, hcy - 28,
            hcx - 40, hcy - 58,
        ]
        self.canvas.create_polygon(head_poly, fill="#051222", outline=ACCENT_CYAN, width=1.8)

        # Forehead Diamond Sensor
        self.canvas.create_polygon(
            [hcx, hcy - 78, hcx + 8, hcy - 68, hcx, hcy - 58, hcx - 8, hcy - 68],
            fill="#0b2440", outline=ACCENT_CYAN, width=1
        )

        # Faceplate Geometry Lines (Cheekbones & Brow)
        self.canvas.create_line(hcx - 30, hcy - 38, hcx - 10, hcy - 32, hcx, hcy - 30, hcx + 10, hcy - 32, hcx + 30, hcy - 38, fill="#144670", width=1)
        self.canvas.create_line(hcx - 18, hcy - 4, hcx - 10, hcy + 12, hcx + 10, hcy + 12, hcx + 18, hcy - 4, fill="#144670", width=1)
        # Chin vent slit
        self.canvas.create_line(hcx - 10, hcy + 20, hcx + 10, hcy + 20, fill=ACCENT_CYAN, width=1.5)

        # Glowing Slanted Eyes (Iconic Iron Man Cyan/White Eyes)
        left_eye = [hcx - 28, hcy - 26, hcx - 8, hcy - 22, hcx - 10, hcy - 17, hcx - 26, hcy - 21]
        right_eye = [hcx + 28, hcy - 26, hcx + 8, hcy - 22, hcx + 10, hcy - 17, hcx + 26, hcy - 21]
        self.canvas.create_polygon(left_eye, fill=eye_glow, outline=core_color, width=1.5)
        self.canvas.create_polygon(right_eye, fill=eye_glow, outline=core_color, width=1.5)

        # Collar & Shoulder Armor Plating
        self.canvas.create_line(hcx - 14, hcy + 28, hcx - 28, hcy + 50, fill=ACCENT_CYAN, width=1.5)
        self.canvas.create_line(hcx + 14, hcy + 28, hcx + 28, hcy + 50, fill=ACCENT_CYAN, width=1.5)

        chest_l = [
            hcx - 28, hcy + 50,
            hcx - 65, hcy + 62,
            hcx - 120, hcy + 82,
            hcx - 110, hcy + 138,
            hcx - 55, hcy + 125,
            hcx - 35, hcy + 85
        ]
        chest_r = [
            hcx + 28, hcy + 50,
            hcx + 65, hcy + 62,
            hcx + 120, hcy + 82,
            hcx + 110, hcy + 138,
            hcx + 55, hcy + 125,
            hcx + 35, hcy + 85
        ]
        self.canvas.create_line(chest_l, fill=ACCENT_CYAN, width=1.5)
        self.canvas.create_line(chest_r, fill=ACCENT_CYAN, width=1.5)

        # Red / Orange Circuit Accent Lines on Collar
        self.canvas.create_line(hcx - 24, hcy + 52, hcx - 45, hcy + 58, fill=ACCENT_ORANGE, width=1)
        self.canvas.create_line(hcx + 24, hcy + 52, hcx + 45, hcy + 58, fill=ACCENT_ORANGE, width=1)

    def _draw_arc_reactor(self, rcx: int, rcy: int, pulse: float, core_color: str):
        """Draws the animated chest Arc Reactor with rotating ring segments."""
        # Outer casing ring
        r_outer = 30 + pulse
        self.canvas.create_oval(rcx - r_outer, rcy - r_outer, rcx + r_outer, rcy + r_outer, outline="#0e3256", width=2)

        # Clockwise spinning arc segments
        for i in range(0, 360, 45):
            self.canvas.create_arc(
                rcx - 24, rcy - 24, rcx + 24, rcy + 24,
                start=self.angle_cw + i, extent=28,
                outline=core_color, width=2.2, style="arc"
            )

        # Counter-clockwise inner dashed ring
        for j in range(0, 360, 60):
            self.canvas.create_arc(
                rcx - 17, rcy - 17, rcx + 17, rcy + 17,
                start=self.angle_ccw + j, extent=35,
                outline=ACCENT_ORANGE, width=1.5, style="arc"
            )

        # Glowing pulsing central core
        r_core = 12 + (pulse * 0.5)
        self.canvas.create_oval(rcx - r_core, rcy - r_core, rcx + r_core, rcy + r_core, fill=core_color, outline="#ffffff", width=1.5)

    def _draw_canvas_telemetry(self, cx: int, cy: int, w: int, h: int, status_text: str, core_color: str):
        """Draws telemetry annotations on the holographic canvas matching the reference image."""
        # Bottom Power Caption
        self.canvas.create_text(
            cx, h - 18,
            text=f"[ {status_text} ]",
            fill=core_color,
            font=("Consolas", 8, "bold")
        )

        # Left-side Mini Telemetry (Above left dial)
        lx = max(30, cx - 220)
        self.canvas.create_text(lx, cy - 70, text="// PROTOCOL: MARK VII", fill=TEXT_MUTED, font=("Consolas", 7), anchor="w")
        self.canvas.create_text(lx, cy - 55, text="// SYS: ALL ONLINE", fill=ACCENT_CYAN, font=("Consolas", 7, "bold"), anchor="w")

        # Right-side Mini Telemetry (Above right dial)
        rx = min(w - 30, cx + 220)
        self.canvas.create_text(rx, cy - 70, text="CORE TEMP: 32°C //", fill=TEXT_MUTED, font=("Consolas", 7), anchor="e")
        self.canvas.create_text(rx, cy - 55, text="STATUS: NOMINAL //", fill=ACCENT_GREEN, font=("Consolas", 7, "bold"), anchor="e")

    def _populate_audio_devices(self):
        """Populates the audio input device dropdown."""
        devices = jarvis.get_audio_input_devices()
        device_labels = ["Default Audio Input Device"]
        self.device_map = {0: None}

        preferred_idx = 0
        for i, (idx, name) in enumerate(devices, start=1):
            clean_name = f"[{idx}] {name}"
            device_labels.append(clean_name)
            self.device_map[i] = idx
            if "microphone" in name.lower() and preferred_idx == 0:
                preferred_idx = i

        self.device_combo['values'] = device_labels
        self.device_combo.current(preferred_idx)
        self.selected_device_index = self.device_map.get(preferred_idx)

    def _on_device_selected(self, event=None):
        selected_idx = self.device_combo.current()
        self.selected_device_index = self.device_map.get(selected_idx)
        dev_name = self.device_combo.get()
        self.mic_feedback_lbl.config(text=f"Selected: {dev_name[:28]}...", fg=ACCENT_CYAN)

    def _test_microphone_stream(self):
        """Tests the microphone in a background thread."""
        def worker():
            self.mic_feedback_lbl.config(text="● Testing... Speak now!", fg=ACCENT_AMBER)
            self._log("System", f"Audio diagnostic on: {self.device_combo.get()}...")

            import speech_recognition as sr
            r = sr.Recognizer()
            try:
                mic_kwargs = {}
                if self.selected_device_index is not None:
                    mic_kwargs["device_index"] = self.selected_device_index

                with sr.Microphone(**mic_kwargs) as source:
                    r.adjust_for_ambient_noise(source, duration=1.2)
                    energy = r.energy_threshold
                    self._log("System", f"Microphone signal confirmed! Ambient level: {energy:.1f}")

                    if energy > 35:
                        self.mic_feedback_lbl.config(text="● Signal OK! (Mic Connected)", fg=ACCENT_GREEN)
                        self._log("Jarvis", "Microphone is connected and ready for voice commands.")
                    else:
                        self.mic_feedback_lbl.config(text="⚠️ Low Signal / Muted", fg=ACCENT_AMBER)
                        self._log("Jarvis", "Signal is low. Please unmute your microphone.")
            except Exception as e:
                self.mic_feedback_lbl.config(text="✖ Device Access Failed", fg=ACCENT_RED)
                self._log("System", f"Mic Test Failed: {e}.")

        threading.Thread(target=worker, daemon=True).start()

    def _log(self, sender: str, message: str):
        """Appends a message safely to the chat transcript."""
        def append():
            self.feed.config(state="normal")
            timestamp = time.strftime("[%H:%M:%S] ")
            self.feed.insert("end", timestamp, "system")

            if sender.lower() == "jarvis":
                self.feed.insert("end", f"{sender}: ", "jarvis")
            elif sender.lower() == "user":
                self.feed.insert("end", f"{sender}: ", "user")
            else:
                self.feed.insert("end", f"{sender}: ", "system")

            self.feed.insert("end", f"{message}\n", "body")
            self.feed.see("end")
            self.feed.config(state="disabled")

        self.root.after(0, append)

    def _initial_greeting(self):
        """Greets user on initial start with voice."""
        time.sleep(0.5)
        jarvis.speak("Hello, what can I help you with?")

    def _clear_feed(self):
        self.feed.config(state="normal")
        self.feed.delete("1.0", "end")
        self.feed.config(state="disabled")

    def _on_text_submit(self):
        query = self.entry.get().strip()
        if not query:
            return
        self.entry.delete(0, "end")
        self._send_command(query)

    def _send_command(self, query: str):
        """Dispatches command to background execution thread."""
        self._log("User", query)
        threading.Thread(target=self._process_command_worker, args=(query,), daemon=True).start()

    def _start_voice_thread(self):
        """Starts listening in a background thread."""
        if self.is_listening:
            return
        threading.Thread(target=self._voice_worker, daemon=True).start()

    def _voice_worker(self):
        self.is_listening = True
        self.mic_btn.config(text="● LISTENING... SPEAK NOW", bg=ACCENT_AMBER)

        query = jarvis.takecommand(device_index=self.selected_device_index)

        self.is_listening = False
        self.mic_btn.config(text="🎙️ ACTIVATE VOICE PROTOCOL", bg=ACCENT_CYAN)

        if query:
            self._log("User", query)
            self._process_command_worker(query)

    def _process_command_worker(self, query: str):
        """Executes the command smoothly via non-blocking Queue TTS."""
        self.is_speaking = True
        try:
            continue_running = jarvis.execute_command(query)
            if not continue_running:
                self.root.after(1400, self.root.destroy)
        except Exception as e:
            self._log("Jarvis", f"An error occurred: {e}")
        finally:
            self.is_speaking = False


def run_gui():
    root = tk.Tk()
    app = JarvisStarkHUD(root)
    root.mainloop()


if __name__ == "__main__":
    run_gui()
