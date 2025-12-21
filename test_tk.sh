#!/bin/bash
source /mnt/d/Python/BiplobOCR/src/python/linux/venv/bin/activate
cd /mnt/d/Python/BiplobOCR
export DISPLAY=${DISPLAY:-:0}
python3 -c "import tkinter; print('Tkinter found'); root = tkinter.Tk(); print('Root created'); root.destroy(); print('Root destroyed')"
