# towers.py
import pygame
import math
from settings import *
from projectiles import Projectile

class Tower(pygame.sprite.Sprite):
    def __init__(self, tower_type, pos):
        super().__init__()
        self.tower_type = tower_type
        self.pos = pygame.math.Vector2(pos)
        
        base_data = TOWER_DATA[tower_type]
        self.base_cost = base_data["cost"]
        self.base_damage = base_data["damage"]
        self.base_fire_rate = base_data["fire_rate"]
        self.base_range = base_data["range"]
        
        self.damage = self.base_damage
        self.fire_rate = self.base_fire_rate
        self.range = self.base_range
        
        self.projectile_type = base_data["projectile"]
        self.image = base_data["image"]
        self.slow_effect = base_data.get("slow_effect", None)
        
        self.upgrade_levels = {"damage": 0, "fire_rate": 0, "range": 0}
        self.total_cost = self.base_cost
        
        self.rect = self.image.get_rect(center=self.pos)
        self.last_shot_time = pygame.time.get_ticks()

    def get_upgrade_cost(self, stat_name):
        level = self.upgrade_levels[stat_name]
        if level >= MAX_UPGRADE_LEVEL: return float('inf')
        cost_multiplier = UPGRADE_LEVEL_COSTS[level]
        return int(self.base_cost * cost_multiplier)

    def upgrade(self, stat_name):
        level = self.upgrade_levels[stat_name]
        if level < MAX_UPGRADE_LEVEL:
            cost = self.get_upgrade_cost(stat_name)
            self.total_cost += cost
            
            if stat_name == "damage":
                self.damage = int(self.damage * (1 + UPGRADE_BONUS))
            elif stat_name == "fire_rate":
                self.fire_rate = int(self.fire_rate * (1 - UPGRADE_BONUS))
            elif stat_name == "range":
                self.range = int(self.range * (1 + UPGRADE_BONUS))
                
            self.upgrade_levels[stat_name] += 1
    
    def get_sell_price(self):
        return int(self.total_cost * SELL_RATIO)

    def update(self, enemies, projectiles_group):
        self.shoot(enemies, projectiles_group)

    def shoot(self, enemies, projectiles_group):
        current_time = pygame.time.get_ticks()
        if current_time - self.last_shot_time > self.fire_rate:
            target = self.find_target(enemies)
            if target:
                self.last_shot_time = current_time
                projectile = Projectile(self.pos, target, self.damage, self.projectile_type, self.slow_effect)
                projectiles_group.add(projectile)
                if SHOOT_SOUND: SHOOT_SOUND.play()
    
    def find_target(self, enemies):
        best_target = None; max_progress = -1
        for enemy in enemies:
            dist = self.pos.distance_to(enemy.pos)
            if dist <= self.range and enemy.path_progress > max_progress:
                max_progress = enemy.path_progress; best_target = enemy
        return best_target
        
    def draw(self, surface):
        surface.blit(self.image, self.rect)
        # Рисуем полоски улучшений под башней
        y_offset = self.rect.height // 2 + 5
        for i, stat in enumerate(self.upgrade_levels.keys()):
            bar_x = self.rect.centerx - 15
            bar_y = self.rect.centery + y_offset + i * 6
            for j in range(MAX_UPGRADE_LEVEL):
                color = UPGRADE_BAR_COLOR if j < self.upgrade_levels[stat] else GREY
                pygame.draw.rect(surface, color, (bar_x + j*11, bar_y, 8, 4))
    
    def draw_range(self, surface):
        range_surface = pygame.Surface((self.range * 2, self.range * 2), pygame.SRCALPHA)
        pygame.draw.circle(range_surface, (*WHITE, 70), (self.range, self.range), self.range)
        pygame.draw.circle(range_surface, (*WHITE, 150), (self.range, self.range), self.range, 1)
        surface.blit(range_surface, (self.pos.x - self.range, self.pos.y - self.range))