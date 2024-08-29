import logging
import os
import pathlib
import time
import traceback
import datetime
from tkinter import *
from tkinter import filedialog, messagebox, ttk

import cv2
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from numpy.typing import ArrayLike
from helpers import mse

from camera_handling import (
    get_bgr_converter,
    get_camera,
    get_img_from_grab_result,
    grab_single_frame,
)
from helpers import load_config

logger = logging.getLogger(__name__)


class CrystalCapture:
    def __init__(self, root, config_path):
        self.root = root
        self.root.title("Crystal Capture")
        self.root.geometry("550x125")
        self.config = load_config(config_path)
        self.latest_img = None

        self.data_loc = StringVar()
        self.exposure_time = DoubleVar()
        self.capture_interval = DoubleVar()
        self.min_mse = DoubleVar()
        self.camera_name = StringVar()

        self.camera = get_camera()
        self.converter = get_bgr_converter()

        self.data_loc.set(self.config["storage"]["data_location"])
        self.exposure_time.set(self.config["camera"]["exposure_time"])
        self.capture_interval.set(self.config["camera"]["capture_interval"])
        self.min_mse.set(self.config["camera"]["min_mse"])
        self.camera_name.set(self.camera.GetDeviceInfo().GetFriendlyName())

        frame = ttk.Frame(self.root, padding="3 3 12 12")
        frame.grid(column=0, row=0, sticky=(N, W, E, S))
        frame.columnconfigure(0, weight=1)
        frame.rowconfigure(0, weight=1)

        ttk.Label(frame, text="Exposure Time (μs)", width=20).grid(
            column=1, row=1, sticky=W
        )
        exposure_time_entry = ttk.Entry(
            frame, textvariable=self.exposure_time, width=50
        )
        exposure_time_entry.grid(column=2, row=1, sticky=(W, E))

        ttk.Label(frame, text="Capture Interval (s)", width=20).grid(
            column=1, row=2, sticky=W
        )
        capture_interval_entry = ttk.Entry(
            frame, textvariable=self.capture_interval, width=50
        )
        capture_interval_entry.grid(column=2, row=2, sticky=(W, E))

        ttk.Label(frame, text="Minimum MSE", width=20).grid(column=1, row=3, sticky=W)
        min_mse_entry = ttk.Entry(frame, textvariable=self.min_mse, width=50)
        min_mse_entry.grid(column=2, row=3, sticky=(W, E))

        ttk.Label(frame, text="Dataset Directory").grid(column=1, row=4, sticky=W)
        data_loc_entry = ttk.Entry(frame, textvariable=self.data_loc)
        data_loc_entry.grid(column=2, row=4, sticky=(W, E))

        data_loc_button = ttk.Button(frame, text="...", command=self._select_folder)
        data_loc_button.grid(column=3, row=4, sticky=W)

        ttk.Label(frame, text="Connected Camera").grid(column=1, row=5, sticky=W)
        camera_label = ttk.Label(frame, textvariable=self.camera_name)
        camera_label.grid(column=2, row=5, sticky=(W, E))

        ttk.Button(frame, text="Start", command=self._run_capture_loop).grid(
            column=2, row=5, sticky=E
        )

    def _run_capture_loop(self):
        grab_result = grab_single_frame(self.camera)
        img = get_img_from_grab_result(grab_result, self.converter)

        if not os.path.exists(self.data_loc.get()):
            os.makedirs(self.data_loc.get())

        if self.latest_img is None:
            self.latest_img = img
            cv2.imwrite(
                os.path.join(
                    self.data_loc.get(),
                    f'{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png',
                ),
                img,
            )
            fig = Figure()
            ax = fig.add_subplot(111)
            ax.imshow(img)
            canvas = FigureCanvasTkAgg(fig, master=self.root)
            canvas.draw()
            canvas.get_tk_widget().grid(column=0, row=1)
            toolbar = NavigationToolbar2Tk(canvas, self.root)
            toolbar.update()
            canvas.get_tk_widget().grid(column=0, row=1)
            return

        m = mse(self.latest_img, img)

        if m < self.min_mse.get():
            logger.info(
                f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}Skipping capture. MSE: {m}'
            )
            return

        logger.info(
            f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}Capturing image. MSE: {m}'
        )
        cv2.imwrite(
            os.path.join(
                self.data_loc.get(),
                f'{datetime.datetime.now().strftime("%Y-%m-%d_%H-%M-%S")}.png',
            ),
            img,
        )

        fig = Figure()
        ax = fig.add_subplot(111)
        ax.imshow(img)
        canvas = FigureCanvasTkAgg(fig, master=self.root)
        canvas.draw()
        canvas.get_tk_widget().grid(column=0, row=1)
        toolbar = NavigationToolbar2Tk(canvas, self.root)
        toolbar.update()
        canvas.get_tk_widget().grid(column=0, row=1)

        time.sleep(self.capture_interval.get())

    def _select_folder(self):
        """Opens a file dialog to select the folder to save the capture to.
        Sets the data_loc variable to the selected folder. Is called when the '...' button is clicked.
        """
        folder = filedialog.askdirectory()
        self.data_loc.set(folder)


if __name__ == "__main__":
    logging.basicConfig(level=logging.DEBUG)
    root = Tk()
    cc_app = CrystalCapture(root, config_path="config.toml")
    root.mainloop()
