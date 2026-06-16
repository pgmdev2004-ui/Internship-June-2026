import pygame
import pyautogui
import sys
import time
import cv2 as cv
import mediapipe as mp

import Game_home as home
import Game_play as play 
#import Game_setting as setting 
import Game_score as score 

# Init pygame + window (Once).
pygame.init()
screen_width, screen_height = pyautogui.size()
screen_width -= screen_width // 3
screen = pygame.display.set_mode((screen_width, screen_height))
pygame.display.set_caption("Pose Rhythm Game")
clock = pygame.time.Clock()

# Load shared assets across all pages.
bg_screen = pygame.image.load(r'C:\Users\pprit\Desktop\Internship June 2026\image\Background\BG1.png')
bg_screen = pygame.transform.scale(bg_screen, (screen_width,screen_height))

fonts = {
    'title': pygame.font.SysFont(None, 64),
    'header': pygame.font.SysFont(None, 36),
    'row': pygame.font.SysFont(None, 32),
    'hint': pygame.font.SysFont(None, 26),
    'big': pygame.font.SysFont(None, 120),
    'med': pygame.font.SysFont(None, 42),
    'small': pygame.font.SysFont(None, 28),
}

shared = {
    'screen': screen,
    'screen_width': screen_width,
    'screen_height': screen_height,
    'bg': bg_screen,
    'fonts': fonts
}

# Pre-init webcam + pose model (most intensive -> done in advance)
cap = cv.VideoCapture(0)
pose = mp.solutions.pose.Pose(min_detection_confidence=0.5, min_tracking_confidence=0.5)

# Allow each module to load its own assets only once.
home.init(shared)
play.init(shared, cap, pose)
score.init(shared)
#setting.init(shared)

# State machine
state = 'home'
context = {'player_name': ''}    # Check the initial structure of the context.

running = True
while running:
    next_state = None

    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        
        if state == 'home':
            returned_state, context = home.handle_event(event, context)
            if returned_state: 
                next_state = returned_state
        elif state == 'play':
            returned_state, context = play.handle_event(event, context)
            if returned_state: 
                next_state = returned_state
        #elif state == 'setting':
            #returned_state, context = setting.handle_event(event, context)
            #if returned_state: 
                #next_state = returned_state
        elif state == 'score':
            returned_state, context = score.handle_event(event, context)
            if returned_state: 
                next_state = returned_state

    # Handle screen transition (State Transition) processes outside the Event loop for stability.
    if next_state:
        if next_state == 'quit':
            running = False
        else:
            state = next_state
            
            # Reload the score from the file every time the scene switches to the 'score' screen.
            if state == 'score':
                score.enter_score()
            # Create a new game session and clear the board when switching to the 'play' screen.
            elif state == 'play':
                play.start_new_game(context.get('player_name', 'Unknown'))
            # If the game resets you back to the 'home' screen, immediately force-reset the subsystems back to the main menu.
            elif state == 'home':
                home.enter_home()
                
    # Logic and Graphic Drawing Update Routine
    if state == 'home':
        home.update()
        home.draw(screen)
    elif state == 'play':
        play.update()
        play.draw(screen)
    #elif state == 'setting':
        #setting.update()
        #setting.draw(screen)
    elif state == 'score':
        score.update()
        score.draw(screen)
    
    pygame.display.flip()
    clock.tick(60)

cap.release()
pose.close()
pygame.quit()
sys.exit()