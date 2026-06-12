import pygame
import pyautogui
import sys
import subprocess

pygame.init()
screen_width, screen_height = pyautogui.size()
screen_width = screen_width - screen_width // 3
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Home")
clock = pygame.time.Clock()

bg_screen = pygame.image.load(r'C:\Users\pprit\Desktop\Internship June 2026\image\Background\BG1.png')
bg_screen = pygame.transform.scale(bg_screen, (screen_width, screen_height))

# ==========================================
# Specify the file path to link to each button.
# ==========================================
START_FILE   = r'C:\Users\pprit\Desktop\Internship June 2026\Game\Game_main.py'
#SETTING_FILE = r'C:\Users\pprit\Desktop\Internship June 2026\Game\Game_setting.py'
SCORE_FILE   = r'C:\Users\pprit\Desktop\Internship June 2026\Game\Game_score.py'
EXIT_FILE    = None


def button_home():
    name_path = r'C:\Users\pprit\Desktop\Internship June 2026\image\Home Game\name_game.png'
    other_paths = [
        r'C:\Users\pprit\Desktop\Internship June 2026\image\Home Game\start_button.png',
        r'C:\Users\pprit\Desktop\Internship June 2026\image\Home Game\score_button.png',
        r'C:\Users\pprit\Desktop\Internship June 2026\image\Home Game\quit_button.png',
    ]

    name_img = pygame.image.load(name_path)
    orig_w = name_img.get_width()
    orig_h = name_img.get_height()
    name_img = pygame.transform.scale(name_img, (orig_w // 4, orig_h // 4))

    other_images = []
    for p in other_paths:
        img = pygame.image.load(p)
        orig_w = img.get_width()
        orig_h = img.get_height()
        img = pygame.transform.scale(img, (int(orig_w // 4.5), int(orig_h / 4.5)))
        other_images.append(img)

    return name_img, other_images


def compute_button_rects(other_images):
    lane_height = screen_height // 3
    x_center = screen_width // 2

    y_top_lane2 = lane_height
    spacing_y = 30
    current_y = y_top_lane2

    rects = []
    for img in other_images:
        img_w = img.get_width()
        img_h = img.get_height()

        blit_x = x_center - img_w // 2
        blit_y = current_y

        rects.append(pygame.Rect(blit_x, blit_y, img_w, img_h))
        current_y += img_h + spacing_y

    return rects


def draw_home_screen(surface, name_img, other_images, button_rects):
    surface.blit(bg_screen, (0, 0))

    lane_height = screen_height // 3
    x_center = screen_width // 2

    name_w = name_img.get_width()
    name_h = name_img.get_height()
    y_center_lane1 = lane_height // 2
    surface.blit(name_img, (x_center - name_w // 2, y_center_lane1 - name_h // 2))

    for img, rect in zip(other_images, button_rects):
        surface.blit(img, (rect.x, rect.y))


# ==========================================
# Enter-Name Screen
# ==========================================
font_title = pygame.font.SysFont(None, 60)
font_input = pygame.font.SysFont(None, 48)
font_hint  = pygame.font.SysFont(None, 28)

MAX_NAME_LENGTH = 12


def draw_enter_name_screen(surface, player_name, input_box):
    surface.blit(bg_screen, (0, 0))

    # Title
    title_surf = font_title.render("Enter your name", True, (255, 255, 255))
    surface.blit(title_surf, (screen_width // 2 - title_surf.get_width() // 2,
                               screen_height // 3 - 80))

    # Input box
    pygame.draw.rect(surface, (255, 255, 255), input_box, border_radius=8)
    pygame.draw.rect(surface, (0, 0, 0), input_box, 3, border_radius=8)

    # Text inside box
    text_surf = font_input.render(player_name, True, (0, 0, 0))
    surface.blit(text_surf, (input_box.x + 15, input_box.y + (input_box.height - text_surf.get_height()) // 2))

    # Hint
    hint_surf = font_hint.render("Press ENTER to start  |  ESC to go back", True, (220, 220, 220))
    surface.blit(hint_surf, (screen_width // 2 - hint_surf.get_width() // 2,
                              input_box.y + input_box.height + 20))


# Load images all at once.
name_image, other_buttons = button_home()
button_rects = compute_button_rects(other_buttons)

start_rect = button_rects[0]
score_rect = button_rects[1]
exit_rect  = button_rects[2]

# Input box rect for enter-name screen
input_box = pygame.Rect(0, 0, 400, 60)
input_box.center = (screen_width // 2, screen_height // 3)


def open_file(path, args=None):
    cmd = [sys.executable, path]
    if args:
        cmd += args
    subprocess.Popen(cmd)
    pygame.quit()
    sys.exit()


# ==========================================
# Main Loop
# ==========================================
state = "home"          # "home" or "enter_name"
player_name = ""

running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        # ---------------- HOME STATE ----------------
        if state == "home":
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                if start_rect.collidepoint(event.pos):
                    state = "enter_name"
                    player_name = ""

                elif score_rect.collidepoint(event.pos):
                    open_file(SCORE_FILE)

                elif exit_rect.collidepoint(event.pos):
                    pygame.quit()
                    sys.exit()

        # ---------------- ENTER NAME STATE ----------------
        elif state == "enter_name":
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if player_name.strip() != "":
                        open_file(START_FILE, [player_name])

                elif event.key == pygame.K_BACKSPACE:
                    player_name = player_name[:-1]

                elif event.key == pygame.K_ESCAPE:
                    state = "home"

                else:
                    if len(player_name) < MAX_NAME_LENGTH and event.unicode.isprintable():
                        player_name += event.unicode

    # ---------------- DRAW ----------------
    if state == "home":
        draw_home_screen(screen, name_image, other_buttons, button_rects)
    elif state == "enter_name":
        draw_enter_name_screen(screen, player_name, input_box)

    pygame.display.flip()
    clock.tick(60)