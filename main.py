"""
J.A.R.V.I.S. Desktop Voice Assistant
Main Application Launcher
"""

import os
import sys

# Add Jarvis directory to Python module search path
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
JARVIS_DIR = os.path.join(BASE_DIR, "Jarvis")
if JARVIS_DIR not in sys.path:
    sys.path.insert(0, JARVIS_DIR)


def check_dependencies():
    """Checks for essential packages and prints helpful notices."""
    missing = []
    optional_missing = []

    try:
        import pyttsx3
    except ImportError:
        missing.append("pyttsx3")

    try:
        import speech_recognition
    except ImportError:
        optional_missing.append("SpeechRecognition")

    try:
        import wikipedia
    except ImportError:
        optional_missing.append("wikipedia")

    try:
        import pyautogui
    except ImportError:
        optional_missing.append("PyAutoGUI")

    try:
        import pyjokes
    except ImportError:
        optional_missing.append("pyjokes")

    if missing:
        print("\n" + "=" * 60)
        print(" [!] Missing Required Packages:")
        for pkg in missing:
            print(f"     - {pkg}")
        print("\n Please install them by running:")
        print("     pip install -r requirements.txt")
        print("=" * 60 + "\n")

    if optional_missing:
        print("\n [Note] Some optional packages are missing:")
        for pkg in optional_missing:
            print(f"     - {pkg}")
        print(" You can install all features with: pip install -r requirements.txt\n")


def main():
    check_dependencies()

    # If --cli flag is given, run CLI version
    if "--cli" in sys.argv or "-c" in sys.argv:
        from Jarvis import jarvis
        jarvis.run_cli()
    else:
        # Default: Launch modern Desktop HUD GUI
        try:
            from Jarvis import jarvis_gui
            jarvis_gui.run_gui()
        except Exception as e:
            print(f"\n[Warning] GUI could not start ({e}). Launching CLI mode instead...\n")
            from Jarvis import jarvis
            jarvis.run_cli()


if __name__ == "__main__":
    main()
