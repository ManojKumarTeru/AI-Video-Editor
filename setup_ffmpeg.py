"""
FFmpeg Setup Script for AI-Editor
Downloads FFmpeg essentials build and extracts to project tools/ directory.
Then provides instructions for adding to system PATH.
"""

import urllib.request
import zipfile
import os
import sys
import shutil

# --- Configuration ---
FFMPEG_URL = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
PROJECT_DIR = os.path.dirname(os.path.abspath(__file__))
TOOLS_DIR = os.path.join(PROJECT_DIR, "tools")
FFMPEG_ZIP = os.path.join(TOOLS_DIR, "ffmpeg.zip")


def main():
    print("=" * 60)
    print("  🎬 FFmpeg Setup for AI-Editor")
    print("=" * 60)
    print()

    # Step 1: Create tools directory
    os.makedirs(TOOLS_DIR, exist_ok=True)
    print(f"📁 Tools directory: {TOOLS_DIR}")

    # Step 2: Download FFmpeg
    print()
    print(f"⬇️  Downloading FFmpeg from gyan.dev...")
    print(f"   URL: {FFMPEG_URL}")
    print(f"   This may take 2-5 minutes depending on your internet speed...")
    print()

    try:
        def progress_hook(block_num, block_size, total_size):
            downloaded = block_num * block_size
            if total_size > 0:
                percent = min(100, downloaded * 100 // total_size)
                mb_downloaded = downloaded / (1024 * 1024)
                mb_total = total_size / (1024 * 1024)
                bar = "█" * (percent // 2) + "░" * (50 - percent // 2)
                sys.stdout.write(
                    f"\r   [{bar}] {percent}% ({mb_downloaded:.1f}/{mb_total:.1f} MB)"
                )
                sys.stdout.flush()

        urllib.request.urlretrieve(FFMPEG_URL, FFMPEG_ZIP, reporthook=progress_hook)
        print()  # newline after progress bar
        print("   ✅ Download complete!")
    except Exception as e:
        print(f"\n   ❌ Download failed: {e}")
        print()
        print("   Manual download alternative:")
        print(f"   1. Go to: https://www.gyan.dev/ffmpeg/builds/")
        print(f"   2. Download 'ffmpeg-release-essentials.zip'")
        print(f"   3. Extract to: {TOOLS_DIR}")
        sys.exit(1)

    # Step 3: Extract
    print()
    print("📦 Extracting FFmpeg...")
    try:
        with zipfile.ZipFile(FFMPEG_ZIP, "r") as zip_ref:
            zip_ref.extractall(TOOLS_DIR)
        print("   ✅ Extraction complete!")
    except Exception as e:
        print(f"   ❌ Extraction failed: {e}")
        sys.exit(1)

    # Step 4: Find the extracted ffmpeg bin directory
    ffmpeg_bin = None
    for root, dirs, files in os.walk(TOOLS_DIR):
        if "ffmpeg.exe" in files:
            ffmpeg_bin = root
            break

    if not ffmpeg_bin:
        print("   ❌ Could not find ffmpeg.exe in extracted files")
        sys.exit(1)

    print(f"   📂 FFmpeg binaries found at: {ffmpeg_bin}")

    # Step 5: Verify the executables
    print()
    print("🔍 Verifying executables...")
    ffmpeg_exe = os.path.join(ffmpeg_bin, "ffmpeg.exe")
    ffprobe_exe = os.path.join(ffmpeg_bin, "ffprobe.exe")

    if os.path.exists(ffmpeg_exe):
        print(f"   ✅ ffmpeg.exe  → {ffmpeg_exe}")
    else:
        print(f"   ❌ ffmpeg.exe not found")

    if os.path.exists(ffprobe_exe):
        print(f"   ✅ ffprobe.exe → {ffprobe_exe}")
    else:
        print(f"   ❌ ffprobe.exe not found")

    # Step 6: Clean up zip
    try:
        os.remove(FFMPEG_ZIP)
        print("   🗑️  Cleaned up zip file")
    except Exception:
        pass

    # Step 7: Print PATH instructions
    print()
    print("=" * 60)
    print("  📋 NEXT STEP: Add FFmpeg to System PATH")
    print("=" * 60)
    print()
    print("  Option A — Run this command in PowerShell (as Administrator):")
    print()
    print(f'  [Environment]::SetEnvironmentVariable("Path",')
    print(f'    $env:Path + ";{ffmpeg_bin}",')
    print(f'    [EnvironmentVariableTarget]::User)')
    print()
    print("  Option B — Manual steps:")
    print("  1. Press Win + R → type 'sysdm.cpl' → Enter")
    print("  2. Click 'Advanced' tab → 'Environment Variables'")
    print("  3. Under 'User variables', select 'Path' → 'Edit'")
    print("  4. Click 'New' → paste this path:")
    print(f"     {ffmpeg_bin}")
    print("  5. Click OK → OK → OK")
    print()
    print("  After adding to PATH, RESTART PowerShell and verify:")
    print("    ffmpeg -version")
    print("    ffprobe -version")
    print()
    print("=" * 60)
    print(f"  ✅ FFmpeg is ready at: {ffmpeg_bin}")
    print("=" * 60)


if __name__ == "__main__":
    main()
