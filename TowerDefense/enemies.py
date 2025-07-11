# enemies.py
import pygame
from settings import ENEMY_DATA, HIT_SOUND, GREEN, RED

class Enemy(pygame.sprite.Sprite):
    def __init__(self, enemy_type, path, game_level):
        super().__init__()
        self.enemy_type = enemy_type
        self.path = path
        self.path_index = 0
        self.game_level = game_level  # Сохраняем ссылку на уровень
        
        data = ENEMY_DATA[enemy_type]
        self.max_health = data["health"]
        self.health = self.max_health
        self.speed = data["speed"]
        self.original_speed = self.speed
        self.reward = data["reward"]
        self.image = data["image"]
        self.steals_gold = data.get("steals_gold", 0)

        self.pos = pygame.math.Vector2(self.path[0])
        self.rect = self.image.get_rect(center=self.pos)
        self.path_progress = 0
        self.slow_timer = 0

    # ======> ИСПРАВЛЕНИЕ ЗДЕСЬ <======
    # Метод update теперь не принимает аргументов, как того требует Pygame
    def update(self):
        self.move()
        self.check_slow_effect()

    def move(self):
        # Используем self.game_level, сохраненный в конструкторе
        if self.path_index >= len(self.path) - 1:
            self.reach_end()
            return
        
        target_pos = pygame.math.Vector2(self.path[self.path_index + 1])
        try:
            direction = (target_pos - self.pos).normalize()
        except ValueError:
            direction = pygame.math.Vector2(0, 0)
        
        distance_to_target = self.pos.distance_to(target_pos)
        
        move_dist = min(self.speed, distance_to_target)
        self.pos += direction * move_dist
        self.rect.center = self.pos
        self.path_progress += move_dist

        if distance_to_target < self.speed:
            self.path_index += 1

    def reach_end(self):
        self.game_level.health -= 1
        if self.steals_gold > 0:
            self.game_level.money = max(0, self.game_level.money - self.steals_gold)
        self.kill()

    def take_damage(self, damage):
        self.health -= damage
        if HIT_SOUND:
            HIT_SOUND.play()
        if self.health <= 0:
            self.die()

    def die(self):
        self.game_level.money += self.reward
        self.game_level.enemies_killed += 1
        
        spawn_info = ENEMY_DATA[self.enemy_type].get("spawns_on_death")
        if spawn_info:
            spawn_type, count = spawn_info
            for _ in range(count):
                # Передаем self.game_level в конструктор нового врага
                new_enemy = Enemy(spawn_type, self.path, self.game_level)
                new_enemy.pos = pygame.math.Vector2(self.pos)
                new_enemy.path_index = self.path_index
                new_enemy.path_progress = self.path_progress
                self.game_level.enemies.add(new_enemy)
        self.kill()

    def apply_slow(self, factor, duration):
        self.speed = self.original_speed * factor
        self.slow_timer = pygame.time.get_ticks() + duration

    def check_slow_effect(self):
        if self.slow_timer > 0 and pygame.time.get_ticks() > self.slow_timer:
            self.speed = self.original_speed
            self.slow_timer = 0

    def draw_health_bar(self, surface):
        if self.health < self.max_health:
            bar_width = 30
            bar_height = 4
            fill_width = int((self.health / self.max_health) * bar_width)
            bar_x = self.rect.centerx - bar_width // 2
            bar_y = self.rect.top - 10
            
            pygame.draw.rect(surface, RED, (bar_x, bar_y, bar_width, bar_height))
            pygame.draw.rect(surface, GREEN, (bar_x, bar_y, fill_width, bar_height))