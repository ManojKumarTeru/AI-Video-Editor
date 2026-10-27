"""
AI-Editor: Environment & Dependency Diagnostic Script
Checks Python, FFmpeg, Hardware capabilities, and package compatibility.
"""

import sys
import os
import subprocess
import shutil
import platform
import ctypes

def print_header(title):
    print("\n" + "=" * 65)
    print(f"  🎬 {title}")
    print("=" * 65)

def check_python():
    print_header("1. Python Environment")
    print(f"Python Version : {sys.version.split()[0]} ({platform.architecture()[0]})")
    print(f"Executable     : {sys.executable}")
    
    # Check other installed Python versions via py launcher
    print("\nChecking all installed Python versions on system...")
    try:
        res = subprocess.run(["py", "-0p"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            print(res.stdout.strip())
        else:
            print("  (Could not list other pythons)")
    except Exception as e:
        print(f"  Could not run 'py -0p': {e}")

def check_hardware():
    print_header("2. Hardware & System Resources")
    cpu_count = os.cpu_count() or 4
    print(f"CPU Cores      : {cpu_count} logical cores")
    print(f"OS             : {platform.system()} {platform.release()} (Build {platform.version()})")
    print(f"Machine Type   : {platform.machine()}")

    # RAM Check on Windows via GlobalMemoryStatusEx
    try:
        class MEMORYSTATUSEX(ctypes.Structure):
            _fields_ = [
                ("dwLength", ctypes.c_ulong),
                ("dwMemoryLoad", ctypes.c_ulong),
                ("ullTotalPhys", ctypes.c_ulonglong),
                ("ullAvailPhys", ctypes.c_ulonglong),
                ("ullTotalPageFile", ctypes.c_ulonglong),
                ("ullAvailPageFile", ctypes.c_ulonglong),
                ("ullTotalVirtual", ctypes.c_ulonglong),
                ("ullAvailVirtual", ctypes.c_ulonglong),
                ("sullAvailExtendedVirtual", ctypes.c_ulonglong),
            ]

        stat = MEMORYSTATUSEX()
        stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
        ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat))
        total_ram_gb = stat.ullTotalPhys / (1024 ** 3)
        avail_ram_gb = stat.ullAvailPhys / (1024 ** 3)
        print(f"Total RAM      : {total_ram_gb:.2f} GB")
        print(f"Available RAM  : {avail_ram_gb:.2f} GB")
    except Exception:
        print("Total RAM      : 16 GB (Assumed)")

    # Disk Space Check
    cwd = os.getcwd()
    total, used, free = shutil.disk_usage(cwd)
    print(f"Free Disk Space: {free / (1024 ** 3):.2f} GB on {os.path.splitdrive(cwd)[0]}")

def check_ffmpeg():
    print_header("3. FFmpeg & FFprobe Direct Access")
    
    # Test FFmpeg
    try:
        res = subprocess.run(["ffmpeg", "-version"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            first_line = res.stdout.splitlines()[0]
            print(f"✅ FFmpeg  : Available -> {first_line}")
        else:
            print("❌ FFmpeg  : Returned non-zero exit code")
    except FileNotFoundError:
        print("❌ FFmpeg  : Not found in PATH from Python environment")
    except Exception as e:
        print(f"❌ FFmpeg  : Error: {e}")

    # Test FFprobe
    try:
        res = subprocess.run(["ffprobe", "-version"], capture_output=True, text=True, timeout=10)
        if res.returncode == 0:
            first_line = res.stdout.splitlines()[0]
            print(f"✅ FFprobe : Available -> {first_line}")
        else:
            print("❌ FFprobe : Returned non-zero exit code")
    except FileNotFoundError:
        print("❌ FFprobe : Not found in PATH from Python environment")
    except Exception as e:
        print(f"❌ FFprobe : Error: {e}")

def test_pip_and_ai_packages():
    print_header("4. AI & Video Package Compatibility Test")
    
    # Test pip dry-run / wheel check for faster-whisper and auto-editor
    packages_to_test = ["faster-whisper", "auto-editor", "pyloudnorm", "noisereduce", "pydub"]
    print("Testing if pre-compiled wheels exist for your Python version...\n")
    
    for pkg in packages_to_test:
        print(f"Checking '{pkg}' ...", end=" ", flush=True)
        try:
            # Using --dry-run to check without modifying the system
            cmd = [sys.executable, "-m", "pip", "install", pkg, "--dry-run", "--no-input"]
            res = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            if res.returncode == 0:
                print("✅ Compatible wheel available!")
            else:
                print("⚠️ May require compilation or wheel issue:")
                # print concise error
                lines = [l for l in res.stderr.splitlines() if "ERROR:" in l or "error" in l.lower()]
                if lines:
                    print(f"   -> {lines[0]}")
                else:
                    print("   -> Pip dry-run reported conflicts or missing build wheel.")
        except Exception as e:
            print(f"❌ Check failed: {e}")

if __name__ == "__main__":
    check_python()
    check_hardware()
    check_ffmpeg()
    test_pip_and_ai_packages()
    print("\n" + "=" * 65)
    print("  Diagnostic complete! Please paste the output above.")
    print("=" * 65 + "\n")
