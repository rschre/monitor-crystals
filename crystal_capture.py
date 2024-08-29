import datetime
import logging
import os
from tkinter import *
from tkinter import filedialog, messagebox, ttk

import cv2
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure
from numpy.typing import ArrayLike

from camera_handling import (
    get_bgr_converter,
    get_camera,
    get_img_from_grab_result,
    grab_single_frame,
)
from helpers import load_config, mse

logger = logging.getLogger(__name__)


class CrystalCapture:
    def __init__(self, root, config_path):
        self.root = root
        self.root.title("Crystal Capture")
        self.root.geometry("550x125")
        self.config = load_config(config_path)
        self.latest_img = None

        self.data_loc = StringVar()
        self.exposure_time = IntVar()
        self.capture_interval = IntVar()
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

        self.img_view = Toplevel(self.root)
        self.img_view.title("Latest Image")
        self.img_view.withdraw()
        self.img_view.figure = Figure()
        self.img_view.ax = self.img_view.figure.add_subplot(111)
        self.img_view.canvas = FigureCanvasTkAgg(
            self.img_view.figure, master=self.img_view
        )
        self.img_view.canvas.draw()
        self.img_view.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)
        self.img_view.toolbar = NavigationToolbar2Tk(
            self.img_view.canvas, self.img_view
        )
        self.img_view.toolbar.update()
        self.img_view.canvas.get_tk_widget().pack(side=TOP, fill=BOTH, expand=1)

        self.countdown = Toplevel(self.root)
        self.countdown.title("Capture Countdown")
        self.countdown.geometry("400x50")
        self.countdown.protocol("WM_DELETE_WINDOW", self._on_closing)
        self.countdown.label = Label(self.countdown, text="", font=("Helvetica", 24))
        self.countdown.label.pack()
        self.countdown.withdraw()

    def _display_img(self, img: ArrayLike):

        self.img_view.ax.clear()
        self.img_view.ax.title.set_text(
            f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )
        self.img_view.ax.imshow(img)
        self.img_view.canvas.draw()
        self.img_view.update()
        self.img_view.deiconify()

        # stop the capture loop if the window is closed
        self.img_view.protocol("WM_DELETE_WINDOW", self._on_closing)

    def _run_capture_loop(self):

        # hide main window
        self.root.withdraw()

        self.root.after(self.capture_interval.get() * 1000, self._run_capture_loop)
        self._display_countdown(self.capture_interval.get() - 1)

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
            self._display_img(img)
            return

        m = mse(self.latest_img, img)

        if m < self.min_mse.get():
            logger.info(
                f'{datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")}Skipping capture. MSE: {m}'
            )
            return

        self._display_img(img)

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

        self.latest_img = img

    def _select_folder(self):
        """Opens a file dialog to select the folder to save the capture to.
        Sets the data_loc variable to the selected folder. Is called when the '...' button is clicked.
        """
        folder = filedialog.askdirectory()
        self.data_loc.set(folder)

    def _on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.camera.Close()
            self.root.destroy()

    def _display_countdown(self, count):
        self.countdown.deiconify()
        if count == 0:
            self.countdown.withdraw()
            return
        text = f"Next capture in {count} seconds"
        self.countdown.label["text"] = text

        if count > 0:
            self.countdown.after(950, self._display_countdown, count - 1)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    root = Tk()
    cc_app = CrystalCapture(root, config_path="config.toml")
    root.mainloop()
