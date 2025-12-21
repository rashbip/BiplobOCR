
import os
import sys
import subprocess

# Add src to path so we can import our modules
sys.path.append(os.path.join(os.getcwd()))

from src.core.platform_utils import setup_ghostscript_environment

print("--- Testing Ghostscript Path Implementation ---")
print(f"Initial PATH (first 200 chars): {os.environ['PATH'][:200]}...")

# Trigger the local setup
setup_ghostscript_environment()

print("\n--- After setup_ghostscript_environment() ---")
print(f"Updated PATH (first 200 chars): {os.environ['PATH'][:200]}...")

# Try to find 'gs' or 'gswin64c' in the path
def find_gs():
    for name in ['gs.exe', 'gswin64c.exe']:
        try:
            # Use 'where' on Windows to find the executable path
            result = subprocess.check_output(['where', name], text=True).strip().split('\n')[0]
            print(f"Found {name} at: {result}")
            
            # Check version
            version = subprocess.check_output([result, '--version'], text=True).strip()
            print(f"Version reported: {version}")
            
            if "BiplobOCR\\src\\ghostscript" in result:
                print("✅ SUCCESS: App is using the INTERNAL Ghostscript!")
            else:
                print("❌ WARNING: App is using a SYSTEM Ghostscript!")
        except Exception as e:
            print(f"Could not find {name} via 'where' or execution failed.")

find_gs()

print("\nGS_LIB Environment Variable:")
print(os.environ.get("GS_LIB", "NOT SET"))
