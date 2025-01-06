import os
import threading
from typing import cast

import win32api
import win32con
from loguru import logger

from .mouse_controller import MouseController
from .overlay import OverlayWindow


class KeyboardHandler:
    def __init__(self, overlay: OverlayWindow, mouse: MouseController) -> None:
        self.overlay = overlay
        self.mouse = mouse
        self.running = False
        self.listener_thread: threading.Thread | None = None
        self.mask = 0x8000
        self.current_sequence = ""
        self.sequence_timeout = 1.0  # секунда на ввод второй буквы
        self.last_key_time = 0.0
        self.last_pressed_key = 0  # Последняя нажатая клавиша
        self.waiting_for_release = False  # Ожидаем отпускания клавиши

        # Коды клавиш
        self.VK_BACKSLASH = 0xDC  # Код клавиши "\"
        self.VK_J = ord("J")
        self.VK_K = ord("K")
        self.VK_Q = ord("Q")

        # Инициализация обработчиков клавиатуры
        self.start()

    def _check_hotkey(self, vk_code: int) -> bool:
        """Проверяет нажатие горячей клавиши (Alt + клавиша)."""
        return bool(
            cast(int, win32api.GetAsyncKeyState(win32con.VK_MENU)) & self.mask
            and cast(int, win32api.GetAsyncKeyState(vk_code)) & self.mask,
        )

    def _check_overlay_key(self, vk_code: int) -> bool:
        """Проверяет, является ли нажатая клавиша буквой для оверлея."""
        if not self.overlay.is_visible:
            return False

        # Проверяем, что нажата буква
        try:
            char = chr(vk_code).lower()
            return char.isalpha()
        except ValueError:
            return False

    def _keyboard_listener(self) -> None:
        """Поток прослушивания клавиатуры."""
        import time

        prev_states = {
            self.VK_BACKSLASH: False,
            self.VK_J: False,
            self.VK_K: False,
            self.VK_Q: False,
        }

        while self.running:
            current_time = time.time()

            # Проверяем горячие клавиши
            current_states = {
                self.VK_BACKSLASH: self._check_hotkey(self.VK_BACKSLASH),
                self.VK_J: self._check_hotkey(self.VK_J),
                self.VK_K: self._check_hotkey(self.VK_K),
                self.VK_Q: self._check_hotkey(self.VK_Q),
            }

            # Обрабатываем нажатия горячих клавиш
            if current_states[self.VK_BACKSLASH] and not prev_states[self.VK_BACKSLASH]:
                self.waiting_for_release = False
                self._toggle_overlay()
            if current_states[self.VK_J] and not prev_states[self.VK_J]:
                self.waiting_for_release = False
                self.mouse.scroll_down()
            if current_states[self.VK_K] and not prev_states[self.VK_K]:
                self.waiting_for_release = False
                self.mouse.scroll_up()
            if current_states[self.VK_Q] and not prev_states[self.VK_Q]:
                self.waiting_for_release = False
                self.quit_app()

            # Проверяем клавиши для оверлея
            if self.overlay.is_visible:
                # Сбрасываем последовательность, если прошло слишком много времени
                if current_time - self.last_key_time > self.sequence_timeout and self.current_sequence:
                    logger.debug(f"Timeout, resetting sequence: {self.current_sequence}")
                    self.current_sequence = ""
                    self.waiting_for_release = False

                # Проверяем, отпущена ли предыдущая клавиша
                if self.waiting_for_release:
                    if not cast(int, win32api.GetAsyncKeyState(self.last_pressed_key)) & self.mask:
                        self.waiting_for_release = False
                        logger.debug("Key released")
                    continue

                # Проверяем нажатия клавиш
                for vk_code in range(65, 91):  # A-Z
                    if cast(int, win32api.GetAsyncKeyState(vk_code)) & self.mask:
                        if not self._check_overlay_key(vk_code):
                            continue

                        char = chr(vk_code).lower()
                        logger.debug(f"Key pressed: {char}")

                        # Если это первая буква
                        if not self.current_sequence:
                            self.current_sequence = char
                            self.last_key_time = current_time
                            self.last_pressed_key = vk_code
                            self.waiting_for_release = True
                            logger.debug(f"First char: {char}")

                        # Если это вторая буква и она отличается от первой
                        elif vk_code != self.last_pressed_key:
                            self.current_sequence += char
                            logger.debug(f"Second char, sequence: {self.current_sequence}")

                            # Проверяем комбинацию
                            target = self.overlay.get_target(self.current_sequence)
                            if target:
                                logger.debug(f"Using combination: {self.current_sequence}")
                                x, y = target
                                self.mouse.move_to(x, y)
                                self._hide_overlay_if_visible()
                                self.mouse.click()
                            else:
                                logger.debug(f"Invalid combination: {self.current_sequence}")

                            # В любом случае сбрасываем последовательность
                            self.current_sequence = ""
                            self.waiting_for_release = True
                            self.last_pressed_key = vk_code

            prev_states = current_states
            win32api.Sleep(10)  # задержка для снижения нагрузки на CPU

    def start(self) -> None:
        """Запускает обработчики клавиатуры."""
        if not self.running:
            self.running = True
            self.listener_thread = threading.Thread(
                target=self._keyboard_listener,
            )
            self.listener_thread.daemon = True
            self.listener_thread.start()
            logger.debug("Keyboard handler started")

    def _toggle_overlay(self) -> None:
        """Переключает видимость оверлея."""
        if not self.overlay.is_visible:
            self.overlay.show()
            logger.debug("overlay shown")
        else:
            self.overlay.hide()
            # Сбрасываем состояние ожидания клавиши при скрытии оверлея
            self.waiting_for_release = False
            self.current_sequence = ""
            logger.debug("overlay hidden")

    def _hide_overlay_if_visible(self) -> None:
        """Скрывает оверлей, если он видим."""
        if self.overlay.is_visible:
            self.overlay.hide()
            # Сбрасываем состояние ожидания клавиши при скрытии оверлея
            self.waiting_for_release = False
            self.current_sequence = ""
            logger.debug("overlay hidden")

    def quit_app(self) -> None:
        """Завершает приложение."""
        logger.info("quiting app")
        self._hide_overlay_if_visible()
        os._exit(0)
