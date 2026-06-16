import pygame
import json
import os

# ==========================================
# Path
# ==========================================
SCORE_FILE = r'C:\Users\pprit\Desktop\Internship June 2026\Game\scores.json'

# ==========================================
# Module-level state is received from shared (set in init)
# ==========================================
_screen_width = None
_screen_height = None
_bg = None

font_title = None
font_header = None
font_row = None
font_hint = None
font_button = None

# Layout (Calculated only once in init because it depends only on screen_width/height)
BOARD_W = 700
ROW_HEIGHT = 42
TOP10_HEIGHT = ROW_HEIGHT * 10
SCROLL_HEIGHT = 200
SCROLL_SPEED = 30

BOARD_X = None
TITLE_Y = None
TOP10_TOP = None
REST_TITLE_Y = None
SCROLL_TOP = None
SCROLL_BOTTOM = None
clear_button_rect = None
HINT_Y = None

# Leaderboard data (reloads each time this page is accessed. See enter_score())
all_scores = []
top10 = []
rest = []
scroll_offset = 0
confirm_delete = False

# ==========================================
# Helper: Load/clear scores from file.
# ==========================================
def load_scores():
    if not os.path.exists(SCORE_FILE):
        return []
    try:
        with open(SCORE_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except (json.JSONDecodeError, ValueError):
        return []

    data.sort(key=lambda item: item.get("score", 0), reverse=True)
    return data


def clear_scores():
    with open(SCORE_FILE, 'w', encoding='utf-8') as f:
        json.dump([], f, ensure_ascii=False, indent=2)


def get_max_scroll():
    content_height = len(rest) * ROW_HEIGHT
    return max(0, content_height - SCROLL_HEIGHT)

# ==========================================
# Helper: Draw each row in the table.
# ==========================================
def draw_row(surface, rank, item, y, highlight=False):
    name = item.get("name", "Unknown")
    score_val = item.get("score", 0)

    bg_color = (255, 215, 0, 60) if (rank <= 3 and not highlight) else (255, 255, 255, 30)

    row_surface = pygame.Surface((BOARD_W, ROW_HEIGHT - 4), pygame.SRCALPHA)
    row_surface.fill(bg_color)
    surface.blit(row_surface, (BOARD_X, y))

    rank_color = (255, 215, 0) if rank == 1 else \
                 (192, 192, 192) if rank == 2 else \
                 (205, 127, 50) if rank == 3 else \
                 (255, 255, 255)

    rank_text = font_row.render(f"#{rank}", True, rank_color)
    name_text = font_row.render(name, True, (255, 255, 255))
    score_text = font_row.render(str(score_val), True, (255, 255, 255))

    surface.blit(rank_text, (BOARD_X + 15, y + 4))
    surface.blit(name_text, (BOARD_X + 100, y + 4))
    surface.blit(score_text, (BOARD_X + BOARD_W - score_text.get_width() - 20, y + 4))
    
# ==========================================
# Helper: Draw the entire leaderboard.
# ==========================================
def draw_score_screen(surface):
    surface.blit(_bg, (0, 0))

    dark_overlay = pygame.Surface((_screen_width, _screen_height), pygame.SRCALPHA)
    dark_overlay.fill((0, 0, 0, 140)) 
    surface.blit(dark_overlay, (0, 0))

    title_text = font_title.render("LEADERBOARD", True, (255, 255, 255))
    surface.blit(title_text, (_screen_width // 2 - title_text.get_width() // 2, TITLE_Y))

    board_rect = pygame.Rect(BOARD_X - 10, TOP10_TOP - 10, BOARD_W + 20, TOP10_HEIGHT + 20)
    board_surface = pygame.Surface((board_rect.width, board_rect.height), pygame.SRCALPHA)
    board_surface.fill((0, 0, 0, 120))
    surface.blit(board_surface, (board_rect.x, board_rect.y))
    pygame.draw.rect(surface, (255, 255, 255), board_rect, 2, border_radius=8)

    if len(top10) == 0:
        empty_text = font_header.render("No scores yet", True, (200, 200, 200))
        surface.blit(empty_text, (_screen_width // 2 - empty_text.get_width() // 2, TOP10_TOP + 20))
    else:
        for i, item in enumerate(top10):
            y = TOP10_TOP + i * ROW_HEIGHT
            draw_row(surface, i + 1, item, y)

    if len(rest) > 0:
        rest_title = font_header.render("Other Ranks (scroll with mouse wheel)", True, (220, 220, 220))
        surface.blit(rest_title, (BOARD_X, REST_TITLE_Y))

        clip_rect = pygame.Rect(BOARD_X - 10, SCROLL_TOP, BOARD_W + 20, SCROLL_HEIGHT)
        surface.set_clip(clip_rect)

        for i, item in enumerate(rest):
            rank = i + 11
            y = SCROLL_TOP + i * ROW_HEIGHT - scroll_offset
            if y + ROW_HEIGHT < SCROLL_TOP or y > SCROLL_BOTTOM:
                continue
            draw_row(surface, rank, item, y, highlight=True)

        surface.set_clip(None)
        pygame.draw.rect(surface, (255, 255, 255), clip_rect, 2, border_radius=8)

    pygame.draw.rect(surface, (180, 40, 40), clear_button_rect, border_radius=8)
    pygame.draw.rect(surface, (255, 255, 255), clear_button_rect, 2, border_radius=8)
    clear_text = font_button.render("Clear Scores", True, (255, 255, 255))
    surface.blit(clear_text, (clear_button_rect.centerx - clear_text.get_width() // 2,
                               clear_button_rect.centery - clear_text.get_height() // 2))

    hint_text = font_hint.render("Press ESC to go back to Home", True, (150, 150, 150))
    surface.blit(hint_text, (_screen_width // 2 - hint_text.get_width() // 2, HINT_Y))

def draw_confirm_dialog(surface):
    overlay = pygame.Surface((_screen_width, _screen_height), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 160))
    surface.blit(overlay, (0, 0))

    box_w, box_h = 460, 180
    box_rect = pygame.Rect(0, 0, box_w, box_h)
    box_rect.center = (_screen_width // 2, _screen_height // 2)

    pygame.draw.rect(surface, (40, 40, 40), box_rect, border_radius=10)
    pygame.draw.rect(surface, (255, 255, 255), box_rect, 2, border_radius=10)

    msg1 = font_header.render("Clear all scores?", True, (255, 255, 255))
    msg2 = font_hint.render("Press Y to confirm  /  N or ESC to cancel", True, (220, 220, 220))

    surface.blit(msg1, (box_rect.centerx - msg1.get_width() // 2, box_rect.y + 35))
    surface.blit(msg2, (box_rect.centerx - msg2.get_width() // 2, box_rect.y + 100))

# ==========================================
# Helper: Access this page — data reloads every time.
# ==========================================
def enter_score():
    global all_scores, top10, rest, scroll_offset, confirm_delete
    all_scores = load_scores()
    top10 = all_scores[:10]
    rest = all_scores[10:]
    scroll_offset = 0
    confirm_delete = False

# ==========================================
# Init — Called once at program startup.
# ==========================================
def init(shared):
    global _screen_width, _screen_height, _bg
    global font_title, font_header, font_row, font_hint, font_button
    global BOARD_X, TITLE_Y, TOP10_TOP, REST_TITLE_Y
    global SCROLL_TOP, SCROLL_BOTTOM, clear_button_rect, HINT_Y

    _screen_width = shared["screen_width"]
    _screen_height = shared["screen_height"]
    _bg = shared["bg"]

    font_title = pygame.font.SysFont(None, 64)
    font_header = pygame.font.SysFont(None, 36)
    font_row = pygame.font.SysFont(None, 32)
    font_hint = pygame.font.SysFont(None, 26)
    font_button = pygame.font.SysFont(None, 30)

    BOARD_X = _screen_width // 2 - BOARD_W // 2

    GAP_TITLE_TO_BOARD = 20
    GAP_BOARD_TO_REST = 30
    GAP_RESTTITLE_TO_LIST = 10
    GAP_LIST_TO_BUTTON = 20
    GAP_BUTTON_TO_HINT = 10

    TITLE_HEIGHT = 64
    RESTTITLE_HEIGHT = 36
    BUTTON_HEIGHT = 50
    HINT_HEIGHT = 26

    total_height = (
        TITLE_HEIGHT + GAP_TITLE_TO_BOARD +
        (TOP10_HEIGHT + 20) + GAP_BOARD_TO_REST +
        RESTTITLE_HEIGHT + GAP_RESTTITLE_TO_LIST +
        SCROLL_HEIGHT + GAP_LIST_TO_BUTTON +
        BUTTON_HEIGHT + GAP_BUTTON_TO_HINT +
        HINT_HEIGHT
    )

    start_y = max(10, (_screen_height - total_height) // 2)

    TITLE_Y = start_y
    TOP10_TOP = TITLE_Y + TITLE_HEIGHT + GAP_TITLE_TO_BOARD
    REST_TITLE_Y = TOP10_TOP + TOP10_HEIGHT + 20 + GAP_BOARD_TO_REST
    SCROLL_TOP = REST_TITLE_Y + RESTTITLE_HEIGHT + GAP_RESTTITLE_TO_LIST
    SCROLL_BOTTOM = SCROLL_TOP + SCROLL_HEIGHT
    button_y = SCROLL_BOTTOM + GAP_LIST_TO_BUTTON
    HINT_Y = button_y + BUTTON_HEIGHT + GAP_BUTTON_TO_HINT

    clear_button_rect = pygame.Rect(0, button_y, 200, BUTTON_HEIGHT)
    clear_button_rect.centerx = _screen_width // 2

# ==========================================
# Handle_event
# ==========================================
def handle_event(event, context):
    global confirm_delete, all_scores, top10, rest, scroll_offset

    if event.type == pygame.KEYDOWN:
        if confirm_delete:
            if event.key == pygame.K_y:
                clear_scores()
                all_scores = []
                top10 = []
                rest = []
                scroll_offset = 0
                confirm_delete = False
            elif event.key in (pygame.K_n, pygame.K_ESCAPE):
                confirm_delete = False
        else:
            if event.key == pygame.K_ESCAPE:
                return "home", context

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        if not confirm_delete:
            if clear_button_rect.collidepoint(event.pos):
                confirm_delete = True

    elif event.type == pygame.MOUSEWHEEL:
        if not confirm_delete:
            scroll_offset -= event.y * SCROLL_SPEED
            scroll_offset = max(0, min(scroll_offset, get_max_scroll()))

    return None, context

# ==========================================
# Update
# ==========================================
def update():
    pass

# ==========================================
# Draw
# ==========================================
def draw(screen):
    draw_score_screen(screen)
    if confirm_delete:
        draw_confirm_dialog(screen)