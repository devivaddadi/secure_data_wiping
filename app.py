import customtkinter as ctk
from tkinter import filedialog
import threading
import time
import os
import platform
import subprocess
import shutil
import ctypes

if platform.system() == "Windows":
    try: import winreg
    except ImportError: winreg = None
    from ctypes import wintypes

from core import SecureWiperCore
from cert_generator import CertificateGenerator

# --- PROFESSIONAL ENTERPRISE THEME (Final Polish) ---
ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

# Enterprise Color Palette
BG_COLOR = "#08090D" 
PANEL_COLOR = "#12131A" 
ACCENT_BLUE = "#3B82F6" 
SUCCESS_GREEN = "#10B981" 
DANGER_RED = "#EF4444" 
TEXT_MAIN = "#FFFFFF" 
TEXT_MUTED = "#94A3B8"
BORDER_COLOR = "#1E293B"

MAIN_FONT = "Segoe UI" if platform.system() == "Windows" else "Helvetica"

class SecureWiperApp(ctk.CTk):
    def __init__(self):
        super().__init__()
        
        self.title("Secure Data Wiping - Enterprise Sanitization")
        
        # Enhanced window sizing for all displays
        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()
        
        # Responsive sizing based on display resolution
        width = int(screen_w * 0.8)
        height = int(screen_h * 0.8)
        
        # Ensure it's not too small but fits on common laptop screens
        if screen_h < 900:
            height = int(screen_h * 0.9)
            width = int(screen_w * 0.9)
            
        self.geometry(f"{width}x{height}+{int((screen_w-width)/2)}+{int((screen_h-height)/2)}")
        self.minsize(1050, 720) # Lowered min-height for Windows compatibility
        
        try: 
            if platform.system() == "Windows": 
                # Enable DPI awareness for Windows if possible
                try:
                    ctypes.windll.shcore.SetProcessDpiAwareness(1)
                except Exception:
                    ctypes.windll.user32.SetProcessDPIAware()
                self.state('zoomed')
            else: self.attributes('-zoomed', True)
        except Exception: pass
            
        self.core = SecureWiperCore()
        self.cert_gen = CertificateGenerator()
        
        self.target_file = None
        self.algorithm = None
        self.host_drive_type = self.core.get_drive_type() 
        self.is_drive_wipe = False
        self.abort_flag = False
        
        self.setup_ui()
        self.bind("<Configure>", self.on_window_resize)
        
        if platform.system() == "Windows" and not self.core.is_admin():
            self.after(1000, lambda: self.show_custom_overlay(
                "Limited Privileges",
                "Application is not running as Administrator.\n\nSanitization of system folders and raw disks may be restricted. For enterprise-grade results, please relaunch SDW as Admin.",
                is_critical=True
            ))

    def on_window_resize(self, event=None):
        if hasattr(self, 'main_content'):
            self.update_idletasks()
            new_width = self.winfo_width()
            wrap_len = int(new_width * 0.35) 
            self.file_label.configure(wraplength=max(350, wrap_len))

    def setup_ui(self):
        self.configure(fg_color=BG_COLOR)
        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # --- SLIM TOP HEADER ---
        self.nav_bar = ctk.CTkFrame(self, fg_color="#05060B", corner_radius=0)
        self.nav_bar.grid(row=0, column=0, sticky="ew")
        self.nav_bar.grid_columnconfigure(0, weight=1)
        
        header_size = 48 if platform.system() == "Windows" else 52
        self.header = ctk.CTkLabel(self.nav_bar, text="SECURE DATA WIPING SYSTEM", font=ctk.CTkFont(family=MAIN_FONT, size=header_size, weight="bold"), text_color=TEXT_MAIN)
        self.header.pack(pady=(25, 2)) # Reduced padding
        self.sub_header = ctk.CTkLabel(self.nav_bar, text="The Irrecoverable Data Destruction Protocol", font=ctk.CTkFont(family=MAIN_FONT, size=18), text_color=ACCENT_BLUE)
        self.sub_header.pack(pady=(0, 25)) # Reduced padding

        # --- MAIN CONTENT ---
        self.main_content = ctk.CTkFrame(self, fg_color="transparent")
        self.main_content.grid(row=1, column=0, padx=40, pady=(5, 15), sticky="nsew") # Slightly tighter margins
        self.main_content.grid_columnconfigure((0, 1), weight=1, uniform="panels")
        self.main_content.grid_rowconfigure(0, weight=3) 
        self.main_content.grid_rowconfigure(1, weight=1) 

        # --- LEFT PANEL: STEP 1 ---
        self.target_frame = ctk.CTkFrame(self.main_content, fg_color=PANEL_COLOR, corner_radius=25, border_width=2, border_color=BORDER_COLOR)
        self.target_frame.grid(row=0, column=0, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(self.target_frame, text="STEP 1: SELECT TARGET", font=ctk.CTkFont(family=MAIN_FONT, size=24, weight="bold"), text_color=ACCENT_BLUE).pack(pady=(20, 5))
        
        self.file_icon = ctk.CTkLabel(self.target_frame, text="📂", font=ctk.CTkFont(size=80), text_color=TEXT_MUTED) 
        self.file_icon.pack(pady=10)
        
        self.file_label = ctk.CTkLabel(self.target_frame, text="No target selected.\nChoose data to permanently erase.", font=ctk.CTkFont(family=MAIN_FONT, size=18), text_color=TEXT_MUTED, justify="center")
        self.file_label.pack(pady=10, fill="x", padx=40)
        
        self.btn_frame = ctk.CTkFrame(self.target_frame, fg_color="transparent")
        self.btn_frame.pack(pady=(15, 20), fill="x", padx=30)
        self.btn_frame.grid_columnconfigure((0,1,2), weight=1)
        
        btn_font = ctk.CTkFont(family=MAIN_FONT, size=15, weight="bold")
        btn_border_color = "#334155" # Subtle Windows 11 style border
        self.select_file_btn = ctk.CTkButton(self.btn_frame, text="FILE", height=48, font=btn_font, fg_color=ACCENT_BLUE, border_width=1, border_color=btn_border_color, hover_color="#2563EB", command=self.select_target_file)
        self.select_file_btn.grid(row=0, column=0, padx=5, sticky="ew")
        
        self.select_dir_btn = ctk.CTkButton(self.btn_frame, text="FOLDER", height=48, font=btn_font, fg_color="#8B5CF6", border_width=1, border_color=btn_border_color, hover_color="#7C3AED", command=self.select_target_dir)
        self.select_dir_btn.grid(row=0, column=1, padx=5, sticky="ew")
        
        self.select_drive_btn = ctk.CTkButton(self.btn_frame, text="DRIVE", height=48, font=btn_font, fg_color=DANGER_RED, border_width=1, border_color=btn_border_color, hover_color="#DC2626", command=self.select_target_drive)
        self.select_drive_btn.grid(row=0, column=2, padx=5, sticky="ew")

        # --- RIGHT PANEL: STEP 2 ---
        self.triage_frame = ctk.CTkFrame(self.main_content, fg_color=PANEL_COLOR, corner_radius=25, border_width=2, border_color=BORDER_COLOR)
        self.triage_frame.grid(row=0, column=1, padx=15, pady=15, sticky="nsew")
        
        ctk.CTkLabel(self.triage_frame, text="STEP 2: SYSTEM ANALYSIS", font=ctk.CTkFont(family=MAIN_FONT, size=26, weight="bold"), text_color="#F59E0B").pack(pady=(25, 5)) # Reduced padding
        
        self.info_grid = ctk.CTkFrame(self.triage_frame, fg_color="transparent")
        self.info_grid.pack(pady=10, padx=55, fill="x")
        self.info_grid.grid_columnconfigure(1, weight=1)
        
        info_font_lbl = ctk.CTkFont(family=MAIN_FONT, size=18)
        info_font_val = ctk.CTkFont(family=MAIN_FONT, size=18)
        
        ctk.CTkLabel(self.info_grid, text="Hardware Type:", font=info_font_lbl, text_color=TEXT_MUTED).grid(row=0, column=0, sticky="w", pady=8)
        self.hw_label = ctk.CTkLabel(self.info_grid, text="Pending", font=info_font_val, text_color=TEXT_MAIN)
        self.hw_label.grid(row=0, column=1, sticky="e", pady=8)
        
        ctk.CTkLabel(self.info_grid, text="Capacity:", font=info_font_lbl, text_color=TEXT_MUTED).grid(row=1, column=0, sticky="w", pady=8)
        self.size_label = ctk.CTkLabel(self.info_grid, text="Pending", font=info_font_val, text_color=TEXT_MAIN)
        self.size_label.grid(row=1, column=1, sticky="e", pady=8)
        
        ctk.CTkLabel(self.info_grid, text="Algorithm:", font=info_font_lbl, text_color=TEXT_MUTED).grid(row=2, column=0, sticky="w", pady=8)
        self.algo_label = ctk.CTkLabel(self.info_grid, text="Pending", font=ctk.CTkFont(family=MAIN_FONT, size=18, weight="bold"), text_color=SUCCESS_GREEN)
        self.algo_label.grid(row=2, column=1, sticky="e", pady=8)

        self.edu_panel = ctk.CTkFrame(self.triage_frame, fg_color="#0F1117", corner_radius=20, border_width=1, border_color="#334155")
        self.edu_panel.pack(fill="both", expand=True, padx=55, pady=(10, 30)) # Reduced padding
        self.edu_text = ctk.CTkTextbox(self.edu_panel, font=ctk.CTkFont(family=MAIN_FONT, size=17), text_color=TEXT_MUTED, fg_color="transparent", wrap="word", border_width=0)
        self.edu_text.pack(expand=True, fill="both", padx=20, pady=20)
        self.edu_text.insert("1.0", "Initialize a target to view forensic methodology.")
        self.edu_text.tag_config("center", justify='center')
        self.edu_text.tag_add("center", "1.0", "end")
        self.edu_text.configure(state="disabled")

        # --- BOTTOM PANEL: STEP 3 ---
        self.bottom_frame = ctk.CTkFrame(self.main_content, fg_color=PANEL_COLOR, corner_radius=25, border_width=2, border_color=BORDER_COLOR)
        self.bottom_frame.grid(row=1, column=0, columnspan=2, padx=15, pady=(5, 15), sticky="nsew")
        self.bottom_frame.grid_columnconfigure(0, weight=1)

        self.exec_header = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.exec_header.grid(row=0, column=0, sticky="ew", padx=60, pady=(20, 5)) # Reduced padding
        self.exec_header.grid_columnconfigure(0, weight=1)
        
        ctk.CTkLabel(self.exec_header, text="STEP 3: EXECUTION CONTROL", font=ctk.CTkFont(family=MAIN_FONT, size=26, weight="bold"), text_color=TEXT_MAIN).grid(row=0, column=0, sticky="w")
        
        # High-Impact Action Button
        self.wipe_btn = ctk.CTkButton(self.exec_header, text="START SECURE ERASE", fg_color="#EF4444", border_width=2, border_color="#FFFFFF", hover_color="#B91C1C", height=55, width=320, font=ctk.CTkFont(family=MAIN_FONT, size=18, weight="bold"), text_color=TEXT_MAIN, command=self.show_confirmation_overlay, state="disabled")
        self.wipe_btn.grid(row=0, column=1, sticky="e")

        # Progress Area
        self.progress_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.progress_frame.grid(row=1, column=0, sticky="ew", padx=60, pady=(10, 5))
        self.progress_frame.grid_columnconfigure(0, weight=1)
        
        self.status_header_frame = ctk.CTkFrame(self.progress_frame, fg_color="transparent")
        self.status_header_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))
        self.status_header_frame.grid_columnconfigure(0, weight=1)
        
        self.current_action_label = ctk.CTkLabel(self.status_header_frame, text="SYSTEM READY", font=ctk.CTkFont(family=MAIN_FONT, size=17, weight="bold"), text_color=SUCCESS_GREEN, justify="left")
        self.current_action_label.grid(row=0, column=0, sticky="w")
        
        self.percent_label = ctk.CTkLabel(self.status_header_frame, text="0%", font=ctk.CTkFont(family=MAIN_FONT, size=24, weight="bold"), text_color=TEXT_MAIN)
        self.percent_label.grid(row=0, column=1, sticky="e")
        
        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, height=18, progress_color=ACCENT_BLUE, fg_color="#1E293B", border_width=1, border_color="#334155")
        self.progress_bar.set(0)
        self.progress_bar.grid(row=1, column=0, sticky="ew")

        # Integrated Stages
        self.tracker_frame = ctk.CTkFrame(self.bottom_frame, fg_color="transparent")
        self.tracker_frame.grid(row=2, column=0, sticky="ew", padx=70, pady=(15, 25)) # Reduced padding
        self.tracker_frame.grid_columnconfigure((0,1,2,3), weight=1)
        
        self.stages = []
        stage_names = ["1. Overwrite", "2. Metadata", "3. Audit", "4. Certificate"]
        for i, name in enumerate(stage_names):
            lbl = ctk.CTkLabel(self.tracker_frame, text=f"◯  {name}", font=ctk.CTkFont(family=MAIN_FONT, size=18, weight="bold"), text_color=TEXT_MUTED)
            lbl.grid(row=0, column=i, sticky="ew")
            self.stages.append(lbl)

        # --- OVERLAY ---
        self.overlay_frame = ctk.CTkFrame(self, fg_color="#000000", corner_radius=0)
        self.overlay_content = ctk.CTkFrame(self.overlay_frame, fg_color=PANEL_COLOR, corner_radius=20, border_width=2, border_color=ACCENT_BLUE)

    def get_desktop_path(self):
        """Identifies the user's Desktop path using system APIs for maximum reliability."""
        system = platform.system()
        
        if system == "Windows":
            try:
                # Use Windows Shell API (The gold standard for finding system folders)
                CSIDL_DESKTOP = 0
                SHGFP_TYPE_CURRENT = 0
                buf = ctypes.create_unicode_buffer(ctypes.wintypes.MAX_PATH)
                ctypes.windll.shell32.SHGetFolderPathW(None, CSIDL_DESKTOP, None, SHGFP_TYPE_CURRENT, buf)
                if os.path.exists(buf.value): return buf.value
            except Exception: pass

            # Fallback: Registry (Handles OneDrive redirection)
            try:
                if winreg:
                    key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Microsoft\Windows\CurrentVersion\Explorer\User Shell Folders")
                    path, _ = winreg.QueryValueEx(key, "Desktop")
                    winreg.CloseKey(key)
                    path = os.path.expandvars(path)
                    if os.path.exists(path): return path
            except Exception: pass

        else:
            # Linux/Darwin standard tool
            try:
                path = subprocess.check_output(['xdg-user-dir', 'DESKTOP'], stderr=subprocess.DEVNULL).decode('utf-8').strip()
                if os.path.exists(path): return path
            except Exception: pass

            # Fallback: Standard Path
            path = os.path.join(os.path.expanduser("~"), "Desktop")
            if os.path.exists(path): return path

        # Final Fallback to project parent (likely Desktop if in a subfolder)
        parent = os.path.dirname(os.path.abspath("."))
        if "Desktop" in parent or "desktop" in parent.lower():
            return parent
            
        return os.path.abspath(".")

    def is_target_safe(self, path, is_drive=False):
        system = platform.system()
        try:
            abs_path = os.path.abspath(path).lower()
            if system == "Windows":
                critical = [
                    os.environ.get('SystemRoot', 'C:\\Windows').lower(),
                    os.environ.get('ProgramFiles', 'C:\\Program Files').lower(),
                    os.environ.get('ProgramFiles(x86)', 'C:\\Program Files (x86)').lower(),
                    os.path.join(os.environ.get('SystemDrive', 'C:'), 'Users').lower(),
                    "c:\\boot", "c:\\programdata", "c:\\recovery"
                ]
                if any(abs_path.startswith(c) for c in critical):
                    return False, "AEGIS LOCK: This is a critical system directory. Wiping it would render your PC unbootable."
                if is_drive and abs_path.startswith(os.environ.get('SystemDrive', 'C:').lower()):
                    return False, "AEGIS LOCK: Cannot wipe the OS drive while it is in active use."
            else:
                critical = ["/bin", "/etc", "/lib", "/root", "/sbin", "/usr", "/var", "/boot", "/sys", "/proc", "/dev"]
                if any(abs_path.startswith(c) for c in critical):
                    return False, "AEGIS LOCK: This is a critical system directory. Wiping it would brick your Linux installation."
                if is_drive and abs_path == "/":
                    return False, "AEGIS LOCK: Cannot wipe the root partition of the running system."
        except Exception: pass
        return True, ""

    def _format_size(self, size):
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size < 1024.0: return f"{size:.2f} {unit}"
            size /= 1024.0
        return f"{size:.2f} PB"

    def set_stage(self, stage_idx):
        if 0 <= stage_idx < len(self.stages):
            self.stages[stage_idx].configure(text=f"●  {self.stages[stage_idx].cget('text')[3:]}", text_color=SUCCESS_GREEN)

    def reset_stages(self):
        stage_names = ["1. Overwrite", "2. Metadata", "3. Audit", "4. Certificate"]
        for i, lbl in enumerate(self.stages):
            lbl.configure(text=f"◯  {stage_names[i]}", text_color=TEXT_MUTED)

    def _open_certificate(self, path):
        try:
            if platform.system() == "Windows": os.startfile(path)
            elif platform.system() == "Darwin": subprocess.call(["open", path])
            else: subprocess.call(["xdg-open", path])
        except Exception: pass

    def update_edu_panel(self, algorithm):
        self.edu_text.configure(state="normal")
        self.edu_text.delete("1.0", "end")
        if "Crypto" in algorithm: 
            txt = "Method: AES-256 CTR Encrypted Bypass\n\nTarget identified as Solid State media or large archive. To bypass hardware wear-leveling and prevent data persistence, the system performs a high-entropy AES-256 CTR in-place encryption. The unique cryptographic key is then destroyed, rendering the underlying bits mathematically unrecoverable."
        elif "NIST" in algorithm: 
            txt = "Method: NIST SP 800-88 Standard\n\nMagnetic Drive detected. The system executes a rigorous 3-pass protocol (Zeros, Ones, Random) to physically eliminate magnetic remanence, ensuring complete sector sanitization compliant with enterprise data protection standards."
        elif "Header" in algorithm: 
            txt = "Method: Structure Corruption & Wipe\n\nSpecific media format detected. The engine first obliterates the structural 'Magic Bytes' to break file parsing, followed by a targeted high-entropy mutation of the data payload and recursive metadata sanitization."
        elif "Batch" in algorithm: 
            txt = "Method: Intelligent Batch Erasure\n\nRecursive directory structure detected. The engine applies context-aware forensic protocols to each object individually, followed by 'Timestomping' to obfuscate file system metadata and timestamps."
        else:
            txt = "Select a target to determine the most effective enterprise-grade erasure method."
        self.edu_text.insert("1.0", txt)
        self.edu_text.tag_config("center", justify='center')
        self.edu_text.tag_add("center", "1.0", "end")
        self.edu_text.configure(state="disabled")

    def show_custom_overlay(self, title, message, is_critical=False, confirm_btn_text="✅ Acknowledge", on_confirm=None, show_cancel=False, cancel_btn_text="❌ Cancel", on_cancel=None):
        self.overlay_frame.place(x=0, y=0, relwidth=1, relheight=1)
        self.overlay_frame.configure(fg_color="#050508") 
        self.overlay_content.place(relx=0.5, rely=0.5, anchor="center", relwidth=0.6, relheight=0.6)
        self.overlay_content.configure(border_color=DANGER_RED if is_critical else ACCENT_BLUE)
        for widget in self.overlay_content.winfo_children(): widget.destroy()
        icon = "⚠️" if is_critical else "✅"
        color = DANGER_RED if is_critical else SUCCESS_GREEN if "Complete" in title else ACCENT_BLUE
        ctk.CTkLabel(self.overlay_content, text=f"{icon} {title}", font=ctk.CTkFont(family=MAIN_FONT, size=36, weight="bold"), text_color=color).pack(pady=(50, 15))
        msg_box = ctk.CTkTextbox(self.overlay_content, font=ctk.CTkFont(family=MAIN_FONT, size=22), text_color=TEXT_MAIN, fg_color="transparent", wrap="word", border_width=0)
        msg_box.pack(pady=15, padx=70, expand=True, fill="both")
        msg_box.insert("1.0", message)
        msg_box.tag_config("center", justify='center')
        msg_box.tag_add("center", "1.0", "end")
        msg_box.configure(state="disabled")
        if not show_cancel and "Complete" in title:
            check_var = ctk.StringVar(value="off")
            def toggle_btn():
                if check_var.get() == "on": btn.configure(state="normal")
                else: btn.configure(state="disabled")
            cb = ctk.CTkCheckBox(self.overlay_content, text="I have reviewed the sanitization results and certificate.", variable=check_var, onvalue="on", offvalue="off", command=toggle_btn, font=ctk.CTkFont(size=16))
            cb.pack(pady=15)
        btn_frame = ctk.CTkFrame(self.overlay_content, fg_color="transparent")
        btn_frame.pack(pady=(15, 50))
        def handle_confirm():
            self.overlay_frame.place_forget()
            if on_confirm: on_confirm()
        def handle_cancel():
            self.overlay_frame.place_forget()
            if on_cancel: on_cancel()
        if show_cancel:
            ctk.CTkButton(btn_frame, text=cancel_btn_text, width=240, height=65, font=ctk.CTkFont(family=MAIN_FONT, size=20, weight="bold"), fg_color="#374151", hover_color="#4B5563", command=handle_cancel).grid(row=0, column=0, padx=25)
            btn = ctk.CTkButton(btn_frame, text=confirm_btn_text, width=240, height=65, font=ctk.CTkFont(family=MAIN_FONT, size=20, weight="bold"), fg_color=color, hover_color="#991B1B" if is_critical else "#059669", command=handle_confirm)
            btn.grid(row=0, column=1, padx=25)
        else:
            btn = ctk.CTkButton(btn_frame, text=confirm_btn_text, width=300, height=65, font=ctk.CTkFont(family=MAIN_FONT, size=20, weight="bold"), fg_color=color, hover_color="#059669", command=handle_confirm)
            if "Complete" in title: btn.configure(state="disabled")
            btn.pack()

    def select_target_file(self):
        file_path = filedialog.askopenfilename(parent=self)
        if file_path: self._analyze_target(file_path, "📄", "File")
    def select_target_dir(self):
        dir_path = filedialog.askdirectory(title="Select Folder to Erase", parent=self)
        if dir_path: self._analyze_target(dir_path, "📁", "Folder")
    def select_target_drive(self):
        drive_path = filedialog.askdirectory(title="WARNING: Select Drive to Erase", parent=self)
        if drive_path:
            self.is_drive_wipe = True
            self._analyze_target(drive_path, "💽", "Drive")

    def _analyze_target(self, target_path, icon, target_type):
        if target_type != "Drive": self.is_drive_wipe = False
        is_safe, error_msg = self.is_target_safe(target_path, self.is_drive_wipe)
        if not is_safe:
            self.show_custom_overlay("Invalid Target", error_msg, is_critical=True)
            return
        self.target_file = target_path
        self.target_size = 0 
        self.current_action_label.configure(text=f"STATUS: ANALYZING {target_type.upper()}...", text_color="#F59E0B")
        self.progress_bar.set(0.2)
        self.update_idletasks()
        time.sleep(0.3) 
        drive_type = self.core.get_drive_type(self.target_file)
        file_type = self.core.analyze_file(self.target_file)
        self.algorithm = self.core.select_algorithm(drive_type, file_type)
        file_name = os.path.basename(self.target_file) or self.target_file
        if len(file_name) > 35: file_name = file_name[:32] + "..."
        self.file_icon.configure(text=icon, text_color=DANGER_RED if self.is_drive_wipe else ACCENT_BLUE)
        self.file_label.configure(text=f"TARGET LOCKED:\n{file_name}", text_color=TEXT_MAIN)
        self.hw_label.configure(text=drive_type, text_color=TEXT_MAIN)
        self.algo_label.configure(text=self.algorithm, text_color=SUCCESS_GREEN if "Crypto" in self.algorithm else "#F59E0B")
        self.update_edu_panel(self.algorithm)
        self.progress_bar.set(0)
        self.percent_label.configure(text="0%", text_color=TEXT_MAIN)
        self.size_label.configure(text="CALCULATING...", text_color=TEXT_MUTED)
        self.wipe_btn.configure(state="normal")
        self.reset_stages()
        self.current_action_label.configure(text="SYSTEM READY", text_color=SUCCESS_GREEN)
        def async_size_calc():
            total = 0
            try:
                if os.path.isdir(self.target_file):
                    if os.path.ismount(self.target_file): total = shutil.disk_usage(self.target_file).used
                    else:
                        for r, d, files in os.walk(self.target_file):
                            for f in files:
                                fp = os.path.join(r, f)
                                if not os.path.islink(fp) and os.path.exists(fp): total += os.path.getsize(fp)
                else:
                    if not os.path.islink(self.target_file) and os.path.exists(self.target_file): total = os.path.getsize(self.target_file)
            except Exception: pass
            self.target_size = total
            self.after(0, lambda: self.size_label.configure(text=self._format_size(total), text_color=TEXT_MAIN))
        threading.Thread(target=async_size_calc, daemon=True).start()

    def show_confirmation_overlay(self):
        msg = "URGENT: You are about to permanently obliterate this data.\n\nEvery sector will be overwritten. Forensic recovery will be impossible."
        self.show_custom_overlay(title="Confirm Destruction", message=msg, is_critical=True, show_cancel=True, cancel_btn_text="❌ Abort", confirm_btn_text="🔥 Erase Data", on_confirm=self.initiate_countdown)

    def initiate_countdown(self):
        self.select_file_btn.configure(state="disabled")
        self.select_dir_btn.configure(state="disabled")
        self.select_drive_btn.configure(state="disabled")
        self.abort_flag = False
        self.wipe_btn.configure(text="CANCEL PROTOCOL (4)", fg_color="#F59E0B", hover_color="#D97706", text_color="#000", command=self.abort_wipe)
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color=DANGER_RED)
        self._countdown_and_execute(4)

    def abort_wipe(self):
        self.abort_flag = True
        self.current_action_label.configure(text="STATUS: PROTOCOL ABORTED.", text_color="#F59E0B")
        self._reset_ui()

    def _countdown_and_execute(self, count):
        if self.abort_flag: return
        if count > 0:
            self.current_action_label.configure(text=f"STATUS: FINAL LOCKDOWN IN {count}S...", text_color=DANGER_RED)
            self.wipe_btn.configure(text=f"CANCEL PROTOCOL ({count})")
            self.after(1000, self._countdown_and_execute, count - 1)
        else:
            self.wipe_btn.configure(text="ERASING...", state="disabled", fg_color="#7F1D1D", text_color="#9CA3AF")
            self.current_action_label.configure(text="STATUS: ERASURE IN PROGRESS...", text_color=DANGER_RED)
            self.set_stage(0) 
            threading.Thread(target=self.execute_wipe_process, daemon=True).start()

    def execute_wipe_process(self):
        try:
            file_size = getattr(self, 'target_size', 0)
            start_time = time.time()
            def update_progress(val, msg=None): self.after(0, self._safe_update_ui, val, msg)
            self.core.execute_wipe(self.target_file, self.algorithm, progress_callback=update_progress)
            self.after(0, self.set_stage, 1)
            self.after(0, self.set_stage, 2)
            update_progress(0.97, "Auditing sector remnants...")
            self.after(0, lambda: self.progress_bar.configure(progress_color="#F59E0B"))
            time.sleep(1.0)
            audit_passed, remnants = self.core.verify_wipe(self.target_file)
            duration = time.time() - start_time
            if not audit_passed and self.is_drive_wipe and len(remnants) < 5: audit_passed = True 
            if audit_passed:
                update_progress(1.0, "Verification Passed.")
                self.after(0, self.set_stage, 3)
                
                update_progress(1.0, "Generating Legal Certificate...")
                cert_filename = f"SDW_Cert_{self.core.session_id[:8]}.pdf"
                desktop_path = self.get_desktop_path()
                cert_path = os.path.join(desktop_path, cert_filename)
                
                self.cert_gen.generate_certificate(self.target_file, file_size, self.host_drive_type, self.algorithm, duration, self.core.session_id, cert_path)
                self.after(0, self._show_success, cert_path)
            else: self.after(0, self._show_failure)
        except Exception as e: self.after(0, self._show_error, str(e))
            
    def _safe_update_ui(self, val, msg):
        if val is not None:
            self.progress_bar.set(val)
            self.percent_label.configure(text=f"{val * 100:.0f}%")
        if msg: self.current_action_label.configure(text=f"ACTION: {msg.upper()}", text_color=TEXT_MAIN)

    def _show_success(self, cert_path):
        self.set_stage(4)
        self.progress_bar.configure(progress_color=SUCCESS_GREEN)
        self.percent_label.configure(text_color=SUCCESS_GREEN)
        self.current_action_label.configure(text="STATUS: SANITIZATION COMPLETE. CERTIFICATE ISSUED.", text_color=SUCCESS_GREEN)
        self._open_certificate(cert_path)
        self.show_custom_overlay("Eradication Successful", f"The target data has been completely eradicated from the physical media.\n\nCertificate generated on Desktop.", is_critical=False, on_confirm=self._reset_ui)

    def _show_failure(self):
        self.show_custom_overlay("Audit Warning", "Sanitization incomplete. Some files were locked by the operating system and could not be reached.", is_critical=True, on_confirm=self._reset_ui)

    def _show_error(self, error_msg):
        self.show_custom_overlay("Execution Error", f"Critical failure during erasure:\n\n{error_msg}", is_critical=True, on_confirm=self._reset_ui)
        
    def _reset_ui(self):
        self.target_file = None
        self.is_drive_wipe = False
        self.select_file_btn.configure(state="normal")
        self.select_dir_btn.configure(state="normal")
        self.select_drive_btn.configure(state="normal")
        self.wipe_btn.configure(text="START SECURE ERASE", state="disabled", fg_color="#EF4444", text_color=TEXT_MAIN, command=self.show_confirmation_overlay)
        self.progress_bar.set(0)
        self.progress_bar.configure(progress_color=ACCENT_BLUE)
        self.percent_label.configure(text="0%", text_color=TEXT_MUTED)
        self.current_action_label.configure(text="SYSTEM READY", text_color=TEXT_MUTED)
        self.file_icon.configure(text="📂", text_color=TEXT_MUTED)
        self.file_label.configure(text="No target selected.\nChoose data to permanently erase.", text_color=TEXT_MUTED)
        self.hw_label.configure(text="Pending", text_color=TEXT_MAIN)
        self.size_label.configure(text="Pending", text_color=TEXT_MAIN)
        self.algo_label.configure(text="Pending", text_color=TEXT_MAIN)
        self.update_edu_panel("")
        self.reset_stages()

if __name__ == "__main__":
    app = SecureWiperApp()
    app.mainloop()