
import json
import os
import locale

CONFIG_FILE = "config.json"

DEFAULT_CONFIG = {
    "theme": "dark",
    "language": "en",
    "ocr_language": "eng",
    "last_used_ocr_languages": [],
    "deskew": False,
    "clean": False,
    "rotate": False,
    "force": False,
    "optimize": "0",
    "use_gpu": False,
    "gpu_device": "Auto",
    "max_cpu_threads": 2,
    "rasterize": False,
    "dpi": 0
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
        "opt_rasterize": "Rasterize Images (Fixes errors, flattens annotations)",
        "lbl_dpi": "Rasterization DPI (0 = Auto/Original)",
        "lbl_optimize": "Optimization Level (0=None, 3=Max)",
        "lbl_lang": "Interface Language",
        "lbl_ocr_lang": "OCR Language (Data Pack)",
        "lbl_theme": "Theme",
        "msg_success": "Success! Files saved.",
        "nav_home": "🏠 Home",
        "nav_tools": "🛠 Tools",
        "nav_batch": "📂 Batch Process",
        "nav_history": "🕒 History",
        "nav_settings": "⚙️ Settings",
        "lbl_gpu": "Enable GPU Acceleration (Safe Mode)",
        "lbl_threads": "Max CPU Threads",
        "lbl_hw_settings": "Performance & Hardware",
        "lbl_dev_select": "Primary Processing Device (GPU/CPU):",
        "msg_restart": "Restart required for language change.",
        "msg_text_detected": "File contains text.",
        "lbl_help": "Help & Support",
        "btn_clear_history": "🗑 Clear All",
        "col_filename": "Filename",
        "col_status": "Status",
        "col_size": "Size",
        "col_date": "Date",
        "home_welcome": "Welcome to BiplobOCR",
        "home_desc": "Ready to digitize your documents? Start a new scan or pick up where you left off.",
        "card_new_task": "Start a new OCR task",
        "card_new_desc": "Proccess PDF Files • Drag & Drop Supported",
        "btn_select_computer": "Select from Computer",
        "btn_open_batch": "Select Files",
        "home_recent": "Recent Activity",
        "batch_title": "Batch Processing",
        "batch_desc": "Process multiple documents automatically.",
        "btn_add_files": "➕ Add Files",
        "btn_clear_list": "🗑 Clear List",
        "lbl_batch_opts": "Batch Options",
        "btn_start_batch": "▶ Start Batch"
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
        "opt_rasterize": "ইমেজ রাস্টারাইজ করুন (ত্রুটি ঠিক করে)",
        "lbl_dpi": "রাস্টারাইজেশন DPI (0 = অটো/আসল)",
        "lbl_optimize": "অপ্টিমাইজেশন (0=নাই, 3=সর্বোচ্চ)",
        "lbl_optimize": "অপ্টিমাইজেশন (0=নাই, 3=সর্বোচ্চ)",
        "lbl_lang": "ইন্টারফেস ভাষা (Interface)",
        "lbl_ocr_lang": "OCR ভাষা (ডাটা প্যাক)",
        "lbl_theme": "থিম",
        "msg_success": "সফল! ফাইল সংরক্ষণ করা হয়েছে।",
        "nav_home": "🏠 হোম",
        "nav_tools": "🛠 টুলস",
        "nav_batch": "📂 ব্যাচ প্রসেস",
        "nav_history": "🕒 ইতিহাস",
        "nav_settings": "⚙️ সেটিংস",
        "lbl_gpu": "GPU এক্সিলারেশন চালু করুন (নিরাপদ মোড)",
        "lbl_threads": "সর্বোচ্চ CPU থ্রেড",
        "lbl_hw_settings": "হার্ডওয়্যার ও পারফরম্যান্স",
        "lbl_dev_select": "প্রাথমিক ডিভাইস (GPU/CPU):",
        "msg_restart": "ভাষা পরিবর্তনের জন্য রিস্টার্ট প্রয়োজন।",
        "msg_text_detected": "ফাইলে টেক্সট পাওয়া গেছে।",
        "lbl_help": "সাহায্য এবং সমর্থন",
        "btn_clear_history": "🗑 সব মুছুন",
        "col_filename": "ফাইলের নাম",
        "col_status": "অবস্থা",
        "col_size": "আকার",
        "col_date": "তারিখ",
        "home_welcome": "BiplobOCR-এ স্বাগতম",
        "home_desc": "আপনার ডকুমেন্ট ডিজিটাইজ করতে প্রস্তুত? নতুন স্ক্যান শুরু করুন বা আগের কাজ চালিয়ে যান।",
        "card_new_task": "নতুন OCR টাস্ক শুরু করুন",
        "card_new_desc": "PDF ফাইল প্রসেস করুন • ড্র্যাগ এবং ড্রপ সমর্থিত",
        "btn_select_computer": "কম্পিউটার থেকে নির্বাচন করুন",
        "btn_open_batch": "ফাইল নির্বাচন করুন",
        "home_recent": "সাম্প্রতিক কার্যকলাপ",
        "batch_title": "ব্যাচ প্রসেসিং",
        "batch_desc": "একাধিক ডকুমেন্ট একসাথে প্রসেস করুন।",
        "btn_add_files": "➕ ফাইল যোগ করুন",
        "btn_clear_list": "🗑 তালিকা পরিষ্কার করুন",
        "lbl_batch_opts": "ব্যাচ অপশন",
        "btn_start_batch": "▶ ব্যাচ শুরু করুন"
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
        text = TRANSLATIONS.get(lang, TRANSLATIONS["en"]).get(key, key)
        
        from . import platform_utils
        if platform_utils.IS_LINUX:
            return platform_utils.sanitize_for_linux(text)
        return text



state = ConfigManager()
