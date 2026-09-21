# 🤖 J.A.R.V.I.S. Desktop Voice Assistant — Complete Installation & User Guide

Welcome to the enhanced **J.A.R.V.I.S. Desktop Voice Assistant**! This guide walks you through every step to install, configure, and run your assistant on Windows.

---

## ⚡ Quick 1-Click Launch (If Python is already installed)
Simply double-click the **`run.bat`** file in the project folder!

---

## 📋 Table of Contents
1. [Prerequisites](#1-prerequisites)
2. [Step 1: Install Python on Windows](#2-step-1-install-python-on-windows)
3. [Step 2: Install Project Requirements](#3-step-2-install-project-requirements)
4. [Step 3: Run the Assistant](#4-step-3-run-the-assistant)
5. [Voice & Text Commands Reference](#5-voice--text-commands-reference)
6. [Troubleshooting & FAQs](#6-troubleshooting--faqs)

---

## 1. Prerequisites
- **Operating System**: Windows 10 or Windows 11 (64-bit recommended)
- **Microphone**: Any built-in laptop mic or external headset/USB mic (optional: keyboard typing is also supported)
- **Internet Connection**: For Google speech recognition, Wikipedia searches, and web browsing

---

## 2. Step 1: Install Python on Windows

If you don't have Python installed yet, choose **Option A** (quickest) or **Option B**:

### Option A: Via Windows Command Line (Fastest)
1. Open PowerShell or Command Prompt.
2. Run this command:
   ```powershell
   winget install Python.Python.3.11 --scope user
   ```
3. Restart your PowerShell or Command Prompt after installation finishes.

### Option B: Official Python Website
1. Go to [python.org/downloads](https://www.python.org/downloads/) and download **Python 3.10** or **3.11**.
2. Run the downloaded installer.
3. ⚠️ **VERY IMPORTANT**: On the very first screen of the installer, check the box at the bottom:
   > ☑️ **"Add python.exe to PATH"**
4. Click **"Install Now"** and let it finish.

---

## 3. Step 2: Install Project Requirements

1. Open PowerShell or Command Prompt inside the project directory:
   ```powershell
   cd "C:\Users\INTEL\Downloads\Jarvis-Desktop-Voice-Assistant-main\Jarvis-Desktop-Voice-Assistant-main"
   ```

2. (Optional but recommended) Create a virtual environment:
   ```powershell
   python -m venv .venv
   .venv\Scripts\activate
   ```

3. Install all dependencies using `pip`:
   ```powershell
   pip install -r requirements.txt
   ```

### 🎙️ Note regarding PyAudio on Windows:
`pyaudio` enables microphone speech recognition. With modern Python, `pip install pyaudio` installs pre-built binary wheels automatically.
If you ever run into a compiler error installing PyAudio:
```powershell
pip install pipwin
pipwin install pyaudio
```
*(Even if PyAudio is not installed, our enhanced Jarvis will gracefully fall back to text input mode so you can type commands without crashes!)*

---

## 4. Step 3: Run the Assistant

### Option 1: Modern Desktop HUD GUI (Recommended)
Double-click `run.bat` OR run:
```powershell
python main.py
```
This launches the sleek Stark Industries dark-mode interface with an animated Arc Reactor HUD, real-time transcript log, quick-action chips, and dual microphone + text input.

### Option 2: Enhanced Terminal / Console Mode
Run:
```powershell
python main.py --cli
```
or directly:
```powershell
python Jarvis/jarvis.py
```

---

## 5. Voice & Text Commands Reference

> 💡 **For an exhaustive guide of every single command (YouTube direct playing, full PC controls, volume, window controls, notes, apps, recording, etc.), check out the dedicated [COMMANDS.md](COMMANDS.md) file!**

You can speak any of these commands into your microphone, or type them directly into the GUI/terminal:

| Category | Example Commands | Action |
| :--- | :--- | :--- |
| **Greeting & Time** | `"What time is it?"`, `"time"` | Tells current time with AM/PM |
| **Date** | `"What is today's date?"`, `"date"` | Tells current day, month, and year |
| **Knowledge** | `"Search Wikipedia for Quantum Computing"` | Summarizes topic from Wikipedia |
| **Web Search** | `"Search Google for best Python projects"` | Opens Google search in default browser |
| **Streaming** | `"Open YouTube"`, `"Search YouTube for lofi music"` | Opens YouTube or searches videos |
| **Music** | `"Play music"`, `"Play a song"` | Plays audio files from your Windows Music folder |
| **Notes / Memory** | `"Remember that I have a doctor's appointment tomorrow"` | Saves note with timestamp into `data.txt` |
| **Read Notes** | `"Do you remember anything?"`, `"Read my notes"` | Reads back all stored notes |
| **Screenshot** | `"Take a screenshot"`, `"Screenshot"` | Captures screen and saves to `Pictures` folder |
| **Humor** | `"Tell me a joke"` | Delivers programming / general jokes |
| **Websites** | `"Open Google"`, `"Open Stack Overflow"`, `"Open GitHub"` | Launches developer websites |
| **Applications** | `"Open Notepad"`, `"Open Calculator"`, `"Open CMD"` | Launches Windows system apps |
| **Assistant Name** | `"What is your name?"`, `"Change your name"` | View or customize your assistant's name |
| **Exit** | `"Offline"`, `"Exit"`, `"Goodbye"` | Shuts down Jarvis cleanly |

---

## 6. Troubleshooting & FAQs

#### Q1: "Python was not found..."
- **Fix**: Make sure you ran `winget install Python.Python.3.11` or reinstalled Python with the **"Add python.exe to PATH"** checkbox checked. Restart your terminal window after installing.

#### Q2: "Microphone is unavailable or timed out"
- **Fix**: Check that your microphone is plugged in and allowed in Windows Settings (*Settings > Privacy & security > Microphone*). If your room is noisy or your mic is muted, simply type your command into the text box and press Enter!

#### Q3: "TTS voice doesn't sound right"
- **Fix**: Windows includes default text-to-speech voices (e.g. Microsoft David or Zira). You can add additional system voices in Windows Settings (*Time & Language > Speech > Add voices*).

#### Q4: "Where are notes and screenshots stored?"
- **Notes**: Stored in `Jarvis/data.txt`.
- **Screenshots**: Stored in your standard Windows `Pictures` folder as `Jarvis_screenshot_<timestamp>.png`.
