import pygame
import random
import time
import sys
import math
from constants import *

# Initialize Pygame
pygame.init()
pygame.display.set_caption("Minesweeper")

# Fonts
try:
    font_small = pygame.font.SysFont("arial", 16)
    font_medium = pygame.font.SysFont("arial", 20, bold=True)
    font_large = pygame.font.SysFont("arial", 24, bold=True)
    font_title = pygame.font.SysFont("arial", 28, bold=True)
except Exception:
    font_small = pygame.font.Font(None, 20)
    font_medium = pygame.font.Font(None, 24)
    font_large = pygame.font.Font(None, 28)
    font_title = pygame.font.Font(None, 32)

class Button:
    def __init__(self, x, y, width, height, text, font):
        self.rect = pygame.Rect(x, y, width, height)
        self.text = text
        self.font = font
        self.is_hovered = False
        
    def draw(self, screen, theme):
        color = theme["revealed"] if self.is_hovered else theme["hidden"]
        pygame.draw.rect(screen, color, self.rect)
        
        # 3D Effect
        pygame.draw.line(screen, theme["highlight"], self.rect.topleft, self.rect.topright, 2)
        pygame.draw.line(screen, theme["highlight"], self.rect.topleft, self.rect.bottomleft, 2)
        pygame.draw.line(screen, theme["shadow"], self.rect.bottomleft, self.rect.bottomright, 2)
        pygame.draw.line(screen, theme["shadow"], self.rect.topright, self.rect.bottomright, 2)
        
        text_surf = self.font.render(self.text, True, BLACK)
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

    def draw(self, screen):
        # Draw main box
        pygame.draw.rect(screen, WHITE, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        
        text = font_small.render(self.options[self.selected_idx], True, BLACK)
        text_rect = text.get_rect(center=self.rect.center)
        screen.blit(text, text_rect)

        # Draw dropdown options
        if self.is_open:
            self.option_rects = []
            for i, option in enumerate(self.options):
                opt_rect = pygame.Rect(self.rect.x, self.rect.y + (i + 1) * self.rect.height, self.rect.width, self.rect.height)
                self.option_rects.append(opt_rect)
                pygame.draw.rect(screen, WHITE, opt_rect)
                pygame.draw.rect(screen, BLACK, opt_rect, 1)
                
                opt_text = font_small.render(option, True, BLACK)
                opt_text_rect = opt_text.get_rect(center=opt_rect.center)
                screen.blit(opt_text, opt_text_rect)

    def handle_event(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if self.is_open:
                for i, rect in enumerate(self.option_rects):
                    if rect.collidepoint(event.pos):
                        self.selected_idx = i
                        self.is_open = False
                        return True # Selection changed
                
                # Clicked outside options
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
                # Limit length to 3 chars
                if len(self.text) < 3:
                    self.text += event.unicode
                    
    def draw(self, screen, theme):
        # Optional: slight background change when active instead of just white
        color = theme["highlight"] if self.active else WHITE
        pygame.draw.rect(screen, color, self.rect)
        pygame.draw.rect(screen, BLACK, self.rect, 2)
        txt_surf = self.font.render(self.text, True, BLACK)
        text_rect = txt_surf.get_rect(midleft=(self.rect.x + 5, self.rect.centery))
        screen.blit(txt_surf, text_rect)
        
        # Blinking cursor
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

    def generate_mines(self, safe_x, safe_y):
        safe_zone = set()
        for dy in [-1, 0, 1]:
            for dx in [-1, 0, 1]:
                nx, ny = safe_x + dx, safe_y + dy
                if 0 <= nx < self.cols and 0 <= ny < self.rows:
                    safe_zone.add((nx, ny))

        available_spots = [(x, y) for y in range(self.rows) for x in range(self.cols) if (x, y) not in safe_zone]
        
        # Fallback if too few available spots
        if len(available_spots) < self.num_mines:
            available_spots = [(x, y) for y in range(self.rows) for x in range(self.cols) if (x, y) != (safe_x, safe_y)]
            
        self.mines = random.sample(available_spots, min(self.num_mines, len(available_spots)))
        
        for x, y in self.mines:
            self.grid[y][x] = -1 # -1 represents a mine
            
        # Calc numbers for adjacent mines
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

        if self.grid[y][x] == -1:
            self.game_over = True
            return

        # Flood fill empty space
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
        
        self.start_timer = 0.0
        self.end_time = 0.0
        
        difficulties_list = list(DIFFICULTIES.keys())
        self.dropdown = Dropdown(10, 25, 120, 30, difficulties_list, difficulties_list.index(self.difficulty_name))
        
        themes_list = list(THEMES.keys())
        self.theme_dropdown = Dropdown(0, 25, 100, 30, themes_list, themes_list.index(self.theme_name))
        
        self.width = max(self.board.cols * CELL_SIZE, MIN_WIDTH)
        self.height = self.board.rows * CELL_SIZE + TOP_BAR_HEIGHT
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        
        # Custom popup state
        self.custom_popup_open = False
        
        # Init text inputs for custom popup
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
        # Enforce minimum width
        self.width = max(self.width, MIN_WIDTH)
        self.height = max(self.height, TOP_BAR_HEIGHT + 100)
        
        # Enforce maximum dimensions relative to the actual desktop resolution
        try:
            desktop_sizes = pygame.display.get_desktop_sizes()
            if desktop_sizes:
                dt_w, dt_h = desktop_sizes[0]
                self.width = min(self.width, dt_w - 50)
                self.height = min(self.height, dt_h - 100)
        except AttributeError:
            # Fallback for older pygame version
            pass
        
        self.screen = pygame.display.set_mode((self.width, self.height), pygame.RESIZABLE)
        
        # Retrieve actual exact window size given by the OS
        self.width, self.height = self.screen.get_size()
        
        # Calculate cell size and offsets
        max_cell_w = self.width // self.board.cols
        max_cell_h = (self.height - TOP_BAR_HEIGHT) // self.board.rows
        self.cell_size = min(max_cell_w, max_cell_h, 60) # Cap max cell size at 60
        
        # If the window isn't bound by desktop limits, let's keep cell size exactly CELL_SIZE (30) when possible
        # so windows don't arbitrarily stretch tiles immediately on generation
        if self.cell_size > CELL_SIZE:
            self.cell_size = CELL_SIZE
        
        board_w = self.board.cols * self.cell_size
        board_h = self.board.rows * self.cell_size
        
        self.board_offset_x = (self.width - board_w) // 2
        self.board_offset_y = TOP_BAR_HEIGHT + (self.height - TOP_BAR_HEIGHT - board_h) // 2
        
        # Center the reset button
        self.reset_btn = Button(self.width // 2 - 40, 25, 80, 30, "Reset", font_small)
        
        # Right align theme dropdown
        self.theme_dropdown.rect.x = self.width - 110
        self.theme_dropdown.rect.y = 25
        self.dropdown.rect.y = 25
        
        # Update popup elements positions
        self.popup_rect.center = (self.width // 2, self.height // 2)
        # Position inputs relative to popup
        self.input_cols.rect.x = self.popup_rect.x + 160
        self.input_cols.rect.y = self.popup_rect.y + 60
        self.input_rows.rect.x = self.popup_rect.x + 160
        self.input_rows.rect.y = self.popup_rect.y + 120
        # Position buttons
        self.apply_btn.rect.x = self.popup_rect.x + 30
        self.apply_btn.rect.y = self.popup_rect.y + 190
        self.cancel_btn.rect.x = self.popup_rect.x + 170
        self.cancel_btn.rect.y = self.popup_rect.y + 190

    def calculate_custom_mines(self, cols, rows):
        tiles = cols * rows
        # requested formula: mines = floor(tiles * (0.12 + 0.00018 * tiles))
        mines = math.floor(tiles * (0.12 + 0.00018 * tiles))
        # Add guardbands so we don't have too few or too many mines
        # Specifically ensuring a 3x3 gap is possible (at least 9 tiles empty)
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
            
        # Clamp to min/max
        cols = max(MIN_CUSTOM_COLS, min(cols, MAX_CUSTOM_COLS))
        rows = max(MIN_CUSTOM_ROWS, min(rows, MAX_CUSTOM_ROWS))
        
        mines = self.calculate_custom_mines(cols, rows)
        
        DIFFICULTIES["Custom"]["cols"] = cols
        DIFFICULTIES["Custom"]["rows"] = rows
        DIFFICULTIES["Custom"]["mines"] = mines
        
        # Reflect clamping in inputs
        self.input_cols.text = str(cols)
        self.input_rows.text = str(rows)

    def reset_game(self, diff_changed=False):
        settings = DIFFICULTIES[self.difficulty_name]
        self.board = Board(settings["cols"], settings["rows"], settings["mines"])
        self.start_timer = 0.0
        self.end_time = 0.0
        
        # Randomize theme on reset/new game UNLESS explicitly changing difficulty 
        # Actually prompt says: randomize when launched, new diff selected, or new game started
        self.theme_name = random.choice(list(THEMES.keys()))
        self.theme = THEMES[self.theme_name]
        
        # Keep dropdowns in sync
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
        for y in range(self.board.rows):
            for x in range(self.board.cols):
                rectx = self.board_offset_x + x * self.cell_size
                recty = self.board_offset_y + y * self.cell_size
                rect = pygame.Rect(rectx, recty, self.cell_size, self.cell_size)
                
                if not self.board.revealed[y][x]:
                    # Hover effect
                    base_color = theme["hidden"]
                    if not self.board.game_over and rect.collidepoint(mouse_pos) and not self.board.flagged[y][x]:
                        base_color = theme["hover"]
                        
                    pygame.draw.rect(self.screen, base_color, rect)
                    # 3D edge effect
                    pygame.draw.line(self.screen, theme["highlight"], rect.topleft, rect.topright, 2)
                    pygame.draw.line(self.screen, theme["highlight"], rect.topleft, rect.bottomleft, 2)
                    pygame.draw.line(self.screen, theme["shadow"], rect.bottomleft, rect.bottomright, 2)
                    pygame.draw.line(self.screen, theme["shadow"], rect.topright, rect.bottomright, 2)
                    
                    if self.board.flagged[y][x]:
                        # Draw flag proportional to cell_size
                        flag_color = RED
                        cx, cy = rect.centerx, rect.centery
                        s = self.cell_size / 30.0 # scale factor relative to base 30
                        
                        pygame.draw.polygon(self.screen, flag_color, [
                            (cx - 2*s, cy + 5*s), 
                            (cx - 2*s, cy - 8*s), 
                            (cx + 8*s, cy - 2*s)
                        ])
                        pygame.draw.line(self.screen, BLACK, (cx - 2*s, cy - 8*s), (cx - 2*s, cy + 10*s), int(max(1, 2*s)))
                        
                    # Reveal all unflagged mines at end
                    if self.board.game_over and not self.board.won and self.board.grid[y][x] == -1 and not self.board.flagged[y][x]:
                        pygame.draw.rect(self.screen, theme["revealed"], rect)
                        pygame.draw.rect(self.screen, theme["grid"], rect, 1)
                        pygame.draw.circle(self.screen, BLACK, rect.center, self.cell_size // 4)
                        
                    # Draw crossed out wrong flags at end
                    if self.board.game_over and not self.board.won and self.board.flagged[y][x] and self.board.grid[y][x] != -1:
                        pygame.draw.line(self.screen, RED, rect.topleft, rect.bottomright, 3)
                        pygame.draw.line(self.screen, RED, rect.topright, rect.bottomleft, 3)
                        
                else:
                    # Draw revealed clear tile
                    pygame.draw.rect(self.screen, theme["revealed"], rect)
                    pygame.draw.rect(self.screen, theme["grid"], rect, 1)
                    
                    if self.board.grid[y][x] == -1:
                        # Draw exploded mine
                        pygame.draw.rect(self.screen, RED, rect)
                        pygame.draw.circle(self.screen, BLACK, rect.center, self.cell_size // 4)
                    elif self.board.grid[y][x] > 0:
                        # Draw number
                        val = self.board.grid[y][x]
                        color = NUM_COLORS.get(val, BLACK)
                        # Scale font size slightly
                        font = pygame.font.SysFont("arial", int(self.cell_size * 0.7), bold=True)
                        text = font.render(str(val), True, color)
                        text_rect = text.get_rect(center=rect.center)
                        self.screen.blit(text, text_rect)

    def draw_ui(self):
        theme = self.theme
        # Draw top bar background
        pygame.draw.rect(self.screen, theme["bg"], (0, 0, self.screen.get_width(), TOP_BAR_HEIGHT))
        
        # UI Elements
        self.reset_btn.draw(self.screen, theme)
        
        # Flags Counter
        flags_left = self.board.num_mines - self.board.flags_placed
        flag_text = font_title.render(f"{flags_left:03d}", True, RED)
        
        # Timer
        time_elapsed = self.get_time_elapsed()
        if self.board.game_over and not self.board.first_click:
            time_str = f"{time_elapsed:.1f}"
        else:
            time_str = f"{int(time_elapsed):03d}"
        time_text = font_title.render(time_str, True, RED)
        
        # Positioning for flags and timer
        # Counters on a slightly dark background for the LED look
        flag_bg = pygame.Rect(self.screen.get_width() // 2 - 140, 25, 70, 40)
        time_bg = pygame.Rect(self.screen.get_width() // 2 + 70, 25, 70, 40)
        
        pygame.draw.rect(self.screen, BLACK, flag_bg)
        pygame.draw.rect(self.screen, BLACK, time_bg)
        
        self.screen.blit(flag_text, flag_text.get_rect(center=flag_bg.center))
        self.screen.blit(time_text, time_text.get_rect(center=time_bg.center))
        
        # Draw Labels
        lbl_diff = font_small.render("Difficulty", True, BLACK)
        self.screen.blit(lbl_diff, lbl_diff.get_rect(centerx=self.dropdown.rect.centerx, y=5))
        
        lbl_theme = font_small.render("Theme", True, BLACK)
        self.screen.blit(lbl_theme, lbl_theme.get_rect(centerx=self.theme_dropdown.rect.centerx, y=5))
        
        lbl_flags = font_small.render("Flags", True, BLACK)
        self.screen.blit(lbl_flags, lbl_flags.get_rect(centerx=flag_bg.centerx, y=5))
        
        lbl_time = font_small.render("Time", True, BLACK)
        self.screen.blit(lbl_time, lbl_time.get_rect(centerx=time_bg.centerx, y=5))
        
        # Draw Game Over Text Overlay (Optional visual cue)
        if self.board.game_over:
            msg = "YOU WIN!" if self.board.won else "GAME OVER!"
            color = (0, 128, 0) if self.board.won else RED
            text = font_large.render(msg, True, color)
            text_rect = text.get_rect(center=(self.screen.get_width() // 2, TOP_BAR_HEIGHT // 2))
            
            # Since topbar is busy, let's draw it in center of the board
            board_center_y = self.board_offset_y + (self.board.rows * self.cell_size) // 2
            text_rect.centery = board_center_y
            
            bg_rect = pygame.Rect(0, 0, text_rect.width + 20, text_rect.height + 10)
            bg_rect.center = text_rect.center
            
            pygame.draw.rect(self.screen, WHITE, bg_rect)
            pygame.draw.rect(self.screen, BLACK, bg_rect, 2)
            self.screen.blit(text, text_rect)

        # Draw custom popup over everything else if open
        if self.custom_popup_open:
            # Draw overlay
            overlay = pygame.Surface((self.width, self.height))
            overlay.set_alpha(128)
            overlay.fill((0, 0, 0))
            self.screen.blit(overlay, (0,0))
            
            # Draw popup background
            pygame.draw.rect(self.screen, theme["bg"], self.popup_rect)
            pygame.draw.rect(self.screen, BLACK, self.popup_rect, 3)
            
            # Draw popup title
            title = font_large.render("Custom Difficulty", True, BLACK)
            self.screen.blit(title, (self.popup_rect.centerx - title.get_width()//2, self.popup_rect.y + 15))
            
            # Draw labels with limits
            lbl_w = font_medium.render(f"Cols ({MIN_CUSTOM_COLS}-{MAX_CUSTOM_COLS}):", True, BLACK)
            lbl_h = font_medium.render(f"Rows ({MIN_CUSTOM_ROWS}-{MAX_CUSTOM_ROWS}):", True, BLACK)
            
            self.screen.blit(lbl_w, (self.popup_rect.x + 20, self.popup_rect.y + 65))
            self.screen.blit(lbl_h, (self.popup_rect.x + 20, self.popup_rect.y + 125))
            
            # Draw inputs and buttons
            self.input_cols.draw(self.screen, theme)
            self.input_rows.draw(self.screen, theme)
            self.apply_btn.draw(self.screen, theme)
            self.cancel_btn.draw(self.screen, theme)
            
            # Info text for mines
            try:
                c = int(self.input_cols.text)
                r = int(self.input_rows.text)
                preview_mines = self.calculate_custom_mines(c, r)
            except ValueError:
                preview_mines = "?"
            mines_lbl = font_small.render(f"Calculated Mines: {preview_mines}", True, BLACK)
            self.screen.blit(mines_lbl, (self.popup_rect.centerx - mines_lbl.get_width()//2, self.popup_rect.y + 160))

        # Draw dropdowns last so they overlap the board if open
        # Draw difficulty then theme to stack correctly depending on open order,
        # but generally they shouldn't overlap each other
        if not self.custom_popup_open:
            self.dropdown.draw(self.screen)
            self.theme_dropdown.draw(self.screen)

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
                
                # Check keyboard reset
                if event.type == pygame.KEYDOWN and event.key == pygame.K_r and not self.custom_popup_open:
                    self.reset_game()

                # Handle Popup events
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
                        # Revert difficulty to previous if it was just selected
                        if self.difficulty_name == "Custom":
                            # We'll just stay on custom with previous settings
                            pass 
                        continue
                        
                    # Skip rest of event handling while popup is open
                    continue

                # Handle top UI clicks
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
                            # Don't reset game until they hit Apply
                        else:
                            self.reset_game(diff_changed=True)
                    continue
                
                # Handle board clicks
                if not self.dropdown.is_open and not self.theme_dropdown.is_open and event.type == pygame.MOUSEBUTTONDOWN and not self.board.game_over:
                    x, y = event.pos
                    if y >= self.board_offset_y and x >= self.board_offset_x:
                        grid_x = (x - self.board_offset_x) // self.cell_size
                        grid_y = (y - self.board_offset_y) // self.cell_size
                        
                        if 0 <= grid_x < self.board.cols and 0 <= grid_y < self.board.rows:
                            if event.button == 1: # Left click (Reveal)
                                if self.board.first_click:
                                    self.start_timer = time.time()
                                self.board.reveal(grid_x, grid_y)
                                if self.board.game_over and self.end_time == 0.0:
                                    self.end_time = time.time() - self.start_timer
                            elif event.button == 3: # Right click (Flag)
                                self.board.toggle_flag(grid_x, grid_y)

                # Reset fast by clicking when game is over
                elif self.board.game_over and event.type == pygame.MOUSEBUTTONDOWN and not self.dropdown.is_open and not self.theme_dropdown.is_open:
                    # Give a small grace period to avoid accidental resets on multi-click
                    x, y = event.pos
                    if y >= self.board_offset_y:
                        # Allow restart from click on board on game over
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
