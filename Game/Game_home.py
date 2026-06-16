import pygame

# ==========================================
# Constants
# ==========================================
MAX_NAME_LENGTH = 12

HOME_IMG_DIR = r'C:\Users\pprit\Desktop\Internship June 2026\image\Home Game'
NAME_IMG_PATH = HOME_IMG_DIR + r'\name_game.png'
START_BTN_PATH = HOME_IMG_DIR + r'\start_button.png'
#SETTING_BTN_PATH = HOME_IMG_DIR + r'\setting_button.png'
SCORE_BTN_PATH = HOME_IMG_DIR + r'\score_button.png'
QUIT_BTN_PATH = HOME_IMG_DIR + r'\quit_button.png'

# ==========================================
# Module-level state (replaces the original global variable)
# ==========================================
_screen_width = None
_screen_height = None
_bg = None

# Assets loaded once in init()
name_image = None
other_buttons = None    # List of button images [start, score, quit]
button_rects = None     # The list of pygame.Rect matches other_buttons
start_rect = None
#setting_rect = None
score_rect = None
exit_rect = None

input_box = None    # pygame.Rect for the enter name field
font_title = None
font_input = None
font_hint = None

# Sub-states within this file: "home" or "enter_name"
_sub_state = 'home'
_player_name = ''

# ==========================================
# Helper functions (moved from the original Game_home.py)
# ==========================================
def load_home_assets():
    global name_image, other_buttons, button_rects

    raw_name = pygame.image.load(NAME_IMG_PATH).convert_alpha()
    name_image = pygame.transform.scale(raw_name, (500, 150)) 
    
    raw_buttons = [
        pygame.image.load(START_BTN_PATH).convert_alpha(),
        pygame.image.load(SCORE_BTN_PATH).convert_alpha(),
        pygame.image.load(QUIT_BTN_PATH).convert_alpha(),
    ]
    
    other_buttons = []
    for img in raw_buttons:
        scaled_btn = pygame.transform.scale(img, (300, 90))
        other_buttons.append(scaled_btn)

    button_rects = [img.get_rect() for img in other_buttons]

    return name_image, other_buttons, button_rects

def computer_button_rects(images, screen_width, screen_height):
    center_x = screen_width // 2
    current_y = screen_height // 3  # Starting point y
    spacing_y = 30

    rects = []
    for img in images:
        img_w = img.get_width()
        img_h = img.get_height()

        blit_x = center_x - img_w // 2
        blit_y = current_y

        rects.append(pygame.Rect(blit_x, blit_y, img_w, img_h))
        current_y += img_h + spacing_y

    return rects

def draw_home_screen(screen):
    # Always draw the background first (overwriting the old background completely on the screen).
    screen.blit(_bg, (0, 0))

    # Draw name_image — it needs to be centered horizontally and in the "top lane" (the very top of the screen, above the buttons).
    name_w = name_image.get_width()
    name_h = name_image.get_height()

    x = _screen_width // 2 - name_w // 2
    y = 150

    screen.blit(name_image, (x, y))

    # Draw all the buttons in the positions calculated in button_rects.
    for img, rect in zip(other_buttons, button_rects):
        screen.blit(img, rect)

def draw_enter_name_screen(screen):
    screen.blit(_bg, (0,0))

    # Title — render and center horizontally, above input_box.
    title_surf = font_title.render('Enter your name', True, (255, 255, 255))
    screen.blit(title_surf, (_screen_width // 2 - title_surf.get_width() // 2, input_box.y - 65))

    # Input box — white background, black border.
    pygame.draw.rect(screen, (255, 255, 255), input_box, border_radius=8)
    pygame.draw.rect(screen, (0, 0, 0), input_box, 3, border_radius=8)

    # The typed text — render it in black and then blit it into a box (center vertically).
    text_surf = font_input.render(_player_name, True, (0, 0, 0))
    screen.blit(text_surf, (input_box.x + 15, input_box.y + (input_box.height - text_surf.get_height()) // 2))

    # Hint — Located below the input box.
    hint_surf = font_hint.render('Press ENTER to start | ESC to go back', True, (255, 255, 255))
    screen.blit(hint_surf, (_screen_width // 2 - hint_surf.get_width() // 2, input_box.y + input_box.height + 25))

# ==========================================
# Init — Called once at program startup
# ==========================================
def init(shared):
    global _screen_width, _screen_height, _bg
    global name_image, other_buttons, button_rects
    global start_rect, score_rect, exit_rect, input_box
    global font_title, font_input, font_hint

    _screen_width = shared['screen_width']
    _screen_height = shared['screen_height']
    _bg = shared['bg']

    font_title = pygame.font.SysFont(None, 60)
    font_input = pygame.font.SysFont(None, 48)
    font_hint = pygame.font.SysFont(None, 28)
    
    box_w, box_h = 400, 50

    box_x = (_screen_width - box_w) // 2
    box_y = (_screen_height - box_h) // 2

    name_image, other_buttons, button_rects = load_home_assets()
    button_rects = computer_button_rects(other_buttons, _screen_width, _screen_height)
    start_rect, score_rect, exit_rect = button_rects
    
    input_box = pygame.Rect(box_x, box_y, box_w, box_h)
    input_box.center = (_screen_width // 2, _screen_height // 2)

# ==========================================
# Handle_event — Receives events one by one from the app loop
# ==========================================
def handle_event(event, context):
    global _sub_state, _player_name

    if _sub_state == 'home':
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if start_rect.collidepoint(event.pos):
                _sub_state = 'enter_name'
                _player_name = ''
            elif score_rect.collidepoint(event.pos):
                return 'score', context
            elif exit_rect.collidepoint(event.pos):
                return 'quit', context
            
    elif _sub_state == 'enter_name':
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                if _player_name.strip() != '':
                    context['player_name'] = _player_name
                    return 'play', context
            elif event.key == pygame.K_BACKSPACE:
                _player_name = _player_name[:-1]
            elif event.key == pygame.K_ESCAPE:
                _sub_state = 'home'
            else:
                if len(_player_name) < MAX_NAME_LENGTH and event.unicode.isprintable():
                    _player_name += event.unicode
    
    return None, context

# ==========================================
# Update — Update logic every frame (This page may not require any action)
# ==========================================
def update():
    pass

# ==========================================
# Draw — Draw the screen based on the current sub_state
# ==========================================
def draw(screen):
    if _sub_state == 'home':
        draw_home_screen(screen)
    elif _sub_state == 'enter_name':
        draw_enter_name_screen(screen)

def enter_home():
    global _sub_state, _player_name
    _sub_state = 'home'
    _player_name = ''