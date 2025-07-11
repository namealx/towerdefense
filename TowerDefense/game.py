import pygame
import settings
from settings import *
from ui import Button, Slider
import os
from PIL import Image, ImageFilter

class Game:
    def __init__(self, screen, clock):
        self.screen = screen
        self.clock = clock
        self.state = "main_menu"
        self.running = True
        self.game_instance = None
        self.previous_state = None
        self.pending_state = None  # Для хранения нового состояния
        self.handling_win = False  # Флаг для предотвращения повторной обработки

        self.game_settings = {"music_volume": 0.5, "sfx_volume": 0.5}
        self.update_volumes()
        
        self.progress_file = "progress.txt"
        self.progress_data = self.load_progress()
        
        self.selected_tower_type = None
        self.selected_tower = None
        self.setup_ui()
    
    def load_progress(self):
        progress = {}
        if os.path.exists(self.progress_file):
            with open(self.progress_file, 'r') as f:
                for line in f:
                    try:
                        level, stars = line.strip().split(':')
                        progress[int(level)] = int(stars)
                    except (ValueError, TypeError): 
                        continue
        return progress

    def save_progress(self, level_num, stars):
        if stars > self.progress_data.get(level_num, 0):
            self.progress_data[level_num] = stars
            with open(self.progress_file, 'w') as f:
                for level, star_count in sorted(self.progress_data.items()):
                    f.write(f"{level}:{star_count}\n")
            self.setup_level_buttons()
    
    def get_unlocked_level(self):
        if not self.progress_data: 
            return 1
        return max(self.progress_data.keys()) + 1

    def update_volumes(self):
        sounds = [SHOOT_SOUND, HIT_SOUND, PLACE_TOWER_SOUND, UPGRADE_SOUND, SELL_SOUND]
        for sound in sounds:
            if sound: 
                sound.set_volume(self.game_settings["sfx_volume"])
        pygame.mixer.music.set_volume(self.game_settings["music_volume"])

    def setup_level_buttons(self):
        btn_w, btn_h = 200, 70
        max_unlocked = self.get_unlocked_level()
        self.level_select_buttons = [Button(SCREEN_WIDTH // 2, 650, 300, 70, "Назад", self.go_to_main_menu)]
        
        for i, level_num in enumerate(LEVELS_CONFIG.keys()):
            row, col = i // 3, i % 3
            x, y = (SCREEN_WIDTH // 4) * (col + 1), 250 + row * 150
            is_locked = level_num > max_unlocked
            callback_func = (lambda l=level_num: self.start_level(l)) if not is_locked else (lambda: None)
            btn = Button(x, y, btn_w, btn_h, f"Уровень {level_num}", callback_func)
            btn.stars = self.progress_data.get(level_num, 0)
            if is_locked: 
                btn.color = btn.hover_color = BUTTON_LOCKED_COLOR
            self.level_select_buttons.append(btn)
            
    def setup_ui(self):
        btn_w, btn_h = 300, 70
        self.main_menu_buttons = [
            Button(SCREEN_WIDTH // 2, 300, btn_w, btn_h, "Начать игру", self.go_to_level_select),
            Button(SCREEN_WIDTH // 2, 400, btn_w, btn_h, "Настройки", self.go_to_settings),
            Button(SCREEN_WIDTH // 2, 500, btn_w, btn_h, "Выход", self.quit_game)
        ]
        self.setup_level_buttons()
        self.settings_buttons = [Button(SCREEN_WIDTH // 2, 550, btn_w, btn_h, "Назад", self.exit_settings)]
        self.music_slider = Slider(SCREEN_WIDTH // 2 - 200, 300, 400, 20, 0, 1, self.game_settings["music_volume"])
        self.sfx_slider = Slider(SCREEN_WIDTH // 2 - 200, 400, 400, 20, 0, 1, self.game_settings["sfx_volume"])
        self.pause_menu_buttons = [
            Button(SCREEN_WIDTH // 2, 250, btn_w, btn_h, "Продолжить", self.resume_game),
            Button(SCREEN_WIDTH // 2, 350, btn_w, btn_h, "Настройки", self.go_to_settings_from_pause),
            Button(SCREEN_WIDTH // 2, 450, btn_w, btn_h, "Выйти в меню", self.exit_to_level_select),
        ]
        
        panel_x = GAME_AREA_WIDTH + RIGHT_PANEL_WIDTH // 2
        self.tower_buy_buttons = [
            Button(panel_x, 250, 200, 60, f"Лучник ({TOWER_DATA['archer']['cost']})", lambda: self.select_tower("archer"), font=FONT_SMALL),
            Button(panel_x, 330, 200, 60, f"Пушка ({TOWER_DATA['cannon']['cost']})", lambda: self.select_tower("cannon"), font=FONT_SMALL),
            Button(panel_x, 410, 200, 60, f"Маг ({TOWER_DATA['mage']['cost']})", lambda: self.select_tower("mage"), font=FONT_SMALL)
        ]
        self.start_wave_button = Button(panel_x, SCREEN_HEIGHT - 80, 200, 60, "Начать Волну", self.trigger_wave_start, font=FONT_SMALL)
        
        self.tower_control_buttons = {
            "sell": Button(panel_x, 500, 200, 50, "Продать", self.sell_selected_tower, font=FONT_SMALL),
            "upgrade_damage": Button(panel_x, 250, 200, 50, "Урон", lambda: self.upgrade_selected_tower('damage'), font=FONT_SMALL),
            "upgrade_fire_rate": Button(panel_x, 320, 200, 50, "Скорость", lambda: self.upgrade_selected_tower('fire_rate'), font=FONT_SMALL),
            "upgrade_range": Button(panel_x, 390, 200, 50, "Дальность", lambda: self.upgrade_selected_tower('range'), font=FONT_SMALL),
        }
        self.settings_icon_rect = settings.UI_IMAGES.get("settings_gear", pygame.Surface((10, 10), pygame.SRCALPHA)).get_rect(topleft=(20, SCREEN_HEIGHT - 60))

    def run(self):
        self.play_music()  # Запускаем музыку при старте
        while self.running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                else:
                    self.handle_events(event)
            self.process_pending_state()
            self.update()
            self.draw()
            self.clock.tick(FPS)

    def play_music(self):
        if settings.BACKGROUND_MUSIC:
            try:
                pygame.mixer.music.play(-1)  # Зацикленное воспроизведение
            except pygame.error:
                print("Error: Failed to play music, check audio setup.")
                settings.BACKGROUND_MUSIC = False

    def handle_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 3: 
            self.selected_tower_type = self.selected_tower = None
        
        # Устанавливаем флаг для предотвращения повторной обработки
        if self.state == "win" and not self.handling_win and self.game_instance is not None:
            self.handling_win = True
            self.game_instance.win_screen_buttons["menu"].handle_event(event)
            self.game_instance.win_screen_buttons["next"].handle_event(event)
            self.handling_win = False
        
        if self.state == "game_over":
            if event.type == pygame.MOUSEBUTTONDOWN or event.type == pygame.KEYDOWN:
                self.pending_state = "level_select"
            return
        
        if self.state == "pause":
            for btn in self.pause_menu_buttons: 
                btn.handle_event(event)
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: 
                self.pending_state = "in_game"
            return
        
        # Затем обрабатываем остальные состояния
        if self.state == "main_menu":
            for btn in self.main_menu_buttons: 
                btn.handle_event(event)
        elif self.state == "level_select":
            for btn in self.level_select_buttons: 
                btn.handle_event(event)
        elif self.state == "settings":
            self.music_slider.handle_event(event)
            self.sfx_slider.handle_event(event)
            for btn in self.settings_buttons: 
                btn.handle_event(event)
        elif self.state == "in_game":
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE: 
                self.pending_state = "pause"
            if self.game_instance:  # Проверяем, что game_instance существует
                if self.selected_tower:
                    for btn in self.tower_control_buttons.values(): 
                        btn.handle_event(event)
                else:
                    for btn in self.tower_buy_buttons: 
                        btn.handle_event(event)
                if self.game_instance.state == "between_waves": 
                    self.start_wave_button.handle_event(event)
                
                if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                    if self.settings_icon_rect.collidepoint(event.pos):
                        self.pending_state = "pause"
                    elif event.pos[0] < GAME_AREA_WIDTH:
                        clicked_on_tower = False
                        for tower in self.game_instance.towers:
                            if tower.rect.collidepoint(event.pos):
                                self.selected_tower = tower
                                self.selected_tower_type = None
                                clicked_on_tower = True
                                break
                        if not clicked_on_tower:
                            if self.selected_tower_type:
                                self.game_instance.place_tower(event.pos)
                            else:
                                self.selected_tower = None

    def process_pending_state(self):
        if self.pending_state:
            if self.pending_state == "level_select":
                self.go_to_level_select()
            elif self.pending_state == "in_game":
                self.resume_game()
            elif self.pending_state == "pause":
                self.state = "pause"
            self.pending_state = None
            self.play_music()  # Перезапускаем музыку при смене состояния

    def update(self):
        if self.state == "settings":
            self.game_settings["sfx_volume"] = self.sfx_slider.val
            self.game_settings["music_volume"] = self.music_slider.val
            self.update_volumes()
        elif self.state == "in_game" and self.game_instance:
            self.game_instance.update()

    def draw(self):
        self.screen.fill(BLACK)
        # Отображение фоновых изображений с размытием
        if self.state == "main_menu":
            self.draw_background("assets/images/backgrounds/main_menu_background.png")
            self.draw_main_menu()
        elif self.state == "level_select":
            self.draw_background("assets/images/backgrounds/level_select_background.png")
            self.draw_level_select()
        elif self.state == "settings":
            self.draw_background("assets/images/backgrounds/settings_background.png")
            self.draw_settings()
        elif self.state in ["in_game", "pause", "win", "game_over"]:
            if self.game_instance:
                self.game_instance.draw(self.screen)
                self.draw_game_hud()
            if self.state == "win" and self.game_instance: 
                self.game_instance.draw_win_screen(self.screen)
            elif self.state == "pause": 
                self.draw_pause_menu()
            elif self.state == "game_over": 
                self.draw_game_over()
        pygame.display.flip()

    def draw_background(self, image_path):
        try:
            # Загружаем изображение с помощью PIL и применяем размытие
            pil_image = Image.open(image_path)
            blurred_image = pil_image.filter(ImageFilter.GaussianBlur(radius=5))  # Радиус размытия 5
            blurred_image = blurred_image.resize((SCREEN_WIDTH, SCREEN_HEIGHT), Image.LANCZOS)
            # Конвертируем обратно в pygame Surface
            mode = blurred_image.mode
            size = blurred_image.size
            data = blurred_image.tobytes()
            pygame_image = pygame.image.fromstring(data, size, mode).convert()
            self.screen.blit(pygame_image, (0, 0))
        except pygame.error:
            self.screen.fill(GREY)  # Заглушка при ошибке загрузки

    def draw_game_hud(self):
        panel_rect = pygame.Rect(GAME_AREA_WIDTH, 0, RIGHT_PANEL_WIDTH, SCREEN_HEIGHT)
        pygame.draw.rect(self.screen, PANEL_COLOR, panel_rect)
        if not self.game_instance: 
            return
        # Статистика
        heart_pos = (GAME_AREA_WIDTH + 40, 40)
        heart_img = settings.UI_IMAGES.get("heart", pygame.Surface((30, 30), pygame.SRCALPHA))
        self.screen.blit(heart_img, heart_img.get_rect(center=heart_pos))
        health_text = FONT_MAIN.render(f"{self.game_instance.health}", True, WHITE)
        self.screen.blit(health_text, (heart_pos[0] + 30, heart_pos[1] - 20))
        coin_pos = (GAME_AREA_WIDTH + 40, 90)
        coin_img = settings.UI_IMAGES.get("coin", pygame.Surface((30, 30), pygame.SRCALPHA))
        self.screen.blit(coin_img, coin_img.get_rect(center=coin_pos))
        money_text = FONT_MAIN.render(f"{self.game_instance.money}", True, WHITE)
        self.screen.blit(money_text, (coin_pos[0] + 30, coin_pos[1] - 20))
        
        # UI на правой панели
        if self.selected_tower: 
            self.draw_tower_control_panel()
        else:
            for button in self.tower_buy_buttons: 
                button.draw(self.screen)
        
        if self.game_instance.state == "between_waves" and self.game_instance.wave_index < len(self.game_instance.waves):
            self.start_wave_button.draw(self.screen)
        
        # Левый верхний HUD
        wave_panel_rect = pygame.Rect(10, 10, 240, 50)
        pygame.draw.rect(self.screen, PANEL_COLOR, wave_panel_rect, border_radius=10)
        wave_text_str = f"Ур. {self.game_instance.level_num} | Волна: {self.game_instance.wave_index}/{len(self.game_instance.waves)}"
        wave_text = FONT_SMALL.render(wave_text_str, True, WHITE)
        self.screen.blit(wave_text, wave_text.get_rect(center=wave_panel_rect.center))
        # Левый нижний HUD
        settings_gear_img = settings.UI_IMAGES.get("settings_gear", pygame.Surface((10, 10), pygame.SRCALPHA))
        self.screen.blit(settings_gear_img, self.settings_icon_rect)

    def draw_tower_control_panel(self):
        tower = self.selected_tower
        panel_x = GAME_AREA_WIDTH + RIGHT_PANEL_WIDTH // 2
        # Словарь для перевода названий башен на русский
        tower_names = {"archer": "Лучник", "cannon": "Пушка", "mage": "Маг"}
        title_text = f"Башня: {tower_names[tower.tower_type]}"
        title_surf = FONT_SMALL.render(title_text, True, WHITE)
        self.screen.blit(title_surf, title_surf.get_rect(center=(panel_x, 150)))
        
        y_offset = 200  # Начальная высота для кнопок
        button_spacing = 60  # Увеличенное пространство между кнопками для лучшего отображения
        stats = ['damage', 'fire_rate', 'range']
        for i, stat in enumerate(stats):
            btn = self.tower_control_buttons[f"upgrade_{stat}"]
            level = tower.upgrade_levels[stat]
            stat_rus = {"damage": "Урон", "fire_rate": "Скорость", "range": "Дальность"}[stat]
            btn.rect = pygame.Rect(panel_x - 100, y_offset + i * button_spacing, 200, 50)
            if level < MAX_UPGRADE_LEVEL:
                cost = tower.get_upgrade_cost(stat)
                btn.text = f"{stat_rus} (+{cost}$)" if cost is not None else f"{stat_rus} (Ошибка)"
                can_afford = self.game_instance.money >= cost if cost is not None else False
                btn.color = BLUE if can_afford else GREY
                btn.hover_color = btn.color
            else:
                btn.text = f"{stat_rus} (МАКС)"
                btn.color = btn.hover_color = BUTTON_LOCKED_COLOR
            btn.draw(self.screen)

        sell_btn = self.tower_control_buttons["sell"]
        sell_price = tower.get_sell_price()
        sell_btn.text = f"Продать (+{sell_price}$)" if sell_price is not None else "Продать (Ошибка)"
        sell_btn.rect = pygame.Rect(panel_x - 100, y_offset + 3 * button_spacing, 200, 50)
        sell_btn.draw(self.screen)

    def draw_menu_background(self, title_text):
        title_surf = FONT_MAIN.render(title_text, True, WHITE)
        self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 100)))

    def draw_main_menu(self):
        for btn in self.main_menu_buttons: 
            btn.draw(self.screen)

    def draw_level_select(self):
        self.setup_level_buttons()
        for button in self.level_select_buttons:
            button.draw(self.screen)
            if hasattr(button, 'stars'):
                for i in range(3):
                    star_img = settings.UI_IMAGES.get("star", pygame.Surface((25, 25), pygame.SRCALPHA)) if i < button.stars else settings.UI_IMAGES.get("star_empty", pygame.Surface((25, 25), pygame.SRCALPHA))
                    self.screen.blit(star_img, (button.rect.left + i * 30 + 35, button.rect.bottom + 5))
            
    def draw_settings(self):
        self.music_slider.draw(self.screen)
        self.sfx_slider.draw(self.screen)
        music_text = FONT_SMALL.render("Громкость музыки", True, WHITE)
        self.screen.blit(music_text, (self.music_slider.rect.centerx - music_text.get_width()//2, self.music_slider.rect.y - 40))
        sfx_text = FONT_SMALL.render("Громкость эффектов", True, WHITE)
        self.screen.blit(sfx_text, (self.sfx_slider.rect.centerx - sfx_text.get_width()//2, self.sfx_slider.rect.y - 40))
        for button in self.settings_buttons: 
            button.draw(self.screen)

    def draw_overlay(self, title, title_color, subtitle):
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        title_surf = FONT_MAIN.render(title, True, title_color)
        self.screen.blit(title_surf, title_surf.get_rect(center=(SCREEN_WIDTH // 2, 300)))
        sub_surf = FONT_SMALL.render(subtitle, True, WHITE)
        self.screen.blit(sub_surf, sub_surf.get_rect(center=(SCREEN_WIDTH // 2, 400)))
        
    def draw_pause_menu(self): 
        self.draw_overlay("", WHITE, "")  # Убрали текст "Пауза", оставили только overlay
        for btn in self.pause_menu_buttons: 
            btn.draw(self.screen)
    
    def draw_game_over(self): 
        self.draw_overlay("Игра окончена", RED, "Нажмите любую кнопку, чтобы продолжить")
    
    def start_level(self, level_num):
        from level import GameLevel
        self.game_instance = GameLevel(level_num, self)
        self.state = "in_game"
        self.selected_tower = None
        self.selected_tower_type = None

    def trigger_wave_start(self):
        if self.game_instance: 
            self.game_instance.trigger_next_wave()
        
    def sell_selected_tower(self):
        if self.selected_tower and self.game_instance:
            self.game_instance.sell_tower(self.selected_tower)
            self.selected_tower = None
            if SELL_SOUND: 
                SELL_SOUND.play()

    def upgrade_selected_tower(self, stat_name):
        if self.selected_tower and self.game_instance:
            self.game_instance.upgrade_tower(self.selected_tower, stat_name)

    def go_to_level_select(self):
        self.state = "level_select"
        self.game_instance = None
        self.selected_tower = None
        self.selected_tower_type = None
        self.setup_level_buttons()
        
    def exit_to_level_select(self):
        self.pending_state = "level_select"
        
    def go_to_main_menu(self): 
        self.state = "main_menu"
        self.game_instance = None
        self.selected_tower = None
        self.selected_tower_type = None
    
    def go_to_settings(self): 
        self.previous_state = self.state
        self.state = "settings"
    
    def go_to_settings_from_pause(self): 
        self.previous_state = "pause"
        self.state = "settings"
    
    def exit_settings(self): 
        self.state = self.previous_state if self.previous_state else "main_menu"
        self.previous_state = None
    
    def resume_game(self): 
        self.state = "in_game"
    
    def quit_game(self): 
        self.running = False
        
    def select_tower(self, tower_type):
        self.selected_tower = None
        if self.game_instance and self.game_instance.money >= TOWER_DATA[tower_type]['cost']:
            self.selected_tower_type = tower_type
        else: 
            self.selected_tower_type = None