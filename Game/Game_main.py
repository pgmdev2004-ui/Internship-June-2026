import cv2 as cv
import pyautogui
import mediapipe as mp
import numpy as np
import time
import random
import pygame
import sys
import json
import os
from datetime import datetime

# ==========================================
# Initialize
# ==========================================
mp_pose = mp.solutions.pose

# รับชื่อผู้เล่นที่ส่งมาจากหน้า Home (ผ่าน command-line argument)
PLAYER_NAME = sys.argv[1] if len(sys.argv) > 1 else "Player"

# ไฟล์เก็บคะแนน (หน้า Score จะมาอ่านไฟล์นี้)
SCORE_FILE = r'C:\Users\pprit\Desktop\Internship June 2026\Game\scores.json'


def save_score(name, score):
    """บันทึกคะแนนของผู้เล่นลงไฟล์ JSON (เก็บเป็น list ต่อท้ายเรื่อยๆ)"""
    scores = []
    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, 'r', encoding='utf-8') as f:
                scores = json.load(f)
        except (json.JSONDecodeError, ValueError):
            scores = []

    scores.append({
        "name": name,
        "score": score,
        "date": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    })

    with open(SCORE_FILE, 'w', encoding='utf-8') as f:
        json.dump(scores, f, ensure_ascii=False, indent=2)


# ==========================================
# Function: Draw Stick Figure (on a pygame Surface)
# ==========================================
def draw_stick_figure(surface, landmarks, w, h):
    def to_pixel(lm):
        return (int(lm.x * w), int(lm.y * h))

    left_shoulder  = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    left_elbow     = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
    right_elbow    = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
    left_wrist     = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_wrist    = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_hip       = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip      = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    left_knee      = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee     = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    left_ankle     = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
    right_ankle    = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]

    color, thickness = (255, 100, 0), 24

    shoulder_width = abs(left_shoulder.x - right_shoulder.x) * w
    head_radius    = max(1, int(shoulder_width * 0.4))

    neck_x = (left_shoulder.x + right_shoulder.x) / 2
    neck_y = (left_shoulder.y + right_shoulder.y) / 2
    hip_cx = (left_hip.x + right_hip.x) / 2
    hip_cy = (left_hip.y + right_hip.y) / 2

    neck_pixel  = (int(neck_x * w), int(neck_y * h))
    hip_pixel   = (int(hip_cx * w), int(hip_cy * h))
    head_center = (int(neck_x * w), int(neck_y * h - head_radius - thickness))

    pygame.draw.line(surface, color, neck_pixel, hip_pixel, thickness)
    pygame.draw.line(surface, color, neck_pixel, to_pixel(left_elbow), thickness)
    pygame.draw.line(surface, color, to_pixel(left_elbow), to_pixel(left_wrist), thickness)
    pygame.draw.line(surface, color, neck_pixel, to_pixel(right_elbow), thickness)
    pygame.draw.line(surface, color, to_pixel(right_elbow), to_pixel(right_wrist), thickness)
    pygame.draw.line(surface, color, hip_pixel, to_pixel(left_knee), thickness)
    pygame.draw.line(surface, color, to_pixel(left_knee), to_pixel(left_ankle), thickness)
    pygame.draw.line(surface, color, hip_pixel, to_pixel(right_knee), thickness)
    pygame.draw.line(surface, color, to_pixel(right_knee), to_pixel(right_ankle), thickness)
    pygame.draw.circle(surface, color, head_center, head_radius, thickness)


# ==========================================
# Function: Get Body Center Position
# ==========================================
def get_body_center(landmarks, frame_w, frame_h):
    left_hip  = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    center_x  = (left_hip.x + right_hip.x) / 2
    center_y  = (left_hip.y + right_hip.y) / 2
    return int(center_x * frame_w), int(center_y * frame_h)


# ==========================================
# Function: Draw Lane System (on a pygame Surface)
# ==========================================
def draw_lane_system(surface, width, height, hit_line, dead_line):
    lane_width = width // 4

    for i in range(1, 4):
        x = i * lane_width
        pygame.draw.line(surface, (232, 232, 232), (x, 0), (x, height), 2)

    pygame.draw.line(surface, (169, 169, 169), (0, hit_line), (width, hit_line), 2)

    return lane_width


# ==========================================
# Classes
# ==========================================
class Notes:
    def __init__(self, lane, x, y, speed, lane_width, game_height):
        self.lane        = lane
        self.x           = x
        self.y           = y
        self.speed       = speed
        self.lane_width  = lane_width
        self.game_height = game_height
        self.active      = True
        self.scored      = False
        self.hit         = False

    def move(self, dt, speed_bonus=0):
        self.y += (self.speed + speed_bonus) * dt
        if self.y > self.game_height:
            self.active = False

    def draw(self, surface):
        if self.active:
            color = (28, 28, 28)
            alpha = 80 if self.hit else 255

            note_surface = pygame.Surface((self.lane_width, self.lane_width), pygame.SRCALPHA)
            note_surface.fill((color[0], color[1], color[2], alpha))

            surface.blit(note_surface, (self.x, int(self.y)))


class Player:
    def __init__(self, lane_width, hit_line):
        self.lane_width = lane_width
        self.lane       = 0
        self.y          = hit_line
        self.x          = self.lane_width // 2
        self.size       = 20

        # --- เพิ่ม: smoothing + hysteresis ---
        self.smoothed_cx        = None
        self.smooth_alpha       = 0.25   # 0-1, ยิ่งน้อยยิ่งนิ่งแต่หน่วงมากขึ้น
        self.pending_lane       = 0
        self.pending_count      = 0
        self.lane_switch_frames = 4      # ต้องอยู่ lane ใหม่ติดกันกี่เฟรมก่อนเปลี่ยนจริง

    def update_from_pose(self, cx, game_width):
        # --- Exponential smoothing ลดอาการสั่นของตำแหน่งตัว ---
        if self.smoothed_cx is None:
            self.smoothed_cx = cx
        else:
            self.smoothed_cx = (self.smooth_alpha * cx
                                 + (1 - self.smooth_alpha) * self.smoothed_cx)

        raw_lane = int(self.smoothed_cx // self.lane_width)
        raw_lane = max(0, min(3, raw_lane))

        # --- Hysteresis: เปลี่ยน lane เมื่ออยู่ lane ใหม่ติดต่อกันถึงเกณฑ์ ---
        if raw_lane == self.pending_lane:
            self.pending_count += 1
        else:
            self.pending_lane  = raw_lane
            self.pending_count = 1

        if self.pending_count >= self.lane_switch_frames and raw_lane != self.lane:
            self.lane = raw_lane

        self.x = self.lane * self.lane_width + self.lane_width // 2

    def get_lane(self):
        return self.lane

    def draw(self, surface):
        pygame.draw.circle(surface, (0, 255, 0), (self.x, self.y), self.size)
        pygame.draw.circle(surface, (0, 200, 0), (self.x, self.y), self.size, 2)


class Score:
    def __init__(self, font, font_name):
        self.value     = 0
        self.font      = font
        self.font_name = font_name

    def add_points(self, points):
        self.value += points

    def draw(self, surface, player_name):
        name_text = self.font_name.render(f"Player: {player_name}", True, (255, 255, 255))
        surface.blit(name_text, (20, 10))

        score_text = self.font.render(f"Score: {self.value}", True, (255, 255, 255))
        surface.blit(score_text, (20, 10 + name_text.get_height() + 5))


class Game:
    def __init__(self, font_score, font_big, font_med, font_small, font_name, player_name):
        screen_width, screen_height = pyautogui.size()
        self.width      = screen_width - screen_width // 3
        self.height     = screen_height
        self.running    = True
        self.game_over  = False
        self.lane_width = self.width // 4
        self.hit_line   = self.height - self.height // 4
        self.dead_line  = self.hit_line + 100

        self.score  = Score(font_score, font_name)
        self.player = Player(self.lane_width, self.hit_line)
        self.notes  = []

        self.player_name = player_name
        self.score_saved = False   # ป้องกันบันทึกซ้ำหลาย frame

        self.last_time      = time.time()
        self.spawn_timer    = 0.0
        self.next_spawn_gap = 1.0

        self.font_big   = font_big
        self.font_med   = font_med
        self.font_small = font_small

        self.game_time         = 0.0
        self.speed_per_second  = 5.0
        self.max_speed_bonus   = 300.0

    def reset(self):
        """รีเซ็ตสถานะเกมทั้งหมดเพื่อเริ่มเล่นใหม่"""
        self.game_over   = False
        self.score.value = 0
        self.notes        = []
        self.score_saved  = False

        self.player.lane = 0
        self.player.x    = self.player.lane_width // 2

        self.last_time      = time.time()
        self.spawn_timer    = 0.0
        self.next_spawn_gap = 1.0

        self.game_time = 0.0

    def get_delta_time(self):
        now            = time.time()
        dt             = now - self.last_time
        self.last_time = now
        return dt

    def spawn_note(self):
        if len(self.notes) > 0:
            return
        lane  = random.randint(0, 3)
        x     = lane * self.lane_width
        y     = -self.lane_width

        speed_bonus = min(self.game_time * self.speed_per_second, self.max_speed_bonus)
        speed = random.uniform(150, 250) + speed_bonus

        note  = Notes(lane, x, y, speed, self.lane_width, self.height)
        self.notes.append(note)

    def update(self, dt):
        if self.game_over:
            return

        self.game_time += dt

        self.spawn_timer += dt
        if self.spawn_timer >= self.next_spawn_gap:
            self.spawn_note()
            self.spawn_timer    = 0.0
            self.next_spawn_gap = random.uniform(1.5, 2.5)

        for note in self.notes:
            note.move(dt, speed_bonus=min(self.game_time * self.speed_per_second, self.max_speed_bonus))

        player_lane = self.player.get_lane()

        for note in self.notes:
            if not note.active:
                continue

            if not note.scored and note.lane == player_lane:
                if note.y + note.lane_width >= self.hit_line:
                    note.scored = True
                    note.hit    = True
                    self.score.add_points(1)

            if not note.scored and note.y + note.lane_width >= self.dead_line:
                self.game_over = True

        self.notes = [n for n in self.notes if n.active]

        # --- บันทึกคะแนนทันทีที่เกม Over (บันทึกครั้งเดียว) ---
        if self.game_over and not self.score_saved:
            save_score(self.player_name, self.score.value)
            self.score_saved = True

    def render(self, surface, background):
        surface.blit(background, (0, 0))

        draw_lane_system(surface, self.width, self.height, self.hit_line, self.dead_line)

        for note in self.notes:
            note.draw(surface)

        self.player.draw(surface)
        self.score.draw(surface, self.player_name)

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 128))
            surface.blit(overlay, (0, 0))

            text1 = self.font_big.render("GAME OVER", True, (255, 0, 0))
            surface.blit(text1, (self.width // 2 - text1.get_width() // 2,
                                  self.height // 2 - 60))

            text2 = self.font_med.render(f"Final Score: {self.score.value}", True, (255, 255, 255))
            surface.blit(text2, (self.width // 2 - text2.get_width() // 2,
                                  self.height // 2 + 10))

            text3 = self.font_small.render("Press Q to quit or R to restart", True, (200, 200, 200))
            surface.blit(text3, (self.width // 2 - text3.get_width() // 2,
                                  self.height // 2 + 60))


# ==========================================
# Main Game Loop
# ==========================================
if __name__ == "__main__":
    pygame.init()

    font_score = pygame.font.SysFont(None, 36)
    font_big   = pygame.font.SysFont(None, 72)
    font_med   = pygame.font.SysFont(None, 36)
    font_small = pygame.font.SysFont(None, 28)
    font_name  = pygame.font.SysFont(None, 30)

    game = Game(font_score, font_big, font_med, font_small, font_name, PLAYER_NAME)

    screen = pygame.display.set_mode((game.width, game.height))
    pygame.display.set_caption("Game Window")
    clock = pygame.time.Clock()

    bg_path        = r'C:\Users\pprit\Desktop\Internship June 2026\image\Background\BG1.png'
    background_src = pygame.image.load(bg_path)
    background     = pygame.transform.scale(background_src, (game.width, game.height))

    cap = cv.VideoCapture(0)

    # --- ตั้งค่ากล้องให้คงที่ ลด lag/กระตุก ---
    cap.set(cv.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv.CAP_PROP_FPS, 30)

    PIP_W, PIP_H = 240, 180

    with mp_pose.Pose(
        min_detection_confidence=0.6,
        min_tracking_confidence=0.6,
        model_complexity=1,        # 0=เร็วแต่หยาบ, 1=กลาง (แนะนำ), 2=แม่นแต่หนัก
        smooth_landmarks=True       # MediaPipe จะ smooth landmark ภายในให้เอง
    ) as pose:
        while game.running:
            dt = game.get_delta_time()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    game.running = False
                elif event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_q:
                        game.running = False
                    elif event.key == pygame.K_r:
                        if game.game_over:
                            game.reset()

            ret, frame = cap.read()
            if not ret:
                break

            mirror_frame = cv.flip(frame, 1)
            h, w, _      = mirror_frame.shape

            image   = cv.cvtColor(mirror_frame, cv.COLOR_BGR2RGB)
            results = pose.process(image)

            stick_surface = pygame.Surface((w, h))
            stick_surface.fill((255, 255, 255))

            if results.pose_landmarks:
                landmarks = results.pose_landmarks.landmark
                draw_stick_figure(stick_surface, landmarks, w, h)
                cx, cy = get_body_center(landmarks, game.width, game.height)
                game.player.update_from_pose(cx, game.width)

            scaled_hit  = int(game.hit_line * h / game.height)
            scaled_dead = int(game.dead_line * h / game.height)
            draw_lane_system(stick_surface, w, h, scaled_hit, scaled_dead)

            game.update(dt)
            game.render(screen, background)

            pip_surface = pygame.transform.scale(stick_surface, (PIP_W, PIP_H))
            pip_x = game.width - PIP_W - 10
            pip_y = 10
            screen.blit(pip_surface, (pip_x, pip_y))
            pygame.draw.rect(screen, (255, 255, 255), (pip_x, pip_y, PIP_W, PIP_H), 2)

            pygame.display.flip()
            clock.tick(60)

    cap.release()
    pygame.quit()
    sys.exit()