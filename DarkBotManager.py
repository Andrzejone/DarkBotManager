#!/usr/bin/env python3
"""
DarkBot Manager - Tkinter GUI tool
- Config stored in %APPDATA%/DarkBotManager/config.json
- Detects bot folders under a selected root
- Cleans logs (*.log), plugins/old (*.jar), plugins/updates (all)
- Copies DarkBot.jar to bot root (only file named exactly "DarkBot.jar")
- Copies plugin .jar files (except DarkBot.jar) from plugin_updates_source -> bot/plugins/updates
- No external dependencies (pure stdlib)
"""

import os
import sys
import json
import locale
import shutil
import threading
import traceback
import webbrowser
from pathlib import Path
from tkinter import (
    Tk, Toplevel, Frame, Label, Entry, Button, Listbox, Scrollbar,
    END, MULTIPLE, messagebox, filedialog, StringVar, LEFT, RIGHT, BOTH, Y, X, VERTICAL
)
import tkinter as tk
from tkinter import ttk
from tkinter import PhotoImage
from ttkbootstrap.scrolled import ScrolledText
from ttkbootstrap import Style

APPNAME = "DarkBotManager - Saimon favourite tool"
CONFIG_DIR = Path(os.getenv("APPDATA", Path.home() / "AppData" / "Roaming")) / "DarkBotManager"
CONFIG_FILE = CONFIG_DIR / "config.json"
translations_path = CONFIG_DIR / "translations.json"
DEFAULT_CONFIG = {
    "bots_root": "",                     # root folder containing individual bot folders (1..N)
    "darkbot_jar_path": "",              # full path to updated DarkBot.jar
    "plugin_updates_folder": "",          # folder containing plugin .jar update files
    "language": "en"                     # default language.
}

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except AttributeError:
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)

def ensure_config():
    """Ensure config dir and file exist. Return config dict."""
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    if not CONFIG_FILE.exists():
        with open(CONFIG_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CONFIG, f, indent=2)
        return DEFAULT_CONFIG.copy()
    try:
        with open(CONFIG_FILE, "r", encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception:
        cfg = DEFAULT_CONFIG.copy()
    # ensure keys exist
    changed = False
    for k, v in DEFAULT_CONFIG.items():
        if k not in cfg:
            cfg[k] = v
            changed = True
    if changed:
        save_config(cfg)
    return cfg


def save_config(cfg):
    CONFIG_DIR.mkdir(parents=True, exist_ok=True)
    with open(CONFIG_FILE, "w", encoding="utf-8") as f:
        json.dump(cfg, f, indent=2)


def is_bot_folder(p: Path) -> bool:
    """Heuristic: a bot folder should be a directory and contain subfolders like logs or plugins."""
    if not p.is_dir():
        return False
    # simple heuristics: has logs or plugins folder
    if (p / "logs").exists() or (p / "plugins").exists():
        return True
    # fallback: treat any directory child of bots_root as bot
    return True


def ensure_translations():
    """Ensure translations.json exists in CONFIG_DIR, copy from bundle if necessary."""
    # Get path to bundled translations.json
    if getattr(sys, 'frozen', False):
        bundled_path = os.path.join(sys._MEIPASS, 'translations.json')
    else:
        # For development mode, assume it's in the script directory
        bundled_path = os.path.join(os.path.dirname(__file__), 'translations.json')

    target_path = translations_path

    if not os.path.exists(bundled_path):
        # If bundled file doesn't exist (e.g., dev mode without file), skip or handle error
        print(f"Warning: Bundled translations.json not found at {bundled_path}")
        return

    CONFIG_DIR.mkdir(parents=True, exist_ok=True)

    if not target_path.exists():
        shutil.copy(bundled_path, target_path)
        print(f"Copied translations.json to {target_path}")
        return

    # Compare contents
    with open(bundled_path, 'rb') as f_bundled, open(target_path, 'rb') as f_target:
        if f_bundled.read() != f_target.read():
            shutil.copy(bundled_path, target_path)
            print(f"Updated translations.json at {target_path}")
        else:
            print(f"translations.json is up to date at {target_path}")


class Translator:
    def __init__(self, translations_path: Path, forced_lang=None):
        self.translations_path = translations_path
        self.translations = self._load()
        self.lang = forced_lang or self._detect_lang()

        if self.lang not in self.translations:
            self.lang = "en"

    def _load(self):
        try:
            with open(self.translations_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}

    def _detect_lang(self):
        try:
            loc = locale.getdefaultlocale()[0]
            return loc.split("_")[0] if loc else "en"
        except Exception:
            return "en"

    def set_language(self, lang: str):
        self.lang = lang if lang in self.translations else "en"

    def t(self, key: str, **kwargs):
        text = self.translations.get(self.lang, {}).get(key, key)
        try:
            return text.format(**kwargs)
        except Exception:
            return text

class DarkBotManagerGUI:
    def __init__(self, root):
        self.root = root
        self.cfg = ensure_config()
        ensure_translations()  # Ensure translations before initializing translator
        self.translator = Translator(CONFIG_DIR / "translations.json", forced_lang=self.cfg.get("language"))
        self.tr = self.translator
        root.geometry("737x563")
        root.resizable(False, False)
        icon_path = resource_path("kekw.ico")
        if os.path.exists(icon_path):
            try:
                self.root.iconbitmap(icon_path)
            except Exception:
                pass
        self.style = Style(theme="darkly")
        self.root.title(self.tr.t("app_title"))
        self._build_ui()
        self.refresh_bot_list()

    def _build_ui(self):
        # Top control frame
        top = ttk.Frame(self.root, padding=6)
        top.pack(fill=X)

        self.bot_root_label = ttk.Label(top, text=self.tr.t("bot_root"))
        self.bot_root_label.translation_key = "bot_root"  # Dodany atrybut
        self.bot_root_label.pack(side=LEFT)
        self.bots_root_var = StringVar(value=self.cfg.get("bots_root", ""))
        self.bots_root_entry = ttk.Entry(top, textvariable=self.bots_root_var, width=49)
        self.bots_root_entry.pack(side=LEFT, padx=6)
        self.browse_bots_root_btn = ttk.Button(top, text=self.tr.t("bot_root_select"), command=self.browse_bots_root)
        self.browse_bots_root_btn.translation_key = "bot_root_select"  # Dodany atrybut
        self.browse_bots_root_btn.pack(side=LEFT)
        self.settings_btn = ttk.Button(top, text=self.tr.t("menu_settings"), command=self.open_settings)
        self.settings_btn.translation_key = "menu_settings"  # Dodany atrybut
        self.settings_btn.pack(side=LEFT, padx=6)
        self.config_folder_btn = ttk.Button(top, text=self.tr.t("settings_folder"), command=self.open_config_folder)
        self.config_folder_btn.translation_key = "settings_folder"  # Dodany atrybut
        self.config_folder_btn.pack(side=LEFT)
        self.extra_btn = ttk.Button(top, text=self.tr.t("extra_btn"), command=self.open_extra_links)
        self.extra_btn.translation_key = "extra_btn"  # Dodany atrybut
        self.extra_btn.pack(side=RIGHT, padx=2)

        # Middle: list of detected bot folders
        mid = ttk.Frame(self.root, padding=6)
        mid.pack(fill=BOTH, expand=True)

        lb_frame = ttk.Frame(mid)
        lb_frame.pack(side=LEFT, fill=BOTH, expand=True)

        self.folder_list_label = ttk.Label(lb_frame, text=self.tr.t("folder_list"))
        self.folder_list_label.translation_key = "folder_list"  # Dodany atrybut
        self.folder_list_label.pack(anchor="w")
        self.listbox = tk.Listbox(
            lb_frame,
            selectmode=MULTIPLE,
            width=60, height=12,
            bg=self.style.lookup("TFrame", "background"),
            fg=self.style.lookup("TLabel", "foreground"),
            highlightbackground=self.style.lookup("TLabel", "foreground"),
            selectbackground=self.style.lookup("TButton", "background"),
        )
        self.listbox.pack(side=LEFT, fill=BOTH, expand=True)
        scrollbar = ttk.Scrollbar(lb_frame, orient=VERTICAL, command=self.listbox.yview)
        scrollbar.pack(side=RIGHT, fill=Y)
        self.listbox.config(yscrollcommand=scrollbar.set)

        # Right controls (operations)
        right = ttk.Frame(mid, padding=6)
        right.pack(side=RIGHT, fill=Y)

        self.refresh_list_btn = ttk.Button(right, text=self.tr.t("btn_refresh_list"), width=30, command=self.refresh_bot_list)
        self.refresh_list_btn.translation_key = "btn_refresh_list"  # Dodany atrybut
        self.refresh_list_btn.pack(pady=6)
        self.clear_update_selected_btn = ttk.Button(right, text=self.tr.t("btn_clear_update_selected"), width=30, command=self.run_on_selected)
        self.clear_update_selected_btn.translation_key = "btn_clear_update_selected"  # Dodany atrybut
        self.clear_update_selected_btn.pack(pady=6)
        self.clear_update_all_btn = ttk.Button(right, text=self.tr.t("btn_clear_update_all"), width=30, command=self.run_on_all)
        self.clear_update_all_btn.translation_key = "btn_clear_update_all"  # Dodany atrybut
        self.clear_update_all_btn.pack(pady=6)
        self.clear_logsold_btn = ttk.Button(right, text=self.tr.t("btn_clear_logsold"), width=30, command=self.clear_old_logs)
        self.clear_logsold_btn.translation_key = "btn_clear_logsold"  # Dodany atrybut
        self.clear_logsold_btn.pack(pady=6)
        self.validate_paths_btn = ttk.Button(right, text=self.tr.t("btn_validate_paths"), width=30, command=self.validate_paths_and_report)
        self.validate_paths_btn.translation_key = "btn_validate_paths"  # Dodany atrybut
        self.validate_paths_btn.pack(pady=6)
        # Log area
        log_frame = ttk.Frame(self.root, padding=6)
        log_frame.pack(fill=BOTH, expand=True)
        self.log_label = ttk.Label(log_frame, text=self.tr.t("log_label"))
        self.log_label.translation_key = "log_label"  # Dodany atrybut
        self.log_label.pack(anchor="w")
        try:
            bg = self.style.lookup("TFrame", "background") or "#222222"
            fg = self.style.lookup("TLabel", "foreground") or "#ffffff"
        except Exception:
            bg = "#222222"
            fg = "#ffffff"
        self.log = ScrolledText(
            log_frame,
            height=12, state="disabled",
            bg=bg,
            fg=fg,
            insertbackground=fg,
            relief="flat",
            wrap="word"
        )
        self.log.pack(fill=BOTH, expand=True)

        # Progress bar
        bottom = ttk.Frame(self.root, padding=(6, 6, 6, 6))
        bottom.pack(fill=X)
        self.progress = ttk.Progressbar(bottom, orient="horizontal", mode="determinate", bootstyle="success-striped")
        self.progress.pack(fill=X, expand=True)
        self.footer_discord_label = ttk.Label(text="Discord: crazygirl3598", foreground="lightblue")
        self.footer_discord_label.pack(side="right")
        self.footer_text_label = ttk.Label(text=self.tr.t("footer_text"), foreground="lightblue")
        self.footer_text_label.translation_key = "footer_text"  # Dodany atrybut
        self.footer_text_label.pack(side="left")

    def refresh_texts(self, widget=None):
        """Rekurencyjne odświeżanie tekstów w wszystkich widgetach z atrybutem translation_key."""
        if widget is None:
            widget = self.root  # Zaczynamy od roota
            self.root.title(self.tr.t("app_title"))  # Odśwież tytuł okna
        
        if hasattr(widget, 'translation_key'):
            key = widget.translation_key
            widget.config(text=self.tr.t(key))
        
        for child in widget.winfo_children():
            self.refresh_texts(child)

    def browse_bots_root(self):
        p = filedialog.askdirectory(title=self.tr.t("window_select_bot_root"), initialdir=self.bots_root_var.get() or None)
        if p:
            self.bots_root_var.set(p)
            self.cfg["bots_root"] = p
            save_config(self.cfg)
            self.refresh_bot_list()

    def open_config_folder(self):
        try:
            os.startfile(str(CONFIG_DIR))
        except Exception:
            messagebox.showinfo(self.tr.t("window_config_folder_error"), self.tr.t("window_config_folder_error_msg").format(path=CONFIG_DIR))

    def open_settings(self):
        S = Toplevel(self.root)
        S.withdraw()  # Ukrywanie na start
        S.title(self.tr.t("window_settings_title"))
        S.resizable(False, False)
        # Wyśrodkowanie...
        self.root.update_idletasks()
        x = self.root.winfo_rootx()
        y = self.root.winfo_rooty()
        parent_w = self.root.winfo_width()
        parent_h = self.root.winfo_height()

        w = 599
        h = 285

        S.geometry(f"{w}x{h}+{x + parent_w//2 - w//2}+{y + parent_h//2 - h//2}")
        S.deiconify()
        S.lift()
        S.transient(self.root)
        S.grab_set()
        S.focus_force()

        frame = ttk.Frame(S, padding=10)
        frame.pack(fill=BOTH, expand=True)

        def add_row(label_text_key, varname, browse_type="dir"):
            row = ttk.Frame(frame)
            row.pack(fill=X, pady=5)
            label = ttk.Label(row, text=self.tr.t(label_text_key), width=27, anchor="w")
            label.translation_key = label_text_key  # Dodany atrybut dla labeli w ustawieniach
            label.pack(side=LEFT)
            v = StringVar(value=self.cfg.get(varname, ""))
            ent = ttk.Entry(row, textvariable=v, width=50)
            ent.pack(side=LEFT, padx=6)
            def browse():
                S.attributes("-topmost", True)
                S.attributes("-topmost", False)
                if browse_type == "file":
                    p = filedialog.askopenfilename(title=self.tr.t("window_title_openfilename"), initialdir=Path(v.get()).parent if v.get() else None)
                else:
                    p = filedialog.askdirectory(title=self.tr.t("window_title_askdirectory"), initialdir=v.get() or None)
                S.lift()
                S.focus_force()
                if p:
                    v.set(p)
            btn = ttk.Button(row, text=self.tr.t("btn_settings_select"), command=browse)
            btn.translation_key = "btn_settings_select"  # Dodany atrybut
            btn.pack(side=LEFT)
            return v

        v1 = add_row("window_settings_row1", "bots_root", "dir")
        v2 = add_row("window_settings_row2", "darkbot_jar_path", "file")
        v3 = add_row("window_settings_row3", "plugin_updates_folder", "dir")

        def save_and_close():
            self.cfg["bots_root"] = v1.get().strip()
            self.cfg["darkbot_jar_path"] = v2.get().strip()
            self.cfg["plugin_updates_folder"] = v3.get().strip()
            save_config(self.cfg)
            self.bots_root_var.set(self.cfg["bots_root"])
            S.destroy()
            self.refresh_bot_list()
            self.log_info(self.tr.t("window_settings_btn_save_msg"))

        btn_row = ttk.Frame(frame)
        btn_row.pack(fill=X, pady=10)
        save_btn = ttk.Button(btn_row, text=self.tr.t("window_settings_btn_save"), command=save_and_close)
        save_btn.translation_key = "window_settings_btn_save"  # Dodany atrybut
        save_btn.pack(side=LEFT, padx=6)
        cancel_btn = ttk.Button(btn_row, text=self.tr.t("window_settings_btn_cancel"), command=S.destroy)
        cancel_btn.translation_key = "window_settings_btn_cancel"  # Dodany atrybut
        cancel_btn.pack(side=LEFT)

        # === Sekcja wyboru języka ===
        lang_frame = ttk.LabelFrame(frame, text=self.tr.t("label_language_section"), padding=10)
        lang_frame.pack(fill=X, pady=10)

        lang_inner = ttk.Frame(lang_frame)
        lang_inner.pack(fill=X)

        lang_label = ttk.Label(lang_inner, text=self.tr.t("label_language"))
        lang_label.translation_key = "label_language"
        lang_label.pack(side=LEFT)

        langs = ["pl", "en"]
        lang_var = StringVar(value=self.cfg.get("language", self.tr.lang))

        option_menu = ttk.OptionMenu(lang_inner, lang_var, lang_var.get(), *langs)
        option_menu.pack(side=LEFT, padx=10)

        save_lang_btn = ttk.Button(
            lang_inner,
            text=self.tr.t("btn_save_lang"),
            command=lambda: self.save_language(S, lang_var.get())
        )
        save_lang_btn.translation_key = "btn_save_lang"
        save_lang_btn.pack(side=LEFT)

        # Dodajemy translation_key również do LabelFrame
        lang_frame.translation_key = "label_language_section"

        # Odśwież teksty w oknie ustawień
        self.refresh_texts(S)

    def save_language(self, settings_window, new_lang):
        self.cfg["language"] = new_lang
        save_config(self.cfg)
        self.tr.set_language(new_lang)
        settings_window.destroy()  # Zamknij okno ustawień
        self.refresh_texts()  # Globalne odświeżenie głównego UI

    def refresh_bot_list(self):
        self.listbox.delete(0, END)
        bots_root = Path(self.bots_root_var.get().strip()) if self.bots_root_var.get().strip() else None
        if not bots_root or not bots_root.exists():
            self.log_warn(self.tr.t("window_main_warn_no_bot_root"))
            return
        children = sorted([p for p in bots_root.iterdir() if p.is_dir()], key=lambda p: p.name.lower())
        for p in children:
            if is_bot_folder(p):
                self.listbox.insert(END, str(p))
        self.log_info(self.tr.t("window_main_log_loaded_bots", count=self.listbox.size(), root=bots_root))

    def validate_paths_and_report(self):
        msgs = []
        ok = True
        broot = Path(self.cfg.get("bots_root", ""))
        darkjar = Path(self.cfg.get("darkbot_jar_path", ""))
        plugins_src = Path(self.cfg.get("plugin_updates_folder", ""))

        if not broot.exists() or not broot.is_dir():
            msgs.append(self.tr.t("msg_error_validation_root", broot=broot))
            ok = False
        else:
            msgs.append(self.tr.t("msg_info_validation_root", broot=broot))

        if not darkjar.exists() or not darkjar.is_file() or darkjar.name != "DarkBot.jar":
            msgs.append(self.tr.t("msg_error_validation_darkbot_jar", darkjar=darkjar))
            ok = False
        else:
            msgs.append(self.tr.t("msg_info_validation_darkbot_jar", darkjar=darkjar))

        if not plugins_src.exists() or not plugins_src.is_dir():
            msgs.append(self.tr.t("msg_error_validation_plugins_folder", plugins_src=plugins_src))
            ok = False
        else:
            msgs.append(self.tr.t("msg_info_validation_plugins_folder", plugins_src=plugins_src))

        # show a messagebox and log
        if ok:
            self.log_info(self.tr.t("msg_info_validation_paths"))
            messagebox.showinfo(self.tr.t("window_info_name_validation"), "\n".join(msgs))
        else:
            self.log_error(self.tr.t("msg_error_validation_paths"))
            messagebox.showwarning(self.tr.t("window_error_name_validation"), "\n".join(msgs))
        for m in msgs:
            self.log_info(m)

    def open_extra_links(self):
    # Otwiera okno z przydatnymi linkami
        extra_win = Toplevel(self.root)
        extra_win.title(self.tr.t("extra_window_title"))
        extra_win.resizable(False, False)
        extra_win.transient(self.root)
        extra_win.grab_set()

    # Wyśrodkowanie względem głównego okna
        self.root.update_idletasks()
        x = self.root.winfo_rootx() + self.root.winfo_width() // 2 - 300
        y = self.root.winfo_rooty() + self.root.winfo_height() // 2 - 200
        extra_win.geometry(f"600x400+{x}+{y}")

        frame = ttk.Frame(extra_win, padding=15)
        frame.pack(fill=BOTH, expand=True)

        ttk.Label(frame, text=self.tr.t("extra_window_title"), font=("-size", 14, "-weight", "bold")).pack(pady=(0, 15))

    # Lista linków: (tekst_opisowy, url)
        links = [
            ("Java 17", "https://download.oracle.com/java/17/archive/jdk-17.0.12_windows-x64_bin.exe"),
            ("Microsoft Visual C++ 17", "https://aka.ms/vs/17/release/vc_redist.x64.exe"),
            ("DarkBot.eu", "https://darkbot.eu"),
            ("DarkBot - Discord", "https://discord.gg/bEFgxCy"),
            ("DarkBot - GitHub", "https://github.com/darkbot-reloaded/DarkBot"),
        ]

        for description, url in links:
            row = ttk.Frame(frame)
            row.pack(fill=X, pady=6)

            label = ttk.Label(row, text=description, width=40, anchor="w")
            label.pack(side=LEFT)

            open_btn = ttk.Button(row, text=self.tr.t("btn_open_link"), width=12)
            open_btn.configure(command=lambda u=url: webbrowser.open_new(u))
            open_btn.pack(side=LEFT, padx=5)
        # Tłumaczenie przycisku
            try:
                open_btn.translation_key = "btn_open_link"  # dla refresh_texts
            except:
                pass

            copy_btn = ttk.Button(row, text=self.tr.t("btn_copy_link"), width=12)
            copy_btn.configure(command=lambda u=url, w=extra_win: self.copy_to_clipboard(u, w))
            copy_btn.pack(side=LEFT)
            try:
                copy_btn.translation_key = "btn_copy_link"
            except:
                pass

    # Odśwież tłumaczenia w nowym oknie
        self.refresh_texts(extra_win)

    def copy_to_clipboard(self, text: str, parent_window):
        """Kopiuje tekst do schowka i pokazuje potwierdzenie"""
        try:
            self.root.clipboard_clear()
            self.root.clipboard_append(text)
            self.root.update()  # żeby schowek się zaktualizował
        except Exception as e:
            messagebox.showerror("Błąd", f"Nie udało się skopiować: {e}", parent=parent_window)

    # Logging helpers
    def _log(self, text, tag=None):
        self.log.text.configure(state="normal")
        self.log.text.insert(END, text + "\n", tag)
        self.log.text.see(END)
        self.log.text.configure(state="disabled")

    def log_info(self, text):
        self._log(text, "info")

    def log_success(self, text):
        self._log(text, "success")

    def log_warn(self, text):
        self._log("⚠ " + text, "warn")

    def log_error(self, text):
        self._log("✖ " + text, "error")

    def _setup_log_tags(self):
        self.log.tag_config("info", foreground="white")
        self.log.tag_config("success", foreground="green")
        self.log.tag_config("warn", foreground="orange")
        self.log.tag_config("error", foreground="red")

    def start(self):
        self._setup_log_tags()
        self.root.protocol("WM_DELETE_WINDOW", self.on_close)
        self.root.mainloop()

    def on_close(self):
        self.root.destroy()

    # Operation runners
    def run_on_selected(self):
        sel = [self.listbox.get(i) for i in self.listbox.curselection()]
        if not sel:
            messagebox.showinfo(self.tr.t("window_error_selection_none"), self.tr.t("window_error_selection_none_msg"))
            return
        t = threading.Thread(target=self._run_worker, args=(sel,), daemon=True)
        t.start()

    def run_on_all(self):
        all_items = [self.listbox.get(i) for i in range(self.listbox.size())]
        if not all_items:
            messagebox.showinfo(self.tr.t("window_error_selection_empty"), self.tr.t("window_error_selection_empty_msg"))
            return
        t = threading.Thread(target=self._run_worker, args=(all_items,), daemon=True)
        t.start()

        messagebox.showinfo(self.tr.t("window_info_name_done"), self.tr.t("msg_info_done"))

    def clear_old_logs(self):
        all_items = [self.listbox.get(i) for i in range(self.listbox.size())]
        if not all_items:
            messagebox.showinfo(self.tr.t("window_error_selection_empty"), self.tr.t("window_error_selection_empty_msg"))
            return
    
        t = threading.Thread(target=self.clear_old_logs_worker, args=(all_items,), daemon=True)
        t.start()


    def _run_worker(self, bot_paths):
        total = len(bot_paths)
        self.progress["value"] = 0
        self.progress["maximum"] = total
        self.log_info(self.tr.t("log_msg_info_operation_start", total=total))
        darkjar = Path(self.cfg.get("darkbot_jar_path", ""))
        plugin_src = Path(self.cfg.get("plugin_updates_folder", ""))
        errors = 0

        for idx, bp in enumerate(bot_paths, start=1):
            try:
                self.log_info(f"[{idx}/{total}] -> Processing: {bp}")
                self.process_single_bot(Path(bp), darkjar, plugin_src)
                self.log_success(f"[{idx}/{total}] Completed: {bp}")
            except Exception as e:
                errors += 1
                tb = traceback.format_exc()
                self.log_error(f"[{idx}/{total}] Error processing {bp}: {e}")
                self.log_info(tb)
            finally:
                self.progress["value"] = idx

        if errors == 0:
            self.log_success(f"Operation completed successfully for {total} folders.")
        else:
            self.log_warn(f"Operation completed with {errors} errors (see log).")
        messagebox.showinfo("Done", "Operation completed. Check the log.")

    def process_single_bot(self, bot_path: Path, darkjar_src: Path, plugin_src_folder: Path):
        if not bot_path.exists() or not bot_path.is_dir():
            raise FileNotFoundError(self.tr.t("msg_error_bot_folder_does_not_exist", bot_path=bot_path))

        # 1) logs
        logs_dir = bot_path / "logs"
        if logs_dir.exists() and logs_dir.is_dir():
            removed = 0
            for f in logs_dir.glob("**/*.log"):
                try:
                    f.unlink()
                    removed += 1
                except Exception as e:
                    self.log_warn(f"Did not remove log file {f}: {e}")
            self.log_info(f"Removed {removed} .log files in {logs_dir}")
        else:
            self.log_warn(f"No logs folder in {bot_path} - skipping.")

        # 2) plugins/old
        plugins_old = bot_path / "plugins" / "old"
        if plugins_old.exists() and plugins_old.is_dir():
            removed = 0
            for jar in plugins_old.glob("*.jar"):
                try:
                    jar.unlink()
                    removed += 1
                except Exception as e:
                    self.log_warn(f"Did not remove {jar}: {e}")
            self.log_info(f"Removed {removed} .jar files in {plugins_old}")
        else:
            self.log_warn(f"No plugins/old folder in {bot_path} - skipping.")

        # 3) plugins/updates -> delete all files inside (but keep folder)
        plugins_updates = bot_path / "plugins" / "updates"
        if plugins_updates.exists() and plugins_updates.is_dir():
            removed = 0
            for p in plugins_updates.iterdir():
                try:
                    if p.is_file():
                        p.unlink()
                        removed += 1
                    elif p.is_dir():
                        shutil.rmtree(p)
                        removed += 1
                except Exception as e:
                    self.log_warn(f"Did not remove {p}: {e}")
            self.log_info(f"Removed {removed} elements in {plugins_updates}")
        else:
            try:
                plugins_updates.mkdir(parents=True, exist_ok=True)
                self.log_info(f"Created folder {plugins_updates}")
            except Exception as e:
                self.log_warn(f"Failed to create {plugins_updates}: {e}")

        # 4) copy DarkBot.jar
        if darkjar_src and darkjar_src.exists() and darkjar_src.is_file() and darkjar_src.name == "DarkBot.jar":
            dest = bot_path / "DarkBot.jar"
            try:
                shutil.copy2(str(darkjar_src), str(dest))
                self.log_info(f"Copied DarkBot.jar -> {dest}")
            except Exception as e:
                self.log_warn(f"Failed to copy DarkBot.jar to {bot_path}: {e}")
        else:
            self.log_warn(f"Invalid or missing DarkBot.jar file: {darkjar_src} - skipping copy.")

        # 5) copy plugin jars
        if plugin_src_folder and plugin_src_folder.exists() and plugin_src_folder.is_dir():
            copied = 0
            for jar in Path(plugin_src_folder).glob("*.jar"):
                if jar.name == "DarkBot.jar":
                    self.log_warn(f"Skipped {jar.name} in plugins folder (DarkBot.jar files are not plugins).")
                    continue
                try:
                    dest = plugins_updates / jar.name
                    shutil.copy2(str(jar), str(dest))
                    copied += 1
                except Exception as e:
                    self.log_warn(f"Failed to copy {jar} to {plugins_updates}: {e}")
            self.log_info(f"Copied {copied} plugins to {plugins_updates}")
        else:
            self.log_warn(f"Invalid plugin updates folder: {plugin_src_folder} - skipping plugin copy.")

    def clear_old_logs_worker(self, bot_paths):
        total = len(bot_paths)
        self.progress["value"] = 0
        self.progress["maximum"] = total
        self.log_info(f"Start clearing in {total} folders...")

        errors = 0

        for idx, bp in enumerate(bot_paths, start=1):
            try:
                self.log_info(f"[{idx}/{total}] -> Clearing: {bp}")
                self.clear_single_bot(Path(bp))
                self.log_success(f"[{idx}/{total}] Cleared: {bp}")
            except Exception as e:
                errors += 1
                tb = traceback.format_exc()
                self.log_error(f"[{idx}/{total}] Error while clearing {bp}: {e}")
                self.log_info(tb)
            finally:
                self.progress["value"] = idx

        if errors == 0:
            self.log_success(f"Clearing completed successfully for {total} folders.")
        else:
            self.log_warn(f"Clearing completed with {errors} errors (details in log).")

        messagebox.showinfo(self.tr.t("window_info_name_clearing_completed"), self.tr.t("msg_info_clearing_completed"))

    def clear_single_bot(self, bot_path: Path):
        if not bot_path.exists() or not bot_path.is_dir():
            raise FileNotFoundError(self.tr.t("msg_error_bot_folder_does_not_exist", bot_path=bot_path))

        # logs/
        logs = bot_path / "logs"
        if logs.exists() and logs.is_dir():
            removed = 0
            for f in logs.glob("**/*.log"):
                try:
                    f.unlink()
                    removed += 1
                except Exception as e:
                    self.log_warn(f"Did not delete .log file {f}: {e}")
            self.log_info(f"Removed {removed} .log files in {logs}")
        else:
            self.log_warn(f"Missing logs folder in {bot_path}")

        # plugins/old/
        old = bot_path / "plugins" / "old"
        if old.exists() and old.is_dir():
            removed = 0
            for jar in old.glob("*.jar"):
                try:
                    jar.unlink()
                    removed += 1
                except Exception as e:
                    self.log_warn(f"Did not delete {jar}: {e}")
            self.log_info(f"Removed {removed} .jar files in {old}")
        else:
            self.log_warn(f"Missing plugins/old folder in {bot_path}")


# Launcher
def main():
    root = Tk()
    app = DarkBotManagerGUI(root)
    app.start()

if __name__ == "__main__":
    main()