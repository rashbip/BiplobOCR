import json
import os
import time

HISTORY_FILE = "history.json"

class HistoryManager:
    def __init__(self):
        self.history = self.load_history()

    def load_history(self):
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_history(self):
        # Keep only last 50
        if len(self.history) > 50:
            self.history = self.history[:50]
        with open(HISTORY_FILE, "w") as f:
            json.dump(self.history, f, indent=4)

    def add_entry(self, filename, status, size="N/A"):
        entry = {
            "filename": filename,
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "size": size,
            "status": status
        }
        self.history.insert(0, entry) # Prepend
        self.save_history()

    def get_all(self):
        return self.history

    def delete_entry(self, index):
        if 0 <= index < len(self.history):
            del self.history[index]
            self.save_history()

    def clear_all(self):
        self.history = []
        self.save_history()

history = HistoryManager()
