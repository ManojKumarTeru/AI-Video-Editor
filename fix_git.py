"""
Git Diagnostic & PATH Fixer for Windows
Checks common Git installation locations, adds Git to User PATH if found,
or offers to install it via winget.
"""

import os
import sys
import glob
import subprocess
import winreg
import ctypes

def print_banner():
    print("=" * 65)
    print("  🔧 Git Diagnostic & Setup Tool")
    print("=" * 65)

def find_git():
    local_app_data = os.environ.get("LOCALAPPDATA", "")
    program_files = os.environ.get("ProgramFiles", r"C:\Program Files")
    program_files_x86 = os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")
    user_profile = os.environ.get("USERPROFILE", "")

    candidates = [
        # Standard 64-bit installer
        os.path.join(program_files, "Git", "cmd", "git.exe"),
        os.path.join(program_files, "Git", "bin", "git.exe"),
        # Standard 32-bit installer
        os.path.join(program_files_x86, "Git", "cmd", "git.exe"),
        os.path.join(program_files_x86, "Git", "bin", "git.exe"),
        # User local installation
        os.path.join(local_app_data, "Programs", "Git", "cmd", "git.exe"),
        os.path.join(local_app_data, "Programs", "Git", "bin", "git.exe"),
        # Scoop
        os.path.join(user_profile, "scoop", "shims", "git.exe"),
        # Chocolatey
        r"C:\ProgramData\chocolatey\bin\git.exe",
    ]

    # Check GitHub Desktop embedded git
    if local_app_data:
        gh_pattern = os.path.join(local_app_data, "GitHubDesktop", "app-*", "resources", "app", "git", "cmd", "git.exe")
        for match in glob.glob(gh_pattern):
            candidates.append(match)

    for path in candidates:
        if os.path.isfile(path):
            return os.path.abspath(path)

    return None

def get_user_path():
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_READ) as key:
            val, _ = winreg.QueryValueEx(key, "Path")
            return val
    except FileNotFoundError:
        return ""
    except Exception as e:
        print(f"⚠️ Could not read User PATH from registry: {e}")
        return os.environ.get("Path", "")

def set_user_path(new_path):
    try:
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Environment", 0, winreg.KEY_SET_VALUE) as key:
            winreg.SetValueEx(key, "Path", 0, winreg.REG_EXPAND_SZ, new_path)
        
        # Broadcast WM_SETTINGCHANGE so new shells pick it up immediately
        HWND_BROADCAST = 0xFFFF
        WM_SETTINGCHANGE = 0x001A
        SMTO_ABORTIFHUNG = 0x0002
        result = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(
            HWND_BROADCAST, WM_SETTINGCHANGE, 0, "Environment",
            SMTO_ABORTIFHUNG, 5000, ctypes.byref(result)
        )
        return True
    except Exception as e:
        print(f"❌ Failed to update registry: {e}")
        return False

def check_winget():
    winget_paths = [
        os.path.join(os.environ.get("LOCALAPPDATA", ""), r"Microsoft\WindowsApps\winget.exe"),
        r"C:\Program Files\WindowsApps\Microsoft.DesktopAppInstaller_*_x64__8wekyb3d8bbwe\winget.exe"
    ]
    for p in winget_paths:
        matches = glob.glob(p)
        if matches and os.path.isfile(matches[0]):
            return matches[0]
    
    # Try running winget directly
    try:
        res = subprocess.run(["winget", "--version"], capture_output=True, text=True, timeout=5)
        if res.returncode == 0:
            return "winget"
    except Exception:
        pass
    return None

def main():
    print_banner()
    
    print("\n🔍 Step 1: Searching for existing Git installation...")
    git_path = find_git()
    
    if git_path:
        print(f"✅ Found Git at: {git_path}")
        
        # Test executing git
        try:
            res = subprocess.run([git_path, "--version"], capture_output=True, text=True, timeout=10)
            print(f"   Version: {res.stdout.strip()}")
        except Exception as e:
            print(f"   (Failed to run git directly: {e})")

        # Get directory to add to PATH
        git_dir = os.path.dirname(git_path)
        # Prefer cmd folder over bin folder if inside Git directory
        parent_dir = os.path.dirname(git_dir)
        cmd_candidate = os.path.join(parent_dir, "cmd")
        if os.path.isdir(cmd_candidate) and os.path.isfile(os.path.join(cmd_candidate, "git.exe")):
            git_dir = cmd_candidate

        print(f"\n🔍 Step 2: Checking User PATH...")
        current_user_path = get_user_path()
        path_entries = [p.strip() for p in current_user_path.split(";") if p.strip()]

        already_present = any(os.path.normcase(git_dir) == os.path.normcase(p) for p in path_entries)

        if already_present:
            print(f"ℹ️  Git directory '{git_dir}' is already in your User PATH.")
            print("\n👉 If PowerShell still says 'git is not recognized':")
            print("   Please restart your PowerShell window or VS Code / IDE terminal to refresh the environment.")
        else:
            print(f"➕ Adding '{git_dir}' to User PATH...")
            new_path = current_user_path.rstrip(";") + ";" + git_dir if current_user_path else git_dir
            if set_user_path(new_path):
                print("✅ Successfully added Git to your User PATH!")
                print("\n🎉 DONE! Please RESTART PowerShell or your IDE terminal window.")
                print("Then run: git --version")
            else:
                print("\n⚠️ Could not automatically modify PATH via registry.")
                print("You can manually run this in PowerShell (Run as Administrator or User):")
                print(f'[Environment]::SetEnvironmentVariable("Path", $env:Path + ";{git_dir}", [EnvironmentVariableTarget]::User)')

    else:
        print("❌ Git was NOT found in standard locations.")
        print("\n🔍 Step 2: Checking if winget (Windows Package Manager) is available...")
        winget = check_winget()
        
        if winget:
            print(f"✅ Windows Package Manager (winget) is available!")
            print("\n💡 You can install Git automatically now by running:")
            print("   winget install --id Git.Git -e --source winget")
            print()
            choice = input("Would you like to install Git via winget right now? (y/n): ").strip().lower()
            if choice == 'y':
                print("\n⬇️ Starting Git installation via winget...")
                print("   (A Windows User Account Control / UAC prompt may appear — please click Yes)\n")
                try:
                    subprocess.run(["winget", "install", "--id", "Git.Git", "-e", "--source", "winget", "--accept-source-agreements", "--accept-package-agreements"])
                    print("\n✅ Git installation command completed!")
                    print("Please RESTART your PowerShell window and run: git --version")
                except Exception as e:
                    print(f"❌ Failed to run winget install: {e}")
            else:
                print("\nSkipped. You can install Git manually whenever you are ready.")
        else:
            print("❌ winget was not detected.")
            print("\n📥 Please download and install Git manually:")
            print("   Download URL: https://git-scm.com/download/win")
            print("   (During installation, keep the default option 'Git from the command line and also from 3rd-party software')")

    print("\n" + "=" * 65 + "\n")

if __name__ == "__main__":
    main()
