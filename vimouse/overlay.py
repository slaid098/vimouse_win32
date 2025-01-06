from typing import cast

from loguru import logger
from PyQt6.QtCore import Qt
from PyQt6.QtGui import (
    QColor,
    QFont,
    QGuiApplication,
    QPainter,
    QPaintEvent,
    QScreen,
)
from PyQt6.QtWidgets import QWidget

from .screen_analyzer import ScreenAnalyzer


class OverlayWindow(QWidget):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint |
            Qt.WindowType.WindowStaysOnTopHint |
            Qt.WindowType.Tool |
            Qt.WindowType.WindowTransparentForInput
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)
        self.setAttribute(Qt.WidgetAttribute.WA_TransparentForMouseEvents)
        self._is_visible = False

        # Настройки отображения
        self.cell_size = 100
        self._font = QFont('Arial', 14)
        self.targets: dict[str, tuple[int, int]] = {}
        self.screen_analyzer = ScreenAnalyzer()

        # Инициализация UI
        self._init_ui()

    @property
    def is_visible(self) -> bool:
        """Возвращает состояние видимости оверлея."""
        return self._is_visible

    def _init_ui(self) -> None:
        """Инициализирует UI оверлея."""
        app = cast(QGuiApplication, QGuiApplication.instance())
        screen = cast(QScreen, app.primaryScreen())
        self.setGeometry(screen.geometry())

    def show(self) -> None:
        """Показывает оверлей и генерирует подсказки."""
        self._generate_targets()
        self._is_visible = True
        super().show()

    def hide(self) -> None:
        """Скрывает оверлей."""
        self._is_visible = False
        super().hide()

    def close(self) -> bool:
        """Закрывает оверлей."""
        self._is_visible = False
        if super().close():
            logger.debug("overlay closed")
            return True
        logger.warning("overlay not closed")
        return False

    def _generate_targets(self) -> None:
        """
        Генерирует точки для перемещения курсора и их буквенные обозначения.
        Использует анализ экрана для поиска кликабельных элементов.
        """
        self.targets.clear()

        # Получаем кликабельные регионы
        clickable_regions = self.screen_analyzer.get_clickable_regions()
        logger.debug(f"Found {len(clickable_regions)} clickable regions")

        # Определяем ряды клавиатуры (QWERTY)
        keyboard_rows = [
            ['q', 'w', 'e', 'r', 't', 'y', 'u', 'i', 'o', 'p'],
            ['a', 's', 'd', 'f', 'g', 'h', 'j', 'k', 'l'],
            ['z', 'x', 'c', 'v', 'b', 'n', 'm'],
        ]

        # Создаем словарь соседних букв для каждой буквы
        neighbors: dict[str, list[str]] = {}
        for row_idx, row in enumerate(keyboard_rows):
            for col_idx, char in enumerate(row):
                neighbors[char] = []
                # Проверяем соседей в текущем ряду
                if col_idx > 0:
                    neighbors[char].append(row[col_idx - 1])  # слева
                if col_idx < len(row) - 1:
                    neighbors[char].append(row[col_idx + 1])  # справа

                # Проверяем соседей в ряду выше
                if row_idx > 0:
                    above_row = keyboard_rows[row_idx - 1]
                    # Находим ближайшие буквы сверху (включая диагональные)
                    for above_idx, above_char in enumerate(above_row):
                        if abs(above_idx - col_idx) <= 2:  # Увеличиваем радиус поиска
                            neighbors[char].append(above_char)

                # Проверяем соседей в ряду ниже
                if row_idx < len(keyboard_rows) - 1:
                    below_row = keyboard_rows[row_idx + 1]
                    # Находим ближайшие буквы снизу (включая диагональные)
                    for below_idx, below_char in enumerate(below_row):
                        if abs(below_idx - col_idx) <= 2:  # Увеличиваем радиус поиска
                            neighbors[char].append(below_char)

        # Генерируем только двухбуквенные комбинации
        labels: list[str] = []

        # Используем все буквы как стартовые
        main_chars = []
        for row in keyboard_rows:
            main_chars.extend(row)

        # Генерируем комбинации в обоих направлениях
        for c1 in main_chars:
            for c2 in neighbors[c1]:
                # Прямая комбинация
                combo1 = f"{c1}{c2}"
                if combo1 not in labels:
                    labels.append(combo1)
                # Обратная комбинация
                combo2 = f"{c2}{c1}"
                if combo2 not in labels:
                    labels.append(combo2)

        # Если нужно больше комбинаций, добавляем диагональные через одну клавишу
        if len(clickable_regions) > len(labels):
            for c1 in main_chars:
                for c2 in neighbors[c1]:
                    for c3 in neighbors[c2]:
                        if c3 != c1:
                            combo = f"{c1}{c3}"
                            if combo not in labels:
                                labels.append(combo)

        logger.debug(f"Generated {len(labels)} two-char combinations")

        # Назначаем метки кликабельным регионам
        for i, (x, y) in enumerate(clickable_regions):
            if i >= len(labels):
                break
            self.targets[labels[i]] = (x, y)

        logger.debug(f"Used targets: {list(self.targets.keys())}")

    def paintEvent(self, a0: QPaintEvent | None) -> None:  # noqa: N802, ARG002
        """Отрисовывает оверлей."""
        painter = QPainter(self)
        painter.setFont(self._font)

        # Полупрозрачный фон
        painter.fillRect(self.rect(), QColor(0, 0, 0, 128))

        # Отрисовка подсказок
        for label, (x, y) in self.targets.items():
            # Увеличиваем размер фона для двойных букв
            width = 30 if len(label) == 1 else 45

            # Фон для метки
            bg_rect = painter.boundingRect(
                x - width//2, y - 15, width, 30,
                Qt.AlignmentFlag.AlignCenter,
                label,
            )
            painter.fillRect(bg_rect, QColor(255, 255, 200, 230))

            # Метка
            painter.setPen(QColor(0, 0, 0))
            painter.drawText(
                x - width//2, y - 15, width, 30,
                Qt.AlignmentFlag.AlignCenter,
                label,
            )

    def get_target(self, char: str) -> tuple[int, int] | None:
        """Возвращает координаты для указанной буквы."""
        return self.targets.get(char.lower())
