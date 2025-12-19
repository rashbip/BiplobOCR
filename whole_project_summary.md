# BiplobOCR - Project Summary

## Overview

BiplobOCR is a comprehensive desktop application designed to perform Optical Character Recognition (OCR) on PDF documents. Built with **Python** and **Tkinter**, it provides a user-friendly interface for the powerful `ocrmypdf` engine, enabling users to convert scanned or image-based PDFs into searchable, text-selectable documents. The application requires no external Tesseract installation if the bundled version is used, making it highly portable and easy to deploy on Windows.

## Key Features

### 1. OCR Capabilities

- **Searchable PDFs**: Converts image-only PDFs into high-quality, searchable text PDFs.
- **Sidecar Text**: Generates a companion `.txt` file containing the extracted text.
- **Automated Image Processing**:
  - **Deskew**: Automatically straightens scanned pages.
  - **Clean**: Removes noise and background artifacts.
  - **Rotate**: Auto-rotates pages to the correct orientation.
- **Optimization**: Compresses and optimizes output PDFs for smaller file sizes.
- **Robust Handling**:
  - **Encrypted PDFs**: Detects and handles password-protected files (prompts user).
  - **Large Files**: Automatically splits large PDFs (>50 pages) into chunks to prevent memory overflows, processing them sequentially and merging them back.
  - **Sanitization**: Includes a fallback mechanism to rasterize and rebuild corrupt PDFs that fail standard processing.

### 2. User Interface (GUI)

The application features a modern, dark-themed interface built with `tkinter` and styled with `ttk`:

- **Dashboard (Home)**: Displays valid actions (scan, batch) and a list of recent activities/history.
- **Scan View**: dedicated interface for single-file processing with file previewing capabilities.
- **Batch View**: Allows users to queue multiple PDF files for sequential unattended processing.
- **Log View**: A real-time log window ("See Process") that displays the raw output from the OCR engine for debugging or progress monitoring.
- **Drag & Drop**: Full support for dragging PDF files directly into the window.

### 3. Performance & Hardware

- **GPU Acceleration**: Supports OpenCL-based GPU acceleration for Tesseract to speed up processing.
- **Multi-threading**: Configurable CPU thread limits to balance system load.
- **Portable Engine**: Capable of using a bundled Tesseract binary located in `src/tesseract/windows`, avoiding PATH conflicts or complex user setups.

### 4. Localization

- **Multi-language Support**: Fully localized interface supporting **English** and **Bengali**.
- **OCR Languages**: Supports multiple OCR languages (based on available `.traineddata` files).

## Technical Architecture

### Directory Structure

- **`src/`**: The core source code.
  - **`gui/`**: Contains all UI-related code.
    - `app.py`: The main application controller and window.
    - `views/`: Separate modules for each screen (Home, scan, Batch, Settings, History, Log).
    - `controllers/`: Logic handlers separating UI from business logic.
  - **`core/`**: Backend logic.
    - `ocr_engine.py`: The wrapper around `ocrmypdf`, `tesseract`, and `ghostscript`. Handles process management, chunking, and error recovery.
    - `config_manager.py`: Manages `config.json` for persistent user settings.
    - `history_manager.py`: Tracks processed files using a JSON database.
  - **`tesseract/`**: Contains the bundled Tesseract binaries and data (Windows specific).
- **`run.py`**: The application entry point. Ensures correct path setup and UTF-8 encoding for Windows consoles.
- **`installer/`**: Resources for building the Setup installer (Inno Setup / PyInstaller artifacts).

### Dependencies

The project relies on several key Python libraries:

- **`ocrmypdf`**: The core engine driving the OCR process.
- **`pikepdf`**: Used for high-speed PDF manipulation (splitting, merging, repairing).
- **`PyMuPDF` (fitz)**: Used for fast PDF analysis (image vs text detection) and rasterization (sanitization).
- **`tkinterdnd2`**: Enabled native drag-and-drop support in Tkinter.
- **`Pillow`**: Image processing helper.

## Deployment

- **Installer**: The project is set up to be built into a standalone Windows executable and packaged with an installer (likely Inno Setup) that handles dependencies.
- **Configuration**: Settings are stored in a `config.json` file in the application root, making it easy to reset or transfer configurations.

## Development Status

- **Current Version**: 2.2
- **Maintainability**: The code uses a View-Controller pattern in the GUI and modularized core logic, making it relatively easy to extend or debug.
