from OpenGL.GL import *
from OpenGL.GLU import *
from OpenGL.GLUT import *
from OpenGL.GLUT import GLUT_BITMAP_TIMES_ROMAN_24
import math
import sys
import time

# Game State Constants
MENU = 0
LEVEL_SELECT = 1
PLAYING = 2
GAME_OVER = 3
PAUSED = 4

# Game Variables
game_state = MENU
current_level = 0
selected_level = 0
paused = False
elapsed_time = 0.0
last_time = time.time()

# Window dimensions
WINDOW_WIDTH = 1280
WINDOW_HEIGHT = 720

# Player Variables
player_x = 0.0
player_y = 0.0
player_z = 0.0
player_vx = 0.0
player_vy = 0.0
player_speed = 1.5
player_hp = 100
player_shield = False
player_bounds_x = 80
player_bounds_y = 50

# Game Objects
obstacles = []  # List of dicts: {'x', 'y', 'z', 'type', 'active'}
OBSTACLE_SPAWN_Z = -800
OBSTACLE_DESPAWN_Z = 50
GAME_SPEED = 2.0  # World movement speed

# Combat
bullets = []
BULLET_SPEED = 5.0
BULLET_MAX_DIST = -1000

missiles = []
MISSILE_SPEED = 4.0
missile_cooldown_timer = 0.0
MISSILE_COOLDOWN_MAX = 5.0

# Pickups
pickups = [] # {'x', 'y', 'z', 'type', 'rot'}
PICKUP_SPEED = 2.0
laser_active = False
laser_timer = 0.0
LASER_DURATION = 10.0

# Scoring & Rings
score = 0
rings = [] # {'x', 'y', 'z', 'rot'}
RING_SPEED = 2.0

enemy_bullets = [] # {'x', 'y', 'z', 'dx', 'dy', 'dz'}

enemies = [] # [{'x', 'y', 'z', 'type', 'hp'}]
ENEMY_SPAWN_Z = -800

boss = None # {'x', 'y', 'z', 'hp', 'max_hp', 'active', 'phase', 'angle'}
cheat_mode = False

# ============ UTILITY FUNCTIONS ============

def get_text_width(text, font=GLUT_BITMAP_TIMES_ROMAN_24):
    """Estimate text width for centering"""
    width = 0
    for char in text:
        if font == GLUT_BITMAP_TIMES_ROMAN_24:
            width += 15  # Approximate width per character
        else:
            width += 12
    return width


def draw_text_2d(text, x, y, color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=False):
    """Draw 2D text at screen position"""
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glColor3f(color[0], color[1], color[2])
    
    # Center text if requested
    if centered:
        text_width = get_text_width(text, font)
        x = x - (text_width / 2)
    
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(font, ord(char))
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_text_with_border(text, x, y, text_color=(1.0, 1.0, 1.0), border_color=(0.0, 0.0, 0.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=False):
    """Draw 2D text with a border"""
    # Draw border
    draw_text_2d(text, x - 1, y, border_color, font, centered)
    draw_text_2d(text, x + 1, y, border_color, font, centered)
    draw_text_2d(text, x, y - 1, border_color, font, centered)
    draw_text_2d(text, x, y + 1, border_color, font, centered)

    # Draw main text
    draw_text_2d(text, x, y, text_color, font, centered)


def draw_sphere(radius, slices=80, stacks=80):
    """Draw a sphere using GLU"""
    quad = gluNewQuadric()
    gluSphere(quad, radius, slices, stacks)


def draw_cylinder(radius, height, slices=80, stacks=80):
    """Draw a cylinder using GLU"""
    quad = gluNewQuadric()
    gluCylinder(quad, radius, radius, height, slices, stacks)


def draw_cube(size):
    """Draw a cube using GL primitives"""
    half = size / 2.0
    glBegin(GL_QUADS)
    
    # Front
    glVertex3f(-half, -half, half)
    glVertex3f(half, -half, half)
    glVertex3f(half, half, half)
    glVertex3f(-half, half, half)
    
    # Back
    glVertex3f(-half, -half, -half)
    glVertex3f(-half, half, -half)
    glVertex3f(half, half, -half)
    glVertex3f(half, -half, -half)
    
    # Left
    glVertex3f(-half, -half, -half)
    glVertex3f(-half, -half, half)
    glVertex3f(-half, half, half)
    glVertex3f(-half, half, -half)
    
    # Right
    glVertex3f(half, -half, -half)
    glVertex3f(half, half, -half)
    glVertex3f(half, half, half)
    glVertex3f(half, -half, half)
    
    # Top
    glVertex3f(-half, half, -half)
    glVertex3f(-half, half, half)
    glVertex3f(half, half, half)
    glVertex3f(half, half, -half)
    
    # Bottom
    glVertex3f(-half, -half, -half)
    glVertex3f(half, -half, -half)
    glVertex3f(half, -half, half)
    glVertex3f(-half, -half, half)
    
    glEnd()


def draw_ground_plane(z_offset, color, size=400, grid_spacing=40):
    """Draw a large ground plane with a grid pattern for infinite stretching effect"""
    # Main ground surface
    glColor3f(color[0], color[1], color[2])
    glBegin(GL_QUADS)
    glVertex3f(-size, -85, z_offset)
    glVertex3f(size, -85, z_offset)
    glVertex3f(size, -250, z_offset)
    glVertex3f(-size, -250, z_offset)
    glEnd()
    
    # Draw grid lines for depth perception
    glColor3f(color[0] * 0.85, color[1] * 0.85, color[2] * 0.85)
    glBegin(GL_LINES)
    
    # Vertical lines (left-right)
    for i in range(-int(size), int(size) + 1, int(grid_spacing)):
        glVertex3f(i, -85, z_offset)
        glVertex3f(i, -250, z_offset)
    
    # Horizontal lines (closer lines are darker/more visible)
    line_count = int((250 - 85) / grid_spacing)
    for j in range(line_count + 1):
        y = -85 - j * grid_spacing
        glVertex3f(-size, y, z_offset)
        glVertex3f(size, y, z_offset)
    
    glEnd()
    
    # Draw horizon line
    glColor3f(color[0] * 0.6, color[1] * 0.6, color[2] * 0.6)
    glBegin(GL_LINES)
    glVertex3f(-size, -240, z_offset)
    glVertex3f(size, -240, z_offset)
    glEnd()


def draw_cloud(x, y, z, scale=1.0):
    """Draw a fluffy cloud made of multiple spheres"""
    glColor3f(1.0, 1.0, 1.0)
    glPushMatrix()
    glTranslatef(x, y, z)
    
    # Create a fluffy cloud effect with overlapping spheres
    for i in range(8):
        glPushMatrix()
        glTranslatef(-6 + i * 1.8, 0, 0)
        draw_sphere(3.5 * scale, slices=60, stacks=60)
        glPopMatrix()
    
    glPopMatrix()


def draw_player_jet():
    """Draw the player jet using hierarchical primitives"""
    glPushMatrix()
    glTranslatef(player_x, player_y, player_z)
    
    # Rotate jet to face forward (-Z direction)
    glRotatef(180, 0, 1, 0)
    
    # Main Body (Fuselage)
    glColor3f(0.7, 0.7, 0.7)  # Light gray
    glPushMatrix()
    glScalef(1.0, 0.6, 4.0)
    draw_cube(5)
    glPopMatrix()
    
    # Cockpit
    glColor3f(0.2, 0.4, 0.8)  # Blue glass
    glPushMatrix()
    glTranslatef(0, 1.5, 2)
    glScalef(0.6, 0.4, 1.2)
    draw_sphere(3)
    glPopMatrix()
    
    # Left Wing
    glColor3f(0.5, 0.5, 0.5)
    glPushMatrix()
    glTranslatef(-6, 0, -1)
    glScalef(2.5, 0.2, 1.5)
    draw_cube(5)
    glPopMatrix()
    
    # Right Wing
    glPushMatrix()
    glTranslatef(6, 0, -1)
    glScalef(2.5, 0.2, 1.5)
    draw_cube(5)
    glPopMatrix()
    
    # Tail Fin
    glColor3f(0.6, 0.6, 0.6)
    glPushMatrix()
    glTranslatef(0, 3, -7)
    glScalef(0.2, 1.5, 1.0)
    draw_cube(4)
    glPopMatrix()
    
    # Engines
    glColor3f(0.2, 0.2, 0.2)
    # Left Engine
    glPushMatrix()
    glTranslatef(-2.5, -1, -8)
    draw_cylinder(1.5, 4)
    glPopMatrix()
    # Right Engine
    glPushMatrix()
    glTranslatef(2.5, -1, -8)
    draw_cylinder(1.5, 4)
    glPopMatrix()
    
    glPopMatrix()
    
    # Draw Shield
    if player_shield:
        glPushMatrix()
        glTranslatef(player_x, player_y, player_z)
        glColor3f(0.0, 0.5, 1.0)
        # glutWireSphere not allowed. Use solid gluSphere.
        # It might obscure the player, so we'll draw it small or rely on a different visual cue?
        # Let's draw it as a small "energy core" above the jet or a large solid sphere
        # If we draw a large solid sphere, we can't see the jet (no transparency).
        # Solution: Draw 4 small spheres rotating around the jet?
        # Or just one small sphere above it.
        glPushMatrix()
        glTranslatef(0, 5, 0)
        draw_sphere(5)
        glPopMatrix()
        glPopMatrix()


# ============ LEVEL RENDERING ============

def draw_common_sky(color):
    """Draw a large background quad for the sky"""
    glPushMatrix()
    glLoadIdentity()
    background_z = -900
    glBegin(GL_QUADS)
    glColor3f(color[0], color[1], color[2])
    glVertex3f(-1000, -1000, background_z)
    glVertex3f(1000, -1000, background_z)
    glVertex3f(1000, 1000, background_z)
    glVertex3f(-1000, 1000, background_z)
    glEnd()
    glPopMatrix()

def draw_moving_ground(color, grid_color):
    """Draw the infinite scrolling ground grid"""
    ground_offset = (elapsed_time * 180) % 40 
    glPushMatrix()
    glTranslatef(0, 0, ground_offset) 
    for z in range(-1000, 200, 40):
        glColor3f(color[0], color[1], color[2])
        glBegin(GL_QUADS)
        glVertex3f(-400, -100, z)
        glVertex3f(400, -100, z)
        glVertex3f(400, -100, z - 40)
        glVertex3f(-400, -100, z - 40)
        glEnd()
        glColor3f(grid_color[0], grid_color[1], grid_color[2])
        glBegin(GL_LINES)
        glVertex3f(-400, -99, z)
        glVertex3f(400, -99, z)
        glEnd()
    glPopMatrix()

def draw_level_1():
    """Level 1: Blue sky + green forest ground"""
    draw_common_sky((0.2, 0.6, 1.0))
    draw_moving_ground((0.2, 0.6, 0.2), (0.1, 0.5, 0.1))
    draw_obstacles()

def draw_level_2():
    """Level 2: Sunset sky + dark blue ocean ground"""
    draw_common_sky((1.0, 0.6, 0.3))
    # Draw a sun
    glPushMatrix()
    glTranslatef(-50, 60, -200)
    glColor3f(1.0, 0.5, 0.0)
    draw_sphere(20)
    glPopMatrix()
    draw_moving_ground((0.1, 0.3, 0.6), (0.2, 0.5, 0.8))
    draw_obstacles()

def draw_level_3():
    """Level 3: Blue sky + orange desert ground"""
    draw_common_sky((0.4, 0.7, 1.0))
    draw_moving_ground((1.0, 0.7, 0.3), (0.9, 0.8, 0.4))
    draw_obstacles()

def draw_level_4():
    """Level 4: Purple sunset + green forest ground"""
    draw_common_sky((0.6, 0.3, 0.8))
    glPushMatrix()
    glTranslatef(60, 50, -200)
    glColor3f(1.0, 0.4, 0.2)
    draw_sphere(18)
    glPopMatrix()
    draw_moving_ground((0.3, 0.5, 0.2), (0.2, 0.4, 0.1))
    draw_obstacles()

def draw_level_5():
    """Level 5: Red sky (final boss level) + red volcanic ground"""
    draw_common_sky((1.0, 0.3, 0.2))
    # Large ominous boss indicator - Pushed very far back
    glPushMatrix()
    glTranslatef(0, 50, -1200) 
    glColor3f(0.8, 0.0, 0.0)
    draw_sphere(150)
    glPopMatrix()
    draw_moving_ground((0.8, 0.2, 0.1), (0.5, 0.1, 0.0))
    draw_obstacles()


def draw_current_level():
    """Draw the current level's visuals"""
    levels = [draw_level_1, draw_level_2, draw_level_3, draw_level_4, draw_level_5]
    
    # glClear and glLoadIdentity removed to preserve camera view set in display()
    
    if 0 <= current_level < len(levels):
        levels[current_level]()


# ============ MENU RENDERING ============

def draw_menu():
    """Draw main menu"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Dark background
    glBegin(GL_QUADS)
    glColor3f(1, 1, 1)
    glVertex3f(-640, 0, -100)
    glVertex3f(640, 0, -100)
    glVertex3f(640, 720, -100)
    glVertex3f(-640, 720, -100)
    glEnd()
    
    # Title
    draw_text_with_border("STRATO QUEST", WINDOW_WIDTH // 2, 150, 
                 text_color=(0.5, 0.5, 0.5), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    
    # Instructions
    draw_text_with_border("Press SPACE to Start", WINDOW_WIDTH // 2, 350,
                 text_color=(0.0, 0.0, 0.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_with_border("or ESC to Quit", WINDOW_WIDTH // 2, 420,
                 text_color=(0.0, 0.0, 0.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)


def draw_level_select():
    """Draw level select screen with selected level animation in background"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Draw the selected level in background with 3D perspective
    levels = [draw_level_1, draw_level_2, draw_level_3, draw_level_4, draw_level_5]
    if 0 <= selected_level < len(levels):
        glMatrixMode(GL_PROJECTION)
        glLoadIdentity()
        gluPerspective(45, (WINDOW_WIDTH / WINDOW_HEIGHT), 0.1, 1000.0)
        glMatrixMode(GL_MODELVIEW)
        glLoadIdentity()
        levels[selected_level]()
    
    # Draw semi-transparent overlay (2D)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Title
    draw_text_with_border("SELECT LEVEL", WINDOW_WIDTH // 2, 80,
                 text_color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    
    # Draw level buttons - centered
    start_x = WINDOW_WIDTH // 2 - 400
    for i in range(5):
        x_pos = start_x + i * 200
        y_pos = 250
        
        # Highlight selected level
        if i == selected_level:
            draw_text_with_border(f"LEVEL {i + 1}", x_pos, y_pos,
                        text_color=(1.0, 1.0, 0.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
        else:
            draw_text_with_border(f"Level {i + 1}", x_pos, y_pos,
                        text_color=(0.7, 0.7, 0.7), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    
    # Instructions - centered
    draw_text_with_border("LEFT/RIGHT arrows to select", WINDOW_WIDTH // 2, 450,
                 text_color=(0.9, 0.9, 0.9), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_with_border("ENTER to play", WINDOW_WIDTH // 2, 520,
                 text_color=(0.9, 0.9, 0.9), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_with_border("ESC to back to menu", WINDOW_WIDTH // 2, 590,
                 text_color=(0.9, 0.9, 0.9), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_pause_menu():
    """Draw pause menu overlay with semi-transparent background"""
    # Draw semi-transparent overlay (2D)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # Text
    draw_text_with_border("PAUSED", WINDOW_WIDTH // 2, 250,
                 text_color=(1.0, 1.0, 0.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_with_border("Press ESC to continue", WINDOW_WIDTH // 2, 350,
                 text_color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_with_border("SPACE to go back to menu", WINDOW_WIDTH // 2, 420,
                 text_color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_hud():
    """Draw 2D HUD overlay"""
    # Use glClear to clear depth buffer for HUD instead of glDisable
    glClear(GL_DEPTH_BUFFER_BIT)
    
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # 2. Health Bar
    bar_x, bar_y = 50, 50
    bar_width, bar_height = 200, 20
    
    # Background (Red/Empty)
    glColor3f(0.5, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex3f(bar_x, bar_y, 0)
    glVertex3f(bar_x + bar_width, bar_y, 0)
    glVertex3f(bar_x + bar_width, bar_y + bar_height, 0)
    glVertex3f(bar_x, bar_y + bar_height, 0)
    glEnd()
    
    # Foreground (Green/HP)
    hp_pct = max(0, player_hp / 100.0)
    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_QUADS)
    glVertex3f(bar_x, bar_y, 0)
    glVertex3f(bar_x + bar_width * hp_pct, bar_y, 0)
    glVertex3f(bar_x + bar_width * hp_pct, bar_y + bar_height, 0)
    glVertex3f(bar_x, bar_y + bar_height, 0)
    glEnd()
    
    # Border
    glColor3f(1.0, 1.0, 1.0)
    # glLineWidth removed
    glBegin(GL_LINE_LOOP)
    glVertex3f(bar_x, bar_y, 0)
    glVertex3f(bar_x + bar_width, bar_y, 0)
    glVertex3f(bar_x + bar_width, bar_y + bar_height, 0)
    glVertex3f(bar_x, bar_y + bar_height, 0)
    glEnd()
    
    draw_text_2d(f"HP: {int(player_hp)}", bar_x, bar_y - 10)
    
    # 3. Level Info & Score
    draw_text_2d(f"LEVEL {current_level + 1}", WINDOW_WIDTH - 150, 50)
    draw_text_2d(f"SCORE: {score}", WINDOW_WIDTH - 150, 80)

    # 4. Missile Cooldown (Pie Chart)
    ui_x = WINDOW_WIDTH - 60
    ui_y = WINDOW_HEIGHT - 60
    radius = 40
    
    glPushMatrix()
    glTranslatef(ui_x, ui_y, 0)
    
    # Background (Gray)
    glColor3f(0.2, 0.2, 0.2)
    draw_circle_fan(radius, 360)
    
    # Foreground (Orange/Yellow)
    if missile_cooldown_timer > 0:
        # Recharging
        ratio = 1.0 - (missile_cooldown_timer / MISSILE_COOLDOWN_MAX)
        if ratio > 0:
            angle = 360 * ratio
            glColor3f(1.0, 0.5, 0.0)
            draw_circle_fan(radius, angle)
    else:
        # Ready!
        glColor3f(1.0, 1.0, 0.0)
        draw_circle_fan(radius, 360)
        
    draw_text_2d("MSL", -15, 5, (0,0,0) if missile_cooldown_timer <= 0 else (1,1,1))
    
    glPopMatrix()
    
    # 5. Boss HP
    if current_level == 4 and boss and boss['active']:
        boss_pct = max(0, boss['hp'] / boss['max_hp'])
        bx, by = WINDOW_WIDTH // 2 - 200, 50
        bw, bh = 400, 20
        
        glColor3f(0.5, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(bx, by, 0); glVertex3f(bx+bw, by, 0)
        glVertex3f(bx+bw, by+bh, 0); glVertex3f(bx, by+bh, 0)
        glEnd()
        
        glColor3f(1.0, 0.0, 0.0)
        glBegin(GL_QUADS)
        glVertex3f(bx, by, 0); glVertex3f(bx+bw*boss_pct, by, 0)
        glVertex3f(bx+bw*boss_pct, by+bh, 0); glVertex3f(bx, by+bh, 0)
        glEnd()
        
        draw_text_with_border("FINAL BOSS", WINDOW_WIDTH // 2, 30, (1,0,0), centered=True)
        
    # 6. Cheat Indicator
    if cheat_mode:
        draw_text_with_border("CHEAT MODE", 100, WINDOW_HEIGHT - 30, (1,1,0), centered=True)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)

def draw_circle_fan(radius, angle_deg):
    """Draw a filled circle sector using allowed primitives"""
    glBegin(GL_TRIANGLE_FAN)
    glVertex3f(0, 0, 0) # Center
    
    # Segments
    segments = int(angle_deg / 10) + 1
    for i in range(segments + 1):
        theta = math.radians(min(angle_deg, i * 10))
        # Note: In HUD (Ortho2D), Y is down. Cos/Sin calculation:
        # 0 deg = Right (X+). 90 deg = Down (Y+).
        x = radius * math.cos(theta)
        y = radius * math.sin(theta)
        glVertex3f(x, y, 0)
        
    glEnd()


def reset_game():
    """Reset all game variables for a new run"""
    global player_hp, player_x, player_y, player_vx, player_vy, bullets, enemy_bullets, enemies, obstacles, score, rings, pickups, boss
    player_hp = 100
    player_x = 0
    player_y = 0
    player_vx = 0
    player_vy = 0
    score = 0
    bullets = []
    enemy_bullets = []
    enemies = []
    obstacles = []
    rings = []
    pickups = []
    boss = None

def draw_game_over():
    """Draw Game Over screen"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Red overlay
    glBegin(GL_QUADS)
    glColor3f(1, 1, 1)
    glVertex3f(-1000, -1000, -100)
    glVertex3f(1000, -1000, -100)
    glVertex3f(1000, 1000, -100)
    glVertex3f(-1000, 1000, -100)
    glEnd()
    
    msg = "GAME OVER"
    color = (1.0, 0.0, 0.0)
    if current_level == 4 and boss and not boss['active']:
        msg = "VICTORY!"
        color = (0.0, 1.0, 0.0)
    
    draw_text_with_border(msg, WINDOW_WIDTH // 2, 250,
                 text_color=color, font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_with_border(f"Final Score: {score}", WINDOW_WIDTH // 2, 300,
                 text_color=(1,1,1), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_with_border("Press SPACE to Retry", WINDOW_WIDTH // 2, 350,
                 text_color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_with_border("ESC to Menu", WINDOW_WIDTH // 2, 420,
                 text_color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)


# ============ DISPLAY & CALLBACKS ============

def display():
    """Display callback"""
    global elapsed_time, last_time
    
    # Update elapsed time
    current_time = time.time()
    delta_time = current_time - last_time
    last_time = current_time
    
    if game_state == PLAYING and not paused:
        elapsed_time += delta_time
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (WINDOW_WIDTH / WINDOW_HEIGHT), 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()  # Reset the modelview matrix before applying camera transforms
    
    if game_state == MENU:
        draw_menu()
    elif game_state == LEVEL_SELECT:
        draw_level_select()
    elif game_state == PLAYING:
        # Set up camera: Third-person behind the jet
        # Look from behind the player (further back in Z)
        gluLookAt(0, 20, 100,  # Eye position
                  0, 0, -100,  # Center position (looking forward)
                  0, 1, 0)     # Up vector
        
        draw_current_level()
        draw_player_jet()
        draw_enemies()
        if current_level == 4:
            draw_boss()
        draw_pickups()
        draw_rings()
        draw_bullets()
        draw_missiles()
        draw_hud()
        
        if paused:
            draw_pause_menu()
    elif game_state == GAME_OVER:
        draw_game_over()
    
    glutSwapBuffers()


def mouse(button, state, x, y):
    """Mouse callback for shooting"""
    global game_state, bullets
    
    if game_state == PLAYING and not paused:
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            # Spawn bullet or laser
            b_type = 'laser' if laser_active else 'normal'
            bullets.append({
                'x': player_x,
                'y': player_y,
                'z': player_z, # Start exactly at player
                'type': b_type
            })
        elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
            spawn_missiles()

def keyboard(key, x, y):
    """Keyboard callback"""
    global game_state, selected_level, current_level, paused, player_x, player_y, player_vx, player_vy
    
    key = key.lower()
    
    if key == b'\x1b':  # ESC
        if game_state == PLAYING:
            if paused:
                paused = False
            else:
                paused = True
        elif game_state == LEVEL_SELECT:
            game_state = MENU
        elif game_state == MENU:
            sys.exit()
        elif game_state == GAME_OVER:
            game_state = MENU
    
    elif key == b' ':  # SPACE
        if game_state == MENU:
            game_state = LEVEL_SELECT
            selected_level = 0
        elif game_state == PLAYING and paused:
            game_state = LEVEL_SELECT
            paused = False
        elif game_state == GAME_OVER:
            reset_game()
            game_state = PLAYING
    
    elif key == b'\r':  # ENTER
        if game_state == LEVEL_SELECT:
            current_level = selected_level
            reset_game()
            game_state = PLAYING
            paused = False
    
    elif key == b'c': # Cheat Toggle
        global cheat_mode
        cheat_mode = not cheat_mode
        print(f"Cheat Mode: {cheat_mode}")
            
    # Apply acceleration (Inertia movement)
    accel = 3.0 
    if game_state == PLAYING and not paused:
        if key == b'w': player_vy += accel
        if key == b'a': player_vx -= accel
        if key == b's': player_vy -= accel
        if key == b'd': player_vx += accel
        
        # Velocity clamping
        max_v = 4.0
        player_vx = max(-max_v, min(max_v, player_vx))
        player_vy = max(-max_v, min(max_v, player_vy))


def special(key, x, y):
    """Special keys callback (arrows)"""
    global selected_level
    
    if game_state == LEVEL_SELECT:
        if key == GLUT_KEY_LEFT:
            selected_level = max(0, selected_level - 1)
        elif key == GLUT_KEY_RIGHT:
            selected_level = min(4, selected_level + 1)


def spawn_pickup():
    """Randomly spawn power-ups"""
    if random.random() < 0.02: # Frequent (was 0.005)
        p_type = random.choice(['health', 'shield', 'laser'])
        
        pickups.append({
            'x': random.uniform(-60, 60),
            'y': random.uniform(-30, 30),
            'z': -800,
            'type': p_type,
            'rot': 0,
            'active': True
        })

def update_pickups():
    """Move pickups and check collisions"""
    global player_hp, player_shield, laser_active, laser_timer
    
    # Update Laser Timer
    if laser_active:
        laser_timer -= 0.016
        if laser_timer <= 0:
            laser_active = False
    
    for p in pickups:
        if not p['active']: continue
        
        p['z'] += PICKUP_SPEED
        p['rot'] = (p['rot'] + 2) % 360
        
        # Collision with Player
        dx = player_x - p['x']
        dy = player_y - p['y']
        dz = player_z - p['z']
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if dist < 12: # Pickup radius + player radius
            p['active'] = False
            
            # Apply Effect
            if p['type'] == 'health':
                player_hp = min(100, player_hp + 20)
                print("Picked up Health!")
            elif p['type'] == 'shield':
                player_shield = True
                print("Shield Activated!")
            elif p['type'] == 'laser':
                laser_active = True
                laser_timer = LASER_DURATION
                print("Laser Weapon Active!")
    
    # Cleanup
    pickups[:] = [p for p in pickups if p['active'] and p['z'] < 50]

def spawn_ring():
    """Spawn bonus rings"""
    if random.random() < 0.005: # Rare (Too many before)
        rings.append({
            'x': random.uniform(-60, 60),
            'y': random.uniform(-30, 30),
            'z': -800,
            'rot': 0,
            'active': True
        })

def update_rings():
    """Move rings and check collision"""
    global score
    
    for r in rings:
        if not r['active']: continue
        
        r['z'] += RING_SPEED
        r['rot'] = (r['rot'] + 1) % 360
        
        # Collision (Fly through)
        dx = player_x - r['x']
        dy = player_y - r['y']
        dz = player_z - r['z']
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if dist < 15: # Ring radius approx
            r['active'] = False
            score += 100
            print("Ring Collected! +100")
            
    rings[:] = [r for r in rings if r['active'] and r['z'] < 50]

def draw_rings():
    """Draw rings using cylinder segments (Torus-like)"""
    for r in rings:
        glPushMatrix()
        glTranslatef(r['x'], r['y'], r['z'])
        glRotatef(r['rot'], 0, 0, 1) # Spin animation
        
        glColor3f(1.0, 0.8, 0.0)
        
        # Approximate torus geometry using segments
        radius = 5 
        tube_radius = 0.8
        segments = 8
        angle_step = 360 / segments
        
        for i in range(segments):
            glPushMatrix()
            angle = i * angle_step
            # Calculate vertex position on circle
            rad = math.radians(angle)
            x = math.cos(rad) * radius
            y = math.sin(rad) * radius
            
            glTranslatef(x, y, 0)
            
            # Rotate segment to be tangent to the circle
            glRotatef(angle + 90, 0, 0, 1) 
            
            # Calculate chord length to close the gap between segments
            length = 2 * radius * math.sin(math.radians(angle_step/2)) * 1.05
            
            # Center and align cylinder
            glTranslatef(0, -length/2, 0)
            glRotatef(90, 1, 0, 0) 
            
            draw_cylinder(tube_radius, length, 8, 1)
            glPopMatrix()
            
        glPopMatrix()

def draw_pickups():
    """Render rotating pickups"""
    for p in pickups:
        glPushMatrix()
        glTranslatef(p['x'], p['y'], p['z'])
        glRotatef(p['rot'], 0, 1, 0)
        
        # Outer Shell (Solid sphere instead of wireframe)
        glColor3f(1.0, 1.0, 1.0)
        # We can't use glBlendFunc for transparency, so we make it small or just rely on color
        # Spec only allows gluSphere
        # We'll just draw the icon larger and skip the shell or make shell small?
        # Let's draw the shell as a small "core" or skip it to avoid obscuring the icon.
        # Or just draw the icon.
        
        # Icon inside
        if p['type'] == 'health':
            glColor3f(0.0, 1.0, 0.0) # Green Cross
            glPushMatrix()
            glScalef(2.0, 0.5, 0.5)
            draw_cube(1.5)
            glPopMatrix()
            glPushMatrix()
            glScalef(0.5, 2.0, 0.5)
            draw_cube(1.5)
            glPopMatrix()
            
        elif p['type'] == 'shield':
            glColor3f(0.0, 0.5, 1.0) # Blue Sphere
            draw_sphere(2.5)
            
        elif p['type'] == 'laser':
            glColor3f(1.0, 0.0, 0.0) # Red Beam/Bar
            glPushMatrix()
            glScalef(0.5, 0.5, 4.0)
            draw_cube(1.5)
            glPopMatrix()
            
        glPopMatrix()


import random

def spawn_obstacle():
    """Spawn a new obstacle at the far end of the world"""
    if random.random() < 0.15:  # Increased spawn rate
        # Determine obstacle type based on level
        if current_level == 0:   # Forest
            obs_type = 'tree'
        elif current_level == 1: # Ocean
            obs_type = 'buoy'
        elif current_level == 2: # Desert
            obs_type = 'cactus'
        elif current_level == 3: # Purple
            obs_type = 'mushroom'
        else:                    # Volcanic
            obs_type = 'spike'
            
        # Spawn mostly on sides, creating a "tunnel" effect
        # Center path (-25 to 25) is safer
        if random.random() < 0.7:
            # Side spawn
            if random.choice([True, False]):
                x_pos = random.uniform(-120, -30)
            else:
                x_pos = random.uniform(30, 120)
        else:
            # Occasional center obstacle
            x_pos = random.uniform(-30, 30)
        
        y_pos = -100 
        
        obstacles.append({
            'x': x_pos,
            'y': y_pos,
            'z': OBSTACLE_SPAWN_Z,
            'type': obs_type,
            'active': True,
            'radius': 8
        })

def update_obstacles():
    """Move obstacles and check collisions"""
    global player_hp, elapsed_time, last_time, player_shield, cheat_mode
    
    # Obstacle movement speed
    move_speed = 3.0 
    
    for obs in obstacles:
        if obs['active']:
            obs['z'] += move_speed 
            
            # Distance calculation for collision
            dx = player_x - obs['x']
            dy = player_y - obs['y']
            dz = player_z - obs['z']
            distance = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            # Check collision against radius
            if distance < (obs['radius'] + 5):
                obs['active'] = False
                if player_shield:
                    player_shield = False
                    print("Shield Absorbed Obstacle!")
                elif not cheat_mode:
                    player_hp -= 10
                    print(f"Collision! HP: {player_hp}")
            
            # Remove if behind camera
            if obs['z'] > OBSTACLE_DESPAWN_Z:
                obs['active'] = False
    
    obstacles[:] = [ob for ob in obstacles if ob['active']]

def draw_obstacles():
    """Render all active obstacles"""
    for obs in obstacles:
        glPushMatrix()
        glTranslatef(obs['x'], obs['y'], obs['z'])
        
        if obs['type'] == 'tree':
            # Forest Tree
            glColor3f(0.4, 0.3, 0.1)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            draw_cylinder(3, 30)
            glPopMatrix()
            glColor3f(0.2, 0.6, 0.1)
            glPushMatrix()
            glTranslatef(0, 30, 0)
            draw_sphere(12)
            glPopMatrix()
            
        elif obs['type'] == 'buoy':
            # Ocean Buoy (Red/White striped)
            glColor3f(0.8, 0.1, 0.1)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            draw_cylinder(4, 15)
            glPopMatrix()
            glColor3f(1.0, 1.0, 1.0) # White top
            glPushMatrix()
            glTranslatef(0, 15, 0)
            draw_sphere(5)
            glPopMatrix()
            
        elif obs['type'] == 'cactus':
            # Desert Cactus
            glColor3f(0.1, 0.6, 0.2)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            draw_cylinder(4, 35) # Main trunk
            glPopMatrix()
            # Arm
            glPushMatrix()
            glTranslatef(3, 20, 0)
            glRotatef(90, 0, 1, 0)
            draw_cylinder(2, 6)
            glPopMatrix()
            # Top of arm
            glPushMatrix()
            glTranslatef(9, 20, 0)
            glRotatef(-90, 1, 0, 0)
            draw_cylinder(2, 10)
            glPopMatrix()
            
        elif obs['type'] == 'mushroom':
            # Alien Mushroom
            glColor3f(0.8, 0.8, 0.9) # White/Purple Stalk
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            draw_cylinder(2, 25)
            glPopMatrix()
            glColor3f(0.6, 0.2, 0.8) # Purple Cap
            glPushMatrix()
            glTranslatef(0, 25, 0)
            glScalef(1.0, 0.3, 1.0)
            draw_sphere(14)
            glPopMatrix()
            
        elif obs['type'] == 'spike':
            # Volcanic Rock Spike
            glColor3f(0.4, 0.2, 0.2)
            glPushMatrix()
            glRotatef(-90, 1, 0, 0)
            draw_cylinder(0.1, 40) # Cone-ish (top radius 0.1, base radius default?)
            # gluCylinder takes baseRadius, topRadius, height. 
            # My wrapper takes radius, height. Let's use custom glutCone or just stacked cylinders
            # or just a sphere
            glPopMatrix()
            draw_sphere(12) # Just a boulder for now to be safe
            
        glPopMatrix()


def spawn_enemy():
    """Spawn enemies based on level difficulty"""
    if random.random() < 0.008: # Reduced spawn rate
        # Types: 'standard', 'fast', 'heavy'
        e_type = random.choice(['standard', 'fast', 'heavy'])
        
        x_pos = random.uniform(-50, 50)
        y_pos = random.uniform(-20, 40)
        
        # Lowered HP to make them easier to kill
        hp = 2 # Was 3
        if e_type == 'fast': hp = 1 # Was 2
        elif e_type == 'heavy': hp = 5 # Was 10
        
        enemies.append({
            'x': x_pos,
            'y': y_pos,
            'z': ENEMY_SPAWN_Z,
            'type': e_type,
            'hp': hp,
            'active': True,
            'radius': 8,
            'last_shot': 0
        })

def update_enemy_bullets():
    """Update enemy projectiles"""
    global player_hp, player_shield, cheat_mode
    
    speed = 3.0
    for b in enemy_bullets:
        b['x'] += b['dx'] * speed
        b['y'] += b['dy'] * speed
        b['z'] += b['dz'] * speed
        
        # Check collision with player
        dx = player_x - b['x']
        dy = player_y - b['y']
        dz = player_z - b['z']
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if dist < 8: # Player hit radius
            b['z'] = 100 # Remove
            if player_shield:
                player_shield = False
                print("Shield Absorbed Shot!")
            elif not cheat_mode:
                player_hp -= 5
                print(f"Hit by enemy! HP: {player_hp}")
            
    # Cleanup
    enemy_bullets[:] = [b for b in enemy_bullets if b['z'] < 50 and b['z'] > -1200]

def update_enemies():
    """Move enemies, handle shooting, and check collisions"""
    global player_hp, elapsed_time, player_shield, score, cheat_mode
    
    for e in enemies:
        if not e['active']: continue
        
        # Movement
        speed = 1.2 # Slower enemies
        if e['type'] == 'fast': speed = 2.0
        elif e['type'] == 'heavy': speed = 0.8
        
        e['z'] += speed 
        
        # Tracking
        if e['type'] != 'heavy':
            dx = player_x - e['x']
            dy = player_y - e['y']
            e['x'] += dx * 0.005
            e['y'] += dy * 0.005
            
        # Shooting Logic
        if random.random() < 0.015 and e['z'] > -700:
            dx = player_x - e['x']
            dy = player_y - e['y']
            dz = player_z - e['z']
            mag = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            enemy_bullets.append({
                'x': e['x'],
                'y': e['y'],
                'z': e['z'],
                'dx': dx / mag,
                'dy': dy / mag,
                'dz': dz / mag
            })
            
        # Collision with Player
        dx = player_x - e['x']
        dy = player_y - e['y']
        dz = player_z - e['z']
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if dist < (e['radius'] + 5):
            e['active'] = False
            if player_shield:
                player_shield = False
                print("Shield Absorbed Collision!")
            elif not cheat_mode:
                player_hp -= 10
                print("Crashed into enemy!")
            else:
                print("Cheat: Collision Ignored")
            
        # Collision with Bullets
        for b in bullets:
            # Check lateral distance (X/Y)
            bdx = b['x'] - e['x']
            bdy = b['y'] - e['y']
            lateral_dist = math.sqrt(bdx*bdx + bdy*bdy)
            
            # Hit radius for lateral check
            hit_radius = e['radius'] + 5 

            if lateral_dist < hit_radius:
                # Check Z depth (Swept collision)
                bullet_step = BULLET_SPEED * 20
                if b.get('type') == 'laser': bullet_step = BULLET_SPEED * 40 # Lasers appear longer
                
                z_start = b['z'] + e['radius']
                z_end = b['z'] - bullet_step - e['radius']
                
                if e['z'] <= z_start and e['z'] >= z_end:
                    # HIT!
                    if b.get('type') == 'laser':
                        e['hp'] -= 5 # High damage per frame
                        # Laser does NOT despawn (Piercing)
                    else:
                        e['hp'] -= 1
                        b['z'] = BULLET_MAX_DIST - 100 # Despawn bullet
                        
                    if e['hp'] <= 0:
                        e['active'] = False
                        pts = 50
                        if e['type'] == 'fast': pts = 100
                        elif e['type'] == 'heavy': pts = 300
                        score += pts
                        print(f"Enemy Destroyed! +{pts}")
                    
                    if b.get('type') != 'laser':
                        break # Bullet consumed (normal only)

    # Cleanup
    enemies[:] = [e for e in enemies if e['active'] and e['z'] < 50]


def draw_enemies():
    """Render enemies with better models"""
    for e in enemies:
        glPushMatrix()
        glTranslatef(e['x'], e['y'], e['z'])
        glRotatef(180, 0, 1, 0)
        
        if e['type'] == 'standard':
            glColor3f(0.8, 0.2, 0.2) # Redish Saucer
            glPushMatrix()
            glScalef(1.0, 0.3, 1.0)
            draw_sphere(8)
            glPopMatrix()
            glColor3f(0.4, 0.8, 1.0) # Cockpit
            glPushMatrix()
            glTranslatef(0, 2, 0)
            draw_sphere(4)
            glPopMatrix()
            
        elif e['type'] == 'fast':
            glColor3f(1.0, 0.8, 0.0) # Yellow Dart
            glPushMatrix()
            glScalef(0.5, 0.5, 2.0)
            draw_sphere(6)
            glPopMatrix()
            glColor3f(0.8, 0.6, 0.0) # Wings
            glPushMatrix()
            glScalef(2.0, 0.1, 0.5)
            draw_cube(8)
            glPopMatrix()
            
        elif e['type'] == 'heavy':
            glColor3f(0.5, 0.0, 0.8) # Purple Mothership
            draw_cube(12)
            glColor3f(0.8, 0.2, 0.8)
            glPushMatrix()
            glTranslatef(4, 4, 4)
            draw_sphere(4)
            glPopMatrix()
            
        glPopMatrix()


def spawn_missiles():
    """Fire a barrage of homing missiles"""
    global missile_cooldown_timer
    
    if missile_cooldown_timer <= 0:
        missile_cooldown_timer = MISSILE_COOLDOWN_MAX
        
        # Spawn 6 missiles in an arc
        for i in range(6):
            # Spread them out slightly
            offset_x = (i - 2.5) * 5
            missiles.append({
                'x': player_x + offset_x,
                'y': player_y,
                'z': player_z,
                'dx': 0, # Initial velocity (will be guided)
                'dy': 0, 
                'dz': -1,
                'target_id': None, # Will find target
                'life': 100 # Frames to live
            })

def update_missiles():
    """Update missile homing logic and collisions"""
    global missile_cooldown_timer, score
    
    # Cooldown tick
    if missile_cooldown_timer > 0:
        missile_cooldown_timer -= 0.016 # Approx 60 FPS
    
    for m in missiles:
        m['life'] -= 1
        m['z'] -= MISSILE_SPEED # Base forward movement
        
        # 1. Find Target if none or dead
        target = None
        best_dist = 9999
        
        # Check if current target is still valid
        valid_target = False
        if m['target_id'] is not None:
            for e in enemies:
                if id(e) == m['target_id'] and e['active']:
                    target = e
                    valid_target = True
                    break
        
        # Find new target if needed
        if not valid_target:
            m['target_id'] = None
            for e in enemies:
                if not e['active']: continue
                dx = e['x'] - m['x']
                dy = e['y'] - m['y']
                dz = e['z'] - m['z']
                dist = math.sqrt(dx*dx + dy*dy + dz*dz)
                
                # Prefer enemies in front
                if dz < 0 and dist < best_dist:
                    best_dist = dist
                    target = e
            
            if target:
                m['target_id'] = id(target)
        
        # 2. Homing Physics
        if target:
            # Vector to target
            tx, ty, tz = target['x'], target['y'], target['z']
            dx = tx - m['x']
            dy = ty - m['y']
            dz = tz - m['z']
            
            # Normalize
            mag = math.sqrt(dx*dx + dy*dy + dz*dz)
            if mag > 0:
                dx /= mag
                dy /= mag
                dz /= mag
                
                # Steer missile (interpolate velocity)
                steer_strength = 0.2
                m['dx'] = m['dx'] * (1 - steer_strength) + dx * steer_strength
                m['dy'] = m['dy'] * (1 - steer_strength) + dy * steer_strength
                m['dz'] = m['dz'] * (1 - steer_strength) + dz * steer_strength
        
        # Apply steering to position
        m['x'] += m['dx'] * MISSILE_SPEED
        m['y'] += m['dy'] * MISSILE_SPEED
        m['z'] += m['dz'] * MISSILE_SPEED # Extra Z push
        
        # 3. Collision with Enemies
        hit = False
        for e in enemies:
            if not e['active']: continue
            
            dx = m['x'] - e['x']
            dy = m['y'] - e['y']
            dz = m['z'] - e['z']
            dist = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            if dist < e['radius'] + 5:
                e['hp'] -= 5 # High damage
                hit = True
                if e['hp'] <= 0:
                    e['active'] = False
                    pts = 50
                    if e['type'] == 'fast': pts = 100
                    elif e['type'] == 'heavy': pts = 300
                    score += pts
                break
        
        if hit:
            m['life'] = 0 # Destroy missile

    # Cleanup
    missiles[:] = [m for m in missiles if m['life'] > 0 and m['z'] > BULLET_MAX_DIST]

def draw_missiles():
    """Render missiles"""
    for m in missiles:
        glPushMatrix()
        glTranslatef(m['x'], m['y'], m['z'])
        
        # Rotate to face direction of travel? 
        # For simplicity, just draw a cool shape
        
        glColor3f(1.0, 0.5, 0.0) # Orange
        draw_sphere(2)
        
        # Trail
        glColor3f(1.0, 1.0, 0.0)
        glBegin(GL_LINES)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0, 10) # Trail behind
        glEnd()
        
        glPopMatrix()


def spawn_boss():
    """Spawn the final level boss"""
    global boss
    boss = {
        'x': 0,
        'y': 20,
        'z': -200, # Stay in distance
        'hp': 500,
        'max_hp': 500,
        'active': True,
        'angle': 0,
        'timer': 0
    }

def update_boss():
    """Update boss behavior"""
    global boss, player_hp, score, game_state, player_shield
    
    if not boss or not boss['active']: return
    
    # Movement: Figure 8 or Sine
    boss['angle'] += 0.02
    boss['x'] = math.sin(boss['angle']) * 80
    boss['y'] = math.cos(boss['angle'] * 2) * 30 + 10
    
    # Shooting
    boss['timer'] += 1
    if boss['timer'] > 60:
        boss['timer'] = 0
        # Fire spread
        for i in range(-1, 2):
            dx = (player_x - boss['x']) + i * 40
            dy = (player_y - boss['y'])
            dz = (player_z - boss['z'])
            mag = math.sqrt(dx*dx + dy*dy + dz*dz)
            
            enemy_bullets.append({
                'x': boss['x'],
                'y': boss['y'],
                'z': boss['z'],
                'dx': dx / mag,
                'dy': dy / mag,
                'dz': dz / mag
            })
            
    # Collision with Player Bullets
    for b in bullets:
        dx = b['x'] - boss['x']
        dy = b['y'] - boss['y']
        dz = b['z'] - boss['z']
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        # Boss Hitbox is large
        if dist < 25:
            if b.get('type') == 'laser':
                boss['hp'] -= 2 # Laser tick
            else:
                boss['hp'] -= 5
                b['z'] = 100 # Despawn
            
            if boss['hp'] <= 0:
                boss['active'] = False
                score += 5000
                print("BOSS DEFEATED!")
                # Trigger Win
                # We'll handle win state in logic
                
            if b.get('type') != 'laser':
                break

    # Collision with Missiles
    for m in missiles:
        dx = m['x'] - boss['x']
        dy = m['y'] - boss['y']
        dz = m['z'] - boss['z']
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if dist < 25:
            boss['hp'] -= 15
            m['life'] = 0
            if boss['hp'] <= 0:
                boss['active'] = False
                score += 5000

def draw_boss():
    """Render the Boss"""
    if not boss or not boss['active']: return
    
    glPushMatrix()
    glTranslatef(boss['x'], boss['y'], boss['z'])
    
    # Main Body
    glColor3f(0.8, 0.0, 0.0) # Red
    draw_sphere(15)
    
    # Spikes / Details
    glColor3f(0.2, 0.0, 0.0)
    for i in range(8):
        glPushMatrix()
        glRotatef(i * 45 + boss['timer'], 0, 0, 1)
        glTranslatef(15, 0, 0)
        glRotatef(90, 0, 1, 0)
        draw_cylinder(2, 10)
        glPopMatrix()
        
    # Core
    glColor3f(1.0, 0.5, 0.0)
    glPushMatrix()
    glScalef(1.2 + math.sin(boss['timer']*0.1)*0.2, 1.2, 1.2) # Pulsing effect
    draw_sphere(8)
    glPopMatrix()
    
    glPopMatrix()


def update_bullets():
    """Move bullets and check cleanup"""
    for b in bullets:
        b['z'] -= BULLET_SPEED * 20 # Move forward fast
    
    # Remove far bullets
    bullets[:] = [b for b in bullets if b['z'] > BULLET_MAX_DIST]

def draw_bullets():
    """Render bullets and 3D crosshair"""
    # Bullets & Lasers
    for b in bullets:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], b['z'])
        
        if b.get('type') == 'laser':
            # Laser: Long Red Beam
            glColor3f(1.0, 0.0, 0.2)
            glScalef(1.5, 0.5, 40.0) # Very long
            draw_cube(2)
        else:
            # Normal: Yellow
            glColor3f(1.0, 1.0, 0.0)
            glScalef(2.0, 2.0, 8.0)
            draw_sphere(2)
            
        glPopMatrix()
        
    # Enemy Bullets
    glColor3f(1.0, 0.0, 0.0) # Red
    for b in enemy_bullets:
        glPushMatrix()
        glTranslatef(b['x'], b['y'], b['z'])
        draw_sphere(1.5) # Smaller and less distracting
        glPopMatrix()
        
    # 3D Crosshair (Projected at target distance)
    # This helps aim
    glPushMatrix()
    glTranslatef(player_x, player_y, player_z - 600) # Slightly closer than max range for visibility
    glColor3f(0.0, 1.0, 0.0)
    # glLineWidth removed
    glBegin(GL_LINES)
    # Plus sign
    glVertex3f(-20, 0, 0); glVertex3f(20, 0, 0)
    glVertex3f(0, -20, 0); glVertex3f(0, 20, 0)
    glEnd()
    # glLineWidth(1) removed
    
    # Add a circle around it for better visibility
    glBegin(GL_LINE_LOOP)
    for i in range(20):
        angle = 2 * 3.14159 * i / 20
        glVertex3f(math.cos(angle)*15, math.sin(angle)*15, 0)
    glEnd()
    
    glPopMatrix()

def update_game_logic():
    """Update movement and game state logic"""
    global player_x, player_y, player_z, player_vx, player_vy, game_state, current_level, score, boss
    
    if game_state == PLAYING and not paused:
        # Check Game Over
        if player_hp <= 0:
            game_state = GAME_OVER
            return

        # Level Progression
        if current_level == 0 and score >= 200:
            current_level = 1
            print("Level Up! -> 2")
        elif current_level == 1 and score >= 500:
            current_level = 2
            print("Level Up! -> 3")
        elif current_level == 2 and score >= 1000:
            current_level = 3
            print("Level Up! -> 4")
        elif current_level == 3 and score >= 1500:
            current_level = 4
            spawn_boss()
            print("BOSS BATTLE START!")
        
        # Boss Win Condition
        if current_level == 4:
            if boss and not boss['active']:
                # Boss Dead
                print("YOU WIN!")
                game_state = GAME_OVER # Reuse screen, maybe change text
                # We can handle text change in draw_game_over based on score/boss state
        
        # Apply Velocity & Friction
        player_x += player_vx
        player_y += player_vy
        
        # Apply friction
        friction = 0.85
        player_vx *= friction
        player_vy *= friction
        
        # Zero out low velocity
        if abs(player_vx) < 0.1: player_vx = 0
        if abs(player_vy) < 0.1: player_vy = 0

        # Boundary checks
        player_x = max(-player_bounds_x, min(player_bounds_x, player_x))
        player_y = max(-player_bounds_y, min(player_bounds_y, player_y))
        
        # Wall bounce
        if player_x == -player_bounds_x or player_x == player_bounds_x: player_vx = 0
        if player_y == -player_bounds_y or player_y == player_bounds_y: player_vy = 0

        # Update World
        spawn_obstacle()
        update_obstacles()
        
        spawn_pickup()
        update_pickups()
        
        if current_level < 4: # No minions during boss? Or maybe just fewer?
            spawn_enemy() # Let them spawn for difficulty
        
        update_enemies()
        update_enemy_bullets()
        
        if current_level == 4:
            update_boss()
        
        spawn_ring()
        update_rings()
        
        update_bullets()
        update_missiles()


def idle():
    """Idle callback for continuous rendering"""
    update_game_logic()
    display()


def reshape(width, height):
    """Reshape callback"""
    glViewport(0, 0, width, height)


# ============ MAIN ============

def main():
    """Initialize and run the game"""
    glutInit(sys.argv)
    glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(100, 100)
    glutCreateWindow(b"StratoQuest")
    
    glEnable(GL_DEPTH_TEST)
    glViewport(0, 0, WINDOW_WIDTH, WINDOW_HEIGHT)
    
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    # glutKeyboardUpFunc removed to comply with spec
    glutSpecialFunc(special)
    glutMouseFunc(mouse)
    glutIdleFunc(idle)
    
    glutMainLoop()


if __name__ == "__main__":
    main()
