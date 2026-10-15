# File Integrity Monitoring System (FIMS)

A beginner-friendly Python project that records SHA-256 hashes of files and detects changes, new files, and deleted files during later scans.

## Features
- Create a trusted baseline of a folder
- Detect **modified**, **new**, and **deleted** files
- SHA-256 hashing
- JSON baseline and scan reports
- Command-line interface
- Optional Streamlit dashboard
- Works on Windows, Linux, and macOS

> Use this project on folders you own or are authorized to monitor. A baseline is only trustworthy if it is created from a known-clean state and protected from unauthorized modification.

## Requirements
- Python 3.10 or newer
- Standard library for the CLI
- Optional dashboard: Streamlit

## Setup (Windows PowerShell)
1. Extract the ZIP file.
2. Open PowerShell in the extracted `File_Integrity_Monitoring_System` folder.
3. Check Python:
   ```powershell
   python --version
   ```
4. Create and activate a virtual environment:
   ```powershell
   python -m venv .venv
   .\.venv\Scripts\Activate.ps1
   ```
   If activation is blocked for this terminal only:
   ```powershell
   Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
   .\.venv\Scripts\Activate.ps1
   ```
5. Install optional dashboard dependency:
   ```powershell
   pip install -r requirements.txt
   ```

## Setup (Kali Linux)
```bash
python3 --version
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```
If `venv` is unavailable on Kali, install it with `sudo apt install python3-venv`.

## Quick demo
The project includes `sample_data/monitored_folder/` with sample files.

### 1. Create baseline
Windows:
```powershell
python fim.py baseline sample_data/monitored_folder
```
Kali/Linux:
```bash
python3 fim.py baseline sample_data/monitored_folder
```

### 2. Scan for changes
```bash
python fim.py scan sample_data/monitored_folder
```
Expected first scan: no changes, if you have not modified the sample files since creating the baseline.

### 3. Test detection
Edit `sample_data/monitored_folder/notes.txt`, add a new file, or delete a sample file. Then run:
```bash
python fim.py scan sample_data/monitored_folder
```
The report should show modified/new/deleted files.

### 4. View the latest report
```bash
python fim.py report
```
Reports are saved in the `reports/` folder.

## Optional Streamlit dashboard
After installing requirements:
```bash
streamlit run dashboard.py
```
Use the sidebar to select the folder, create a baseline, or run a scan. The dashboard displays the latest result.

## Commands
```text
python fim.py baseline <folder> [--exclude DIR_OR_FILE ...]
python fim.py scan <folder> [--exclude DIR_OR_FILE ...]
python fim.py report [--file REPORT_JSON]
```
The baseline is stored in `data/baseline.json`. Scan reports are stored in `reports/`.

## Project structure
```text
File_Integrity_Monitoring_System/
├── fim.py
├── fim_core.py
├── dashboard.py
├── requirements.txt
├── README.md
├── sample_data/
│   └── monitored_folder/
│       ├── notes.txt
│       └── config.ini
├── data/
│   └── .gitkeep
└── reports/
    └── .gitkeep
```

## Important limitations
- SHA-256 detects content changes; it does not prove who changed a file or why.
- The baseline JSON can be tampered with if an attacker can modify it. Store it separately or make it read-only for stronger protection.
- This demo scans when you run a command; it does not continuously monitor in real time.
- Files that cannot be read are reported as errors and are not silently treated as unchanged.
