import pygame
from settings import SLATE_GREY, BLUE, WHITE

class Button:
    def __init__(self, x, y, width, height, text, callback, font=None, color=(100, 100, 200), hover_color=(150, 150, 250)):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.callback = callback
        self.font = font or pygame.font.SysFont("arial", 30)
        self.color = color
        self.hover_color = hover_color
        self.text_surface = self.font.render(text, True, (255, 255, 255))

    

    def draw(self, surface):
        current_color = self.hover_color if self.rect.collidepoint(pygame.mouse.get_pos()) else self.color
        pygame.draw.rect(surface, current_color, self.rect, border_radius=10)
        text_rect = self.text_surface.get_rect(center=self.rect.center)
        surface.blit(self.text_surface, text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.callback:
                    self.callback()

class Slider:
    def __init__(self, x, y, width, height, min_val, max_val, initial_val):
        self.rect = pygame.Rect(x, y, width, height)
        self.min_val = min_val
        self.max_val = max_val
        self.val = max(min(initial_val, max_val), min_val)  
        self.handle_radius = height * 1.5
        self.dragging = False

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.get_handle_rect().collidepoint(event.pos):
                self.dragging = True
        elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            self.dragging = False
        elif event.type == pygame.MOUSEMOTION and self.dragging:
            mouse_x = event.pos[0]
            new_val = self.min_val + (mouse_x - self.rect.left) / self.rect.width * (self.max_val - self.min_val)
            self.val = max(self.min_val, min(new_val, self.max_val))

    def get_handle_rect(self):
        handle_x = self.rect.left + (self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.width - self.handle_radius // 2
        return pygame.Rect(handle_x, self.rect.centery - self.handle_radius // 2, self.handle_radius, self.handle_radius)

    def draw(self, surface):
        pygame.draw.rect(surface, SLATE_GREY, self.rect, border_radius=5)
        fill_width = (self.val - self.min_val) / (self.max_val - self.min_val) * self.rect.width
        pygame.draw.rect(surface, BLUE, (self.rect.left, self.rect.top, fill_width, self.rect.height), border_radius=5)
        handle_rect = self.get_handle_rect()
        pygame.draw.circle(surface, WHITE, handle_rect.center, self.handle_radius // 2, 0)
        pygame.draw.circle(surface, BLUE, handle_rect.center, self.handle_radius // 2 - 2, 0)