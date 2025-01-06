import os
import sys

from PyQt6.QtGui import QIcon
from PyQt6.QtWidgets import QApplication, QMenu, QSystemTrayIcon
from PyQt6.QtCore import QObject

from vimouse.keyboard_handler import KeyboardHandler
from vimouse.mouse_controller import MouseController
from vimouse.overlay import OverlayWindow


class ViMouse(QObject):
    def __init__(self) -> None:
        super().__init__()
        self.app = QApplication(sys.argv)

        # Устанавливаем иконку приложения
        icon_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'icon_256x256.ico')
        self.app_icon = QIcon(icon_path)
        self.app.setWindowIcon(self.app_icon)

        self.overlay = OverlayWindow()
        self.mouse = MouseController()
        self.keyboard_handler = KeyboardHandler(self.overlay, self.mouse)

        # Создаем иконку в трее
        self.tray = QSystemTrayIcon(self.app)
        self.tray.setIcon(self.app_icon)
        self.tray.setToolTip('ViMouse')

        # Создаем контекстное меню
        self.tray_menu = QMenu()
        exit_action = self.tray_menu.addAction('Выход')
        exit_action.triggered.connect(self.cleanup)

        # Устанавливаем меню и показываем иконку
        self.tray.setContextMenu(self.tray_menu)
        self.tray.show()

    def toggle_overlay(self) -> None:
        """Переключает видимость оверлея."""
        if self.overlay.is_visible:
            self.overlay.hide()
        else:
            self.overlay.show()

    def run(self) -> None:
        """Запускает основной цикл приложения."""
        print("ViMouse запущен!")
        print("\nДоступные команды:")
        print("  Alt + \\ - показать/скрыть оверлей для перемещения курсора")
        print("  Alt + K - прокрутка вверх")
        print("  Alt + J - прокрутка вниз")
        print("  Alt + Q - выход из программы")

        self.app.exec()

    def cleanup(self) -> None:
        """Освобождает ресурсы перед выходом."""
        self.keyboard_handler.quit_app()
        self.tray.hide()
        self.app.quit()
