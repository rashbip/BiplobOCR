# BiplobOCR User Documentation

Welcome to the detailed documentation for **BiplobOCR**. This guide covers detailed usage instructions, configuration explainers, and troubleshooting tips.

---

## 📖 Table of Contents

1.  [Getting Started](#getting-started)
2.  [Feature Guide](#feature-guide)
    - [Scanning Single Files](#scanning-single-files)
    - [Batch Processing](#batch-processing)
    - [History Log](#history-log)
3.  [Settings & Configuration](#settings--configuration)
4.  [Advanced Features](#advanced-features)
5.  [Troubleshooting](#troubleshooting)

---

## 1. Getting Started

BiplobOCR helps you convert scanned PDF documents (which are essentially images) into **searchable, selectable text PDFs**. It uses powerful open-source engines (Tesseract & OCRmyPDF) wrapped in a friendly interface.

### Launching

Run the application using the launcher shortcut or by running the script:

```bash
python run.py
```

_If using the compiled executable, simply double-click `BiplobOCR.exe`._

---

## 2. Feature Guide

### Scanning Single Files (Tools Tab)

Use this mode when you want to process one specific document and need granular control over the settings.

1.  **Import**:
    - Click **"Select from Computer"** on the Home screen or **"Open PDF"** in the Tools tab.
    - Alternatively, **Drag and Drop** a PDF file directly onto the window.
2.  **Preview**: The application will attempt to show the first page of the PDF to verify you loaded the correct file.
3.  **Adjust Options**: On the right panel, you can toggle specific filters (see [Settings](#settings--configuration)).
4.  **Process**: Click **"Start OCR"**.
    - A progress bar will show the current page being scanned.
    - You can view detailed logs by clicking **"See Process"**.
5.  **Save**: Once finished, a success screen will appear allowing you to:
    - **Save PDF**: The searchable version.
    - **Save Text**: A `.txt` file containing just the extracted text.

### Batch Processing

Use this mode to process a folder full of documents automatically.

1.  Navigate to the **"Batch Process"** tab.
2.  **Add Files**: Click "Add Files" to select multiple PDFs, or drag a selection of files into the list area.
3.  **Queue**: Files appear in the list with status "Pending".
4.  **Start**: Click **"Start Batch"**. The app will process file #1, save it (auto-saving to the same folder with `_ocr` suffix or as configured), then move to file #2.
5.  **Stop**: You can hit "STOP" at any time to halt the queue after the current file finishes.

### History Log

The application keeps a local database of your activity.

- View recently processed files.
- Check the status (Success/Failed).
- **Double-click** an entry to open the output file.
- **Right-click** to open the file location.

---

## 3. Settings & Configuration

The **Settings** tab allows you to customize how the OCR engine behaves.

### 🖼 Image Processing Filters

These options change how the image is treated _before_ text recognition.

- **Auto-Deskew**: Attempts to straighten pages that were scanned at an angle. Highly recommended.
- **Clean Background**: Removes pepper noise and dark scanning artifacts.
- **Auto-Rotate**: Detects if text is upside down or sideways and rotates the page to be readable.
- **Force OCR**: Use this if the file already has some text but it's garbage/incorrect. It forces the engine to ignore existing text layers and re-scan the images.

### 🚀 Hardware & Performance

- **Primary Device (GPU/CPU)**:
  - _CPU_: Standard mode. Reliable.
  - _GPU (OpenCL)_: Uses your graphics card to accelerate Tesseract. Note: This can sometimes be unstable depending on drivers. If it fails, the app automatically falls back to CPU.
- **Max CPU Threads**: Limits how many processor cores the OCR engine can use. Reduce this if your computer lags while scanning.
- **Optimization**:
  - _0 (None)_: High quality, larger file size.
  - _1-3_: Various levels of compression (lossy). Level 1 is a good balance.

### 🌐 Language

- **Interface Language**: Switch the entire app UI between **English** and **Bengali**.
- **OCR Language**: This is crucial. Steps to ensure the engine looks for the correct characters.
  - If your document is in English, select `eng`.
  - If it's in Bengali, select `ben`.
  - _Note: You must have the corresponding `.traineddata` file in the `tesseract/tessdata` folder._

---

## 4. Advanced Features

### 📦 Large File Chunking

BiplobOCR includes a smart memory management system.

- If a PDF is larger than **50 pages**, the application enters **Chunking Mode**.
- It splits the PDF into smaller blocks (e.g., 20 pages each).
- It processes these blocks individually to keep RAM usage low.
- Finally, it merges them back together seamlessly.
- _User Action_: None required. This happens automatically.

### 🔐 Password Protection

- If a PDF is encrypted, the app detects it immediately.
- A popup will ask for the password.
- The app decrypts it to a temporary file, processes it, and then deletes the temporary insecure copy.

### 🩹 Self-Healing (Sanitization)

- Sometimes PDFs have corrupt internal streams (common with old scanners).
- If OCR fails with an error like "Invalid Stream" or "Corrupt JPEG", the app triggers **Sanitization**.
- It purely rasterizes (takes a picture of) every page and rebuilds a fresh, clean PDF, then tries OCR again.

---

## 5. Troubleshooting

| Problem                          | Possible Cause     | Solution                                                                                     |
| :------------------------------- | :----------------- | :------------------------------------------------------------------------------------------- |
| **"Tesseract not found"**        | Missing binaries   | Ensure the `src/tesseract` folder exists or Tesseract is installed in your system PATH.      |
| **"Ghostscript missing"**        | Dependency missing | Install Ghostscript (required by `ocrmypdf`).                                                |
| **App freezes while processing** | Heavy CPU usage    | Lower the "Max CPU Threads" in Settings.                                                     |
| **"Permission Denied"**          | Write protection   | Move the application to a user folder (e.g., Desktop/Documents) instead of C:\Program Files. |
| **Garbage text output**          | Wrong language     | Check the **OCR Language** setting matches the document language.                            |
| **"Visual C++ Runtime Error"**   | Missing DLLs       | Install the standard "Microsoft Visual C++ Redistributable".                                 |

---

_Documentation Version 2.2 - Generated for BiplobOCR_
