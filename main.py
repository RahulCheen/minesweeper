import pygame
import random
import time
import sys
import math
import sqlite3
from constants import *

pygame.init()
pygame.display.set_caption("Minesweeper")

import os
font_path = os.path.join(os.path.dirname(__file__), "Fonts", "PressStart2P-Regular.ttf")
try:
    font_small = pygame.font.Font(font_path, 8)
    font_medium = pygame.font.Font(font_path, 12)
    font_large = pygame.font.Font(font_path, 16)
    font_title = pygame.font.Font(font_path, 20)
except Exception:
    font_small = pygame.font.Font(None, 20)
    font_medium = pygame.font.Font(None, 24)
    font_large = pygame.font.Font(None, 28)
    font_title = pygame.font.Font(None, 32)

class TimeDB:
    def __init__(self, db_name="times.db"):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS best_times (
                difficulty TEXT PRIMARY KEY,
                best_time REAL
            )
        ''')
        self.conn.commit()

    def update_time(self, difficulty, time_val):
        self.cursor.execute('SELECT best_time FROM best_times WHERE difficulty = ?', (difficulty,))
        row = self.cursor.fetchone()
        
        if row is None:
            self.cursor.execute('INSERT INTO best_times (difficulty, best_time) VALUES (?, ?)', (difficulty, time_val))
            self.conn.commit()
            return time_val
        else:
            best = row[0]
            if time_val < best:
                self.cursor.execute('UPDATE best_times SET best_time = ? WHERE difficulty = ?', (time_val, difficulty))
                self.conn.commit()
                return time_val
            return best

    def get_best_time(self, difficulty):
        self.cursor.execute('SELECT best_time FROM best_times WHERE difficulty = ?', (difficulty,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    def close(self):
        self.conn.close()

class Button:
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.is_hovered = False
        
    def draw(self, screen, theme):
        color = theme["highlight"] if self.is_hovered else theme["hidden"]
        
        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        
        inner_rect = self.rect.inflate(-4, -4)
        pygame.draw.rect(screen, theme["highlight"], self.rect, width=2, border_radius=8)
        pygame.draw.arc(screen, theme["highlight"], self.rect, 0, 3.14159/2, 2)
        pygame.draw.rect(screen, theme["shadow"], inner_rect, width=2, border_radius=6)
        
        text_surf = self.font.render(self.text, False, BLACK)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)
        
    def check_hover(self, pos):
        self.is_hovered = self.rect.collidepoint(pos)
        
    def is_clicked(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                return True
        return False

class Dropdown:
    def __init__(self, x, y, width, height, options, selected_idx):
        self.rect = pygame.Rect(x, y, width, height)
        self.options = options
        self.selected_idx = selected_idx
        self.is_open = False
        self.option_rects = []

    def draw(self, screen, theme):
        mouse_pos = pygame.mouse.get_pos()
        is_hovered_main = self.rect.collidepoint(mouse_pos) or self.is_open
        color = theme["highlight"] if is_hovered_main else theme["hidden"]

        pygame.draw.rect(screen, color, self.rect, border_radius=8)
        
        inner_rect = self.rect.inflate(-4, -4)
        pygame.draw.rect(screen, theme["highlight"], self.rect, width=2, border_radius=8)
        pygame.draw.arc(screen, theme["highlight"], self.rect, 0, 3.14159/2, 2)
        pygame.draw.rect(screen, theme["shadow"], inner_rect, width=2, border_radius=6)
        
        text = font_small.render(self.options[self.selected_idx], False, BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

        if self.is_open:
            self.option_rects = []
            for i, option in enumerate(self.options):
                opt_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                self.option_rects.append(opt_rect)
                
                is_hover = opt_rect.collidepoint(mouse_pos)
                opt_color = theme["highlight"] if is_hover else theme["revealed"]
                
                b_radius = 8 if i == len(self.options) - 1 else 0
                
                pygame.draw.rect(screen, opt_color, opt_rect, border_bottom_left_radius=b_radius, border_bottom_right_radius=b_radius)
                pygame.draw.rect(screen, theme["shadow"], opt_rect, 1, border_bottom_left_radius=b_radius, border_bottom_right_radius=b_radius)
                
                opt_text = font_small.render(option, False, BLACK)
                opt_text_rect = opt_text.get_rect(center=opt_rect.center)
                screen.blit(opt_text, opt_text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_open:
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_idx = i
                        self.is_open = False
                        return True
                
                self.is_open = False
            else:
                if self.rect.collidepoint(event.pos):
                    self.is_open = True
        return False
        
    def get_selected(self):
        return self.options[self.selected_idx]

class TextInput:
    def __init__(self, x, y, width, height, font, initial_text=""):
        self.rect = pygame.Rect(x, y, width, height)
        self.font = font
        self.text = initial_text
        self.active = False
        
    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            if self.rect.collidepoint(event.pos):
                self.active = True
            else:
                self.active = False
                
        if self.active and event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.text = self.text[:-1]
            elif event.unicode.isdigit():
                if len(self.text) < 3:
                    self.text += event.unicode
                    
    def draw(self, screen, theme):
        color = theme["highlight"] if self.active else WHITE
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        txt_surf = self.font.render(self.text, False, BLACK)
        text_rect = txt_surf.get_rect(midleft=(self.rect.x + 5, self.rect.centery))
        screen.blit(txt_surf, text_rect)
        
        if self.active:
            if pygame.time.get_ticks() % 1000 < 500:
                cursor_x = text_rect.right + 2 if self.text else self.rect.x + 5
                pygame.draw.line(screen, BLACK, (cursor_x, text_rect.top), (cursor_x, text_rect.bottom), 2)

class Board:
    def __init__(self, cols, rows, num_mines):
        self.cols = cols
        self.rows = rows
        self.num_mines = num_mines
        self.grid = [[0 for _ in range(cols)] for _ in range(rows)]
        self.revealed = [[False for _ in range(cols)] for _ in range(rows)]
        self.flagged = [[False for _ in range(cols)] for _ in range(rows)]
        self.mines = []
        self.first_click = True
        self.game_over = False
        self.won = False
        self.flags_placed = 0
        
        self.reveal_times = [[0 for _ in range(cols)] for _ in range(rows)]
        self.flag_times = [[0 for _ in range(cols)] for _ in range(rows)]

    def generate_mines(self, safe_x, safe_y):
        safe_zone = set()
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx, ny = safe_x + dx, safe_y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    safe_zone.add((nx, ny))

        available_spots = [(x, y) for y in range(self.rows) for x in range(self.cols) if (x, y) not in safe_zone]
        
        if len(available_spots) < self.num_mines:
            available_spots = [(x, y) for y in range(self.rows) for x in range(self.cols) if (x, y) != (safe_x, safe_y)]
            
        self.mines = random.sample(available_spots, min(self.num_mines, len(available_spots)))
        
        for x, y in self.mines:
            self.grid[y][x] = -1
            
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] == -1:
                    continue
                count = 0
                for dy in [-1, 0, 1]:
                    for dx in [-1, 0, 1]:
                        nx, ny = x + dx, y + dy
                        if 0 <= nx < self.cols and 0 <= ny < self.rows and self.grid[ny][nx] == -1:
                            count += 1
                self.grid[y][x] = count

    def reveal(self, x, y):
        if self.game_over or self.won or self.flagged[y][x] or self.revealed[y][x]:
            return

        if self.first_click:
            self.generate_mines(x, y)
            self.first_click = False

        self.revealed[y][x] = True
        self.reveal_times[y][x] = pygame.time.get_ticks()

        if self.grid[y][x] == -1:
            self.game_over = True
            return

        if self.grid[y][x] == 0:
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    nx, ny = x + dx, y + dy
                    if 0 <= nx < self.cols and 0 <= ny < self.rows:
                        if not self.revealed[ny][nx]:
                            self.reveal(nx, ny)

        self.check_win()

    def toggle_flag(self, x, y):
        if self.game_over or self.won or self.revealed[y][x] or self.first_click:
            return

        if not self.flagged[y][x]:
            if self.flags_placed < self.num_mines:
                self.flagged[y][x] = True
                self.flag_times[y][x] = pygame.time.get_ticks()
                self.flags_placed += 1
        else:
            self.flagged[y][x] = False
            self.flags_placed -= 1

    def check_win(self):
        for y in range(self.rows):
            for x in range(self.cols):
                if self.grid[y][x] != -1 and not self.revealed[y][x]:
                    return
        self.won = True
        self.game_over = True

class Game:
    def __init__(self):
        self.difficulty_name = DEFAULT_DIFFICULTY
        self.theme_name = random.choice(list(THEMES.keys()))
        self.theme = THEMES[self.theme_name]
        
        settings = DIFFICULTIES[self.difficulty_name]
        self.board = Board(settings["cols"], settings["rows"], settings["mines"])
        
        self.db = TimeDB()
        self.best_time = None
        
        self.start_timer = 0.0
        self.end_time = 0.0
        
        difficulties_list = list(DIFFICULTIES.keys())
        self.dropdown = Dropdown(10, 25, 120, 30, difficulties_list, difficulties_list.index(self.difficulty_name))
        
        themes_list = list(THEMES.keys())
        self.theme_dropdown = Dropdown(0, 25, 100, 30, themes_list, themes_list.index(self.theme_name))
        
        self.width = max(self.board.cols * CELL_SIZE, MIN_WIDTH)
        self.height = self.board.rows * CELL_SIZE + TOP_BAR_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        
        self.custom_popup_open = False
        
        custom_cols = DIFFICULTIES["Custom"]["cols"]
        custom_rows = DIFFICULTIES["Custom"]["rows"]
        popup_w, popup_h = 300, 250
        self.popup_rect = pygame.Rect(0, 0, popup_w, popup_h)
        self.input_cols = TextInput(0, 0, 60, 30, font_medium, str(custom_cols))
        self.input_rows = TextInput(0, 0, 60, 30, font_medium, str(custom_rows))
        self.apply_btn = Button(0, 0, 100, 30, "Apply", font_medium)
        self.cancel_btn = Button(0, 0, 100, 30, "Cancel", font_medium)

        self.update_screen_size()

    def update_screen_size(self):
        self.width = max(self.width, MIN_WIDTH)
        self.height = max(self.height, TOP_BAR_HEIGHT + 100)
        
        try:
            desktop_sizes = pygame.display.get_desktop_sizes()
            if desktop_sizes:
                dt_w, dt_h = desktop_sizes[0]
                self.width = min(self.width, dt_w - 50)
                self.height = min(self.height, dt_h - 100)
        except AttributeError:
            pass
        
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        
        self.width, self.height = self.screen.get_size()
        
        max_cell_w = self.width // self.board.cols
        max_cell_h = (self.height - TOP_BAR_HEIGHT) // self.board.rows
        self.cell_size = min(max_cell_w, max_cell_h, 60)
        
        if self.cell_size > CELL_SIZE:
            self.cell_size = CELL_SIZE
        
        board_w = self.board.cols * self.cell_size
        board_h = self.board.rows * self.cell_size
        
        self.board_offset_x = (self.width - board_w) // 2
        self.board_offset_y = TOP_BAR_HEIGHT + (self.height - TOP_BAR_HEIGHT - board_h) // 2
        
        self.reset_btn = Button(self.width // 2 - 40, 25, 80, 30, "Reset", font_small)
        
        self.theme_dropdown.rect.x = self.width - 110
        self.theme_dropdown.rect.y = 25
        self.dropdown.rect.y = 25
        
        self.popup_rect.center = (self.width // 2, self.height // 2)
        self.input_cols.rect.x = self.popup_rect.x + 160
        self.input_cols.rect.y = self.popup_rect.y + 60
        self.input_rows.rect.x = self.popup_rect.x + 160
        self.input_rows.rect.y = self.popup_rect.y + 120
        self.apply_btn.rect.x = self.popup_rect.x + 30
        self.apply_btn.rect.y = self.popup_rect.y + 190
        self.cancel_btn.rect.x = self.popup_rect.x + 170
        self.cancel_btn.rect.y = self.popup_rect.y + 190

    def calculate_custom_mines(self, cols, rows):
        tiles = cols * rows
        mines = math.floor(tiles * (0.12 + 0.00018 * tiles))
        max_mines = max(1, tiles - 9)
        mines = min(mines, max_mines)
        mines = max(1, mines)
        return mines

    def apply_custom_settings(self):
        try:
            cols = int(self.input_cols.text)
        except ValueError:
            cols = DIFFICULTIES["Custom"]["cols"]
            
        try:
            rows = int(self.input_rows.text)
        except ValueError:
            rows = DIFFICULTIES["Custom"]["rows"]
            
        cols = max(MIN_CUSTOM_COLS, min(cols, MAX_CUSTOM_COLS))
        rows = max(MIN_CUSTOM_ROWS, min(rows, MAX_CUSTOM_ROWS))
        
        mines = self.calculate_custom_mines(cols, rows)
        
        DIFFICULTIES["Custom"]["cols"] = cols
        DIFFICULTIES["Custom"]["rows"] = rows
        DIFFICULTIES["Custom"]["mines"] = mines
        
        self.input_cols.text = str(cols)
        self.input_rows.text = str(rows)

    def reset_game(self, diff_changed=False):
        settings = DIFFICULTIES[self.difficulty_name]
        self.board = Board(settings["cols"], settings["rows"], settings["mines"])
        self.start_timer = 0.0
        self.end_time = 0.0
        self.best_time = None
        
        self.theme_name = random.choice(list(THEMES.keys()))
        self.theme = THEMES[self.theme_name]
        
        themes_list = list(THEMES.keys())
        self.theme_dropdown.selected_idx = themes_list.index(self.theme_name)
        
        if diff_changed:
            self.width = max(self.board.cols * CELL_SIZE, MIN_WIDTH)
            self.height = self.board.rows * CELL_SIZE + TOP_BAR_HEIGHT
            self.update_screen_size()

    def get_time_elapsed(self):
        if self.board.first_click:
            return 0.0
        if self.board.game_over:
            return float(self.end_time)
        return time.time() - self.start_timer

    def draw_board(self, mouse_pos):
        theme = self.theme
        current_time = pygame.time.get_ticks()
        
        for y in range(self.board.rows):
            for x in range(self.board.cols):
                rectx = self.board_offset_x + x * self.cell_size
                recty = self.board_offset_y + y * self.cell_size
                rect = pygame.Rect(rectx, recty, self.cell_size, self.cell_size)
                
                if not self.board.revealed[y][x]:
                    base_color = theme["hidden"]
                    if not self.board.game_over and rect.collidepoint(mouse_pos) and not self.board.flagged[y][x]:
                        base_color = theme["hover"]
                        
                    pygame.draw.rect(self.screen, base_color, rect)
                    pygame.draw.line(self.screen, theme["highlight"], rect.topleft, rect.topright, 2)
                    pygame.draw.line(self.screen, theme["highlight"], rect.topleft, rect.bottomleft, 2)
                    pygame.draw.line(self.screen, theme["shadow"], rect.bottomleft, rect.bottomright, 2)
                    pygame.draw.line(self.screen, theme["shadow"], rect.topright, rect.bottomright, 2)
                    
                    if self.board.flagged[y][x]:
                        anim_time = current_time - self.board.flag_times[y][x]
                        anim_progress = min(1.0, anim_time / 75.0)
                        
                        scale = self.cell_size / 30.0
                        if anim_progress < 1.0:
                            scale = scale * (1.2 - abs(anim_progress - 0.5) * 0.4) 
                            
                        flag_color = RED
                        cx, cy = rect.centerx, rect.centery
                        
                        pygame.draw.polygon(self.screen, flag_color, [
                            (cx - 2*scale, cy + 5*scale), 
                            (cx - 2*scale, cy - 8*scale), 
                            (cx + 8*scale, cy - 2*scale)
                        ])
                        pygame.draw.line(self.screen, BLACK, (cx - 2*scale, cy - 8*scale), (cx - 2*scale, cy + 10*scale), int(max(1, 2*scale)))
                        
                    if self.board.game_over and not self.board.won and self.board.grid[y][x] == -1 and not self.board.flagged[y][x]:
                        pygame.draw.rect(self.screen, theme["revealed"], rect)
                        pygame.draw.rect(self.screen, theme["grid"], rect, 1)
                        anim_time = current_time - self.end_time * 1000 
                        radius = min(self.cell_size // 4, max(4, int(self.cell_size // 4 * min(1.0, (current_time % 1000)/150.0))))
                        pygame.draw.circle(self.screen, BLACK, rect.center, radius)
                        
                    if self.board.game_over and not self.board.won and self.board.flagged[y][x] and self.board.grid[y][x] != -1:
                        pygame.draw.line(self.screen, RED, rect.topleft, rect.bottomright, 3)
                        pygame.draw.line(self.screen, RED, rect.topright, rect.bottomleft, 3)
                        
                else:
                    pygame.draw.rect(self.screen, theme["revealed"], rect)
                    pygame.draw.rect(self.screen, theme["grid"], rect, 1)
                    
                    time_since_reveal = current_time - self.board.reveal_times[y][x]
                    anim_scale = min(1.0, time_since_reveal / 100.0) 
                    
                    if self.board.grid[y][x] == -1:
                        pygame.draw.rect(self.screen, RED, rect)
                        pygame.draw.circle(self.screen, BLACK, rect.center, int((self.cell_size // 4) * anim_scale))
                    elif self.board.grid[y][x] > 0:
                        val = self.board.grid[y][x]
                        color = NUM_COLORS.get(val, BLACK)
                        font_size = int(self.cell_size * 0.5 * (0.5 + 0.5 * anim_scale))
                        if font_size > 5: 
                            font = pygame.font.Font(font_path, font_size)
                            text = font.render(str(val), False, color)
                            text_rect = text.get_rect(center=rect.center)
                            self.screen.blit(text, text_rect)

    def draw_ui(self):
        theme = self.theme
        pygame.draw.rect(self.screen, theme["bg"], (0, 0, self.screen.get_width(), TOP_BAR_HEIGHT))
        
        self.reset_btn.draw(self.screen, theme)
        
        flags_left = self.board.num_mines - self.board.flags_placed
        flag_text = font_title.render(f"{flags_left:03d}", False, RED)
        
        time_elapsed = self.get_time_elapsed()
        if self.board.game_over and not self.board.first_click:
            time_str = f"{time_elapsed:.1f}"
            time_text = font_large.render(time_str, False, RED)
        else:
            time_str = f"{int(time_elapsed):03d}"
            time_text = font_title.render(time_str, False, RED)
        
        flag_bg = pygame.Rect(self.screen.get_width() // 2 - 140, 25, 70, 40)
        time_bg = pygame.Rect(self.screen.get_width() // 2 + 70, 25, 70, 40)
        
        pygame.draw.rect(self.screen, BLACK, flag_bg, border_radius=6)
        pygame.draw.rect(self.screen, theme["shadow"], flag_bg, width=2, border_radius=6)
        
        pygame.draw.rect(self.screen, BLACK, time_bg, border_radius=6)
        pygame.draw.rect(self.screen, theme["shadow"], time_bg, width=2, border_radius=6)
        
        self.screen.blit(flag_text, flag_text.get_rect(center=flag_bg.center))
        self.screen.blit(time_text, time_text.get_rect(center=time_bg.center))
        
        lbl_diff = font_small.render("Difficulty", False, BLACK)
        self.screen.blit(lbl_diff, lbl_diff.get_rect(centerx=self.dropdown.rect.centerx, y=5))
        
        lbl_theme = font_small.render("Theme", False, BLACK)
        self.screen.blit(lbl_theme, lbl_theme.get_rect(centerx=self.theme_dropdown.rect.centerx, y=5))
        
        lbl_flags = font_small.render("Flags", False, BLACK)
        self.screen.blit(lbl_flags, lbl_flags.get_rect(centerx=flag_bg.centerx, y=5))
        
        lbl_time = font_small.render("Time", False, BLACK)
        self.screen.blit(lbl_time, lbl_time.get_rect(centerx=time_bg.centerx, y=5))
        
        if self.board.game_over:
            board_center_y = self.board_offset_y + (self.board.rows * self.cell_size) // 2
            
            if self.board.won:
                title_msg = "YOU WIN!"
                title_color = (0, 128, 0) 
                
                if self.difficulty_name != "Custom" and self.best_time is not None:
                    if self.end_time <= self.best_time:
                        title_msg = "NEW RECORD!"
                        title_color = (255, 215, 0) 
                        
                    lines = [
                        (title_msg, font_large, title_color),
                        (f"Time: {self.end_time:.1f}s", font_medium, BLACK),
                        (f"Best: {self.best_time:.1f}s", font_medium, BLACK)
                    ]
                else:
                    lines = [
                        (title_msg, font_large, title_color),
                        (f"Time: {self.end_time:.1f}s", font_medium, BLACK)
                    ]
            else:
                lines = [
                    ("GAME OVER!", font_large, RED)
                ]
                
            total_h = 0
            max_w = 0
            rendered_lines = []
            for text, font, color in lines:
                surf = font.render(text, False, color)
                rendered_lines.append(surf)
                max_w = max(max_w, surf.get_width())
                total_h += surf.get_height() + 10
            
            total_h -= 10
            
            bg_rect = pygame.Rect(0, 0, max_w + 40, total_h + 30)
            bg_rect.center = (self.screen.get_width() // 2, board_center_y)
            
            pygame.draw.rect(self.screen, theme["bg"], bg_rect, border_radius=8)
            pygame.draw.rect(self.screen, BLACK, bg_rect, 3, border_radius=8)
            
            current_y = bg_rect.y + 15
            for surf in rendered_lines:
                s_rect = surf.get_rect(centerx=bg_rect.centerx, y=current_y)
                self.screen.blit(surf, s_rect)
                current_y += surf.get_height() + 10

        if self.custom_popup_open:
            overlay = pygame.Surface((self.width, self.height))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0,0))
            
            pygame.draw.rect(self.screen, theme["bg"], self.popup_rect)
            pygame.draw.rect(self.screen, BLACK, self.popup_rect, 3)
            
            title = font_large.render("Custom Difficulty", False, BLACK)
            self.screen.blit(title, (self.popup_rect.centerx - title.get_width()//2, self.popup_rect.y + 15))
            
            lbl_w = font_medium.render(f"Cols ({MIN_CUSTOM_COLS}-{MAX_CUSTOM_COLS}):", False, BLACK)
            lbl_h = font_medium.render(f"Rows ({MIN_CUSTOM_ROWS}-{MAX_CUSTOM_ROWS}):", False, BLACK)
            
            self.screen.blit(lbl_w, (self.popup_rect.x + 20, self.popup_rect.y + 65))
            self.screen.blit(lbl_h, (self.popup_rect.x + 20, self.popup_rect.y + 125))
            
            self.input_cols.draw(self.screen, theme)
            self.input_rows.draw(self.screen, theme)
            self.apply_btn.draw(self.screen, theme)
            self.cancel_btn.draw(self.screen, theme)
            
            try:
                c = int(self.input_cols.text)
                r = int(self.input_rows.text)
                preview_mines = self.calculate_custom_mines(c, r)
            except ValueError:
                preview_mines = "?"
            mines_lbl = font_small.render(f"Calculated Mines: {preview_mines}", False, BLACK)
            self.screen.blit(mines_lbl, (self.popup_rect.centerx - mines_lbl.get_width()//2, self.popup_rect.y + 160))

        if not self.custom_popup_open:
            self.dropdown.draw(self.screen, theme)
            self.theme_dropdown.draw(self.screen, theme)

    def run(self):
        clock = pygame.time.Clock()
        running = True
        
        while running:
            self.screen.fill(self.theme["bg"])
            mouse_pos = pygame.mouse.get_pos()
            
            if self.custom_popup_open:
                self.apply_btn.check_hover(mouse_pos)
                self.cancel_btn.check_hover(mouse_pos)
            else:
                self.reset_btn.check_hover(mouse_pos)
            
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                if event.type == pygame.VIDEORESIZE:
                    self.width = event.w
                    self.height = event.h
                    self.update_screen_size()
                
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r and not self.custom_popup_open:
                    self.reset_game()

                if self.custom_popup_open:
                    self.input_cols.handle_event(event)
                    self.input_rows.handle_event(event)
                    
                    if self.apply_btn.is_clicked(event):
                        self.apply_custom_settings()
                        self.custom_popup_open = False
                        self.reset_game(diff_changed=True)
                        continue
                        
                    if self.cancel_btn.is_clicked(event):
                        self.custom_popup_open = False
                        if self.difficulty_name == "Custom":
                            pass 
                        continue
                        
                    continue

                if not self.dropdown.is_open and not self.theme_dropdown.is_open and self.reset_btn.is_clicked(event):
                    self.reset_game()
                    continue

                if self.theme_dropdown.handle_event(event):
                    new_theme = self.theme_dropdown.get_selected()
                    if new_theme != self.theme_name:
                        self.theme_name = new_theme
                        self.theme = THEMES[self.theme_name]
                    continue

                if self.dropdown.handle_event(event):
                    new_diff = self.dropdown.get_selected()
                    if new_diff != self.difficulty_name:
                        self.difficulty_name = new_diff
                        if new_diff == "Custom":
                            self.custom_popup_open = True
                        else:
                            self.reset_game(diff_changed=True)
                    continue
                
                if not self.dropdown.is_open and not self.theme_dropdown.is_open and event.type == pygame.MOUSEBUTTONDOWN and not self.board.game_over:
                    x, y = event.pos
                    if y >= self.board_offset_y and x >= self.board_offset_x:
                        grid_x = (x - self.board_offset_x) // self.cell_size
                        grid_y = (y - self.board_offset_y) // self.cell_size
                        
                        if 0 <= grid_x < self.board.cols and 0 <= grid_y < self.board.rows:
                            if event.button == 1:
                                if self.board.first_click:
                                    self.start_timer = time.time()
                                self.board.reveal(grid_x, grid_y)
                                if self.board.game_over and self.end_time == 0.0:
                                    self.end_time = time.time() - self.start_timer
                                    if self.board.won and self.difficulty_name != "Custom":
                                        self.best_time = self.db.update_time(self.difficulty_name, self.end_time)
                            elif event.button == 3:
                                self.board.toggle_flag(grid_x, grid_y)

                elif self.board.game_over and event.type == pygame.MOUSEBUTTONDOWN and not self.dropdown.is_open and not self.theme_dropdown.is_open:
                    x, y = event.pos
                    if y >= self.board_offset_y:
                        self.reset_game()

            self.draw_board(mouse_pos)
            self.draw_ui()
            
            pygame.display.flip()
            clock.tick(FPS)
            
        pygame.quit()
        sys.exit()

if __name__ == "__main__":
    game = Game()
    game.run()
