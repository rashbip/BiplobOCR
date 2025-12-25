# BiplobOCR

**BiplobOCR** is a powerful, user-friendly desktop application for Optical Character Recognition (OCR). It transforms scanned, image-based PDFs into searchable, selectable text documents using the robust `ocrmypdf` engine. Designed for Windows, it features a modern interface, batch processing, and hardware acceleration support.

![Version](https://img.shields.io/badge/version-2.2-blue) ![Python](https://img.shields.io/badge/python-3.x-green)

## ✨ Features

- **Searchable PDF Creation**: Convert scanned documents into standard PDFs with selectable text.
- **Intelligent Processing**:
  - **Auto-Deskew**: Straightens crooked pages.
  - **Clean**: Removes background noise and artifacts.
  - **Rotate**: Automatically corrects page orientation.
- **Batch Processing**: Queue multiple files to process them one after another automatically.
- **Large File Support**: Automatically splits and processes large PDF files (>50 pages) to manage memory efficiently.
- **Multi-Language Interface**: Fully localized in **English** and **Bengali**.
- **Hardware Acceleration**: Supports GPU acceleration (via OpenCL) to speed up OCR operations.
- **Drag & Drop**: Simply drag PDF files into the window to start processing.
- **Sidecar Output**: Optionally generates a `.txt` file with the raw text content alongside the PDF.
- **Secure**: Handles password-protected PDFs by prompting for credentials.

## 🚀 Installation

### Prerequisites

- Python 3.8 or higher
- Windows 10/11

### Setup from Source

1.  **Clone the Repository**:

    ```bash
    git clone https://github.com/yourusername/BiplobOCR.git
    cd BiplobOCR
    ```

2.  **Install Dependencies**:

    ```bash
    pip install -r requirements.txt
    ```

3.  **External Tools**:
    BiplobOCR relies on `Tesseract-OCR` and `Ghostscript`.
    - The application is designed to look for a bundled version in `src/tesseract/windows`.
    - Alternatively, ensure `tesseract` and `ocrmypdf` dependencies are installed on your system and added to your PATH.

## 💻 Usage

To start the application, run the setup script:

```bash
python run.py
```

### Main Interface

- **Home**: View recent files and quick actions.
- **Tools (Scan)**: Process a single file. You can preview the PDF and adjust specific settings.
- **Batch**: Add multiple files to a queue. The app will process them sequentially.
- **History**: A log of all processed files with quick links to open them.
- **Settings**: Configure OCR languages, performance options (CPU threads, GPU), and themes.

## 🛠 Project Structure

```plaintext
BiplobOCR/
├── src/
│   ├── core/           # Backend logic (OCR engine, Config, History)
│   ├── gui/            # User Interface (Tkinter Views & Controllers)
│   ├── tesseract/      # Bundled Tesseract binaries (Windows)
│   └── assets/         # Icons and static resources
├── installer/          # Installer build scripts
├── run.py              # Application entry point
├── requirements.txt    # Python dependencies
└── whole_project_summary.md # Detailed technical documentation
```

## 📦 Building Executable

To package the application for distribution (creates a single `.exe`):

1.  Install PyInstaller:

    ```bash
    pip install pyinstaller
    ```

2.  Run the build command:
    ```bash
    pyinstaller --name "BiplobOCR" --windowed --onefile --icon=src/assets/icon.ico run.py
    ```
    _(Note: You may need to update the PyInstaller spec file to include `src/tesseract` and `src/assets` directories as data resources.)_

## 📝 License

This project is licensed under the MIT License - see the `LICENSE` file for details.

## 🤝 Support

For detailed documentation, visit: [BiplobOCR Docs](https://rashidul.is-a.dev/BiplobOCRdocs/)
