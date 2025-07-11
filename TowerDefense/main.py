import pygame
import os
import settings  # Импортируем весь модуль
from game import Game

pygame.init()
screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
pygame.display.set_caption("Tower Defense")
print(f"Current working directory: {os.getcwd()}")
try:
    settings.load_images()  # Вызываем загрузку изображений
    settings.update_unit_data()  # Обновляем данные юнитов
    print(f"UI_IMAGES after load: {list(settings.UI_IMAGES.keys())}")  # Диагностика
    if not settings.UI_IMAGES:
        print("Warning: UI_IMAGES is empty. Using placeholder images.")
    else:
        for key in settings.UI_IMAGES:
            if settings.UI_IMAGES[key] is None or settings.UI_IMAGES[key].get_width() == 0:
                print(f"Warning: Invalid image for {key}")
except Exception as e:
    print(f"Error loading images: {e}")
    pygame.quit()
    exit(1)
clock = pygame.time.Clock()
game = Game(screen, clock)
game.run()
pygame.quit()