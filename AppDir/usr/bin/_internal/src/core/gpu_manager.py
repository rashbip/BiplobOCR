
import subprocess
import os

def get_available_gpus():
    """
    Detects available GPUs on Windows (PowerShell) and Linux (lspci).
    Returns a list of strings including CPU and GPUs.
    """
    devices = ["CPU (Default)"]
    
    if os.name == 'nt':
        try:
            # PowerShell is often more reliable/cleaner than wmic for this
            cmd = ["powershell", "-Command", "Get-CimInstance Win32_VideoController | Select-Object -ExpandProperty Name"]
            proc = subprocess.run(cmd, capture_output=True, text=True, creationflags=subprocess.CREATE_NO_WINDOW)
            
            if proc.returncode == 0:
                lines = proc.stdout.strip().split('\n')
                for line in lines:
                    clean = line.strip()
                    if clean and clean not in devices:
                        devices.append(clean)
        except Exception as e:
            # Fallback to wmic if powershell fails
            try:
                cmd = ['wmic', 'path', 'win32_VideoController', 'get', 'name']
                proc = subprocess.run(cmd, capture_output=True, text=True, shell=True)
                lines = proc.stdout.strip().split('\n')
                for line in lines[1:]: # Skip header
                    clean = line.strip()
                    if clean and clean not in devices:
                        devices.append(clean)
            except: 
                pass
    elif os.name == 'posix':
        # Linux/Mac
        try:
            # Try lspci
            cmd = ["lspci"]
            proc = subprocess.run(cmd, capture_output=True, text=True)
            if proc.returncode == 0:
                lines = proc.stdout.strip().split('\n')
                for line in lines:
                    if "VGA" in line or "3D controller" in line or "Display controller" in line:
                         # Extract the device name (usually after the address)
                         parts = line.split(":", 2) 
                         if len(parts) > 2:
                             clean = parts[2].strip()
                             if clean and clean not in devices:
                                 devices.append(clean)
        except:
            pass
            
    return devices

def get_system_info():
    """
    Returns dict with cpu_count and gpus
    """
    return {
        "cpu_count": os.cpu_count() or 4,
        "gpus": get_available_gpus()
    }
