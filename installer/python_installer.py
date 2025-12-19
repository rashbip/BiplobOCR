"""
BiplobOCR - Python Environment Setup
Handles Python installation and dependency management
"""

import subprocess
import sys
import os
import json
import tkinter as tk
from tkinter import messagebox, ttk
import webbrowser
from pathlib import Path
import urllib.request
import tempfile

class PythonInstaller:
    """Manages Python installation and dependencies"""
    
    REQUIRED_PACKAGES = [
        'pikepdf',
        'ocrmypdf',
        'PyMuPDF',
        'Pillow',
        'tkinterdnd2'
    ]
    
    PYTHON_MIN_VERSION = (3, 8)
    PYTHON_DOWNLOAD_URL = "https://www.python.org/downloads/windows/"
    PYTHON_INSTALLER_URL = "https://www.python.org/ftp/python/{version}/python-{version}-amd64.exe"
    
    def __init__(self):
        self.root = None
        self.progress = None
        self.status_label = None
        
    def check_python_installed(self):
        """Check if Python is installed and accessible"""
        try:
            result = subprocess.run(
                [sys.executable, '--version'],
                capture_output=True,
                text=True,
                timeout=5
            )
            if result.returncode == 0:
                version_str = result.stdout.strip()
                return True, version_str
        except (FileNotFoundError, subprocess.TimeoutExpired):
            pass
        
        # Try finding python in PATH
        for cmd in ['python', 'python3', 'py']:
            try:
                result = subprocess.run(
                    [cmd, '--version'],
                    capture_output=True,
                    text=True,
                    timeout=5,
                    shell=True
                )
                if result.returncode == 0:
                    version_str = result.stdout.strip() or result.stderr.strip()
                    return True, version_str
            except:
                continue
        
        return False, None
    
    def check_python_in_path(self):
        """Check if Python is in system PATH"""
        path = os.environ.get('PATH', '')
        return any('python' in p.lower() for p in path.split(os.pathsep))
    
    def get_latest_python_version(self):
        """Get the latest stable Python version (simplified - returns hardcoded)"""
        return "3.12.7"  # Update this periodically
    
    def download_python_installer(self, version, progress_callback=None):
        """Download Python installer"""
        url = self.PYTHON_INSTALLER_URL.format(version=version)
        temp_dir = tempfile.gettempdir()
        installer_path = os.path.join(temp_dir, f"python-{version}-installer.exe")
        
        try:
            def reporthook(blocknum, blocksize, totalsize):
                if progress_callback and totalsize > 0:
                    downloaded = blocknum * blocksize
                    percent = min(100, int((downloaded / totalsize) * 100))
                    progress_callback(percent)
            
            urllib.request.urlretrieve(url, installer_path, reporthook)
            return installer_path
        except Exception as e:
            return None
    
    def install_python_automatic(self, installer_path):
        """Install Python silently with recommended settings"""
        try:
            # Silent install with pip, add to PATH, install for all users
            cmd = [
                installer_path,
                '/quiet',
                'InstallAllUsers=1',
                'PrependPath=1',
                'Include_pip=1',
                'Include_tcltk=1'
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            return result.returncode == 0
        except Exception as e:
            return False
    
    def check_package_compatibility(self, package_name):
        """Check if installed package is compatible"""
        try:
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'show', package_name],
                capture_output=True,
                text=True,
                timeout=10
            )
            
            if result.returncode == 0:
                # Package is installed
                # For simplicity, we'll consider it compatible if installed
                # More complex version checking can be added here
                return True, "installed"
            else:
                return False, "not installed"
        except:
            return False, "check failed"
    
    def install_requirements(self, progress_callback=None):
        """Install all required packages"""
        total = len(self.REQUIRED_PACKAGES)
        
        for idx, package in enumerate(self.REQUIRED_PACKAGES):
            if progress_callback:
                progress_callback(package, int((idx / total) * 100))
            
            # Check if already installed and compatible
            is_installed, status = self.check_package_compatibility(package)
            
            if is_installed:
                if progress_callback:
                    progress_callback(f"{package} (already installed)", int(((idx + 1) / total) * 100))
                continue
            
            # Install package
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'pip', 'install', package],
                    capture_output=True,
                    text=True,
                    timeout=300  # 5 minutes timeout per package
                )
                
                if result.returncode != 0:
                    return False, f"Failed to install {package}: {result.stderr}"
                
            except subprocess.TimeoutExpired:
                return False, f"Timeout installing {package}"
            except Exception as e:
                return False, f"Error installing {package}: {str(e)}"
        
        if progress_callback:
            progress_callback("All packages installed", 100)
        
        return True, "All packages installed successfully"
    
    def create_gui(self):
        """Create installation GUI"""
        self.root = tk.Tk()
        self.root.title("BiplobOCR - Python Setup")
        self.root.geometry("500x300")
        self.root.resizable(False, False)
        
        # Title
        title = tk.Label(
            self.root,
            text="BiplobOCR Installation",
            font=("Segoe UI", 16, "bold")
        )
        title.pack(pady=20)
        
        # Status
        self.status_label = tk.Label(
            self.root,
            text="Checking Python installation...",
            font=("Segoe UI", 10)
        )
        self.status_label.pack(pady=10)
        
        # Progress bar
        self.progress = ttk.Progressbar(
            self.root,
            mode='indeterminate',
            length=400
        )
        self.progress.pack(pady=20)
        
        return self.root
    
    def update_status(self, message, progress_value=None):
        """Update status message and progress"""
        if self.status_label:
            self.status_label.config(text=message)
        if self.progress and progress_value is not None:
            self.progress['mode'] = 'determinate'
            self.progress['value'] = progress_value
        if self.root:
            self.root.update()
    
    def run_installation_wizard(self):
        """Run the complete installation wizard"""
        # Check Python
        has_python, version = self.check_python_installed()
        
        if not has_python:
            choice = messagebox.askyesnocancel(
                "Python Not Found",
                "Python is required but not found on your system.\n\n"
                "Click YES to install automatically\n"
                "Click NO to download manually\n"
                "Click CANCEL to abort installation",
                icon='warning'
            )
            
            if choice is None:  # Cancel
                return False
            elif choice:  # Yes - Auto install
                latest_version = self.get_latest_python_version()
                
                if messagebox.askyesno(
                    "Downloading Python",
                    f"Will download and install Python {latest_version}\n"
                    f"This may take several minutes.\n\n"
                    f"Continue?"
                ):
                    self.create_gui()
                    self.update_status(f"Downloading Python {latest_version}...", 0)
                    self.progress.start()
                    self.root.update()
                    
                    installer = self.download_python_installer(
                        latest_version,
                        lambda p: self.update_status(f"Downloading: {p}%", p)
                    )
                    
                    if installer:
                        self.update_status("Installing Python...", 50)
                        if self.install_python_automatic(installer):
                            messagebox.showinfo(
                                "Success",
                                "Python installed successfully!\n"
                                "Please restart this installer."
                            )
                            self.root.destroy()
                            return False
                        else:
                            messagebox.showerror("Error", "Python installation failed")
                            self.root.destroy()
                            return False
                    else:
                        messagebox.showerror("Error", "Failed to download Python")
                        self.root.destroy()
                        return False
            else:  # No - Manual
                webbrowser.open(self.PYTHON_DOWNLOAD_URL)
                messagebox.showinfo(
                    "Manual Installation",
                    "Opening Python download page in browser.\n"
                    "Please download and install Python, then run this installer again."
                )
                return False
        
        # Check if Python is in PATH
        if not self.check_python_in_path():
            if messagebox.askyesno(
                "Python Not in PATH",
                "Python is installed but not found in system PATH.\n"
                "Would you like to add it to PATH?\n\n"
                "(Recommended for proper operation)",
                icon='warning'
            ):
                messagebox.showinfo(
                    "Add to PATH",
                    "Please add Python to your system PATH manually:\n\n"
                    "1. Search for 'Environment Variables' in Windows\n"
                    "2. Edit the 'Path' variable\n"
                    "3. Add the Python installation directory\n"
                    "4. Restart this installer"
                )
                return False
        
        # Install requirements
        self.create_gui()
        self.update_status("Installing required packages...", 0)
        self.progress.start()
        self.root.update()
        
        def progress_cb(pkg, percent):
            self.update_status(f"Installing: {pkg}", percent)
        
        success, message = self.install_requirements(progress_cb)
        
        if success:
            messagebox.showinfo("Success", message)
            self.root.destroy()
            return True
        else:
            messagebox.showerror("Error", message)
            self.root.destroy()
            return False


if __name__ == "__main__":
    installer = PythonInstaller()
    success = installer.run_installation_wizard()
    sys.exit(0 if success else 1)
