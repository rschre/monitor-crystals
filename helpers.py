import glob
import logging
import os

import numpy as np
import toml

logger = logging.getLogger(__name__)


def mse(imageA, imageB):
    err = np.sum((imageA.astype("float") - imageB.astype("float")) ** 2)
    err /= float(imageA.shape[0] * imageA.shape[1])

    return err


def load_config(path: str):
    """Loads a TOML config file and returns a dict of the values.
    If the capture directory is not defined, prompts the user to select one.

    Args:
        path (str): Path to the TOML config file.

    Returns:
        dict: Dictionary of the config values."""

    try:
        config = toml.load(path)

    except toml.TomlDecodeError:
        logger.error(
            f"Config file is not a valid TOML file. Verify that {path} is valid."
        )
        exit(1)
    except FileNotFoundError:
        logger.error(f"Config file not found. Verify that {path} exists.")
        exit(1)

    if (
        config.get("storage").get("data_location") is None
        or config.get("storage").get("data_location") == ""
    ):
        logger.debug("No capture path defined in config file. Defaulting to Desktop")
        # get current users desktop path
        data_loc = os.path.join(os.path.expanduser("~"), "Desktop")
        if not os.path.exists(data_loc):
            data_loc = glob.glob(os.path.join(os.path.expanduser("~"), "*", "Desktop"))[
                0
            ]

        if data_loc == "":
            print("No folder selected. Exiting.")
            exit(0)
        else:
            config["storage"]["data_location"] = data_loc

    return config
