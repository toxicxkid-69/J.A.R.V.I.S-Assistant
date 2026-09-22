import ast
import datetime
import json
import math
import operator
import os
import queue
import random
import re
import subprocess
import sys
import threading
import time
import urllib.parse
import urllib.request
import webbrowser as wb

try:
    import speech_recognition as sr
except ImportError:
    sr = None

try:
    import pyautogui
    pyautogui.FAILSAFE = False
except ImportError:
    pyautogui = None

try:
    import pyjokes
except ImportError:
    pyjokes = None

try:
    import wikipedia
except ImportError:
    wikipedia = None

try:
    import pyttsx3
except ImportError:
    pyttsx3 = None

try:
    from ddgs import DDGS
except ImportError:
    DDGS = None

try:
    import asyncio
    import tempfile
    os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "1"
    import edge_tts
    import pygame
except ImportError:
    edge_tts = None
    pygame = None

try:
    import psutil
except ImportError:
    psutil = None

try:
    import pythoncom
    import win32com.client
    import win32gui
    import win32con
    import win32process
    import win32service
except ImportError:
    pythoncom = None
    win32com = None
    win32gui = None
    win32con = None
    win32process = None
    win32service = None

try:
    import pygetwindow
except ImportError:
    pygetwindow = None


# Base directory for local files
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_FILE = os.path.join(BASE_DIR, "data.txt")
NAME_FILE = os.path.join(BASE_DIR, "assistant_name.txt")

# Global GUI callback hook
gui_callback = None


# =============================================================================
# MULTI-ENGINE VOICE DICTATION SYSTEM (Windows SAPI5 + pyttsx3 + PowerShell)
# =============================================================================
def _speak_neural_voice(text: str) -> bool:
    """
    Speaks text using Microsoft Natural Neural Voice (Guy / Christopher)
    giving a human-like, articulate male conversational voice.
    """
    if not (edge_tts and pygame):
        return False
    try:
        async def _synthesize(filepath: str):
            communicate = edge_tts.Communicate(text, "en-US-GuyNeural")
            await communicate.save(filepath)

        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as f:
            tmp_path = f.name

        try:
            try:
                loop = asyncio.get_event_loop()
                if loop.is_running():
                    import concurrent.futures
                    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
                        pool.submit(asyncio.run, _synthesize(tmp_path)).result(timeout=10)
                else:
                    loop.run_until_complete(_synthesize(tmp_path))
            except RuntimeError:
                asyncio.run(_synthesize(tmp_path))

            if os.path.exists(tmp_path) and os.path.getsize(tmp_path) > 0:
                pygame.mixer.init()
                pygame.mixer.music.load(tmp_path)
                pygame.mixer.music.play()
                while pygame.mixer.music.get_busy():
                    pygame.time.Clock().tick(15)
                pygame.mixer.music.stop()
                pygame.mixer.quit()
                return True
        finally:
            if os.path.exists(tmp_path):
                try:
                    os.remove(tmp_path)
                except Exception:
                    pass
    except Exception:
        pass
    return False


def dictate_voice(text: str) -> bool:
    """
    Dictates text out loud through computer speakers using a natural human male voice
    calibrated to natural conversational pacing (~85-90% human likeness).
    """
    if not text:
        return True

    clean_text = text.strip()

    # Engine 1: Microsoft Natural Neural Voice (Articulate Human Male Voice)
    if _speak_neural_voice(clean_text):
        return True

    # Engine A: Native Windows SAPI (Natural Human Male Voice Microsoft David)
    try:
        if pythoncom and win32com:
            pythoncom.CoInitialize()
            spk = win32com.client.Dispatch("SAPI.SpVoice")

            # Select natural male voice (e.g., David, Mark, Male)
            for v in spk.GetVoices():
                desc = v.GetDescription().lower()
                if any(m in desc for m in ['david', 'mark', 'george', 'male']):
                    spk.Voice = v
                    break

            # Rate 0 is steady, natural conversational human cadence
            spk.Rate = 0
            spk.Volume = 100
            spk.Speak(clean_text)
            return True
    except Exception:
        pass
    finally:
        try:
            if pythoncom:
                pythoncom.CoUninitialize()
        except Exception:
            pass

    # Engine B: pyttsx3 engine fallback with explicit male voice selection
    if pyttsx3:
        try:
            eng = pyttsx3.init()
            voices = eng.getProperty('voices')
            for v in voices:
                desc = (getattr(v, 'name', '') + ' ' + getattr(v, 'id', '')).lower()
                if any(m in desc for m in ['david', 'mark', 'george', 'male']):
                    eng.setProperty('voice', v.id)
                    break
            eng.setProperty('rate', 155)  # Natural human conversational speed
            eng.setProperty('volume', 1.0)
            eng.say(clean_text)
            eng.runAndWait()
            return True
        except Exception:
            pass

    # Engine C: Windows PowerShell System.Speech with male voice hint
    try:
        escaped = clean_text.replace("'", "''").replace('"', ' ')
        ps_cmd = f"Add-Type -AssemblyName System.Speech; $s = New-Object System.Speech.Synthesis.SpeechSynthesizer; try {{ $s.SelectVoiceByHints([System.Speech.Synthesis.VoiceGender]::Male) }} catch {{}}; $s.Rate = 0; $s.Speak('{escaped}')"
        subprocess.run(["powershell", "-NoProfile", "-Command", ps_cmd], capture_output=True, timeout=12)
        return True
    except Exception:
        pass

    return False


def speak(audio: str) -> None:
    """
    Replies in the shell/terminal and dictates the answer aloud via voice.
    Also sends response to HUD GUI feed if connected.
    """
    if not audio:
        return

    # 1. Reply in the shell
    print(f"\n[Jarvis]: {audio}")

    # 2. Update GUI feed
    if gui_callback:
        try:
            gui_callback("Jarvis", audio)
        except Exception:
            pass

    # 3. Dictate the answer aloud by voice
    dictate_voice(audio)


# =============================================================================
# UNIVERSAL APPLICATION & WEB CATALOGS
# =============================================================================
POPULAR_SITES = {
    "youtube": "https://www.youtube.com",
    "google": "https://www.google.com",
    "gmail": "https://mail.google.com",
    "github": "https://www.github.com",
    "stackoverflow": "https://www.stackoverflow.com",
    "stack overflow": "https://www.stackoverflow.com",
    "chatgpt": "https://chatgpt.com",
    "chat gpt": "https://chatgpt.com",
    "openai": "https://www.openai.com",
    "netflix": "https://www.netflix.com",
    "amazon": "https://www.amazon.com",
    "flipkart": "https://www.flipkart.com",
    "twitter": "https://www.twitter.com",
    "x": "https://www.x.com",
    "instagram": "https://www.instagram.com",
    "facebook": "https://www.facebook.com",
    "reddit": "https://www.reddit.com",
    "linkedin": "https://www.linkedin.com",
    "spotify": "https://open.spotify.com",
    "wikipedia": "https://www.wikipedia.org",
    "twitch": "https://www.twitch.tv",
    "discord": "https://discord.com",
    "leetcode": "https://leetcode.com",
    "geeksforgeeks": "https://www.geeksforgeeks.org",
    "canva": "https://www.canva.com",
    "coursera": "https://www.coursera.org",
    "udemy": "https://www.udemy.com",
    "prime video": "https://www.primevideo.com",
    "hotstar": "https://www.hotstar.com",
    "whatsapp": "https://web.whatsapp.com",
    "telegram": "https://web.telegram.org"
}

APP_COMMANDS = {
    # Web Browsers
    "microsoft edge": "msedge",
    "edge": "msedge",
    "msedge": "msedge",
    "ms edge": "msedge",
    "google chrome": "chrome",
    "chrome": "chrome",
    "chorme": "chrome",
    "firefox": "firefox",
    "mozilla firefox": "firefox",
    "brave": "brave",
    "opera": "opera",

    # Core Windows Tools & Utilities
    "notepad": "notepad",
    "calculator": "calc",
    "calc": "calc",
    "cmd": "cmd",
    "command prompt": "cmd",
    "terminal": "powershell",
    "powershell": "powershell",
    "task manager": "taskmgr",
    "taskmgr": "taskmgr",
    "paint": "mspaint",
    "mspaint": "mspaint",
    "file explorer": "explorer",
    "explorer": "explorer",
    "files": "explorer",
    "my computer": "explorer",
    "this pc": "explorer",
    "settings": "ms-settings:",
    "windows settings": "ms-settings:",
    "control panel": "control",
    "device manager": "devmgmt.msc",
    "disk management": "diskmgmt.msc",
    "registry editor": "regedit",
    "regedit": "regedit",
    "snipping tool": "snippingtool",
    "snip": "snippingtool",
    "camera": "microsoft.windows.camera:",
    "clock": "ms-clock:",
    "alarm": "ms-clock:",
    "alarms": "ms-clock:",
    "microsoft store": "ms-windows-store:",
    "store": "ms-windows-store:",
    "photos": "ms-photos:",
    "weather": "bingweather:",
    "maps": "bingmaps:",

    # Developers & Office
    "vs code": "code",
    "vscode": "code",
    "code": "code",
    "visual studio code": "code",
    "word": "winword",
    "ms word": "winword",
    "microsoft word": "winword",
    "excel": "excel",
    "ms excel": "excel",
    "microsoft excel": "excel",
    "powerpoint": "powerpnt",
    "ppt": "powerpnt",
    "wordpad": "write",

    # Multimedia & Social
    "vlc": "vlc",
    "vlc player": "vlc",
    "vlc media player": "vlc",
    "media player": "wmplayer",
    "spotify": "spotify",
    "discord": "discord",
    "steam": "steam",
}



# =============================================================================
# TIME, DATE & GREETING
# =============================================================================
def tell_time() -> str:
    """Tells the current time."""
    current_time = datetime.datetime.now().strftime("%I:%M:%S %p")
    msg = f"The current time is {current_time}"
    speak(msg)
    return msg


def tell_date() -> str:
    """Tells the current date."""
    now = datetime.datetime.now()
    date_str = f"{now.day} {now.strftime('%B')} {now.year}"
    msg = f"Today is {now.strftime('%A')}, {date_str}"
    speak(msg)
    return msg


def tell_time_and_date() -> str:
    """Tells both current time and date."""
    now = datetime.datetime.now()
    t_str = now.strftime("%I:%M %p")
    d_str = f"{now.day} {now.strftime('%B')} {now.year}"
    msg = f"The current time is {t_str}, and today is {now.strftime('%A')}, {d_str}."
    speak(msg)
    return msg


def load_name() -> str:
    """Loads the assistant's name from file or defaults to Jarvis."""
    try:
        if os.path.exists(NAME_FILE):
            with open(NAME_FILE, "r", encoding="utf-8") as f:
                name = f.read().strip()
                if name:
                    return name
    except Exception:
        pass
    return "Jarvis"


def set_name(new_name: str = None) -> None:
    """Sets a new name for the assistant."""
    if not new_name:
        speak("What would you like to name me?")
        new_name = takecommand()

    if new_name:
        try:
            with open(NAME_FILE, "w", encoding="utf-8") as f:
                f.write(new_name.strip().title())
            speak(f"Alright, I will be called {new_name.strip().title()} from now on.")
        except Exception as e:
            speak(f"Could not save the name: {e}")
    else:
        speak("Sorry, I couldn't catch that.")


def wishme() -> None:
    """Greets the user based on the time of day."""
    hour = datetime.datetime.now().hour
    if 4 <= hour < 12:
        greeting = "Good morning!"
    elif 12 <= hour < 16:
        greeting = "Good afternoon!"
    elif 16 <= hour < 22:
        greeting = "Good evening!"
    else:
        greeting = "Good night, sir."

    speak("Welcome back, sir!")
    speak(greeting)
    assistant_name = load_name()
    speak(f"{assistant_name} at your service. Please tell me how I may assist you today.")


# =============================================================================
# NOTES MANAGEMENT (Add, Read, Clear/Delete)
# =============================================================================
def remember_note(content: str = None) -> None:
    """Saves a note to data.txt."""
    if not content:
        speak("What should I remember for you?")
        content = takecommand()

    if content:
        try:
            timestamp = datetime.datetime.now().strftime("%Y-%m-%d %I:%M %p")
            with open(DATA_FILE, "a", encoding="utf-8") as f:
                f.write(f"[{timestamp}] {content}\n")
            speak(f"I have recorded that: {content}")
        except Exception as e:
            speak(f"Could not save note: {e}")
    else:
        speak("No note content received.")


def recall_notes() -> None:
    """Reads saved notes from data.txt."""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "r", encoding="utf-8") as f:
                content = f.read().strip()
            if content:
                speak("Here are all your saved notes:")
                speak(content)
            else:
                speak("You have no notes saved right now.")
        else:
            speak("You don't have any notes saved yet.")
    except Exception as e:
        speak(f"Could not read notes: {e}")


def clear_notes() -> None:
    """Clears and deletes all saved notes."""
    try:
        if os.path.exists(DATA_FILE):
            with open(DATA_FILE, "w", encoding="utf-8") as f:
                f.write("")
            speak("All your saved notes have been cleared and deleted.")
        else:
            speak("Your notes file is already empty.")
    except Exception as e:
        speak(f"Could not clear notes: {e}")


# =============================================================================
# FULL COMPUTER & WINDOWS HARDWARE CONTROLS
# =============================================================================
def change_volume(action: str) -> None:
    """Controls Windows Master Volume."""
    if pyautogui is None:
        speak("PyAutoGUI is required for volume control.")
        return
    if action == "up":
        pyautogui.press('volumeup', presses=6)
        speak("Increasing volume")
    elif action == "down":
        pyautogui.press('volumedown', presses=6)
        speak("Lowering volume")
    elif action == "mute":
        pyautogui.press('volumemute')
        speak("Toggling volume mute")


def media_control(action: str) -> None:
    """Controls Windows Media Playback."""
    if pyautogui is None:
        return
    if action == "playpause":
        pyautogui.press('playpause')
        speak("Toggled media play and pause")
    elif action == "next":
        pyautogui.press('nexttrack')
        speak("Skipping to next track")
    elif action == "prev":
        pyautogui.press('prevtrack')
        speak("Returning to previous track")


def window_control(action: str) -> None:
    """Controls Windows, Desktop, and Active Applications."""
    if action == "minimize":
        if pyautogui:
            pyautogui.hotkey('win', 'd')
            speak("Showing desktop and minimizing windows")
        else:
            os.system("powershell -Command (New-Object -ComObject Shell.Application).MinimizeAll()")
    elif action == "close":
        if pyautogui:
            pyautogui.hotkey('alt', 'f4')
            speak("Closing active window")
    elif action == "switch":
        if pyautogui:
            pyautogui.hotkey('alt', 'tab')
            speak("Switched window")
    elif action == "lock":
        system_power("lock")


def system_power(action: str) -> None:
    """Controls System Power states: Lock, Sleep, Restart, Shutdown, and Abort."""
    act = action.lower().strip()
    if act == "lock":
        speak("Locking your workstation now, sir")
        os.system("rundll32.exe user32.dll,LockWorkStation")
    elif act == "sleep":
        speak("Putting the system to sleep, sir")
        try:
            subprocess.run(
                ["powershell", "-Command", "Add-Type -AssemblyName System.Windows.Forms; [System.Windows.Forms.Application]::SetSuspendState([System.Windows.Forms.PowerState]::Suspend, $false, $false)"],
                shell=True
            )
        except Exception:
            os.system("rundll32.exe powrprof.dll,SetSuspendState 0,1,0")
    elif act == "restart":
        speak("Restarting the system in ten seconds. Save your work, sir.")
        os.system("shutdown /r /t 10")
    elif act == "shutdown":
        speak("Shutting down the system in ten seconds. Save your work, sir.")
        os.system("shutdown /s /t 10")
    elif act in ["abort", "cancel"]:
        speak("Aborting system shutdown, sir.")
        os.system("shutdown /a")


# =============================================================================
# SINGLE / TARGETED APPLICATION WINDOW MANAGEMENT
# =============================================================================
APP_TARGET_MAP = {
    "chrome": {
        "label": "Google Chrome",
        "keywords": ["google chrome", "chrome"],
        "process_names": ["chrome.exe"],
    },
    "chorme": {  # Direct common typo alias
        "label": "Google Chrome",
        "keywords": ["google chrome", "chrome"],
        "process_names": ["chrome.exe"],
    },
    "google chrome": {
        "label": "Google Chrome",
        "keywords": ["google chrome", "chrome"],
        "process_names": ["chrome.exe"],
    },
    "edge": {
        "label": "Microsoft Edge",
        "keywords": ["microsoft edge", "edge"],
        "process_names": ["msedge.exe"],
    },
    "microsoft edge": {
        "label": "Microsoft Edge",
        "keywords": ["microsoft edge", "edge"],
        "process_names": ["msedge.exe"],
    },
    "firefox": {
        "label": "Mozilla Firefox",
        "keywords": ["firefox", "mozilla"],
        "process_names": ["firefox.exe"],
    },
    "mozilla firefox": {
        "label": "Mozilla Firefox",
        "keywords": ["firefox", "mozilla"],
        "process_names": ["firefox.exe"],
    },
    "brave": {
        "label": "Brave",
        "keywords": ["brave"],
        "process_names": ["brave.exe"],
    },
    "opera": {
        "label": "Opera",
        "keywords": ["opera"],
        "process_names": ["opera.exe"],
    },
    "notepad": {
        "label": "Notepad",
        "keywords": ["notepad"],
        "process_names": ["notepad.exe"],
    },
    "code": {
        "label": "Visual Studio Code",
        "keywords": ["visual studio code", "vscode", "code"],
        "process_names": ["code.exe"],
    },
    "vscode": {
        "label": "Visual Studio Code",
        "keywords": ["visual studio code", "vscode", "code"],
        "process_names": ["code.exe"],
    },
    "vs code": {
        "label": "Visual Studio Code",
        "keywords": ["visual studio code", "vscode", "code"],
        "process_names": ["code.exe"],
    },
    "visual studio code": {
        "label": "Visual Studio Code",
        "keywords": ["visual studio code", "vscode", "code"],
        "process_names": ["code.exe"],
    },
    "word": {
        "label": "Microsoft Word",
        "keywords": ["word"],
        "process_names": ["winword.exe"],
    },
    "ms word": {
        "label": "Microsoft Word",
        "keywords": ["word"],
        "process_names": ["winword.exe"],
    },
    "excel": {
        "label": "Microsoft Excel",
        "keywords": ["excel"],
        "process_names": ["excel.exe"],
    },
    "ms excel": {
        "label": "Microsoft Excel",
        "keywords": ["excel"],
        "process_names": ["excel.exe"],
    },
    "powerpoint": {
        "label": "PowerPoint",
        "keywords": ["powerpoint", "ppt"],
        "process_names": ["powerpnt.exe"],
    },
    "calculator": {
        "label": "Calculator",
        "keywords": ["calculator", "calc"],
        "process_names": ["calculatorapp.exe", "calc.exe"],
    },
    "calc": {
        "label": "Calculator",
        "keywords": ["calculator", "calc"],
        "process_names": ["calculatorapp.exe", "calc.exe"],
    },
    "explorer": {
        "label": "File Explorer",
        "keywords": ["file explorer", "explorer"],
        "process_names": ["explorer.exe"],
    },
    "file explorer": {
        "label": "File Explorer",
        "keywords": ["file explorer", "explorer"],
        "process_names": ["explorer.exe"],
    },
    "files": {
        "label": "File Explorer",
        "keywords": ["file explorer", "explorer"],
        "process_names": ["explorer.exe"],
    },
    "task manager": {
        "label": "Task Manager",
        "keywords": ["task manager", "taskmgr"],
        "process_names": ["taskmgr.exe"],
    },
    "taskmgr": {
        "label": "Task Manager",
        "keywords": ["task manager", "taskmgr"],
        "process_names": ["taskmgr.exe"],
    },
    "cmd": {
        "label": "Command Prompt",
        "keywords": ["command prompt", "cmd"],
        "process_names": ["cmd.exe"],
    },
    "command prompt": {
        "label": "Command Prompt",
        "keywords": ["command prompt", "cmd"],
        "process_names": ["cmd.exe"],
    },
    "terminal": {
        "label": "Terminal",
        "keywords": ["terminal", "powershell", "cmd"],
        "process_names": ["windowsterminal.exe", "powershell.exe", "cmd.exe"],
    },
    "powershell": {
        "label": "PowerShell",
        "keywords": ["powershell"],
        "process_names": ["powershell.exe"],
    },
    "spotify": {
        "label": "Spotify",
        "keywords": ["spotify"],
        "process_names": ["spotify.exe"],
    },
    "vlc": {
        "label": "VLC Media Player",
        "keywords": ["vlc media player", "vlc"],
        "process_names": ["vlc.exe"],
    },
    "discord": {
        "label": "Discord",
        "keywords": ["discord"],
        "process_names": ["discord.exe"],
    },
    "steam": {
        "label": "Steam",
        "keywords": ["steam"],
        "process_names": ["steam.exe", "steamservice.exe"],
    },
    "settings": {
        "label": "Settings",
        "keywords": ["settings"],
        "process_names": ["systemsettings.exe"],
    },
}


def manage_specific_window(action: str, target: str) -> bool:
    """
    Minimizes, closes, or restores a single targeted application window.
    Targets only the specified app, leaving all other windows untouched.
    """
    action = action.lower().strip()
    target_clean = target.lower().strip()
    # Resolve target alias or generate dynamic search profile


    alias_info = APP_TARGET_MAP.get(target_clean)
    if alias_info:
        label = alias_info["label"]
        keywords = alias_info["keywords"]
        process_names = alias_info["process_names"]
    else:
        label = target.strip().title()
        keywords = [target_clean]
        clean_proc = target_clean.replace(" ", "")
        process_names = [f"{target_clean}.exe", f"{clean_proc}.exe"]

    found_windows = []
    seen_hwnds = set()

    def check_window_candidate(hwnd):
        if not win32gui or not win32gui.IsWindow(hwnd) or not win32gui.IsWindowVisible(hwnd):
            return
        if hwnd in seen_hwnds:
            return
        seen_hwnds.add(hwnd)

        title = win32gui.GetWindowText(hwnd).strip()

        # Filter out system desktop components and Jarvis HUD itself
        if ("stark industries mark vii" in title.lower() or "tactical hud" in title.lower()) and "jarvis" not in target_clean:
            return
        if title.lower() in ["program manager", "windows input experience"]:
            return


        # Determine process executable name
        proc_name = ""
        if win32process and psutil:
            try:
                _, pid = win32process.GetWindowThreadProcessId(hwnd)
                proc_name = psutil.Process(pid).name().lower()
            except Exception:
                proc_name = ""

        title_lower = title.lower()
        title_matched = any(k in title_lower for k in keywords)
        proc_matched = any(p == proc_name or p in proc_name for p in process_names)

        if title_matched or proc_matched:
            found_windows.append((hwnd, title, proc_name))

    # 1. Enumerate active windows via win32gui across desktop stations
    if win32gui:
        import ctypes
        orig_hdesk = None
        try:
            orig_hdesk = ctypes.windll.user32.GetThreadDesktop(ctypes.windll.kernel32.GetCurrentThreadId())
        except Exception:
            pass

        desktops_to_check = []
        if win32service and win32con:
            try:
                hdesk = win32service.OpenDesktop('default', 0, False, win32con.GENERIC_ALL)
                if hdesk:
                    desktops_to_check.append(hdesk)
            except Exception:
                pass
        desktops_to_check.append(None)

        for desk in desktops_to_check:
            try:
                if desk:
                    ctypes.windll.user32.SetThreadDesktop(int(desk))
                    win32gui.EnumDesktopWindows(desk, lambda h, e: check_window_candidate(h), None)
                elif orig_hdesk:
                    ctypes.windll.user32.SetThreadDesktop(int(orig_hdesk))
                    win32gui.EnumWindows(lambda h, e: check_window_candidate(h), None)
                else:
                    win32gui.EnumWindows(lambda h, e: check_window_candidate(h), None)
            except Exception:
                pass

        if orig_hdesk:
            try:
                ctypes.windll.user32.SetThreadDesktop(int(orig_hdesk))
            except Exception:
                pass




    # 2. PyGetWindow fallback if win32gui produced no matches
    if not found_windows and pygetwindow:
        try:
            for w in pygetwindow.getAllWindows():
                if w._hWnd in seen_hwnds:
                    continue
                w_title = (w.title or "").strip().lower()
                if any(k in w_title for k in keywords):
                    found_windows.append((w._hWnd, w.title, ""))
        except Exception:
            pass

    # 3. If no window was found
    if not found_windows:
        speak(f"I couldn't find an open window for {label}.")
        return False

    # 4. Perform the requested action on the matching window(s)
    acted_count = 0
    for hwnd, title, _ in found_windows:
        try:
            if action == "minimize":
                if win32gui and win32con:
                    win32gui.ShowWindow(hwnd, win32con.SW_MINIMIZE)
                    acted_count += 1
                elif pygetwindow:
                    w = pygetwindow.Win32Window(hwnd)
                    w.minimize()
                    acted_count += 1
            elif action == "close":
                if win32gui and win32con:
                    win32gui.PostMessage(hwnd, win32con.WM_CLOSE, 0, 0)
                    acted_count += 1
                elif pygetwindow:
                    w = pygetwindow.Win32Window(hwnd)
                    w.close()
                    acted_count += 1
            elif action in ["maximize", "restore"]:
                if win32gui and win32con:
                    win32gui.ShowWindow(hwnd, win32con.SW_RESTORE)
                    acted_count += 1
                elif pygetwindow:
                    w = pygetwindow.Win32Window(hwnd)
                    w.restore()
                    acted_count += 1
        except Exception as e:
            print(f"[Window Action Error on hwnd {hwnd}]: {e}")

    if acted_count > 0:
        past_tense = "Minimized" if action == "minimize" else ("Closed" if action == "close" else "Restored")
        speak(f"{past_tense} {label}.")
        return True
    else:
        speak(f"Unable to {action} {label}.")
        return False



def empty_recycle_bin() -> None:
    """Empties the Windows Recycle Bin."""
    speak("Emptying the Recycle Bin...")
    try:
        os.system('powershell -Command "Clear-RecycleBin -Force -ErrorAction SilentlyContinue"')
        speak("Recycle Bin is now empty.")
    except Exception as e:
        speak(f"Could not empty recycle bin: {e}")


def check_battery() -> None:
    """Reports battery and power status."""
    try:
        res = subprocess.check_output(
            'powershell -Command "Get-CimInstance -ClassName Win32_Battery -ErrorAction SilentlyContinue | Select-Object -ExpandProperty EstimatedChargeRemaining"',
            shell=True
        ).decode().strip()
        if res and res.isdigit():
            speak(f"Battery is currently at {res} percent.")
        else:
            speak("Your computer is plugged in and running on direct AC desktop power.")
    except Exception:
        speak("Your computer is connected to AC power.")


# =============================================================================
# MUSIC & MULTIMEDIA
# =============================================================================
def play_music(song_name: str = None) -> None:
    """Plays music from local Music folder or streams directly on YouTube."""
    music_dir = os.path.expanduser("~\\Music")
    audio_extensions = ('.mp3', '.wav', '.m4a', '.flac', '.aac', '.wma')
    songs = []

    if os.path.exists(music_dir):
        songs = [f for f in os.listdir(music_dir) if f.lower().endswith(audio_extensions)]

    if song_name:
        filtered = [s for s in songs if song_name.lower() in s.lower()]
        if filtered:
            chosen = random.choice(filtered)
            speak(f"Playing {chosen} from your Music library")
            os.startfile(os.path.join(music_dir, chosen))
            return
        else:
            # Not in local storage -> Stream immediately on YouTube!
            play_on_youtube(song_name)
            return

    if songs:
        chosen = random.choice(songs)
        speak(f"Playing {chosen} from your Music folder")
        os.startfile(os.path.join(music_dir, chosen))
    else:
        # No local MP3s? Automatically stream top trending hits on YouTube!
        speak("Streaming top trending music for you on YouTube")
        play_on_youtube("top trending music 2026")


def play_on_youtube(query: str, browser: str = None) -> None:
    """Searches YouTube and directly plays the top matching video."""
    speak(f"Playing {query} on YouTube")
    try:
        url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}"
        req = urllib.request.Request(url, headers={'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64)'})
        html = urllib.request.urlopen(req, timeout=4).read().decode('utf-8')
        video_ids = re.findall(r'/watch\?v=([a-zA-Z0-9_-]{11})', html)
        if video_ids:
            top_video_url = f"https://www.youtube.com/watch?v={video_ids[0]}"
            open_in_browser(top_video_url, browser)
            return
    except Exception as e:
        print(f"Direct video resolve notice: {e}")

    # Fallback to search results page
    open_in_browser(f"https://www.youtube.com/results?search_query={urllib.parse.quote(query)}", browser)


def subscribe_on_youtube(channel: str, browser: str = None) -> None:
    """Opens a YouTube channel search for easy 1-click subscribing."""
    speak(f"Opening {channel.title()} on YouTube for you to subscribe")
    channel_url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(channel)}&sp=EgIQAg%253D%253D"
    open_in_browser(channel_url, browser)


def record_audio(duration: int = 5) -> str:
    """Records audio from microphone and saves it as a WAV file."""
    try:
        import pyaudio
        import wave

        speak(f"Recording audio for {duration} seconds. Please speak now...")
        p = pyaudio.PyAudio()
        CHUNK = 1024
        FORMAT = pyaudio.paInt16
        CHANNELS = 2
        RATE = 44100

        stream = p.open(format=FORMAT, channels=CHANNELS, rate=RATE, input=True, frames_per_buffer=CHUNK)
        frames = []
        for _ in range(0, int(RATE / CHUNK * duration)):
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)

        stream.stop_stream()
        stream.close()
        p.terminate()

        save_dir = os.path.expanduser(r"~\Music")
        os.makedirs(save_dir, exist_ok=True)
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        filepath = os.path.join(save_dir, f"Jarvis_Audio_Recording_{timestamp}.wav")

        wf = wave.open(filepath, 'wb')
        wf.setnchannels(CHANNELS)
        wf.setsampwidth(p.get_sample_size(FORMAT))
        wf.setframerate(RATE)
        wf.writeframes(b''.join(frames))
        wf.close()

        speak("Recording completed and saved to your Music folder.")
        return filepath
    except Exception as e:
        msg = f"Audio recording failed: {e}"
        speak(msg)
        return msg


def take_screenshot() -> str:
    """Takes a screenshot and saves it in the user's Pictures folder."""
    if pyautogui is None:
        msg = "PyAutoGUI is not installed. Run 'pip install pyautogui' to enable screenshots."
        speak(msg)
        return msg

    try:
        timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        pictures_dir = os.path.expanduser("~\\Pictures")
        os.makedirs(pictures_dir, exist_ok=True)
        img_path = os.path.join(pictures_dir, f"Jarvis_screenshot_{timestamp}.png")
        img = pyautogui.screenshot()
        img.save(img_path)
        speak("Screenshot taken and saved successfully to your Pictures folder.")
        return img_path
    except Exception as e:
        msg = f"Failed to take screenshot: {e}"
        speak(msg)
        return msg


def search_wikipedia(query: str) -> str:
    """Searches Wikipedia and summarizes the topic."""
    if wikipedia is None:
        msg = "Wikipedia module not installed. Run 'pip install wikipedia'."
        speak(msg)
        return msg

    clean_query = query.replace("wikipedia", "").replace("search", "").strip()
    if not clean_query:
        speak("What would you like me to look up on Wikipedia?")
        clean_query = takecommand()
        if not clean_query:
            return ""

    try:
        speak(f"Searching Wikipedia for {clean_query}...")
        results = wikipedia.summary(clean_query, sentences=2)
        speak("According to Wikipedia:")
        speak(results)
        return results
    except wikipedia.exceptions.DisambiguationError:
        msg = f"Multiple results found for {clean_query}. Please be more specific."
        speak(msg)
        return msg
    except wikipedia.exceptions.PageError:
        msg = f"No Wikipedia page found for {clean_query}."
        speak(msg)
        return msg
    except Exception:
        msg = "I was unable to retrieve information from Wikipedia at this time."
        speak(msg)
        return msg


def tell_joke() -> None:
    """Tells a programmer or general joke."""
    if pyjokes:
        try:
            joke = pyjokes.get_joke()
            speak(joke)
            return
        except Exception:
            pass
    fallback_jokes = [
        "Why do programmers prefer dark mode? Because light attracts bugs!",
        "There are 10 types of people in the world: those who understand binary, and those who don't.",
        "Why did the developer go broke? Because he used up all his cache!",
        "Why do Java programmers wear glasses? Because they don't C#!"
    ]
    speak(random.choice(fallback_jokes))


def open_in_browser(url: str, browser: str = None) -> None:
    """Opens a URL in a specific browser (chrome/edge) or system default."""
    chrome_paths = [
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
        os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
    ]
    edge_paths = [
        r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
        r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
    ]

    try:
        if browser == "chrome":
            for path in chrome_paths:
                if os.path.exists(path):
                    subprocess.Popen([path, url])
                    return
            os.system(f'start chrome "{url}"')
            return

        elif browser == "edge":
            for path in edge_paths:
                if os.path.exists(path):
                    subprocess.Popen([path, url])
                    return
            os.system(f'start msedge "{url}"')
            return
    except Exception as e:
        print(f"Browser launch warning: {e}")

    # Fallback to system default browser
    wb.open(url)


def launch_application(target: str) -> bool:
    """
    Launches desktop applications, Windows tools, or web browsers directly.
    Handles executable paths, Windows URI schemes, and shell commands.
    """
    target_clean = target.lower().strip()

    # 1. Dedicated browser launching with verified installation paths
    if target_clean in ["microsoft edge", "edge", "msedge", "ms edge"]:
        edge_paths = [
            r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
            r"C:\Program Files\Microsoft\Edge\Application\msedge.exe"
        ]
        for p in edge_paths:
            if os.path.exists(p):
                subprocess.Popen([p])
                return True
        try:
            os.startfile("msedge.exe")
            return True
        except Exception:
            os.system("start msedge")
            return True

    if target_clean in ["google chrome", "chrome", "chorme"]:
        chrome_paths = [
            r"C:\Program Files\Google\Chrome\Application\chrome.exe",
            r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
            os.path.expanduser(r"~\AppData\Local\Google\Chrome\Application\chrome.exe")
        ]
        for p in chrome_paths:
            if os.path.exists(p):
                subprocess.Popen([p])
                return True
        try:
            os.startfile("chrome.exe")
            return True
        except Exception:
            os.system("start chrome")
            return True

    if target_clean in ["firefox", "mozilla firefox"]:
        try:
            os.startfile("firefox.exe")
            return True
        except Exception:
            os.system("start firefox")
            return True

    if target_clean in ["brave", "brave browser"]:
        try:
            os.startfile("brave.exe")
            return True
        except Exception:
            os.system("start brave")
            return True

    # 2. Check registered APP_COMMANDS
    cmd = APP_COMMANDS.get(target_clean)
    if cmd:
        try:
            if ":" in cmd:
                os.startfile(cmd)
                return True
            if cmd.endswith(".msc"):
                subprocess.Popen(["mmc.exe", cmd])
                return True
            os.system(f"start {cmd}")
            return True
        except Exception as e:
            print(f"[App Launch Error]: {e}")
            try:
                os.system(f"start {cmd}")
                return True
            except Exception:
                pass

    # 3. Check if executable exists directly on system PATH
    try:
        import shutil
        if shutil.which(target_clean):
            os.system(f"start {target_clean}")
            return True
    except Exception:
        pass

    return False



def parse_browser_intent(query: str):
    """Extracts target browser (chrome/edge/firefox/brave) and strips filler phrases."""
    q = query.strip()
    browser = None

    if re.search(r'\b(on|in|using|with)\s+(google\s+)?chrome\b', q, re.IGNORECASE):
        browser = "chrome"
        q = re.sub(r'\b(on|in|using|with)\s+(google\s+)?chrome\b', '', q, flags=re.IGNORECASE)
    elif re.search(r'\b(on|in|using|with)\s+(microsoft\s+)?edge\b', q, re.IGNORECASE):
        browser = "edge"
        q = re.sub(r'\b(on|in|using|with)\s+(microsoft\s+)?edge\b', '', q, flags=re.IGNORECASE)
    elif re.search(r'\b(on|in|using|with)\s+firefox\b', q, re.IGNORECASE):
        browser = "firefox"
        q = re.sub(r'\b(on|in|using|with)\s+firefox\b', '', q, flags=re.IGNORECASE)
    elif re.search(r'\b(on|in|using|with)\s+brave\b', q, re.IGNORECASE):
        browser = "brave"
        q = re.sub(r'\b(on|in|using|with)\s+brave\b', '', q, flags=re.IGNORECASE)

    return q.strip(), browser


# =============================================================================
# MATH & ARITHMETIC CALCULATION ENGINE
# =============================================================================
WORD_NUMS = {
    'zero': '0', 'one': '1', 'two': '2', 'three': '3', 'four': '4',
    'five': '5', 'six': '6', 'seven': '7', 'eight': '8', 'nine': '9',
    'ten': '10', 'eleven': '11', 'twelve': '12', 'thirteen': '13',
    'fourteen': '14', 'fifteen': '15', 'sixteen': '16', 'seventeen': '17',
    'eighteen': '18', 'nineteen': '19', 'twenty': '20', 'thirty': '30',
    'forty': '40', 'fifty': '50', 'sixty': '60', 'seventy': '70',
    'eighty': '80', 'ninety': '90', 'hundred': '100', 'thousand': '1000'
}

OPERATORS = {
    ast.Add: operator.add,
    ast.Sub: operator.sub,
    ast.Mult: operator.mul,
    ast.Div: operator.truediv,
    ast.Pow: operator.pow,
    ast.Mod: operator.mod,
    ast.USub: operator.neg,
    ast.UAdd: operator.pos
}


def eval_math_ast(expr: str):
    """Safely evaluates an arithmetic expression using Python AST without eval()."""
    def _eval(node):
        if isinstance(node, ast.Constant):
            if isinstance(node.value, (int, float)):
                return node.value
            raise TypeError("Non-numeric constant")
        elif isinstance(node, ast.BinOp):
            if type(node.op) in OPERATORS:
                return OPERATORS[type(node.op)](_eval(node.left), _eval(node.right))
            raise TypeError("Unsupported operator")
        elif isinstance(node, ast.UnaryOp):
            if type(node.op) in OPERATORS:
                return OPERATORS[type(node.op)](_eval(node.operand))
            raise TypeError("Unsupported operator")
        else:
            raise TypeError("Unsupported expression node")
    tree = ast.parse(expr, mode='eval')
    return _eval(tree.body)


def try_calculate(query: str) -> str | None:
    """
    Attempts to solve spoken or typed math questions.
    Returns a clean response like "It's 4" or None if not a calculation.
    """
    if not query:
        return None
    q = query.lower().strip()

    # Convert spoken numbers to digits (e.g. "two plus two" -> "2 plus 2")
    words = q.split()
    normalized_words = [WORD_NUMS.get(w.strip('?,.!'), w) for w in words]
    q_norm = ' '.join(normalized_words)

    # 1. Percentages: "what is 20 percent of 200", "20% of 500"
    pct_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:percent|%)\s+of\s+(\d+(?:\.\d+)?)', q_norm)
    if pct_match:
        try:
            p = float(pct_match.group(1))
            val = float(pct_match.group(2))
            res = (p / 100.0) * val
            if res.is_integer():
                res = int(res)
            return f"It's {res}"
        except Exception:
            pass

    # 2. Square roots: "square root of 144", "sqrt of 64"
    sqrt_match = re.search(r'(?:square\s+root|sqrt)\s+(?:of\s+)?(\d+(?:\.\d+)?)', q_norm)
    if sqrt_match:
        try:
            val = float(sqrt_match.group(1))
            res = math.sqrt(val)
            if res.is_integer():
                res = int(res)
            return f"It's {res}"
        except Exception:
            pass

    # Clean leading conversational prefixes
    cleaned = re.sub(
        r'^(?:jarvis\s+)?(?:please\s+)?(?:can\s+you\s+)?(?:tell\s+me\s+)?(?:what\s+is|what\'s|whats|calculate|solve|evaluate|how\s+much\s+is|compute)\s+',
        '',
        q_norm,
        flags=re.IGNORECASE
    ).strip()
    cleaned = cleaned.rstrip('?=. ')

    # Natural language operators to symbols
    replacements = [
        (r'\bplus\b', '+'),
        (r'\badd\b', '+'),
        (r'\band\b', '+'),
        (r'\bminus\b', '-'),
        (r'\bsubtract\b', '-'),
        (r'\btimes\b', '*'),
        (r'\bmultiplied\s+by\b', '*'),
        (r'\bmultiply\b', '*'),
        (r'\binto\b', '*'),
        (r'\bx\b', '*'),
        (r'\bdivided\s+by\b', '/'),
        (r'\bdivide\b', '/'),
        (r'\bover\b', '/'),
        (r'\bto\s+the\s+power\s+of\b', '**'),
        (r'\bpower\s+of\b', '**'),
        (r'\braised\s+to\b', '**'),
        (r'\bmodulo\b', '%'),
        (r'\bmod\b', '%'),
        (r'\^', '**'),
    ]

    expr = cleaned
    for pat, rep in replacements:
        expr = re.sub(pat, rep, expr)

    expr = expr.strip()
    # Must contain at least one digit and one operator, or be a valid arithmetic string
    if re.search(r'\d', expr) and re.search(r'[\+\-\*/%\^]', expr) and re.match(r'^[\d\s\+\-\*/%\.\(\)\*]+$', expr):
        try:
            res = eval_math_ast(expr)
            if isinstance(res, float) and res.is_integer():
                res = int(res)
            elif isinstance(res, float):
                res = round(res, 4)
            return f"It's {res}"
        except Exception:
            pass

    return None


# =============================================================================
# INTELLIGENT FACTUAL & KNOWLEDGE QUESTION ANSWERING
# =============================================================================
def clean_speech_text(text: str) -> str:
    """Cleans pronunciation guides, citations, timestamps, and bracketed notes for spoken voice."""
    if not text:
        return ""
    cleaned = text
    # Clean unicode replacement characters and stray bullet characters
    cleaned = cleaned.replace('\ufffd', ' - ')
    # Remove parenthetical pronunciation or extra dates e.g. '(listen); ...'
    cleaned = re.sub(r'\s*\([^)]*\)', '', cleaned)
    # Remove citation brackets like [1], [2], [a]
    cleaned = re.sub(r'\[[0-9a-zA-Z]+\]', '', cleaned)
    # Remove leading dates / timestamps e.g. 'Jul 20, 2026 -', 'August 7, 2023 ·', '2 days ago -'
    cleaned = re.sub(r'^[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\s*[\s\-\–\—\·\•\:\.\,\?\!]+\s*', '', cleaned)
    cleaned = re.sub(r'^\d+\s+(?:days?|hours?|months?|years?|weeks?)\s+ago\s*[\s\-\–\—\·\•\:\.\,\?\!]+\s*', '', cleaned)
    cleaned = re.sub(r'^(?:Published|Updated)\s*:\s*[A-Za-z]{3,9}\s+\d{1,2},?\s+\d{4}\s*[\s\-\–\—\·\•\:\.\,\?\!]+\s*', '', cleaned, flags=re.IGNORECASE)
    # Clean redundant whitespaces
    cleaned = re.sub(r'\s+', ' ', cleaned).strip()
    return cleaned


def fetch_web_knowledge_answer(query: str) -> str | None:
    """
    Fetches real-time web knowledge to answer any factual, lifestyle, or general
    knowledge question directly using web search snippets.
    """
    if not DDGS or not query:
        return None
    try:
        clean_q = query.strip()
        results = list(DDGS().text(clean_q, max_results=6))
        best_candidate = None
        for r in results:
            body = r.get('body', '').strip()
            if len(body) < 25:
                continue
            cleaned = clean_speech_text(body)
            # Split into clean sentences
            sentences = [s.strip() for s in re.split(r'(?<=[.!?])\s+', cleaned) if s.strip()]
            valid_sentences = [s for s in sentences if not s.endswith('...') and len(s) > 15]
            if not valid_sentences and sentences:
                valid_sentences = [sentences[0].rstrip('. ') + '.']

            if not valid_sentences:
                continue

            joined = ' '.join(valid_sentences[:2]).strip()
            if not joined.endswith('.'):
                joined += '.'

            # Filter out promotional / meta snippets vs direct knowledge
            lower_j = joined.lower()
            is_promo = any(p in lower_j for p in [
                'this article', 'read more', 'click here', 'in this guide', 
                'subscribe to', 'learn some of the reasons', 'we explore'
            ])

            if not is_promo:
                return joined
            elif best_candidate is None:
                best_candidate = joined

        return best_candidate
    except Exception:
        return None


def answer_knowledge_question(query: str) -> str | None:
    """Answers any question directly via Wikipedia and Web Knowledge Engine without opening browser."""
    if not query:
        return None
    raw = query.strip()
    q = raw.lower()

    # Specific conversational responses
    if any(k in q for k in ["who created you", "who made you", "who developed you", "who is your creator"]):
        return "I was created by Stark Industries and my brilliant engineer, sir."
    if any(k in q for k in ["tell me a fact", "interesting fact", "random fact", "give me a fact"]):
        facts = [
            "Honey never spoils. Archaeologists have found pots of honey in ancient tombs that are over three thousand years old and still perfectly edible.",
            "Octopuses have three hearts and blue blood.",
            "A day on Venus is longer than a year on Venus.",
            "Bananas are curved because they grow towards the sun against gravity, a process known as negative geotropism.",
            "Light travels from the Sun to the Earth in about eight minutes and twenty seconds."
        ]
        return random.choice(facts)

    # Universal question detection patterns
    question_pattern = re.match(
        r'^(?:jarvis\s+)?(?:please\s+)?(?:can\s+you\s+)?(?:could\s+you\s+)?(?:tell\s+me\s+)?(what(?:\'s|s|\s+is|\s+are|\s+was|\s+were)?|who(?:\'s|s|\s+is|\s+was|\s+were)?|where(?:\'s|s|\s+is|\s+are|\s+was|\s+were)?|when(?:\'s|s|\s+is|\s+was|\s+did)?|why(?:\s+is|\s+are|\s+does|\s+do|\s+did)?|how(?:\'s|s|\s+is|\s+are|\s+does|\s+do|\s+did|\s+can|\s+many|\s+much|\s+far|\s+long|\s+old)?|which|can|could|do|does|did|is|are|tell\s+me\s+about|define|explain|meaning\s+of)\s+(.+)$',
        q,
        re.IGNORECASE
    )

    clean_term = None
    if question_pattern:
        clean_term = question_pattern.group(2).strip().rstrip('?=. ')
    elif q.endswith('?') and len(q.split()) >= 2:
        clean_term = q.rstrip('?=. ')

    if not clean_term:
        return None

    # Filter out system queries or app intents that might start with 'what is'
    if clean_term in ["time", "current time", "the time", "date", "today's date", "your name"]:
        return None

    core_search = re.sub(r'^(the|a|an)\s+', '', clean_term, flags=re.IGNORECASE).strip()
    if not core_search:
        return None

    headers = {
        'User-Agent': 'JarvisVoiceAssistant/2.0 (stark_assistant@example.com)'
    }

    # Step 1: OpenSearch for matching article title and REST summary
    try:
        search_url = f"https://en.wikipedia.org/w/api.php?action=opensearch&search={urllib.parse.quote(core_search)}&limit=3&namespace=0&format=json"
        req = urllib.request.Request(search_url, headers=headers)
        with urllib.request.urlopen(req, timeout=4) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            titles = data[1] if len(data) > 1 else []
            if titles:
                best_title = titles[0].replace(' ', '_')
                summary_url = f"https://en.wikipedia.org/api/rest_v1/page/summary/{urllib.parse.quote(best_title)}"
                sum_req = urllib.request.Request(summary_url, headers=headers)
                with urllib.request.urlopen(sum_req, timeout=4) as sum_resp:
                    sum_data = json.loads(sum_resp.read().decode('utf-8'))
                    extract = sum_data.get('extract', '')
                    if extract:
                        cleaned = clean_speech_text(extract)
                        sentences = re.split(r'\.\s+', cleaned)
                        res = '. '.join(sentences[:2]).strip()
                        if res and not res.endswith('.'):
                            res += '.'
                        return res
    except Exception:
        pass

    # Step 2: Fallback to wikipedia library
    if wikipedia:
        try:
            summary = wikipedia.summary(core_search, sentences=2, auto_suggest=False)
            if summary:
                return clean_speech_text(summary)
        except Exception:
            pass

    # Step 3: Real-Time Universal Web Knowledge Engine (DuckDuckGo Knowledge Retrieval)
    # Answers any lifestyle, health, factual, or general question known to man
    web_ans = fetch_web_knowledge_answer(raw) or fetch_web_knowledge_answer(core_search)
    if web_ans:
        return web_ans

    return None


# =============================================================================
# UNIVERSAL COMMAND EXECUTION ENGINE (Master Control)
# =============================================================================
def execute_command(query: str) -> bool:
    """
    Processes and executes any voice or text command with full computer control.
    Returns True to continue listening, or False to exit.
    """
    if not query:
        return True

    raw_q = query.strip()
    q = raw_q.lower()

    # 0. Standalone Wake-Word Greeting
    if q in ["jarvis", "hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis", "okay jarvis"]:
        speak("Yes, sir? I am listening.")
        return True

    # Strip leading wake-word if query was "Jarvis, [command]"
    if re.match(r'^(?:hey\s+jarvis|ok\s+jarvis|okay\s+jarvis|hello\s+jarvis|jarvis)\s*[,:]?\s*', q):
        raw_q = re.sub(r'^(?:hey\s+jarvis|ok\s+jarvis|okay\s+jarvis|hello\s+jarvis|jarvis)\s*[,:]?\s*', '', raw_q, flags=re.IGNORECASE).strip()
        q = raw_q.lower()

    # 1. Exit Commands
    if any(k in q for k in ["offline", "exit", "quit", "goodbye", "bye jarvis", "sleep jarvis", "close jarvis"]):
        speak("Going offline. Have a great day, sir!")
        return False

    # 2. System Power Controls (Lock, Sleep, Restart, Shutdown, Abort)
    if any(action in q for action in ["cancel", "abort", "stop"]) and any(target in q for target in ["shutdown", "shut down", "restart", "reboot"]):
        system_power("abort")
        return True

    if any(k in q for k in ["shutdown", "shut down", "power off", "turn off pc", "turn off computer", "turn off system"]) and not any(k in q for k in ["cancel", "abort", "don't", "dont"]):
        system_power("shutdown")
        return True

    if q in ["restart", "restart pc", "restart computer", "restart system", "reboot", "reboot pc", "reboot computer", "reboot system"] or (
        any(r in q for r in ["restart", "reboot"]) and any(k in q for k in ["pc", "computer", "system", "workstation", "windows", "machine"])
    ):
        system_power("restart")
        return True

    if q in ["sleep", "sleep pc", "sleep computer", "sleep system", "pc sleep", "suspend pc"] or (
        "sleep" in q and any(k in q for k in ["pc", "computer", "system", "workstation", "windows"])
    ) or any(phrase in q for phrase in ["put pc to sleep", "put computer to sleep", "put system to sleep"]):
        system_power("sleep")
        return True

    if q in ["lock", "lock pc", "lock screen", "lock computer", "lock workstation", "lock windows", "lock system"] or (
        "lock" in q and any(k in q for k in ["pc", "computer", "screen", "workstation", "windows", "system", "work station"])
    ):
        system_power("lock")
        return True

    # 3. Math & Calculation Engine (Answers direct math queries like "what is 2 plus 2")
    calc_res = try_calculate(raw_q)
    if calc_res:
        speak(calc_res)
        return True

    # 4. Notes Management (Must precede generic checks, but exclude Notepad app)
    if "notepad" not in q and (re.search(r'\b(notes?|remember)\b', q)):
        if any(k in q for k in ["delete", "clear", "remove", "erase", "reset"]):
            clear_notes()
            return True
        elif any(k in q for k in ["read", "show", "view", "check", "what", "tell me what"]):
            recall_notes()
            return True
        else:
            note_content = q
            for prefix in ["remember that", "remember to", "remember", "add note that", "add note to", "add note", "take note that", "take note to", "take note", "write note that", "write note to", "write note", "record note"]:
                note_content = note_content.replace(prefix, "")
            remember_note(note_content.strip())
            return True

    # 3. Time and Date (Smart detection)
    if "date" in q and "time" in q:
        tell_time_and_date()
        return True
    elif any(k in q for k in ["time", "clock", "what time", "current time", "what's the time"]):
        tell_time()
        return True
    elif any(k in q for k in ["date", "what date", "today's date", "current date", "what day"]):
        tell_date()
        return True

    # 4. Volume & Master Audio Controls
    if "volume" in q or "sound" in q:
        if any(k in q for k in ["up", "increase", "raise", "high", "louder", "boost"]):
            change_volume("up")
            return True
        elif any(k in q for k in ["down", "decrease", "lower", "reduce", "low", "softer"]):
            change_volume("down")
            return True
        elif any(k in q for k in ["mute", "unmute"]):
            change_volume("mute")
            return True

    if q in ["mute", "unmute"]:
        change_volume("mute")
        return True

    # 5. Media Playback Controls
    if any(k in q for k in ["pause", "resume", "play/pause", "stop video", "stop music"]):
        media_control("playpause")
        return True
    if any(k in q for k in ["next song", "next track", "skip song"]):
        media_control("next")
        return True
    if any(k in q for k in ["previous song", "prev track"]):
        media_control("prev")
        return True

    # 6. Windows Desktop & Window Controls
    if "lock" in q and any(k in q for k in ["pc", "computer", "screen", "workstation", "windows"]):
        window_control("lock")
        return True

    # 6a. Single / Specific Window Management (e.g., "minimize chrome", "close chorme", "close notepad", "restore edge")
    single_win_match = re.match(
        r'^(?:jarvis\s+)?(?:please\s+)?(?:can\s+you\s+)?(?:could\s+you\s+)?(close|minimize|maximize|restore)\s+(?:the\s+)?(?:window\s+(?:of|for)\s+)?([a-zA-Z0-9\s._\-]+?)(?:\s+window|\s+app|\s+application)?$',
        q,
        re.IGNORECASE
    )
    if single_win_match:
        action_word = single_win_match.group(1).lower()
        target_name = single_win_match.group(2).strip().lower()

        if target_name in ["all", "windows", "desktop", "all windows"]:
            window_control("minimize")
            return True
        elif target_name in ["window", "active", "current", "this", "active window", "current window", "active app", "app", "application", "tab"]:
            window_control(action_word if action_word in ["close", "minimize"] else "minimize")
            return True
        else:
            manage_specific_window(action_word, target_name)
            return True

    if any(k in q for k in ["minimize all", "minimize windows", "show desktop", "go to desktop"]):
        window_control("minimize")
        return True
    if "close" in q and any(k in q for k in ["window", "app", "application", "tab"]):
        window_control("close")
        return True

    if any(k in q for k in ["switch window", "switch app", "next window", "alt tab"]):
        window_control("switch")
        return True
    if "recycle bin" in q or "clean trash" in q or "empty trash" in q:
        empty_recycle_bin()
        return True
    if "battery" in q:
        check_battery()
        return True

    # 7. Screenshot
    if "screenshot" in q or "take snapshot" in q or "capture screen" in q:
        take_screenshot()
        return True

    # 8. Audio Recording
    if "record" in q and any(k in q for k in ["audio", "voice", "my voice", "sound"]):
        sec_match = re.search(r'(\d+)\s+seconds?', q)
        duration = int(sec_match.group(1)) if sec_match else 5
        record_audio(duration)
        return True

    # 9. Compound Browser Search: "open [browser] and search [query]"
    compound_match = re.match(
        r'^open\s+(google\s+chrome|chrome|microsoft\s+edge|edge|firefox|brave|browser)\s+(and\s+search\s+for|and\s+search|search\s+for|search)\s+(.+)$',
        q,
        re.IGNORECASE
    )
    if compound_match:
        b_name = compound_match.group(1).lower()
        target_browser = "chrome" if "chrome" in b_name else ("edge" if "edge" in b_name else None)
        b_label = f" on {target_browser.title()}" if target_browser else ""
        search_term = compound_match.group(3).strip()
        speak(f"Searching {search_term}{b_label}")
        url = f"https://www.google.com/search?q={urllib.parse.quote(search_term)}"
        open_in_browser(url, target_browser)
        return True

    # Browser preference extraction
    cleaned_q, target_browser = parse_browser_intent(q)
    b_label = f" on {target_browser.title()}" if target_browser else ""

    # 10. YouTube Direct Playback
    if "play" in cleaned_q and ("youtube" in raw_q.lower() or cleaned_q.startswith("open youtube and play")):
        play_target = re.sub(r'^(open\s+youtube\s+(and\s+)?play|play(\s+video|\s+song)?)\s+', '', cleaned_q, flags=re.IGNORECASE)
        play_target = re.sub(r'\s+(on|in)\s+youtube$', '', play_target, flags=re.IGNORECASE).strip()
        if play_target:
            play_on_youtube(play_target, target_browser)
            return True

    # 11. YouTube Channel Subscription
    if any(k in cleaned_q for k in ["subscribe", "subscrive", "channel"]) and ("youtube" in raw_q.lower() or "subscri" in cleaned_q):
        channel_target = re.sub(r'^(open\s+youtube\s+(and\s+)?|subscri[bv]e\s+(to\s+)?|open\s+(the\s+)?channel\s+)+', '', cleaned_q, flags=re.IGNORECASE)
        channel_target = re.sub(r'(\s+(on|in)\s+youtube|\s+channel)$', '', channel_target, flags=re.IGNORECASE).strip()
        if channel_target:
            subscribe_on_youtube(channel_target, target_browser)
            return True

    # 12. YouTube Search
    if "youtube" in cleaned_q and any(k in cleaned_q for k in ["search", "find", "look up"]):
        search_target = re.sub(r'^(open\s+youtube\s+(and\s+)?(search\s+for|search|find)|search\s+youtube\s+for|search\s+for|search)\s*', '', cleaned_q, flags=re.IGNORECASE)
        search_target = re.sub(r'\s+(on|in)\s+youtube$', '', search_target, flags=re.IGNORECASE).strip()
        if search_target:
            speak(f"Searching YouTube for {search_target}{b_label}")
            url = f"https://www.youtube.com/results?search_query={urllib.parse.quote(search_target)}"
            open_in_browser(url, target_browser)
            return True

    # 13. Music (Local library or YouTube Streaming)
    if any(k in cleaned_q for k in ["play music", "play a music", "play some music", "play song", "start music"]) or cleaned_q == "music":
        song_name = cleaned_q.replace("play music", "").replace("play a music", "").replace("play some music", "").replace("play song", "").replace("start music", "").replace("music", "").strip()
        play_music(song_name if song_name else None)
        return True

    # 14. Wikipedia Search
    wiki_match = re.match(
        r'^(search\s+on\s+wikipedia\s+for|search\s+wikipedia\s+for|search\s+for|search)\s+(.+?)\s+(on\s+wikipedia|in\s+wikipedia)$',
        cleaned_q,
        re.IGNORECASE
    )
    if wiki_match:
        search_wikipedia(wiki_match.group(2).strip())
        return True

    if "wikipedia" in cleaned_q:
        term = cleaned_q.replace("search wikipedia for", "").replace("search wikipedia", "").replace("wikipedia", "").strip()
        search_wikipedia(term)
        return True

    # 15. Universal "Open [Website / Application / Service]"
    open_match = re.match(r'^(?:jarvis\s+)?(?:please\s+)?(?:can\s+you\s+)?(?:could\s+you\s+)?(open|launch|start|run)\s+(.+)$', cleaned_q, re.IGNORECASE)
    if open_match:
        target = open_match.group(2).strip().lower()

        # Check Desktop Applications & Browsers
        if target in APP_COMMANDS or any(target == b for b in ["microsoft edge", "edge", "chrome", "google chrome", "chorme", "firefox", "brave", "opera"]):
            display_title = "Microsoft Edge" if "edge" in target else ("Google Chrome" if "chrome" in target or "chorme" in target else target.title())
            speak(f"Opening {display_title}")
            launch_application(target)
            return True

        # Check Popular Web Catalog
        if target in POPULAR_SITES:
            speak(f"Opening {target.title()}{b_label}")
            open_in_browser(POPULAR_SITES[target], target_browser)
            return True

        # Check Direct URLs (e.g. 'open github.com', 'open bbc.com')
        if "." in target and " " not in target:
            url = target if target.startswith("http") else f"https://{target}"
            speak(f"Opening {target}{b_label}")
            open_in_browser(url, target_browser)
            return True

        # Single word -> general website domain (e.g. 'open leetcode' -> leetcode.com)
        if " " not in target:
            speak(f"Opening {target.title()}{b_label}")
            open_in_browser(f"https://www.{target}.com", target_browser)
            return True

        # Multi-word phrase with spaces that is not an app or URL -> Clean Google Search
        speak(f"Searching for {target.title()}{b_label}")
        url = f"https://www.google.com/search?q={urllib.parse.quote(target)}"
        open_in_browser(url, target_browser)
        return True


    # 16. Jokes & Humor
    if "joke" in cleaned_q or "make me laugh" in cleaned_q:
        tell_joke()
        return True

    # 17. Assistant Identity & Status
    if "change your name" in cleaned_q or "set name" in cleaned_q:
        set_name()
        return True

    if "what is your name" in cleaned_q or "who are you" in cleaned_q:
        name = load_name()
        speak(f"I am {name}, your personal desktop voice assistant.")
        return True

    if "how are you" in cleaned_q:
        speak("I am functioning at 100% capacity, sir! Ready for your commands.")
        return True

    if "what can you do" in cleaned_q or cleaned_q in ["help", "commands"]:
        speak("I can control your PC volume, windows, media playback, lock screen, empty recycle bin, play music, tell time and date, manage notes, record audio, and open any app or website.")
        return True

    # 18. Direct Factual & Question Answering (Answers via voice without launching browser)
    direct_ans = answer_knowledge_question(raw_q)
    if direct_ans:
        speak(direct_ans)
        return True

    # 19. Explicit Searches: "search [query]" or "search [query] on google" or "google [query]"
    if cleaned_q.startswith("search for ") or cleaned_q.startswith("search ") or "search google" in cleaned_q or cleaned_q.startswith("google "):
        term = re.sub(r'^(search\s+google\s+for|search\s+for|search\s+google|search|google)\s*', '', cleaned_q).strip()
        term = re.sub(r'\s+(on|in|using)\s+google$', '', term, flags=re.IGNORECASE).strip()
        if term:
            speak(f"Searching {term}{b_label}")
            url = f"https://www.google.com/search?q={urllib.parse.quote(term)}"
            open_in_browser(url, target_browser)
            return True

    # 20. Universal Voice-First Fallback (Never blindly launches browser on general queries)
    fallback_ans = (
        answer_knowledge_question(raw_q)
        or answer_knowledge_question(f"what is {raw_q}")
        or fetch_web_knowledge_answer(raw_q)
        or fetch_web_knowledge_answer(f"what is {raw_q}")
    )
    if fallback_ans:
        speak(fallback_ans)
        return True

    speak(f"I couldn't find a direct answer for that, sir. You can say 'search for {raw_q}' if you would like me to check Google.")
    return True


# =============================================================================
# MICROPHONE & SPEECH RECOGNITION
# =============================================================================
def get_audio_input_devices():
    """Returns a list of tuples (index, name) of valid audio input devices."""
    if sr is None:
        return []
    try:
        import pyaudio
        p = pyaudio.PyAudio()
        devices = []
        for i in range(p.get_device_count()):
            info = p.get_device_info_by_index(i)
            if info.get('maxInputChannels', 0) > 0:
                devices.append((i, info.get('name', f'Device {i}')))
        p.terminate()
        return devices
    except Exception:
        return []


def takecommand(device_index: int = None) -> str:
    """Takes voice input from microphone using SpeechRecognition with fallback."""
    if sr is None:
        print("[Notice] SpeechRecognition module is not installed. Type your command below:")
        return input("Command > ").strip()

    r = sr.Recognizer()

    if device_index is None:
        try:
            devs = get_audio_input_devices()
            for idx, name in devs:
                if "microphone" in name.lower():
                    device_index = idx
                    break
        except Exception:
            device_index = None

    try:
        mic_kwargs = {}
        if device_index is not None:
            mic_kwargs["device_index"] = device_index

        with sr.Microphone(**mic_kwargs) as source:
            print(f"\nListening... (Using device {device_index if device_index is not None else 'Default'})")
            print("[Speak clearly into your microphone]")
            r.pause_threshold = 1
            r.adjust_for_ambient_noise(source, duration=0.6)
            try:
                audio = r.listen(source, timeout=6, phrase_time_limit=8)
            except sr.WaitTimeoutError:
                print("Listening timed out. (No speech detected)")
                return ""
    except (AttributeError, OSError, Exception) as e:
        print(f"\n[Microphone Error / Access Failed]: {e}")
        print("Falling back to keyboard input.")
        try:
            return input("Command > ").strip()
        except (KeyboardInterrupt, EOFError):
            return "offline"

    try:
        print("Recognizing speech...")
        query = r.recognize_google(audio, language="en-in")
        print(f"User: {query}")
        q_clean = query.strip()
        q_low = q_clean.lower()

        # If user just said the wake word "Jarvis"
        if q_low in ["jarvis", "hey jarvis", "hi jarvis", "hello jarvis", "ok jarvis", "okay jarvis"]:
            speak("Yes, sir? I am listening.")
            return takecommand(device_index=device_index)

        # If user said "Jarvis, [command]" in one breath: e.g. "Jarvis what is 2 plus 2"
        if re.match(r'^(?:hey\s+jarvis|ok\s+jarvis|okay\s+jarvis|hello\s+jarvis|jarvis)\s*[,:]?\s*', q_low):
            q_clean = re.sub(r'^(?:hey\s+jarvis|ok\s+jarvis|okay\s+jarvis|hello\s+jarvis|jarvis)\s*[,:]?\s*', '', q_clean, flags=re.IGNORECASE).strip()

        return q_clean
    except sr.UnknownValueError:
        speak("Sorry, I could not understand that. Could you please repeat?")
        return ""
    except sr.RequestError:
        speak("Speech recognition network service is currently unavailable. Please type your command.")
        return input("Command > ").strip()
    except Exception as e:
        print(f"Recognition Error: {e}")
        return ""


def listen_for_wake_word(device_index: int = None) -> tuple:
    """
    Listens passively for the wake-word 'jarvis' on the microphone.
    Returns (True, remainder_command) if detected, or (False, "") otherwise.
    """
    if sr is None:
        return False, ""

    r = sr.Recognizer()
    r.energy_threshold = 300
    r.dynamic_energy_threshold = True

    if device_index is None:
        try:
            devs = get_audio_input_devices()
            for idx, name in devs:
                if "microphone" in name.lower():
                    device_index = idx
                    break
        except Exception:
            device_index = None

    try:
        mic_kwargs = {}
        if device_index is not None:
            mic_kwargs["device_index"] = device_index

        with sr.Microphone(**mic_kwargs) as source:
            try:
                audio = r.listen(source, timeout=2.5, phrase_time_limit=4.5)
            except (sr.WaitTimeoutError, Exception):
                return False, ""

        phrase = r.recognize_google(audio, language="en-in").strip()
        phrase_low = phrase.lower()
        if "jarvis" in phrase_low:
            remainder = re.sub(r'.*?\bjarvis\b\s*[,:]?\s*', '', phrase, flags=re.IGNORECASE).strip()
            return True, remainder
    except Exception:
        pass

    return False, ""


def wishme():
    """Speaks the startup greeting."""
    speak("Hello, what can I help you with?")


def run_cli():
    """Starts the CLI version of Jarvis."""
    print("=" * 60)
    print("      J A R V I S   V O I C E   A S S I S T A N T")
    print("=" * 60)
    print(" [Voice Activation]: Say 'Jarvis' into your mic to activate.")
    print(" [Direct Commands]: Or speak/type any question or command directly.")
    print("=" * 60 + "\n")
    wishme()

    while True:
        query = takecommand()
        if not query:
            continue
        continue_running = execute_command(query)
        if not continue_running:
            break


if __name__ == "__main__":
    run_cli()
