"""
ViMouse for Windows - Control mouse with keyboard using Vim-style shortcuts
"""

import os
import sys
from datetime import datetime

import pyautogui
from loguru import logger

from vimouse import ViMouse


def main() -> None:
    # Настраиваем логирование в файл
    log_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "vimouse_debug.log")
    logger.remove()  # Удаляем стандартный обработчик
    logger.add(log_path, rotation="1 MB", level="DEBUG")

    vimouse = None
    try:
        logger.info(f"Starting ViMouse at {datetime.now()}")
        logger.info(f"Python executable: {sys.executable}")
        logger.info(f"Working directory: {os.getcwd()}")

        # off fail safe for pyautogui
        pyautogui.FAILSAFE = False
        logger.info("PyAutoGUI failsafe disabled")

        vimouse = ViMouse()
        logger.info("ViMouse instance created")

        try:
            logger.info("Starting main loop")
            vimouse.run()
        except Exception:
            logger.exception("Error in main loop")
            raise
    except Exception:
        logger.exception("Fatal error during startup")
        raise
    finally:
        logger.info("Cleaning up")
        if vimouse is not None:
            vimouse.cleanup()
        logger.info("Cleanup complete")


if __name__ == "__main__":
    main()
