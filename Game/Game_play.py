import pygame
import time
import random
from datetime import datetime
import json
import os

import cv2 as cv 
import mediapipe as mp 

# ==========================================
# Constants
# ==========================================
GAME_DIR = r'C:\Users\pprit\Desktop\Internship June 2026\Game'
SCORE_FILE = os.path.join(GAME_DIR, 'scores.json')

PIP_W, PIP_H = 240,180  # Webcam preview frame size (top right corner)

mp_pose = mp.solutions.pose

# ==========================================
# Module-level state
# ==========================================
_screen_width = None
_screen_height = None
_bg = None

_cap = None     # cv.VideoCapture — received from app, do not cap = cv.VideoCapture(0) duplicate
_pose = None    # mp_pose.Pose instance — received from app

font_score = None
font_big = None
font_med = None
font_small = None
font_name = None

game = None     # An instance of the game is recreated every time it starts playing.

# ==========================================
# Helper: Save scores to scores.json
# ==========================================
def save_score(name, score_value):
    scores_list = []

    if os.path.exists(SCORE_FILE):
        try:
            with open(SCORE_FILE, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    scores_list = data
        except (json.JSONDecodeError, IOError):
            # If the file is corrupted or there is no read permission, ignore it (scores_list will be an empty list []).
            pass
    
    current_time = datetime.now().strftime('%Y-%m-%d %H:%M')
    new_entry = {
        'name': name,
        'score': score_value,
        'date': current_time
    }
    scores_list.append(new_entry)

    try:
        with open(SCORE_FILE, 'w', encoding='utf-8') as f:
            json.dump(scores_list, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f'Error saving score to file: {e}')

# ==========================================
# Helper functions related to pose/drawing (moved from the original Game_main.py)
# ==========================================
def draw_stick_figure(surface, landmarks, w, h):
    def to_pixel(lm):
        return (int(lm.x * w), int(lm.y * h))
    
    # Drag all the necessary landmarks (left to right).
    left_shoulder = landmarks[mp_pose.PoseLandmark.LEFT_SHOULDER]
    right_shoulder = landmarks[mp_pose.PoseLandmark.RIGHT_SHOULDER]
    left_elbow = landmarks[mp_pose.PoseLandmark.LEFT_ELBOW]
    right_elbow = landmarks[mp_pose.PoseLandmark.RIGHT_ELBOW]
    left_wrist = landmarks[mp_pose.PoseLandmark.LEFT_WRIST]
    right_wrist = landmarks[mp_pose.PoseLandmark.RIGHT_WRIST]
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    left_knee = landmarks[mp_pose.PoseLandmark.LEFT_KNEE]
    right_knee = landmarks[mp_pose.PoseLandmark.RIGHT_KNEE]
    left_ankle = landmarks[mp_pose.PoseLandmark.LEFT_ANKLE]
    right_ankle = landmarks[mp_pose.PoseLandmark.RIGHT_ANKLE]

    color, thickness = (255, 100, 0), 16

    # Calculate the midpoint of the neck (average of the left and right shoulders) and the hip.
    neck_x = (left_shoulder.x + right_shoulder.x) / 2
    neck_y = (left_shoulder.y + right_shoulder.y) / 2
    neck_pixel = (int(neck_x * w), int(neck_y * h))

    hip_cx = (left_hip.x + right_hip.x) / 2
    hip_cy = (left_hip.y + right_hip.y) / 2
    hip_pixel = (int(hip_cx * w), int(hip_cy * h))

    # Calculate the head position (above the neck, based on shoulder size).
    shoulder_width = abs(left_shoulder.x - right_shoulder.x) * w
    head_radius = max(1, int(shoulder_width * 0.4))
    head_center = (neck_pixel[0], int(neck_y * h - head_radius - thickness // 2))

    # Draw connecting lines for the outline.
    pygame.draw.line(surface, color, neck_pixel, hip_pixel, thickness)
    pygame.draw.line(surface, color, neck_pixel, to_pixel(left_elbow), thickness)
    pygame.draw.line(surface, color, to_pixel(left_elbow), to_pixel(left_wrist), thickness)
    pygame.draw.line(surface, color, neck_pixel, to_pixel(right_elbow), thickness)
    pygame.draw.line(surface, color, to_pixel(right_elbow), to_pixel(right_wrist), thickness)
    pygame.draw.line(surface, color, hip_pixel, to_pixel(left_knee), thickness)
    pygame.draw.line(surface, color, to_pixel(left_knee), to_pixel(left_ankle), thickness)
    pygame.draw.line(surface, color, hip_pixel, to_pixel(right_knee), thickness)
    pygame.draw.line(surface, color, to_pixel(right_knee), to_pixel(right_ankle), thickness)

    # Draw the head as a circle.
    pygame.draw.circle(surface, color, head_center, head_radius, thickness)

def get_body_center_ratio(landmarks):
    left_hip = landmarks[mp_pose.PoseLandmark.LEFT_HIP]
    right_hip = landmarks[mp_pose.PoseLandmark.RIGHT_HIP]
    return (left_hip.x + right_hip.x) / 2

def draw_lane_system(surface, width, height, hit_line, dead_line):
    lane_width = width // 4

    # Draw vertical lane dividers — there are 4 lanes, so there are 3 dividers (at i=1,2,3).
    for i in range(1, 4):
        x = i * lane_width
        pygame.draw.line(surface, (232, 232, 232), (x, 0), (x, height), 2)

    # Draw a horizontal hit line — the point where a player "catches" a note.
    pygame.draw.line(surface, (169, 169, 169), (0, hit_line), (width, hit_line), 2)

    return lane_width

# ==========================================
# Main Classes of the Game
# ==========================================
class Notes:
    def __init__(self, lane, x, y, speed, lane_width, game_height):
        self.lane = lane
        self.x = x
        self.y = y
        self.speed = speed
        self.lane_width = lane_width
        self.game_height = game_height
        self.active = True
        self.scored = False
        self.hit = False 

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
        self.lane = 0
        self.y = hit_line
        self.x = self.lane_width // 2
        self.size = 20
 
        # For smoothing the position of a pose to prevent jerking.
        self.smoothed_ratio = None
        self.smooth_alpha = 0.18
        self.pending_lane = 0
        self.pending_count = 0
        self.lane_switch_frames = 3

    def update_from_pose(self, center_x_ratio, game_width):
        # Clamp the input value to be within the range of 0.0-1.0 (to prevent the value from going outside the range of the mediapipe).
        center_x_ratio = max(0.0, min(1.0, center_x_ratio))

        # exponential moving average smoothing
        if self.smoothed_ratio is None:
            self.smoothed_ratio = center_x_ratio
        else:
            self.smoothed_ratio = (self.smooth_alpha * center_x_ratio + (1 - self.smooth_alpha) * self.smoothed_ratio)

        # Convert ratio (0.0-1.0) to lane (0-3)
        raw_lane = int(self.smoothed_ratio * 4)
        raw_lane = max(0, min(3, raw_lane))

        # Count how many consecutive frames the original raw_lane is repeated before actually changing self.lane.
        if raw_lane == self.pending_lane:
            self.pending_count += 1
        else:
            self.pending_lane = raw_lane
            self.pending_count = 1

        if self.pending_count >= self.lane_switch_frames and raw_lane != self.lane:
            self.lane = raw_lane

        # Update the position of x according to the current lane.
        self.x = self.lane * self.lane_width + self.lane_width // 2


    def get_lane(self):
        return self.lane


    def draw(self, surface):
        pygame.draw.circle(surface, (0, 255, 0), (self.x, self.y), self.size)
        pygame.draw.circle(surface, (0, 200, 0), (self.x, self.y), self.size, 2)

class Score:
    def __init__(self, font, font_name_):
        self.value = 0
        self.font = font
        self.font_name = font_name_
 
    def add_points(self, points):
        self.value += points

    def draw(self, surface, player_name):
        name_text = self.font_name.render(f"Player: {player_name}", True, (255, 255, 255))
        surface.blit(name_text, (20, 15))

        score_text = self.font.render(f"Score: {self.value}", True, (255, 255, 255))
        surface.blit(score_text, (20, 15 + name_text.get_height() + 5))

class Game:
    def __init__(self, font_score_, font_big_, font_med_, font_small_, font_name_, player_name):
        self.width = _screen_width
        self.height = _screen_height
        self.game_over = False
        self.lane_width = self.width // 4
        self.hit_line = self.height - self.height // 4
        self.dead_line = self.hit_line + 100
 
        self.score = Score(font_score_, font_name_)
        self.player = Player(self.lane_width, self.hit_line)
        self.notes = []
 
        self.player_name = player_name
        self.score_saved = False
 
        self.font_big = font_big_
        self.font_med = font_med_
        self.font_small = font_small_
 
        # Countdown before the game starts — Wait until you see the player's pose.
        self.is_counting_down = True
        self.countdown_time = 3.9
        self.has_seen_player = False
 
        self.last_time = time.time()
        self.spawn_timer = 0.0
        self.next_spawn_gap = 1.0
        self.game_time = 0.0
        self.speed_per_second = 5.0
        self.max_speed_bonus = 300.0

    def reset(self):
        self.game_over = False
        self.score.value = 0
        self.notes = []
        self.score_saved = False

        self.player.lane = 0
        self.player.x = self.player.lane_width // 2

        self.is_counting_down = True
        self.countdown_time = 3.9
        self.has_seen_player = False

        self.last_time = time.time()
        self.spawn_timer = 0.0
        self.next_spawn_gap = 1.0
        self.game_time = 0.0

    def get_delta_time(self):
        now = time.time()
        dt = now - self.last_time
        self.last_time = now
        return dt
    
    def spawn_note(self):
        if len(self.notes) > 0:
            return

        lane = random.randint(0, 3)
        x = lane * self.lane_width
        y = -self.lane_width

        speed_bonus = min(self.game_time * self.speed_per_second, self.max_speed_bonus)
        speed = random.uniform(150, 250) + speed_bonus

        note = Notes(lane, x, y, speed, self.lane_width, self.height)
        self.notes.append(note)

    def update(self, dt):
        if self.game_over:
            return

        if self.is_counting_down:
            if self.has_seen_player:
                self.countdown_time -= dt
                if self.countdown_time <= 1.0:
                    self.is_counting_down = False
            return

        self.game_time += dt
        self.spawn_timer += dt
        if self.spawn_timer >= self.next_spawn_gap:
            self.spawn_note()
            self.spawn_timer = 0.0
            self.next_spawn_gap = random.uniform(1.5, 2.5)

        speed_bonus = min(self.game_time * self.speed_per_second, self.max_speed_bonus)
        for note in self.notes:
            note.move(dt, speed_bonus=speed_bonus)

        player_lane = self.player.get_lane()
        for note in self.notes:
            if not note.active:
                continue
            if not note.scored and note.lane == player_lane:
                if note.y + self.lane_width >= self.hit_line:
                    note.scored = True
                    note.hit = True
                    self.score.add_points(1)
            if not note.scored and note.y + self.lane_width >= self.dead_line:
                self.game_over = True

        self.notes = [n for n in self.notes if n.active]

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

        if self.is_counting_down:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))

            if not self.has_seen_player:
                text_warn = self.font_med.render("Waiting for player appearance...", True, (255, 255, 0))
                surface.blit(text_warn, (self.width // 2 - text_warn.get_width() // 2, self.height // 2 - 20))
            else:
                display_num = int(self.countdown_time)
                text_count = self.font_big.render(str(display_num), True, (0, 255, 255))
                surface.blit(text_count, (self.width // 2 - text_count.get_width() // 2, self.height // 2 - 50))

                text_ready = self.font_med.render("GET READY!", True, (255, 255, 255))
                surface.blit(text_ready, (self.width // 2 - text_ready.get_width() // 2, self.height // 2 + 30))

        if self.game_over:
            overlay = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            surface.blit(overlay, (0, 0))

            text1 = self.font_big.render("GAME OVER", True, (255, 0, 0))
            surface.blit(text1, (self.width // 2 - text1.get_width() // 2, self.height // 2 - 100))

            text2 = self.font_med.render(f"Final Score: {self.score.value}", True, (255, 255, 255))
            surface.blit(text2, (self.width // 2 - text2.get_width() // 2, self.height // 2))

            text3 = self.font_small.render("Press Q to open score screen or R to restart", True, (240, 240, 240))
            surface.blit(text3, (self.width // 2 - text3.get_width() // 2, self.height // 2 + 60))

# ==========================================
# Init — Called once at program startup
# ==========================================
def init(shared, cap, pose):
    global _screen_width, _screen_height, _bg, _cap, _pose
    global font_score, font_big, font_med, font_small, font_name

    _screen_width = shared["screen_width"]
    _screen_height = shared["screen_height"]
    _bg = shared["bg"]

    _cap = cap
    _pose = pose

    font_score = pygame.font.SysFont(None, 36)
    font_big   = pygame.font.SysFont(None, 120)
    font_med   = pygame.font.SysFont(None, 42)
    font_small = pygame.font.SysFont(None, 28)
    font_name  = pygame.font.SysFont(None, 30)

# ==========================================
# Helper: Start a new game (called when entering the "play" state)
# ==========================================
def start_new_game(player_name):
    global game
    game = Game(font_score, font_big, font_med, font_small, font_name, player_name)

# ==========================================
# Handle_event
# ==========================================
def handle_event(event, context):
    global game

    if game is None:
        start_new_game(context["player_name"])

    if event.type == pygame.KEYDOWN:
        if event.key == pygame.K_q:
            if game.game_over:
                return "score", context
            else:
                return "quit", context
        elif event.key == pygame.K_r:
            if game.game_over:
                game.reset()

    return None, context

# ==========================================
# Update — read camera, run pose, update game state
# ==========================================
def update():
    global _pip_frame, _pip_landmarks

    dt = game.get_delta_time()

    ret, frame = _cap.read()
    if ret:
        mirror_frame = cv.flip(frame, 1)
        h, w, _ = mirror_frame.shape

        image = cv.cvtColor(mirror_frame, cv.COLOR_BGR2RGB)
        results = _pose.process(image)

        if results.pose_landmarks:
            game.has_seen_player = True
            landmarks = results.pose_landmarks.landmark

            cx_ratio = get_body_center_ratio(landmarks)
            game.player.update_from_pose(cx_ratio, game.width)

            _pip_landmarks = landmarks
        else:
            if game.is_counting_down:
                game.has_seen_player = False
            _pip_landmarks = None

        _pip_frame = mirror_frame

    game.update(dt)

# ==========================================
# Draw
# ==========================================
def draw(screen):
    game.render(screen, _bg)

    if _pip_frame is not None:
        h, w, _ = _pip_frame.shape

        stick_surface = pygame.Surface((w, h))
        stick_surface.fill((255, 255, 255))

        scaled_hit = int(game.hit_line * h / game.height)
        scaled_dead = int(game.dead_line * h / game.height)
        draw_lane_system(stick_surface, w, h, scaled_hit, scaled_dead)

        if _pip_landmarks is not None:
            draw_stick_figure(stick_surface, _pip_landmarks, w, h)

            sim_x = game.player.lane * (w // 4) + (w // 8)
            sim_y = scaled_hit
            pygame.draw.circle(stick_surface, (0, 255, 0), (sim_x, sim_y), 10)

        pip_surface = pygame.transform.scale(stick_surface, (PIP_W, PIP_H))
        pip_x = game.width - PIP_W - 10
        pip_y = 10
        screen.blit(pip_surface, (pip_x, pip_y))
        pygame.draw.rect(screen, (255, 255, 255), (pip_x, pip_y, PIP_W, PIP_H), 2)