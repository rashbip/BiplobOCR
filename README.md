# Biplob OCR

A PDF OCR utility application.

## Project Structure

- `src/`: Source code.
  - `main.py`: Main entry point logic.
  - `gui/`: GUI components (Tkinter).
  - `core/`: Core OCR logic and subprocess handling.
  - `assets/`: Images/Icons.
- `run.py`: Script to launch the application.
- `requirements.txt`: Python dependencies.

## Setup

1. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
2. Ensure `tesseract` and `ocrmypdf` dependencies (like ghostscript, tesseract-ocr) are installed on your system and in PATH.

## Running

Run the application:

```bash
python run.py
```

## Packaging

To create an executable (exe), you can use PyInstaller:

```bash
pyinstaller --name "BiplobOCR" --windowed --onefile run.py
```

(Note: You might need to adjust PyInstaller spec to include `src` and other data).
