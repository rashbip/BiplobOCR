# Tesseract Cleanup Report

## Summary

- **Original Size**: ~85 MB
- **Final Size**: ~62 MB
- **Actual Savings**: ~23 MB (~27% reduction)

### Why Not More?

The largest file remaining is `libicudt75.dll` (30.7 MB) - the **ICU Unicode Data library**.
This is **REQUIRED** by Tesseract for Unicode text processing and cannot be safely removed.

## Files SAFE to Remove (Training Tools)

These executables are only used for **training** Tesseract models, not for running OCR:

### Training Executables (Total: ~2.6 MB)

- `ambiguous_words.exe`
- `classifier_tester.exe`
- `cntraining.exe`
- `combine_lang_model.exe`
- `dawg2wordlist.exe`
- `lstmeval.exe`
- `lstmtraining.exe`
- `merge_unicharsets.exe`
- `mftraining.exe`
- `set_unicharset_properties.exe`
- `shapeclustering.exe`
- `text2image.exe`
- `unicharset_extractor.exe`
- `winpath.exe`
- `wordlist2dawg.exe`

## DLLs SAFE to Remove

### Training-Only Libraries

These are dependencies for training tools, not for tesseract.exe:

| DLL                       | Size   | Reason Safe to Remove         |
| ------------------------- | ------ | ----------------------------- |
| `libcairo-2.dll`          | 1.2 MB | text2image only               |
| `libpango-1.0-0.dll`      | 411 KB | text2image only               |
| `libpangocairo-1.0-0.dll` | 74 KB  | text2image only               |
| `libpangoft2-1.0-0.dll`   | 103 KB | text2image only               |
| `libpangowin32-1.0-0.dll` | 115 KB | text2image only               |
| `libdatrie-1.dll`         | 34 KB  | Pango dependency              |
| `libthai-0.dll`           | 70 KB  | Pango dependency              |
| `libfribidi-0.dll`        | 156 KB | Pango dependency              |
| `libpixman-1-0.dll`       | 709 KB | Cairo dependency              |
| `libglib-2.0-0.dll`       | 1.5 MB | Pango/Cairo dependency        |
| `libgobject-2.0-0.dll`    | 357 KB | GLib dependency               |
| `libgmodule-2.0-0.dll`    | 27 KB  | GLib dependency               |
| `libgio-2.0-0.dll`        | 1.8 MB | GLib dependency               |
| `libfontconfig-1.dll`     | 350 KB | text2image font discovery     |
| `libgraphite2.dll`        | 153 KB | Advanced font shaping         |
| `libharfbuzz-0.dll`       | 1.4 MB | Font shaping for text2image   |
| `libexpat-1.dll`          | 192 KB | XML parser for fontconfig     |
| `libfreetype-6.dll`       | 788 KB | Font rendering for text2image |
| `libffi-8.dll`            | 34 KB  | Foreign function interface    |
| `libpcre2-8-0.dll`        | 406 KB | Regex for GLib                |

### Network Libraries (NOT used for OCR)

| DLL                   | Size   | Reason Safe to Remove                     |
| --------------------- | ------ | ----------------------------------------- |
| `libcurl-4.dll`       | 1 MB   | Network requests - not used               |
| `libssh2-1.dll`       | 256 KB | SSH library - not used                    |
| `libcrypto-3-x64.dll` | 5.3 MB | OpenSSL crypto - not used                 |
| `libpsl-5.dll`        | 104 KB | Public suffix list for libcurl            |
| `libidn2-0.dll`       | 243 KB | Internationalized domain names - for curl |
| `libunistring-5.dll`  | 2 MB   | Unicode for libidn2                       |
| `libbrotlicommon.dll` | 143 KB | Compression for curl                      |
| `libbrotlidec.dll`    | 61 KB  | Decompression for curl                    |

### Archive Libraries (NOT needed for image OCR)

| DLL                 | Size   | Reason Safe to Remove            |
| ------------------- | ------ | -------------------------------- |
| `libarchive-13.dll` | 790 KB | Archive handling - not used      |
| `libb2-1.dll`       | 34 KB  | BLAKE2 hash - archive dependency |
| `liblz4.dll`        | 159 KB | LZ4 compression for archive      |
| `libzstd.dll`       | 1.2 MB | Zstandard compression            |

### Potential Large ICU Reduction (~36 MB)

| DLL              | Size        | Status                               |
| ---------------- | ----------- | ------------------------------------ |
| `libicudt75.dll` | **30.7 MB** | ⚠️ CAUTION - needed for some scripts |
| `libicuin75.dll` | 3.4 MB      | ICU i18n - may be needed for Bengali |
| `libicuuc75.dll` | 1.9 MB      | ICU core - may be needed             |

**Note on ICU**: The ICU libraries provide Unicode support for complex scripts like Bengali. Since you use Bengali (ben+eng), do NOT remove ICU libraries!

## Files MUST KEEP (Essential for Runtime)

### Core Tesseract Files

- `tesseract.exe` - The main OCR engine
- `libtesseract-5.dll` - Core Tesseract library

### Image Processing (Leptonica & Dependencies)

- `libleptonica-6.dll` - Image processing library
- `libjpeg-8.dll` - JPEG support
- `libpng16-16.dll` - PNG support
- `libtiff-6.dll` - TIFF support
- `libwebp-7.dll` - WebP support
- `libgif-7.dll` - GIF support
- `libopenjp2-7.dll` - JPEG 2000 support
- `zlib1.dll` - Compression
- `libLerc.dll` - LERC compression for TIFF
- `libjbig-0.dll` - JBIG compression
- `libsharpyuv-0.dll` - WebP dependency
- `libwebpmux-3.dll` - WebP mux
- `libdeflate.dll` - Fast compression
- `liblzma-5.dll` - LZMA compression
- `libbz2-1.dll` - BZ2 compression

### C++ Runtime

- `libstdc++-6.dll` - C++ standard library
- `libgcc_s_seh-1.dll` - GCC runtime
- `libwinpthread-1.dll` - Thread support

### Internationalization (Keep for Bengali!)

- `libiconv-2.dll` - Character encoding
- `libintl-8.dll` - Internationalization
- `libicudt75.dll` - ICU data (KEEP for Bengali)
- `libicuin75.dll` - ICU i18n (KEEP for Bengali)
- `libicuuc75.dll` - ICU common (KEEP for Bengali)

### Tessdata (Keep)

- `tessdata/eng.traineddata` - English
- `tessdata/osd.traineddata` - Orientation detection
- `tessdata/pdf.ttf` - PDF font
- `tessdata/configs/*` - Config files
- `tessdata/tessconfigs/*` - Additional configs

## Recommended Cleanup Script

Safe to run this PowerShell command to remove training tools and unnecessary DLLs:

```powershell
# Training executables
$training_exes = @(
    "ambiguous_words.exe", "classifier_tester.exe", "cntraining.exe",
    "combine_lang_model.exe", "dawg2wordlist.exe", "lstmeval.exe",
    "lstmtraining.exe", "merge_unicharsets.exe", "mftraining.exe",
    "set_unicharset_properties.exe", "shapeclustering.exe", "text2image.exe",
    "unicharset_extractor.exe", "winpath.exe", "wordlist2dawg.exe"
)

# Training/Network DLLs not needed for runtime
$unused_dlls = @(
    "libcairo-2.dll", "libpango-1.0-0.dll", "libpangocairo-1.0-0.dll",
    "libpangoft2-1.0-0.dll", "libpangowin32-1.0-0.dll", "libdatrie-1.dll",
    "libthai-0.dll", "libfribidi-0.dll", "libpixman-1-0.dll",
    "libglib-2.0-0.dll", "libgobject-2.0-0.dll", "libgmodule-2.0-0.dll",
    "libgio-2.0-0.dll", "libfontconfig-1.dll", "libgraphite2.dll",
    "libharfbuzz-0.dll", "libexpat-1.dll", "libfreetype-6.dll",
    "libffi-8.dll", "libpcre2-8-0.dll", "libcurl-4.dll", "libssh2-1.dll",
    "libcrypto-3-x64.dll", "libpsl-5.dll", "libidn2-0.dll",
    "libunistring-5.dll", "libbrotlicommon.dll", "libbrotlidec.dll",
    "libarchive-13.dll", "libb2-1.dll", "liblz4.dll", "libzstd.dll"
)
```
