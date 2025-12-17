
import subprocess
import os

def get_available_gpus():
    """
    Detects available GPUs on Windows using wmic.
    Returns a list of strings, e.g. ['NVIDIA GeForce RTX 3060', 'Intel(R) UHD Graphics']
    """
    gpus = []
    if os.name == 'nt':
        try:
            cmd = ['wmic', 'path', 'win32_VideoController', 'get', 'name']
            proc = subprocess.run(cmd, capture_output=True, text=True, shell=True) # shell=True might find wmic if it's a built-in alias
            if proc.returncode == 0:
                lines = proc.stdout.strip().split('\n')
                # First line is header "Name", skip it
                for line in lines[1:]:
                    clean = line.strip()
                    if clean:
                        gpus.append(clean)
        except Exception as e:
            # Silently fail if wmic missing
            pass
            
    # Add a fallback/simulated entry if none found
    if not gpus:
        gpus.append("Standard Graphics Adaptor")
        
    return gpus

def get_system_info():
    """
    Returns dict with cpu_count and gpus
    """
    return {
        "cpu_count": os.cpu_count() or 4,
        "gpus": get_available_gpus()
    }
