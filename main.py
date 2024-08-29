from crystal_capture import CrystalCapture
from tkinter import Tk
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

if __name__ == "__main__":
    root = Tk()
    cc_app = CrystalCapture(root, config_path="config.toml")
    root.mainloop()
