# DarkBotManager
A Simple Manager of multiple DarkBot instances (folders). Update plugins, bot file, clear junk logs and old plugins in many bot folders from one place.

DarkBot Manager

![image](https://img.shields.io/badge/Python-FFD43B?style=for-the-badge&logo=python&logoColor=blue)
![image](https://img.shields.io/badge/License-MIT-green.svg)
![image](https://img.shields.io/badge/Platform-Windows-lightgrey.svg)
![image](https://img.shields.io/badge/json-5E5C5C?style=for-the-badge&logo=json&logoColor=white)

A professional GUI tool for managing multiple DarkBot instances. This application helps automate maintenance tasks, update bot files, plugins and clean up unnecessary files across multiple bot installations.
<img width="739" height="595" alt="LoveRussia2025 12 21 16 42 24" src="https://github.com/user-attachments/assets/50ca52a4-3a5b-4564-9626-fe9c80cc126a" />

<img width="739" height="595" alt="LoveRussia2025 12 21 16 23 32" src="https://github.com/user-attachments/assets/255e73b2-e787-4691-b932-4388fce0f0fb" />

<img width="739" height="595" alt="LoveRussia2025 12 21 16 25 20" src="https://github.com/user-attachments/assets/5c232556-c968-440b-9614-6297b54a2d64" />



## ✨ Features
### 🔧 Core Functionality
Multi-instance Management: Automatically detects bot folders under a selected root directory

Batch Operations: Perform actions on selected bots or all bots simultaneously

Thread-safe Processing: Background operations with real-time progress tracking

### 🧹 Cleaning Operations
Log Cleanup: Automatically removes all .log files from bot logs folders

Plugin Maintenance: Cleans up plugins/old and plugins/updates directories

Smart Detection: Heuristically identifies valid bot folders based on structure

### 📦 Update System
JAR Distribution: Copies updated DarkBot.jar to all bot instances

Plugin Updates: Distributes plugin .jar files to bot update folders

Intelligent Filtering: Skips DarkBot.jar in plugin folders (treats it as core file)

### 🌐 Internationalization
Multi-language Support: English and Polish interfaces

Auto-detection: Automatically uses system language

Language Switching: Change interface language on-the-fly

Extensible: Easy to add new language files

### ⚙️ Configuration
Persistent Settings: Configuration stored in %APPDATA%/DarkBotManager/

Path Management: Easy setup of bot root, DarkBot.jar location, and plugin sources

Validation System: Verifies all configured paths before operations

## 📋 Requirements
Python 3.6+ (if running from source)

Windows OS (primary target, may work on other systems but NOT TESTED)

No external dependencies (pure Python standard library)

## 🚀 Installation
### Option 1: Using Pre-built Executable (Recommended)
Download the latest release from the Releases page

Extract the archive

Run DarkBotManager.exe

The application will create necessary configuration files on first launch
This does not require python to be installed. It will work without it as any other .exe application

### Option 2: Running from Source
bash
 Clone the repository
git clone https://github.com/yourusername/DarkBotManager.git
cd DarkBotManager

 Run directly
python DarkBotManager.py
🖥️ Usage
Initial Setup
Launch the application

Click the Settings button (gear icon)

Configure the following paths:

Bot Root: Folder containing your bot instances (each in separate subfolders)

DarkBot.jar Path: Location of your updated DarkBot.jar file

Plugin Updates Folder: Directory containing plugin .jar files for distribution

Click Save

## Managing Bots
Refresh List: Scans the bot root and lists all detected bot folders

Clear & Update Selected: Performs all operations on selected bots only

Clear & Update All: Performs operations on all detected bots

Clear Logs/Old Only: Only cleans logs and old plugins without updating files

Validate Paths: Checks if all configured paths are valid

Folder Structure
Your bot root should follow this structure:

text
BotRoot/
├── BotInstance1/
│   ├── DarkBot.jar
│   ├── logs/
│   └── plugins/
│       ├── old/
│       └── updates/
├── BotInstance2/
│   ├── DarkBot.jar
│   ├── logs/
│   └── plugins/
│       ├── old/
│       └── updates/
└── BotInstance3/
    ├── DarkBot.jar
    ├── logs/
    └── plugins/
        ├── old/
        └── updates/
        
## 🗂️ Configuration Files
The application stores configuration in:

Config: %APPDATA%\DarkBotManager\config.json

Translations: %APPDATA%\DarkBotManager\translations.json

You can access the configuration folder via the Open Config Folder button.

## 🔧 Technical Details
Bot Detection Logic
A folder is considered a bot folder if:

It's a direct subdirectory of the bot root

AND contains either logs/ or plugins/ subdirectories

OR (fallback) any directory under the bot root

### Operation Sequence
When running "Clear & Update", the following operations are performed on each bot:

Delete all .log files in logs/ folder

Delete all .jar files in plugins/old/ folder

Clear everything in plugins/updates/ folder (files and subdirectories)

Copy DarkBot.jar to bot root (if source is valid)

Copy all plugin .jar files (except DarkBot.jar) to plugins/updates/

### Threading Model
GUI remains responsive during operations

Each bot processed in sequence (not parallel)

Progress bar updates in real-time

Detailed logging in the application console

### 🌍 Language Support
Currently supported languages:

English (default)

Polish (auto-detected for Polish systems)

Adding New Languages
Copy and edit translations.json in the config folder

Add a new language code (e.g., "de" for German)

Provide translations for all keys

Submit translation via pull request or other means (crowdin - coming soon, discord contact)

### 📝 Logging
The application provides detailed logging:

Info: General operation messages (white)

Success: Completed operations (green)

Warning: Non-critical issues (orange)

Error: Critical failures (red)

All logs are displayed in the application interface and can be scrolled through.

##🤝 Contributing
Contributions are welcome! Please feel free to submit a Pull Request.

## Development Setup
bash
### Clone and install development dependencies
git clone https://github.com/yourusername/DarkBotManager.git
cd DarkBotManager
### No external dependencies required!
Building Executables
bash
### Using PyInstaller
pyinstaller --onefile --noconsole --add-data "translations.json;." DarkBotManager.py

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments
Built with Python's Tkinter and ttkbootstrap, wrapped by pyinstaller

Inspired by the needs of DarkBot power users

Thanks to the community for feedback and testing

## 📞 Support
Discord: youknowwho5111

GitHub Issues: Report bugs or request features
