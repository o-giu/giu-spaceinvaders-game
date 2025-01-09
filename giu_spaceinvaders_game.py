# by Giu
# https://github.com/o-giu

import pygame
import random
import sys
from enum import Enum, auto
from typing import List, Tuple
from dataclasses import dataclass
from pathlib import Path
from cryptography.fernet import Fernet
import math

@dataclass
class GameConfig:
    WINDOW_SIZE: Tuple[int, int] = (800, 700)  # Increased height from 600 to 700
    PLAYER_SIZE: Tuple[int, int] = (50, 40)
    ENEMY_SIZE: Tuple[int, int] = (40, 40)
    BULLET_SIZE: Tuple[int, int] = (4, 15)
    ENEMY_BULLET_SIZE: Tuple[int, int] = (4, 15)
    PLAYER_SPEED: int = 6
    BULLET_SPEED: int = 8
    ENEMY_BULLET_SPEED: int = 6
    ENEMY_SPEED: float = 1.5
    ENEMY_MOVE_DOWN: int = 30
    COLORS: dict = None

    def __post_init__(self):
        self.COLORS = {
            'background': (15, 15, 15),
            'player': (50, 205, 50),
            'enemy': (220, 20, 60),
            'bullet': (0, 255, 255),
            'text': (255, 255, 255),
            'inactive_text': (128, 128, 128),
            'shield': (0, 255, 255),
            'damaged': (255, 0, 0)
        }

class Entity:
    def __init__(self, x: float, y: float, width: int, height: int):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.rect = pygame.Rect(x, y, width, height)

    def update_rect(self):
        self.rect.x = self.x
        self.rect.y = self.y

class Player(Entity):
    def __init__(self, config: GameConfig):
        super().__init__(
            (config.WINDOW_SIZE[0] - config.PLAYER_SIZE[0]) // 2,
            config.WINDOW_SIZE[1] - config.PLAYER_SIZE[1] - 20,
            config.PLAYER_SIZE[0],
            config.PLAYER_SIZE[1]
        )
        self.config = config
        self.speed = config.PLAYER_SPEED
        self.shoot_cooldown = 0
        self.lives = 3
        self.damage_effect = 0
        self.invincible = False
        self.invincible_timer = 0

    def draw(self, screen):
        color = self.config.COLORS['damaged'] if self.damage_effect > 0 else self.config.COLORS['player']
        if self.invincible and pygame.time.get_ticks() % 200 < 100:
            return  # Skip drawing to create blinking effect

        # Draw spaceship
        points = [
            (self.x + self.width // 2, self.y),  # Top
            (self.x, self.y + self.height),  # Bottom left
            (self.x + self.width // 4, self.y + self.height * 0.7),  # Inner left
            (self.x + self.width * 3 // 4, self.y + self.height * 0.7),  # Inner right
            (self.x + self.width, self.y + self.height)  # Bottom right
        ]
        pygame.draw.polygon(screen, color, points)
        
        # Draw engine flame
        if random.random() < 0.7:  # Flicker effect
            flame_points = [
                (self.x + self.width * 0.4, self.y + self.height),
                (self.x + self.width // 2, self.y + self.height + 10),
                (self.x + self.width * 0.6, self.y + self.height)
            ]
            pygame.draw.polygon(screen, (255, 165, 0), flame_points)

    def take_damage(self):
        if not self.invincible:
            self.lives -= 1
            self.damage_effect = 30
            self.invincible = True
            self.invincible_timer = 120  # 2 seconds at 60 FPS

    def update(self):
        if self.damage_effect > 0:
            self.damage_effect -= 1
        if self.invincible:
            self.invincible_timer -= 1
            if self.invincible_timer <= 0:
                self.invincible = False

    def move(self, direction: int):
        self.x = max(0, min(self.x + direction * self.speed,
                           self.config.WINDOW_SIZE[0] - self.width))
        self.update_rect()

class Enemy(Entity):
    def __init__(self, x: float, y: float, config: GameConfig, points: int, enemy_type: int):
        super().__init__(x, y, config.ENEMY_SIZE[0], config.ENEMY_SIZE[1])
        self.config = config
        self.points = points
        self.direction = 1
        self.enemy_type = enemy_type
        self.animation_frame = 0
        self.animation_timer = 0

    def draw(self, screen):
        if self.enemy_type == 0:  # Small alien
            self._draw_small_alien(screen)
        elif self.enemy_type == 1:  # Medium alien
            self._draw_medium_alien(screen)
        else:  # Large alien
            self._draw_large_alien(screen)

    def _draw_small_alien(self, screen):
        color = self.config.COLORS['enemy']
        # Animate tentacles
        wave = math.sin(self.animation_timer * 0.1) * 3
        
        # Body
        pygame.draw.ellipse(screen, color, (self.x, self.y + 10, self.width, self.height - 20))
        # Eyes
        pygame.draw.circle(screen, (255, 255, 255), (self.x + 15, self.y + 20), 5)
        pygame.draw.circle(screen, (255, 255, 255), (self.x + 25, self.y + 20), 5)
        # Tentacles
        for i in range(4):
            x_offset = i * 10 + 5
            pygame.draw.line(screen, color, 
                           (self.x + x_offset, self.y + self.height - 10),
                           (self.x + x_offset, self.y + self.height + wave), 2)

    def _draw_medium_alien(self, screen):
        color = self.config.COLORS['enemy']
        wave = math.sin(self.animation_timer * 0.1) * 3
        
        # Head
        pygame.draw.ellipse(screen, color, (self.x + 5, self.y, self.width - 10, self.height - 10))
        # Eyes
        pygame.draw.circle(screen, (255, 255, 255), (self.x + 15, self.y + 15), 6)
        pygame.draw.circle(screen, (255, 255, 255), (self.x + 25, self.y + 15), 6)
        # Tentacles
        for i in range(3):
            x_offset = i * 15 + 5
            pygame.draw.line(screen, color,
                           (self.x + x_offset, self.y + self.height - 10),
                           (self.x + x_offset, self.y + self.height + wave), 3)

    def _draw_large_alien(self, screen):
        color = self.config.COLORS['enemy']
        wave = math.sin(self.animation_timer * 0.1) * 4
        
        # Body
        pygame.draw.ellipse(screen, color, (self.x, self.y, self.width, self.height - 5))
        # Eyes
        eye_color = (255, 255, 0)
        pygame.draw.circle(screen, eye_color, (self.x + 12, self.y + 15), 7)
        pygame.draw.circle(screen, eye_color, (self.x + 28, self.y + 15), 7)
        # Mouth
        pygame.draw.arc(screen, color, (self.x + 10, self.y + 20, 20, 15), 0, math.pi, 2)
        # Tentacles
        for i in range(5):
            x_offset = i * 8 + 4
            pygame.draw.line(screen, color,
                           (self.x + x_offset, self.y + self.height - 5),
                           (self.x + x_offset, self.y + self.height + wave), 2)

    def update(self):
        self.animation_timer += 1
        if self.animation_timer >= 60:
            self.animation_timer = 0
            self.animation_frame = (self.animation_frame + 1) % 2

class Bullet(Entity):
    def __init__(self, x: float, y: float, config: GameConfig, is_enemy: bool = False):
        size = config.ENEMY_BULLET_SIZE if is_enemy else config.BULLET_SIZE
        super().__init__(x, y, size[0], size[1])
        self.config = config
        self.speed = config.ENEMY_BULLET_SPEED if is_enemy else config.BULLET_SPEED
        self.is_enemy = is_enemy

    def move(self):
        self.y += self.speed if self.is_enemy else -self.speed
        self.update_rect()
        return 0 <= self.y <= self.config.WINDOW_SIZE[1]

class Shield(Entity):
    def __init__(self, x: float, y: float, size: int):
        super().__init__(x, y, size, size)
        self.health = 3

class ScoreManager:
    def __init__(self):
        self.save_dir = Path('save')
        self.save_dir.mkdir(parents=True, exist_ok=True)
        self.key_file = self.save_dir / 'space_invaders_score.key'
        self.score_file = self.save_dir / 'space_invaders_score.encrypted'
        self._initialize_encryption()

    def _initialize_encryption(self):
        try:
            if self.key_file.exists():
                self.key = self.key_file.read_bytes()
            else:
                self.key = Fernet.generate_key()
                self.key_file.write_bytes(self.key)
            self.fernet = Fernet(self.key)
        except Exception as e:
            print(f"Error initializing encryption: {e}")
            self.key = Fernet.generate_key()
            self.fernet = Fernet(self.key)

    def load_high_score(self) -> int:
        try:
            if self.score_file.exists():
                encrypted_data = self.score_file.read_bytes()
                decrypted_data = self.fernet.decrypt(encrypted_data)
                return int(decrypted_data.decode())
        except Exception as e:
            print(f"Error loading high score: {e}")
        return 0

    def save_high_score(self, score: int):
        try:
            encrypted_data = self.fernet.encrypt(str(score).encode())
            self.score_file.write_bytes(encrypted_data)
        except Exception as e:
            print(f"Error saving high score: {e}")

class BonusShip(Entity):
    def __init__(self, config: GameConfig):
        super().__init__(
            -60,  # Start outside the screen
            30,   # Height position
            60,   # Width
            30,   # Height
            )
        self.config = config
        self.speed = 3
        self.points = 100  # Base points, will be randomized
        
    def update(self):
        self.x += self.speed
        self.update_rect()
        return self.x < self.config.WINDOW_SIZE[0] + 60  # True while still on screen
        
    def draw(self, screen):
        # Draw UFO shape
        pygame.draw.ellipse(screen, (255, 0, 0), 
                          (self.x, self.y, self.width, self.height))
        pygame.draw.ellipse(screen, (150, 150, 150),
                          (self.x + 10, self.y - 5, self.width - 20, 15))

class SpaceInvaders:
    def __init__(self):
        pygame.init()
        self.config = GameConfig()
        self.screen = pygame.display.set_mode(self.config.WINDOW_SIZE)
        pygame.display.set_caption("Giu - Space Invaders v1.0")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)

        self.bonus_ship = None
        self.bonus_ship_timer = 0
        
        self.score_manager = ScoreManager()
        self.high_score = self.score_manager.load_high_score()
        self.reset_game()

    def reset_game(self):
        self.score = 0
        self.level = 1
        self.player = Player(self.config)
        self.enemies = self.create_enemies()
        self.bullets = []
        self.enemy_bullets = []
        self.shields = self.create_shields()
        self.enemy_move_timer = 0
        self.enemy_shoot_timer = 0
        self.game_over = False
        self.direction = 1
        self.bonus_ship = None
        self.bonus_ship_timer = random.randint(300, 900)  # 5-15 seconds
        self.shields = self.create_shields()
        
    def create_enemies(self) -> List[Enemy]:
        enemies = []
        rows = 5
        cols = 11
        spacing_x = 60
        spacing_y = 50
        start_x = (self.config.WINDOW_SIZE[0] - (cols * spacing_x)) // 2
        start_y = 80  # Increased from 50 to 80 to start higher

        points_per_row = [30, 20, 20, 10, 10]
        enemy_types = [2, 1, 1, 0, 0]  # Map rows to enemy types
        
        for row in range(rows):
            for col in range(cols):
                x = start_x + col * spacing_x
                y = start_y + row * spacing_y
                enemies.append(Enemy(x, y, self.config, points_per_row[row], enemy_types[row]))
                
        return enemies

    def create_shields(self) -> List[Shield]:
        shields = []
        shield_size = 60
        num_shields = 4
        spacing = self.config.WINDOW_SIZE[0] // (num_shields + 1)
        
        for i in range(num_shields):
            x = spacing * (i + 1) - shield_size // 2
            y = self.config.WINDOW_SIZE[1] - 150
            shields.append(Shield(x, y, shield_size))
            
        return shields

    def handle_input(self):
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    return "pause"
                elif event.key == pygame.K_SPACE:
                    if self.player.shoot_cooldown <= 0:
                        self.bullets.append(Bullet(
                            self.player.x + self.player.width // 2,
                            self.player.y,
                            self.config
                        ))
                        self.player.shoot_cooldown = 20

        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            self.player.move(-1)
        if keys[pygame.K_RIGHT]:
            self.player.move(1)

        return "continue"

    def update(self):
        # Update bonus ship
        self.bonus_ship_timer -= 1
        if self.bonus_ship_timer <= 0 and self.bonus_ship is None:
            self.bonus_ship = BonusShip(self.config)
            self.bonus_ship_timer = random.randint(300, 900)  # Reset timer
            
        if self.bonus_ship:
            if not self.bonus_ship.update():
                self.bonus_ship = None
                
        # Update enemy speed based on remaining enemies
        remaining_enemies = len(self.enemies)
        speed_multiplier = 1 + (55 - remaining_enemies) * 0.05  # Increases speed as enemies are destroyed
        level_multiplier = 1 + (self.level - 1) * 0.2  # Increases speed with level
        self.config.ENEMY_SPEED = min(5.0, 1.5 * speed_multiplier * level_multiplier)

        # Update player
        if self.player.shoot_cooldown > 0:
            self.player.shoot_cooldown -= 1
        self.player.update()

        # Update bullets
        self.bullets = [bullet for bullet in self.bullets if bullet.move()]
        self.enemy_bullets = [bullet for bullet in self.enemy_bullets if bullet.move()]

        # Update enemies
        for enemy in self.enemies:
            enemy.update()
        self.enemy_move_timer += 1
        if self.enemy_move_timer >= 60 // self.config.ENEMY_SPEED:
            self.enemy_move_timer = 0
            move_down = False
            
            for enemy in self.enemies:
                new_x = enemy.x + self.direction * 10
                if new_x <= 0 or new_x >= self.config.WINDOW_SIZE[0] - enemy.width:
                    move_down = True
                    break
                    
            if move_down:
                self.direction *= -1
                for enemy in self.enemies:
                    enemy.y += self.config.ENEMY_MOVE_DOWN
                    if enemy.y + enemy.height >= self.player.y:
                        self.game_over = True
            else:
                for enemy in self.enemies:
                    enemy.x += self.direction * 10
                    enemy.update_rect()

        # Enemy shooting
        self.enemy_shoot_timer += 1
        if self.enemy_shoot_timer >= 60:
            self.enemy_shoot_timer = 0
            if self.enemies:
                shooting_enemy = random.choice(self.enemies)
                self.enemy_bullets.append(Bullet(
                    shooting_enemy.x + shooting_enemy.width // 2,
                    shooting_enemy.y + shooting_enemy.height,
                    self.config,
                    True
                ))

        # Check collisions
        self.check_collisions()

        # Check win condition
        if not self.enemies:
            self.level += 1
            self.config.ENEMY_SPEED = min(4.0, 1.0 + (self.level - 1) * 0.5)
            self.enemies = self.create_enemies()
            self.shields = self.create_shields()  # Reset shields for new level

    def check_collisions(self):
        # Player bullets with enemies
        for bullet in self.bullets[:]:
            for enemy in self.enemies[:]:
                if bullet.rect.colliderect(enemy.rect):
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    if enemy in self.enemies:
                        self.enemies.remove(enemy)
                        self.score += enemy.points
                    break

        # Enemy bullets with player
        for bullet in self.enemy_bullets[:]:
            if bullet.rect.colliderect(self.player.rect):
                self.enemy_bullets.remove(bullet)
                self.player.take_damage()
                if self.player.lives <= 0:
                    self.game_over = True

        # Check bonus ship collisions
        if self.bonus_ship:
            for bullet in self.bullets[:]:
                if bullet.rect.colliderect(self.bonus_ship.rect):
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    points = random.randint(100, 300)  # Random bonus points
                    self.score += points
                    self.bonus_ship = None
                    break

        # Bullets with shields
        for shield in self.shields[:]:
            for bullet in self.bullets[:]:
                if bullet.rect.colliderect(shield.rect):
                    if bullet in self.bullets:
                        self.bullets.remove(bullet)
                    shield.health -= 1
                    if shield.health <= 0:
                        self.shields.remove(shield)
                    break
                    
            for bullet in self.enemy_bullets[:]:
                if bullet.rect.colliderect(shield.rect):
                    if bullet in self.enemy_bullets:
                        self.enemy_bullets.remove(bullet)
                    shield.health -= 1
                    if shield.health <= 0:
                        self.shields.remove(shield)
                    break

    def draw(self):
        self.screen.fill(self.config.COLORS['background'])
        
        # Draw game elements
        self.player.draw(self.screen)

        if self.bonus_ship:
            self.bonus_ship.draw(self.screen)
        
        for enemy in self.enemies:
            enemy.draw(self.screen)
            
        for bullet in self.bullets + self.enemy_bullets:
            pygame.draw.rect(self.screen, self.config.COLORS['bullet'], bullet.rect)
            
        for shield in self.shields:
            color = tuple(int(c * (shield.health / 3)) for c in self.config.COLORS['shield'])
            pygame.draw.rect(self.screen, color, shield.rect)

        # Draw UI
        score_text = self.font.render(f'Score: {self.score}', True, self.config.COLORS['text'])
        high_score_text = self.font.render(f'High Score: {self.high_score}', True, self.config.COLORS['text'])
        level_text = self.font.render(f'Level: {self.level}', True, self.config.COLORS['text'])
        lives_text = self.font.render(f'Lives: {self.player.lives}', True, self.config.COLORS['text'])
        
        # Add semi-transparent background for text
        text_bg_height = 70
        text_bg_surface = pygame.Surface((self.config.WINDOW_SIZE[0], text_bg_height))
        text_bg_surface.fill((0, 0, 0))
        text_bg_surface.set_alpha(128)
        self.screen.blit(text_bg_surface, (0, 0))
        
        self.screen.blit(score_text, (10, 10))
        self.screen.blit(high_score_text, (self.config.WINDOW_SIZE[0] - 200, 10))
        self.screen.blit(level_text, (10, 40))
        self.screen.blit(lives_text, (self.config.WINDOW_SIZE[0] - 200, 40))

        pygame.display.flip()

    def run(self):
        try:
            while True:
                # Main menu loop
                menu = Menu(self.screen, self.font, self.config)
                menu_running = True
                while menu_running:
                    menu.draw()
                    selection = menu.handle_input()
                    if selection == 0:  # Start Game
                        menu_running = False
                    elif selection == 1:  # Quit
                        return

                # Game loop
                self.reset_game()
                game_running = True
                
                while game_running:
                    input_result = self.handle_input()
                    
                    if input_result == "quit":
                        return
                    elif input_result == "pause":
                        pause_menu = PauseMenu(self.screen, self.font, self.config)
                        paused = True
                        while paused:
                            pause_menu.draw()
                            pause_selection = pause_menu.handle_input()
                            if pause_selection == 0:  # Return to Game
                                paused = False
                            elif pause_selection == 1:  # Back to Menu
                                game_running = False
                                paused = False
                            elif pause_selection == 2:  # Quit
                                return
                    if not game_running:
                        break

                    if not self.game_over:
                        self.update()
                        self.draw()
                    else:
                        if self.score > self.high_score:
                            self.high_score = self.score
                            self.score_manager.save_high_score(self.high_score)
                            
                        game_over = GameOver(self.screen, self.font, self.config, self.score)
                        game_over_running = True
                        while game_over_running:
                            game_over.draw()
                            game_over_selection = game_over.handle_input()
                            if game_over_selection == 0:  # Play Again
                                self.reset_game()
                                game_over_running = False
                            elif game_over_selection == 1:  # Main Menu
                                game_running = False
                                game_over_running = False
                            elif game_over_selection == 2:  # Quit
                                return

                    self.clock.tick(60)

        finally:
            pygame.quit()

class Menu:
    def __init__(self, screen, font, config):
        self.screen = screen
        self.font = font
        self.config = config
        self.options = ["Start Game", "Quit"]
        self.selected_index = 0
        self._initialize_title()
        
    def _initialize_title(self):
        title = "Giu - Space Invaders v1.0"
        gradient_colors = [
            (50, 205, 50),  # Light green
            (34, 139, 34),  # Forest green
            (0, 100, 0)     # Dark green
        ]
        
        title_font = pygame.font.Font(None, 72)
        self.title_surfaces = []
        total_width = 0
        
        for i, letter in enumerate(title):
            color_idx = (i / (len(title) - 1)) * (len(gradient_colors) - 1)
            base_idx = int(color_idx)
            next_idx = min(base_idx + 1, len(gradient_colors) - 1)
            blend = color_idx - base_idx
            
            color = tuple(
                int(gradient_colors[base_idx][j] * (1 - blend) + 
                    gradient_colors[next_idx][j] * blend)
                for j in range(3)
            )
            
            letter_surface = title_font.render(letter, True, color)
            self.title_surfaces.append((letter_surface, total_width))
            total_width += letter_surface.get_width()
        
        self.title_total_width = total_width

    def draw(self):
        self.screen.fill(self.config.COLORS['background'])
        
        title_start_x = (self.config.WINDOW_SIZE[0] - self.title_total_width) // 2
        title_y = 100
        for surface, offset in self.title_surfaces:
            self.screen.blit(surface, (title_start_x + offset, title_y))
        
        for i, option in enumerate(self.options):
            color = self.config.COLORS['text'] if i == self.selected_index else self.config.COLORS['inactive_text']
            option_text = self.font.render(option, True, color)
            option_rect = option_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 250 + i * 50))
            self.screen.blit(option_text, option_rect)
        
        pygame.display.flip()

    def handle_input(self) -> int:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 1
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 1
        return -1

class GameOver:
    def __init__(self, screen, font, config, final_score):
        self.screen = screen
        self.font = font
        self.config = config
        self.final_score = final_score
        self.options = ["Play Again", "Main Menu", "Quit"]
        self.selected_index = 0
        self.title_font = pygame.font.Font(None, 72)

    def draw(self):
        self.screen.fill(self.config.COLORS['background'])
        
        game_over_text = self.title_font.render("Game Over", True, (255, 0, 0))
        game_over_rect = game_over_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 100))
        self.screen.blit(game_over_text, game_over_rect)
        
        score_text = self.font.render(f"Final Score: {self.final_score}", True, self.config.COLORS['text'])
        score_rect = score_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 180))
        self.screen.blit(score_text, score_rect)

        for i, option in enumerate(self.options):
            color = self.config.COLORS['text'] if i == self.selected_index else self.config.COLORS['inactive_text']
            option_text = self.font.render(option, True, color)
            option_rect = option_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 280 + i * 50))
            self.screen.blit(option_text, option_rect)

        pygame.display.flip()

    def handle_input(self) -> int:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 2
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 1
        return -1

class PauseMenu:
    def __init__(self, screen, font, config):
        self.screen = screen
        self.font = font
        self.config = config
        self.options = ["Return to Game", "Back to Menu", "Quit"]
        self.selected_index = 0

    def draw(self):
        self.screen.fill(self.config.COLORS['background'])
        pause_text = self.font.render("Paused", True, self.config.COLORS['text'])
        pause_rect = pause_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 100))
        self.screen.blit(pause_text, pause_rect)

        for i, option in enumerate(self.options):
            color = self.config.COLORS['text'] if i == self.selected_index else self.config.COLORS['inactive_text']
            option_text = self.font.render(option, True, color)
            option_rect = option_text.get_rect(center=(self.config.WINDOW_SIZE[0] // 2, 200 + i * 50))
            self.screen.blit(option_text, option_rect)

        pygame.display.flip()

    def handle_input(self) -> int:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return 2
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_UP:
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                elif event.key == pygame.K_DOWN:
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif event.key == pygame.K_RETURN:
                    return self.selected_index
                elif event.key == pygame.K_ESCAPE:
                    return 0
        return -1

if __name__ == "__main__":
    try:
        game = SpaceInvaders()
        game.run()
    except Exception as e:
        import traceback
        error_msg = f"An error occurred:\n{str(e)}\n\n{traceback.format_exc()}"
        print(error_msg)
        try:
            import ctypes
            ctypes.windll.user32.MessageBoxW(0, error_msg, "Error", 0)
        except:
            input("Press Enter to exit...")
    finally:
        pygame.quit()
