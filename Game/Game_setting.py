"""
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
# กำหนด path ไฟล์ที่จะเชื่อมไปแต่ละปุ่ม
# ==========================================
START_FILE   = r'C:\Users\pprit\Desktop\Internship June 2026\game.py'
SETTING_FILE = r'C:\Users\pprit\Desktop\Internship June 2026\setting.py'
SCORE_FILE   = r'C:\Users\pprit\Desktop\Internship June 2026\score.py'
EXIT_FILE    = r'C:\Users\pprit\Desktop\Internship June 2026\exit.py'  # ถ้าไม่ใช้ ปล่อย None ได้


def button_home():
    name_path = r'C:\Users\pprit\Desktop\Internship June 2026\image\Home Game\name_game.png'
    other_paths = [
        r'C:\Users\pprit\Desktop\Internship June 2026\image\Home Game\start_game.png',
        r'C:\Users\pprit\Desktop\Internship June 2026\image\Home Game\setting_game.png',
        r'C:\Users\pprit\Desktop\Internship June 2026\image\Home Game\score_game.png',
        r'C:\Users\pprit\Desktop\Internship June 2026\image\Home Game\exis_game.png',
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
        img = pygame.transform.scale(img, (int(orig_w / 1.5), int(orig_h / 1.5)))
        other_images.append(img)

    return name_img, other_images


def compute_button_rects(other_images):
    #คำนวณตำแหน่ง rect ของแต่ละปุ่ม (ไม่วาด) ใช้สำหรับเช็คคลิกและวาดให้ตรงกัน
    lane_height = screen_height // 3
    x_center = screen_width // 2

    y_top_lane2 = lane_height  # ขอบบนของ lane 2
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

    # --- Lane 1: name_game (กึ่งกลาง lane 1) ---
    name_w = name_img.get_width()
    name_h = name_img.get_height()
    y_center_lane1 = lane_height // 2
    surface.blit(name_img, (x_center - name_w // 2, y_center_lane1 - name_h // 2))

    # --- Lane 2-3: ปุ่มที่เหลือ ---
    for img, rect in zip(other_images, button_rects):
        surface.blit(img, (rect.x, rect.y))


# โหลดรูปครั้งเดียว
name_image, other_buttons = button_home()
button_rects = compute_button_rects(other_buttons)

# ลำดับตรงกับ other_paths: [start, setting, score, exis]
start_rect   = button_rects[0]
setting_rect = button_rects[1]
score_rect   = button_rects[2]
exit_rect    = button_rects[3]


def open_file(path):
    #เปิดไฟล์ python อื่นด้วย subprocess แล้วปิดหน้าต่าง Home ปัจจุบัน
    subprocess.Popen([sys.executable, path])
    pygame.quit()
    sys.exit()


running = True
while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            pygame.quit()
            sys.exit()

        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            if start_rect.collidepoint(event.pos):
                open_file(r'C:\Users\pprit\Desktop\Internship June 2026\Game\Game_main.py')

            elif setting_rect.collidepoint(event.pos):
                open_file(SETTING_FILE)

            elif score_rect.collidepoint(event.pos):
                open_file(SCORE_FILE)

            elif exit_rect.collidepoint(event.pos):
                if EXIT_FILE:
                    pygame.quit()
                    sys.exit()

    draw_home_screen(screen, name_image, other_buttons, button_rects)

    pygame.display.flip()
    clock.tick(60)
"""