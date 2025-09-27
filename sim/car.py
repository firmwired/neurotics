#!/usr/bin/env python3
"""
Top-down car game / simulation (pygame).
- Place a 'car.png' sprite (top-down view, pointing up) in the same folder to use it.
- Controls:
    UP / W    : accelerate forward
    DOWN / S  : brake / reverse
    LEFT / A  : steer left
    RIGHT / D : steer right
    R         : reset
    ESC / Q   : quit
- The world contains circular obstacles and a goal marker; reaching the goal wins the level.
"""

import pygame
import sys
import os
import math
import random

# ----- PARAMETERS -----
SCREEN_W, SCREEN_H = 800, 800
WORLD_SIZE = 2.0  # conceptual world meters (for scaling if needed)
FPS = 60

CAR_SPRITE = "car.png"  # put your top-down car sprite here (pointing up)
USE_SPRITE = os.path.exists(CAR_SPRITE)

# Car physical parameters (feel free to tweak)
MAX_SPEED = 2.5        # m/s (conceptual)
ACCEL = 4.0            # m/s^2
BRAKE = 6.0
STEER_SPEED = 2.5      # rad/s at full steering input
DRAG = 0.8             # velocity damping per second

# Visual scaling: map world (0..WORLD_SIZE) to pixels
MARGIN = 50
FIELD_W = SCREEN_W - 2*MARGIN
FIELD_H = SCREEN_H - 2*MARGIN

# Car drawing size (pixels)
CAR_W_PX = 40
CAR_H_PX = 60

# Obstacles: (x, y, r) in world coords (0..WORLD_SIZE)
NUM_OBSTACLES = 6
OBSTACLE_RADIUS_MIN = 0.04
OBSTACLE_RADIUS_MAX = 0.12

# Goal
GOAL_POS = (1.9, 1.0)  # world coords
GOAL_RADIUS = 0.06

# Colors
COLOR_BG = (30, 30, 30)
COLOR_FIELD = (40, 40, 48)
COLOR_OBS = (200, 140, 18)
COLOR_GOAL = (32, 200, 60)
COLOR_TEXT = (230, 230, 230)
COLOR_CAR_BOX = (80, 160, 240)

# -----------------------

def world_to_screen(x, y):
    """Map world coords (0..WORLD_SIZE) to screen pixels"""
    sx = MARGIN + (x / WORLD_SIZE) * FIELD_W
    sy = MARGIN + ((WORLD_SIZE - y) / WORLD_SIZE) * FIELD_H  # flip y for screen
    return int(sx), int(sy)

def screen_to_world(sx, sy):
    x = (sx - MARGIN) / FIELD_W * WORLD_SIZE
    y = WORLD_SIZE - (sy - MARGIN) / FIELD_H * WORLD_SIZE
    return x, y

class Car:
    def __init__(self, x=0.05, y=1.0, theta=0.0):
        self.x = x
        self.y = y
        self.theta = theta  # radians, 0 = right, but our sprite faces up; we'll rotate accordingly
        self.v = 0.0        # forward speed (m/s)
        self.steer = 0.0    # -1..1 steering input
        self.width = 0.12
        self.length = 0.2
        self.history = []

    def reset(self, x=0.05, y=1.0, theta=0.0):
        self.__init__(x, y, theta)

    def step(self, accel_input, steer_input, dt):
        # accel_input: -1..1
        # steer_input: -1..1
        if accel_input > 0:
            self.v += accel_input * ACCEL * dt
        else:
            self.v += accel_input * BRAKE * dt  # braking/retro

        # drag / clamp
        self.v -= self.v * DRAG * dt
        # clamp speed
        if self.v > MAX_SPEED: self.v = MAX_SPEED
        if self.v < -MAX_SPEED * 0.5: self.v = -MAX_SPEED * 0.5

        # steering: angular velocity proportional to steering * speed
        # simple kinematic turning (steer more effective at higher speed)
        angular_vel = steer_input * STEER_SPEED * (0.4 + abs(self.v)/MAX_SPEED)
        self.theta += angular_vel * dt
        # move forward in heading direction
        dx = self.v * math.cos(self.theta) * dt
        dy = self.v * math.sin(self.theta) * dt
        self.x += dx
        self.y += dy
        # clamp inside world
        self.x = min(max(self.x, 0.0), WORLD_SIZE)
        self.y = min(max(self.y, 0.0), WORLD_SIZE)
        self.history.append((self.x, self.y))
        if len(self.history) > 5000:
            self.history.pop(0)

    def get_polygon(self):
        # return a polygon of the car (for collision) in world coords
        l = self.length / 2.0
        w = self.width / 2.0
        corners = [(-l, -w), (-l, w), (l, w), (l, -w)]
        pts = []
        for (cx, cy) in corners:
            rx = cx * math.cos(self.theta) - cy * math.sin(self.theta)
            ry = cx * math.sin(self.theta) + cy * math.cos(self.theta)
            pts.append((self.x + rx, self.y + ry))
        return pts

    def draw(self, surf, sprite=None):
        sx, sy = world_to_screen(self.x, self.y)
        if sprite is not None:
            # sprite assumed pointing up: rotate so that 0 radians = right -> convert
            # We'll rotate by -(theta - pi/2) because sprite faces up
            angle_deg = -math.degrees(self.theta) + 90
            img = pygame.transform.rotozoom(sprite, angle_deg, CAR_W_PX / sprite.get_width())
            rect = img.get_rect(center=(sx, sy))
            surf.blit(img, rect)
        else:
            # draw rectangle rotated
            pts = []
            for (wx, wy) in self.get_polygon():
                pts.append(world_to_screen(wx, wy))
            pygame.draw.polygon(surf, COLOR_CAR_BOX, pts)

def generate_obstacles(seed=None):
    rng = random.Random(seed)
    obs = []
    for _ in range(NUM_OBSTACLES):
        x = rng.uniform(0.12, WORLD_SIZE - 0.12)
        y = rng.uniform(0.12, WORLD_SIZE - 0.12)
        r = rng.uniform(OBSTACLE_RADIUS_MIN, OBSTACLE_RADIUS_MAX)
        obs.append((x,y,r))
    # optionally ensure none overlap start/goal too closely
    return obs

def check_collision(car, obstacles):
    # approximate collision if car center within obstacle radius + car radius
    car_radius = max(car.width, car.length) * 0.6
    for (ox, oy, r) in obstacles:
        dist2 = (car.x - ox)**2 + (car.y - oy)**2
        if dist2 <= (r + car_radius)**2:
            return True
    # also check walls
    if car.x <= 0.0 or car.x >= WORLD_SIZE or car.y <= 0.0 or car.y >= WORLD_SIZE:
        return True
    return False

def reached_goal(car):
    gx, gy = GOAL_POS
    return ((car.x - gx)**2 + (car.y - gy)**2) <= GOAL_RADIUS**2

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_W, SCREEN_H))
    pygame.display.set_caption("Top-down Car Game (neurotics demo)")
    clock = pygame.time.Clock()
    font = pygame.font.SysFont("Arial", 18)

    # load sprite if present
    sprite = None
    if USE_SPRITE:
        try:
            sprite_img = pygame.image.load(CAR_SPRITE).convert_alpha()
            sprite = sprite_img
        except Exception as e:
            print("Could not load sprite:", e)
            sprite = None

    car = Car()
    obstacles = generate_obstacles(seed=2)
    playing = True
    paused = False
    win = False
    collision = False

    # controls state
    acc_input = 0.0
    steer_input = 0.0
    key_state = {'up':False,'down':False,'left':False,'right':False}

    while playing:
        dt = clock.tick(FPS) / 1000.0  # seconds
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                playing = False
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_a):
                    playing = False
                elif event.key in (pygame.K_r,):
                    # reset
                    car.reset()
                    obstacles = generate_obstacles(seed=random.randint(0,9999))
                    win = False; collision = False
                elif event.key in (pygame.K_SPACE,):
                    car.v = 0.0
                # mark keys
                if event.key in (pygame.K_UP, pygame.K_z):
                    key_state['up'] = True
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    key_state['down'] = True
                if event.key in (pygame.K_LEFT, pygame.K_q):
                    key_state['left'] = True
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    key_state['right'] = True
            elif event.type == pygame.KEYUP:
                if event.key in (pygame.K_UP, pygame.K_z):
                    key_state['up'] = False
                if event.key in (pygame.K_DOWN, pygame.K_s):
                    key_state['down'] = False
                if event.key in (pygame.K_LEFT, pygame.K_q):
                    key_state['left'] = False
                if event.key in (pygame.K_RIGHT, pygame.K_d):
                    key_state['right'] = False

        if not paused and not win and not collision:
            # compute input
            accel = 0.0
            if key_state['up']:
                accel += 1.0
            if key_state['down']:
                accel -= 1.0
            steer = 0.0
            if key_state['left']:
                steer -= 1.0
            if key_state['right']:
                steer += 1.0
            car.step(accel, steer, dt)

            # check collision / goal
            if check_collision(car, obstacles):
                collision = True
            if reached_goal(car):
                win = True

        # DRAW
        screen.fill(COLOR_BG)
        # field
        pygame.draw.rect(screen, COLOR_FIELD, (MARGIN, MARGIN, FIELD_W, FIELD_H))

        # obstacles
        for (ox, oy, r) in obstacles:
            sx, sy = world_to_screen(ox, oy)
            rr = int(r / WORLD_SIZE * FIELD_W)
            pygame.draw.circle(screen, COLOR_OBS, (sx, sy), rr)

        # goal
        gx, gy = GOAL_POS
        gsx, gsy = world_to_screen(gx, gy)
        gg = int(GOAL_RADIUS / WORLD_SIZE * FIELD_W)
        pygame.draw.circle(screen, COLOR_GOAL, (gsx, gsy), gg)

        # path
        if len(car.history) > 1:
            pts = [world_to_screen(px, py) for (px, py) in car.history]
            pygame.draw.lines(screen, (200,200,255), False, pts, 2)

        # car
        car.draw(screen, sprite)

        # HUD
        txt1 = font.render(f"Pos: ({car.x:.2f}, {car.y:.2f})  Speed: {car.v:.2f} m/s  Theta: {math.degrees(car.theta):.1f}°", True, COLOR_TEXT)
        screen.blit(txt1, (10, 10))
        if win:
            ttxt = font.render("GOAL REACHED! Press R to reset.", True, (200,255,200))
            screen.blit(ttxt, (10, 40))
        if collision:
            ctxt = font.render("COLLISION! Press R to reset.", True, (255,160,160))
            screen.blit(ctxt, (10, 40))

        controls_txt = font.render("Controls: Arrows/WASD to drive. R reset. Q/ESC quit.", True, COLOR_TEXT)
        screen.blit(controls_txt, (10, SCREEN_H - 30))

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()
