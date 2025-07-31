import pygame
import os
import settings  
from game import Game

pygame.init()
screen = pygame.display.set_mode((settings.SCREEN_WIDTH, settings.SCREEN_HEIGHT))
pygame.display.set_caption("Защита королевства")
settings.load_images()  
settings.update_unit_data()  
clock = pygame.time.Clock()
game = Game(screen, clock)
game.run()
pygame.quit()