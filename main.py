from crystal_capture import CrystalCapture
from tkinter import Tk

if __name__ == "__main__":
    root = Tk()
    cc_app = CrystalCapture(root, config_path="config.toml")
    root.mainloop()
