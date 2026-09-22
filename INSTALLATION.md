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
   *Alternatively, install them manually in a single command:*
   ```powershell
   pip install edge-tts pygame ddgs SpeechRecognition pyaudio pywin32 pygetwindow pyautogui psutil pyjokes wikipedia pyttsx3
   ```

### 📦 Complete Breakdown of Installed Libraries

| Package | Purpose in Jarvis |
| :--- | :--- |
| **`edge-tts`** | Generates a natural human male voice (`en-US-GuyNeural`) with ~85-90% human likeness. |
| **`pygame`** | Fast, high-fidelity audio playback engine for the neural voice. |
| **`ddgs`** | Real-time web knowledge retrieval engine to answer any lifestyle, health, or factual question known to man. |
| **`SpeechRecognition`** | Translates your spoken microphone audio into text commands. |
| **`pyaudio`** | Windows microphone audio capture for hands-free and `"Jarvis"` wake-word activation. |
| **`pywin32`** | Windows OS integration, native SAPI speech engine, and window focus control. |
| **`pygetwindow`** | System window tracking, focus, minimization, and maximization. |
| **`pyautogui`** | Hardware media keys, volume control, and automated screenshot capture. |
| **`psutil`** | Live system telemetry (CPU usage %, RAM %, and battery status). |
| **`wikipedia`** | Direct access to Wikipedia knowledge summaries. |
| **`pyjokes`** | Humorous programming and geek jokes. |
| **`pyttsx3`** | Offline text-to-speech fallback engine. |

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
| **Wake-Word Activation** | Say `"Jarvis"` into microphone | Activates voice listening mode automatically |
| **Universal Knowledge** | `"What is the benefit of eating apple"` | Spoken direct answer via real-time web knowledge engine |
| **Math & Calculation** | `"What is 2 plus 2"`, `"20% of 500"` | Speaks direct arithmetic answers: *"It's 4"*, *"It's 100"* |
| **Science & Facts** | `"Who walked on the moon first"`, `"Why is ocean salty"` | Direct factual answer spoken aloud in male voice |
| **Greeting & Time** | `"What time is it?"`, `"time"` | Tells current time with AM/PM |
| **Date** | `"What is today's date?"`, `"date"` | Tells current day, month, and year |
| **Wikipedia** | `"Search Wikipedia for Quantum Computing"` | Summarizes topic from Wikipedia |
| **Web Search** | `"Search Google for best Python projects"` | Opens Google search in browser |
| **Streaming** | `"Open YouTube"`, `"Search YouTube for lofi music"` | Opens YouTube or searches videos |
| **Direct YouTube Play** | `"Open YouTube and play CarryMinati latest video"` | Resolves video ID and streams immediately |
| **Music** | `"Play music"`, `"Play a song"` | Plays audio files from Windows Music folder or online hits |
| **Notes / Memory** | `"Remember that I have a doctor's appointment tomorrow"` | Saves note with timestamp into `data.txt` |
| **Read Notes** | `"Do you remember anything?"`, `"Read my notes"` | Reads back all stored notes |
| **Screenshot** | `"Take a screenshot"`, `"Screenshot"` | Captures screen and saves to `Pictures` folder |
| **PC Hardware Controls** | `"Volume up"`, `"Mute"`, `"Next track"`, `"Empty recycle bin"` | Controls volume, media, and trash |
| **Humor** | `"Tell me a joke"` | Delivers programming / general jokes |
| **Websites** | `"Open Google"`, `"Open Stack Overflow"`, `"Open GitHub"` | Launches websites |
| **Applications** | `"Open Notepad"`, `"Open Calculator"`, `"Open CMD"` | Launches Windows system apps |
| **Assistant Name** | `"What is your name?"`, `"Change your name"` | View or customize your assistant's name |
| **Exit** | `"Offline"`, `"Exit"`, `"Goodbye"` | Shuts down Jarvis cleanly |

---

## 6. Troubleshooting & FAQs

#### Q1: "Python was not found..."
- **Fix**: Make sure you ran `winget install Python.Python.3.11` or reinstalled Python with the **"Add python.exe to PATH"** checkbox checked. Restart your terminal window after installing.

#### Q2: "How to reinstall all required packages if pip gives an error?"
- **Fix**: Run:
  ```powershell
  python -m pip install --upgrade pip
  pip install -r requirements.txt
  ```

#### Q3: "Microphone is unavailable or timed out"
- **Fix**: Check that your microphone is plugged in and allowed in Windows Settings (*Settings > Privacy & security > Microphone*). If your room is noisy or your mic is muted, simply type your command into the text box and press Enter!

#### Q4: "How does the Natural Male Voice work?"
- **Fix**: Jarvis automatically uses Microsoft's Natural Neural Male Voice (`en-US-GuyNeural`) via `edge-tts` and `pygame`. If you are completely offline, Jarvis seamlessly switches to your local Windows SAPI voice (`Microsoft David Desktop` or `Microsoft Mark`) so speech never fails.

#### Q5: "Where are notes and screenshots stored?"
- **Notes**: Stored in `Jarvis/data.txt`.
- **Screenshots**: Stored in your standard Windows `Pictures` folder as `Jarvis_screenshot_<timestamp>.png`.

