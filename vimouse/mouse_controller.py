from dataclasses import dataclass

import pyautogui


@dataclass
class MousePosition:
    x: int
    y: int


class MouseController:
    def __init__(self) -> None:
        # Настройки скроллинга
        self.scroll_step = 100
        self._last_position: MousePosition | None = None

    def move_to(self, x: int, y: int) -> None:
        """Перемещает курсор в указанные координаты."""
        pyautogui.moveTo(x, y)
        self._last_position = MousePosition(x, y)

    def click(self, button: str = 'left') -> None:
        """Выполняет клик указанной кнопкой мыши."""
        pyautogui.click(button=button)

    def right_click(self) -> None:
        """Выполняет правый клик."""
        self.click(button='right')

    def start_selection(self) -> None:
        """Начинает выделение (зажимает левую кнопку)."""
        pyautogui.mouseDown()

    def end_selection(self) -> None:
        """Заканчивает выделение (отпускает левую кнопку)."""
        pyautogui.mouseUp()

    def scroll_up(self) -> None:
        """Прокручивает страницу вверх."""
        pyautogui.scroll(self.scroll_step)

    def scroll_down(self) -> None:
        """Прокручивает страницу вниз."""
        pyautogui.scroll(-self.scroll_step)

    @property
    def position(self) -> MousePosition:
        """Возвращает текущую позицию курсора."""
        x, y = pyautogui.position()
        return MousePosition(int(x), int(y))
