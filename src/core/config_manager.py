
import json
import os
import locale

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "theme": "dark",
    "language": "en",
    "deskew": True,
    "clean": False,
    "rotate": True,
    "force": False,
    "optimize": "0",
    "use_gpu": False
}

TRANSLATIONS = {
    "en": {
        "app_title": "BiplobOCR - PDF Scanner",
        "settings_title": "Settings",
        "btn_process": "Start OCR",
        "btn_cancel": "Cancel",
        "lbl_status_idle": "Ready",
        "lbl_status_processing": "Processing... Please wait.",
        "lbl_status_done": "Completed Successfully!",
        "grp_options": "OCR Options",
        "opt_deskew": "Auto-Deskew (Straighten)",
        "opt_clean": "Clean Background (Remove Noise)",
        "opt_rotate": "Auto-Rotate Pages",
        "opt_force": "Force OCR (Ignore existing text)",
        "lbl_optimize": "Optimization Level (0=None, 3=Max)",
        "lbl_lang": "Language",
        "lbl_theme": "Theme",
        "msg_success": "Success! Files saved."
    },
    "bn": {
        "app_title": "BiplobOCR - PDF স্ক্যানার",
        "settings_title": "সেটিংস",
        "btn_process": "OCR শুরু করুন",
        "btn_cancel": "বাতিল",
        "lbl_status_idle": "প্রস্তুত",
        "lbl_status_processing": "প্রসেসিং চলছে... অপেক্ষা করুন",
        "lbl_status_done": "সফলভাবে সম্পন্ন হয়েছে!",
        "grp_options": "OCR অপশন",
        "opt_deskew": "অটো-সোজা করুন (Deskew)",
        "opt_clean": "ব্যাকগ্রাউন্ড পরিষ্কার করুন",
        "opt_rotate": "পেজ ঘোরান (Rotate)",
        "opt_force": "জোরপূর্বক OCR করুন",
        "lbl_optimize": "অপ্টিমাইজেশন (0=নাই, 3=সর্বোচ্চ)",
        "lbl_lang": "ভাষা",
        "lbl_theme": "থিম",
        "msg_success": "সফল! ফাইল সংরক্ষণ করা হয়েছে।"
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
        return self.config.get(key)
    
    def set_option(self, key, value):
        self.config[key] = value

    def t(self, key):
        lang = self.get("language", "en")
        return TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)

state = ConfigManager()
