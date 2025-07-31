# projectiles.py
import pygame
import math
from settings import PROJECTILE_DATA

class Projectile(pygame.sprite.Sprite):
    def __init__(self, start_pos, target, damage, proj_type, slow_effect):
        super().__init__()
        self.pos = pygame.math.Vector2(start_pos)
        self.target = target
        self.damage = damage
        self.slow_effect = slow_effect
        
        data = PROJECTILE_DATA[proj_type]
        self.speed = data["speed"]
        self.original_image = data["image"]
        self.image = self.original_image
        self.rect = self.image.get_rect(center=self.pos)

   
    def update(self):
        if self.target and self.target.alive():
            try:
                direction = (self.target.pos - self.pos).normalize()
            except ValueError:
                direction = pygame.math.Vector2(0, 0)

            self.rotate(direction)
            self.pos += direction * self.speed
            self.rect.center = self.pos
        else:
            self.kill()
            return
            
        if self.rect.colliderect(self.target.rect):
            self.target.take_damage(self.damage)
            if self.slow_effect:
                factor, duration = self.slow_effect
                self.target.apply_slow(factor, duration)
            self.kill()
    
    def rotate(self, direction):
        if direction.length() > 0:
            angle = math.degrees(math.atan2(-direction.y, direction.x))
            self.image = pygame.transform.rotate(self.original_image, angle)
            self.rect = self.image.get_rect(center=self.rect.center)