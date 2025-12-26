import json
import os
import time

# HISTORY_FILE moved to instance level

class HistoryManager:
    def __init__(self):
        from . import platform_utils
        self.history_path = os.path.join(platform_utils.get_app_data_dir(), "history.json")
        self.history = self.load_history()

    def load_history(self):
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r") as f:
                    return json.load(f)
            except:
                return []
        return []

    def save_history(self):
        # Keep only last 50
        if len(self.history) > 50:
            self.history = self.history[:50]
        with open(self.history_path, "w") as f:
            json.dump(self.history, f, indent=4)

    def add_entry(self, filename, status, size="N/A", source_path=None, output_path=None):
        entry = {
            "filename": filename,
            "date": time.strftime("%Y-%m-%d %H:%M:%S"),
            "size": size,
            "status": status,
            "source_path": source_path,
            "output_path": output_path
        }
        self.history.insert(0, entry) # Prepend
        self.save_history()

    def update_output_path(self, filename, new_path):
        # Update specific item by filename (the most recent one usually)
        for item in self.history:
            if item["filename"] == filename:
                item["output_path"] = new_path
                self.save_history()
                return

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
