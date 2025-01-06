import cv2
import numpy as np
import win32con
import win32gui
import win32ui
from loguru import logger


class ScreenAnalyzer:
    def __init__(self) -> None:
        """Инициализирует анализатор экрана."""
        self.min_regions_count = 20
        self.max_regions_count = 250
        self.min_region_area = 16
        self.max_region_area = 35000
        self.min_region_contrast = 10
        self.max_region_contrast = 450

        # Параметры фильтрации
        self.min_aspect_ratio = 0.04
        self.max_aspect_ratio = 24.0
        self.min_edge_density = 0.02
        self.min_brightness = 12
        self.max_brightness = 500
        self.min_distance = 9

    def get_clickable_regions(self) -> list[tuple[int, int]]:
        """
        Анализирует скриншот и возвращает список координат кликабельных
        элементов.

        Использует различные методы компьютерного зрения для поиска:
        - Контрастных областей
        - Границ элементов
        - Текстовых блоков
        """
        # Объявляем переменные для ресурсов, чтобы освободить их в finally
        hwnd_dc = None
        mfc_dc = None
        save_dc = None
        save_bit_map = None
        hwnd: int = 0

        try:
            # Получаем размеры экрана через GetWindowRect
            hwnd: int = win32gui.GetDesktopWindow()  # type: ignore[arg-type]
            left, top, right, bottom = win32gui.GetWindowRect(hwnd)  # type: ignore[arg-type]
            width = right - left
            height = bottom - top

            # Создаем контекст для захвата
            hwnd_dc = win32gui.GetWindowDC(hwnd)  # type: ignore[arg-type]
            mfc_dc = win32ui.CreateDCFromHandle(hwnd_dc)
            save_dc = mfc_dc.CreateCompatibleDC()

            # Создаем битмап
            save_bit_map = win32ui.CreateBitmap()
            save_bit_map.CreateCompatibleBitmap(mfc_dc, width, height)
            save_dc.SelectObject(save_bit_map)

            # Копируем экран в битмап
            save_dc.BitBlt(
                (0, 0),
                (width, height),
                mfc_dc,
                (0, 0),
                win32con.SRCCOPY,
            )

            # Конвертируем в массив numpy
            size = width * height * 4  # 4 байта на пиксель (BGRA)
            bmpstr = save_bit_map.GetBitmapBits(size)  # type: ignore[arg-type]
            img = np.frombuffer(bmpstr, dtype=np.uint8)  # type: ignore[arg-type]
            img.shape = (height, width, 4)

            # Конвертируем в оттенки серого
            gray = cv2.cvtColor(img, cv2.COLOR_BGRA2GRAY)

            # 1. Метод градиентов с меньшими порогами
            sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
            sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
            gradient_magnitude = np.sqrt(sobelx**2 + sobely**2)
            gradient_magnitude = cv2.normalize(
                gradient_magnitude,
                None,
                0,
                255,
                cv2.NORM_MINMAX,
            )
            gradient_magnitude = np.uint8(gradient_magnitude)

            # 2. Метод адаптивной бинаризации с меньшим размером окна
            binary_adaptive = cv2.adaptiveThreshold(
                gray,
                255,
                cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
                cv2.THRESH_BINARY_INV,
                9,
                3,
            )

            # 3. Метод Кэнни с меньшими порогами
            edges = cv2.Canny(gray, 15, 80)

            # Комбинируем результаты
            combined = cv2.bitwise_or(gradient_magnitude, edges)
            combined = cv2.bitwise_or(combined, binary_adaptive)

            # Морфологические операции для улучшения результата
            kernel = np.ones((2, 2), np.uint8)
            combined = cv2.morphologyEx(combined, cv2.MORPH_CLOSE, kernel)
            combined = cv2.morphologyEx(combined, cv2.MORPH_OPEN, kernel)

            # Находим компоненты связности
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(combined)

            # Фильтруем компоненты по размеру и форме
            clickable_regions: list[tuple[int, int]] = []

            for i in range(1, num_labels):  # Пропускаем фон (метка 0)
                area = stats[i, cv2.CC_STAT_AREA]
                width = stats[i, cv2.CC_STAT_WIDTH]
                height = stats[i, cv2.CC_STAT_HEIGHT]

                if self.min_region_area < area < self.max_region_area:
                    aspect_ratio = float(width) / height if height > 0 else 0
                    if self.min_aspect_ratio < aspect_ratio < self.max_aspect_ratio:
                        x = stats[i, cv2.CC_STAT_LEFT]
                        y = stats[i, cv2.CC_STAT_TOP]
                        roi = gray[y : y + height, x : x + width]

                        if roi.size > 0:
                            # Проверяем несколько характеристик области
                            std = float(np.std(np.asarray(roi, dtype=np.float64)))  # Контрастность
                            mean = float(np.mean(roi))  # Средняя яркость
                            edges_roi = edges[y : y + height, x : x + width]
                            edge_density = float(np.sum(edges_roi)) / area  # Плотность краев

                            # Ослабляем критерии проверки
                            if (
                                std > 10  # Ещё меньше порог контрастности
                                and (mean < 245 or mean > 15)  # Расширяем диапазон яркости
                                and edge_density > 0.02  # Меньше плотность краев
                            ):
                                center_x = int(centroids[i][0])
                                center_y = int(centroids[i][1])
                                clickable_regions.append((center_x, center_y))

            # Удаляем слишком близкие точки
            filtered_regions: list[tuple[int, int]] = []
            min_distance = 18  # Уменьшаем минимальное расстояние между точками

            for x1, y1 in clickable_regions:
                too_close = False
                for x2, y2 in filtered_regions:
                    distance = np.sqrt((x2 - x1) ** 2 + (y2 - y1) ** 2)
                    if distance < min_distance:
                        too_close = True
                        break
                if not too_close:
                    filtered_regions.append((x1, y1))

            clickable_regions = filtered_regions

            # Если нашли слишком много регионов, фильтруем по контрастности
            if len(clickable_regions) > self.max_regions_count:

                def get_region_contrast(region: tuple[int, int]) -> float:
                    x, y = region
                    region_size = 15  # Увеличиваем размер области
                    x1, y1 = max(0, x - region_size), max(0, y - region_size)
                    x2, y2 = (
                        min(gray.shape[1], x + region_size),
                        min(gray.shape[0], y + region_size),
                    )
                    region_pixels = gray[y1:y2, x1:x2]
                    if region_pixels.size == 0:
                        return 0.0
                    return float(np.std(np.asarray(region_pixels, dtype=np.float64)))

                clickable_regions.sort(key=get_region_contrast, reverse=True)
                clickable_regions = clickable_regions[: self.max_regions_count]

            # Если нашли слишком мало регионов, добавляем сетку
            if len(clickable_regions) < self.min_regions_count:
                grid_points = self._generate_grid_points(width, height)
                clickable_regions.extend(grid_points)

            logger.debug(f"Found {len(clickable_regions)} clickable regions")

        except Exception as e:
            logger.error(f"Error analyzing screen: {e}")
            # В случае ошибки возвращаем сетку точек
            return self._generate_grid_points(1920, 1080)  # Стандартное Full HD разрешение
        else:
            return clickable_regions
        finally:
            # Освобождаем ресурсы Windows в правильном порядке
            try:
                if save_bit_map:
                    win32gui.DeleteObject(save_bit_map.GetHandle())
                if save_dc:
                    save_dc.DeleteDC()
                if mfc_dc:
                    mfc_dc.DeleteDC()
                if hwnd_dc:
                    win32gui.ReleaseDC(hwnd, hwnd_dc)  # type: ignore[arg-type]
            except Exception as e:
                logger.error(f"Error releasing resources: {e}")

    def _generate_grid_points(
        self,
        width: int,
        height: int,
    ) -> list[
        tuple[
            int,
            int,
        ]
    ]:
        """Генерирует равномерную сетку точек."""
        points: list[tuple[int, int]] = []
        cols = 10
        rows = 6
        cell_width = width // cols
        cell_height = height // rows

        for row in range(rows):
            for col in range(cols):
                x = col * cell_width + cell_width // 2
                y = row * cell_height + cell_height // 2
                points.append((x, y))

        return points
