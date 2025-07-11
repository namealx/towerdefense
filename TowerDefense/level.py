import pygame
from settings import *
from enemies import Enemy
from towers import Tower
from ui import Button

class GameLevel:
    def __init__(self, level_num, game_controller):
        self.game_controller = game_controller
        self.level_num = level_num
        self.config = LEVELS_CONFIG[level_num]
        self.game_area = pygame.Surface((GAME_AREA_WIDTH, SCREEN_HEIGHT))

        self.path = self.config["path"]
        self.waves = self.config["waves"]
        
        self.start_health = 20; self.health = self.start_health
        self.money = 500
        self.wave_index = 0
        self.enemies_killed = 0
        self.start_time = pygame.time.get_ticks()

        self.enemies_to_spawn = []; self.state = "between_waves"
        self.enemies = pygame.sprite.Group(); self.towers = pygame.sprite.Group(); self.projectiles = pygame.sprite.Group()
        
        self._create_path_hitbox()
        self.setup_win_screen_ui()

    def setup_win_screen_ui(self):
        next_level_exists = (self.level_num + 1) in LEVELS_CONFIG
        max_unlocked = self.game_controller.get_unlocked_level()
        next_level_unlocked = (self.level_num + 1) <= max_unlocked

        self.win_screen_buttons = {
            "menu": Button(SCREEN_WIDTH//2, SCREEN_HEIGHT - 200, 250, 60, "В меню", lambda: self.game_controller.exit_to_level_select(), font=FONT_SMALL),
            "next": Button(SCREEN_WIDTH//2, SCREEN_HEIGHT - 120, 250, 60, "След. уровень", lambda: self.game_controller.start_level(self.level_num + 1), font=FONT_SMALL)
        }
        if not next_level_exists or not next_level_unlocked:
            self.win_screen_buttons["next"].color = BUTTON_LOCKED_COLOR
            self.win_screen_buttons["next"].hover_color = BUTTON_LOCKED_COLOR
            self.win_screen_buttons["next"].callback = lambda: None
        
    def _create_path_hitbox(self):
        self.path_rects = []
        path_width = 50
        for i in range(len(self.path) - 1):
            p1 = pygame.math.Vector2(self.path[i]); p2 = pygame.math.Vector2(self.path[i+1])
            rect_x = min(p1.x, p2.x) - path_width/2; rect_y = min(p1.y, p2.y) - path_width/2
            rect_w = abs(p1.x - p2.x) + path_width; rect_h = abs(p1.y - p2.y) + path_width
            self.path_rects.append(pygame.Rect(rect_x, rect_y, rect_w, rect_h))

    def trigger_next_wave(self):
        if self.state == "between_waves" and self.wave_index < len(self.waves):
            self.state = "wave_in_progress"
            wave_data = self.waves[self.wave_index]
            self.enemies_to_spawn = []
            for enemy_type, count in wave_data.items():
                for _ in range(count):
                    self.enemies_to_spawn.append(enemy_type)
            self.wave_index += 1
            self.wave_spawn_timer = pygame.time.get_ticks()

    def update(self):
        if self.state == "wave_in_progress": self.spawn_enemies()
        self.enemies.update()
        self.towers.update(self.enemies, self.projectiles)
        self.projectiles.update()
        
        if self.state == "wave_in_progress" and not self.enemies_to_spawn and not self.enemies:
            if self.wave_index >= len(self.waves):
                self.end_time = pygame.time.get_ticks()
                self.game_controller.save_progress(self.level_num, self.calculate_stars())
                self.setup_win_screen_ui()  # Обновляем доступность кнопки "След. уровень"
                self.game_controller.state = "win"
            else:
                self.state = "between_waves"
                
        if self.health <= 0:
            self.game_controller.state = "game_over"

    def spawn_enemies(self):
        spawn_interval = 500
        if self.enemies_to_spawn and pygame.time.get_ticks() - self.wave_spawn_timer > spawn_interval:
            enemy_type = self.enemies_to_spawn.pop(0)
            new_enemy = Enemy(enemy_type, self.path, self)
            self.enemies.add(new_enemy)
            self.wave_spawn_timer = pygame.time.get_ticks()

    def draw(self, surface):
        self.game_area.fill(self.config["bg_color"])
        pygame.draw.lines(self.game_area, PATH_COLOR, False, self.path, 40)
        
        mouse_pos = pygame.mouse.get_pos()
        if self.game_controller.selected_tower_type is None and self.game_controller.selected_tower is None:
            for tower in self.towers:
                if tower.rect.collidepoint(mouse_pos): tower.draw_range(self.game_area)
        if self.game_controller.selected_tower: self.game_controller.selected_tower.draw_range(self.game_area)

        self.towers.draw(self.game_area)
        self.projectiles.draw(self.game_area)
        for enemy in self.enemies:
            self.game_area.blit(enemy.image, enemy.rect)
            enemy.draw_health_bar(self.game_area)

        self.draw_tower_preview(self.game_area)
        surface.blit(self.game_area, (0, 0))
        
    def draw_win_screen(self, surface):
        rect = pygame.Rect(0, 0, 500, 450); rect.center = (SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2)
        pygame.draw.rect(surface, PANEL_COLOR, rect, border_radius=15)
        pygame.draw.rect(surface, WHITE, rect, 2, border_radius=15)

        title_surf = FONT_MAIN.render("Уровень пройден!", True, GREEN)
        surface.blit(title_surf, title_surf.get_rect(center=(rect.centerx, rect.top + 50)))

        stars = self.calculate_stars()
        for i in range(3):
            star_img = UI_IMAGES["star"] if i < stars else UI_IMAGES["star_empty"]
            surface.blit(star_img, star_img.get_rect(center=(rect.centerx - 50 + i * 50, rect.top + 120)))

        time_spent = (self.end_time - self.start_time) // 1000
        stats = [ f"Осталось жизней: {self.health} / {self.start_health}", f"Убито врагов: {self.enemies_killed}", f"Время: {time_spent // 60}м {time_spent % 60}с" ]
        for i, stat_text in enumerate(stats):
            stat_surf = FONT_SMALL.render(stat_text, True, WHITE)
            surface.blit(stat_surf, stat_surf.get_rect(center=(rect.centerx, rect.top + 200 + i * 40)))
            
        self.win_screen_buttons["menu"].draw(surface)
        self.win_screen_buttons["next"].draw(surface)

    def calculate_stars(self):
        if self.health == self.start_health: return 3
        if self.health >= self.start_health / 2: return 2
        return 1

    def draw_tower_preview(self, surface):
        if self.game_controller.selected_tower_type:
            mouse_pos = pygame.mouse.get_pos()
            if mouse_pos[0] >= GAME_AREA_WIDTH: return
            can_place = self.check_placement_legality(mouse_pos)
            data = TOWER_DATA[self.game_controller.selected_tower_type]
            tower_img = data["image"].copy()
            preview_color = (0, 255, 0, 150) if can_place else (255, 0, 0, 150)
            tower_img.fill(preview_color, special_flags=pygame.BLEND_RGBA_MULT)
            rect = tower_img.get_rect(center=mouse_pos)
            surface.blit(tower_img, rect)
            range_val = data["range"]
            range_surface = pygame.Surface((range_val * 2, range_val * 2), pygame.SRCALPHA)
            pygame.draw.circle(range_surface, (255, 255, 255, 100), (range_val, range_val), range_val, 1)
            surface.blit(range_surface, (mouse_pos[0] - range_val, mouse_pos[1] - range_val))
    
    def check_placement_legality(self, pos, new_tower_radius=25):
        if not (new_tower_radius <= pos[0] <= GAME_AREA_WIDTH - new_tower_radius and \
                new_tower_radius <= pos[1] <= SCREEN_HEIGHT - new_tower_radius): return False
        temp_rect = pygame.Rect(pos[0] - new_tower_radius, pos[1] - new_tower_radius, new_tower_radius * 2, new_tower_radius * 2)
        if temp_rect.collidelist(self.path_rects) != -1: return False
        for tower in self.towers:
            if temp_rect.colliderect(tower.rect): return False
        return True

    def place_tower(self, pos):
        if self.game_controller.selected_tower_type and self.check_placement_legality(pos):
            tower_type = self.game_controller.selected_tower_type
            cost = TOWER_DATA[tower_type]['cost']
            if self.money >= cost:
                new_tower = Tower(tower_type, pos); self.towers.add(new_tower)
                self.money -= cost
                if PLACE_TOWER_SOUND: PLACE_TOWER_SOUND.play()
                self.game_controller.selected_tower_type = None
    
    def sell_tower(self, tower):
        self.money += tower.get_sell_price(); tower.kill()

    def upgrade_tower(self, tower, stat_name):
        cost = tower.get_upgrade_cost(stat_name)
        if self.money >= cost:
            self.money -= cost; tower.upgrade(stat_name)
            if UPGRADE_SOUND: UPGRADE_SOUND.play()