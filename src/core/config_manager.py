import json
import os
import tkinter as tk
from tkinter import ttk

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "theme": "system",  # system, dark, light
    "language": "en",   # en, bn
    "ocr_options": {
        "deskew": False,
        "clean": False,
        "rotate": False,
        "force": False,
        "optimize": "0"
    }
}

TRANSLATIONS = {
    "en": {
        "app_title": "Biplob OCR",
        "tab_viewer": "PDF Preview",
        "tab_logs": "Logs",
        "tab_text": "Text Content",
        "btn_open": "📂 Open PDF",
        "grp_options": "OCR Options",
        "opt_deskew": "Deskew",
        "opt_clean": "Clean Background",
        "opt_rotate": "Auto Rotate",
        "opt_force": "Force OCR",
        "lbl_optimize": "Optimization:",
        "btn_process": "⚡ Start Processing",
        "lbl_status_idle": "Idle",
        "lbl_status_processing": "Processing...",
        "lbl_status_done": "Done!",
        "msg_success": "Success",
        "msg_saved": "PDF Saved to:",
        "title_export": "Export Data",
        "lbl_export_prompt": "Processing complete. Choose action:",
        "btn_save_txt": "Save Text (.txt)",
        "btn_save_hocr": "Save hOCR (.hocr)",
        "btn_close_export": "Close",
        "settings_title": "Settings",
        "lbl_theme": "Theme:",
        "lbl_lang": "Language:",
        "btn_save_settings": "Save Settings"
    },
    "bn": {
        "app_title": "বিপ্লব ওসিআর",
        "tab_viewer": "পিডিএফ প্রিভিউ",
        "tab_logs": "লগ",
        "tab_text": "টেক্সট কন্টেন্ট",
        "btn_open": "📂 পিডিএফ খুলুন",
        "grp_options": "ওসিআর অপশন",
        "opt_deskew": "সোজা করুন (Deskew)",
        "opt_clean": "ব্যাকগ্রাউন্ড পরিষ্কার",
        "opt_rotate": "অটো রোটেট",
        "opt_force": "জোরপূর্বক ওসিআর",
        "lbl_optimize": "অপ্টিমাইজেশন:",
        "btn_process": "⚡ শুরু করুন",
        "lbl_status_idle": "অপেক্ষমান",
        "lbl_status_processing": "কাজ চলছে...",
        "lbl_status_done": "সম্পন্ন!",
        "msg_success": "সাফল্য",
        "msg_saved": "পিডিএফ সংরক্ষিত হয়েছে:",
        "title_export": "এক্সপোর্ট",
        "lbl_export_prompt": "প্রসেসিং শেষ। পরবর্তী ধাপ নির্বাচন করুন:",
        "btn_save_txt": "টেক্সট সেভ করুন (.txt)",
        "btn_save_hocr": "hOCR সেভ করুন (.hocr)",
        "btn_close_export": "বন্ধ করুন",
        "settings_title": "সেটিংস",
        "lbl_theme": "থিম:",
        "lbl_lang": "ভাষা:",
        "btn_save_settings": "সেটিংস সেভ করুন"
    }
}

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, "r") as f:
                    return {**DEFAULT_CONFIG, **json.load(f)}
            except:
                return DEFAULT_CONFIG.copy()
        return DEFAULT_CONFIG.copy()

    def save_config(self, new_config):
        self.config = {**self.config, **new_config}
        with open(CONFIG_FILE, "w") as f:
            json.dump(self.config, f, indent=4)

    def get(self, key, default=None):
        return self.config.get(key, default)
        
    def get_option(self, key):
        return self.config["ocr_options"].get(key, False)

    def set_option(self, key, value):
        self.config["ocr_options"][key] = value

    def t(self, key):
        lang = self.config.get("language", "en")
        return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

# Global Instance
state = ConfigManager()
