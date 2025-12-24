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

enemies = [] # [{'x', 'y', 'z', 'type', 'hp'}]
ENEMY_SPAWN_Z = -800

# Movement state
keys_pressed = {
    'w': False,
    'a': False,
    's': False,
    'd': False
}

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
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    # 1. Crosshair
    mid_x, mid_y = WINDOW_WIDTH / 2, WINDOW_HEIGHT / 2
    size = 15
    glColor3f(0.0, 1.0, 0.0) # Green
    glBegin(GL_LINES)
    glVertex2f(mid_x - size, mid_y)
    glVertex2f(mid_x + size, mid_y)
    glVertex2f(mid_x, mid_y - size)
    glVertex2f(mid_x, mid_y + size)
    glEnd()
    
    # 2. Health Bar
    bar_x, bar_y = 50, 50
    bar_width, bar_height = 200, 20
    
    # Background (Red/Empty)
    glColor3f(0.5, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + bar_width, bar_y)
    glVertex2f(bar_x + bar_width, bar_y + bar_height)
    glVertex2f(bar_x, bar_y + bar_height)
    glEnd()
    
    # Foreground (Green/HP)
    hp_pct = max(0, player_hp / 100.0)
    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + bar_width * hp_pct, bar_y)
    glVertex2f(bar_x + bar_width * hp_pct, bar_y + bar_height)
    glVertex2f(bar_x, bar_y + bar_height)
    glEnd()
    
    # Border
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2)
    glBegin(GL_LINE_LOOP)
    glVertex2f(bar_x, bar_y)
    glVertex2f(bar_x + bar_width, bar_y)
    glVertex2f(bar_x + bar_width, bar_y + bar_height)
    glVertex2f(bar_x, bar_y + bar_height)
    glEnd()
    glLineWidth(1)
    
    draw_text_2d(f"HP: {int(player_hp)}", bar_x, bar_y - 10)
    
    # 3. Level Info
    draw_text_2d(f"LEVEL {current_level + 1}", WINDOW_WIDTH - 150, 50)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


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
        draw_bullets()
        draw_hud()
        
        if paused:
            draw_pause_menu()
    elif game_state == GAME_OVER:
        draw_menu()
    
    glutSwapBuffers()


def mouse(button, state, x, y):
    """Mouse callback for shooting"""
    global game_state, bullets
    
    if game_state == PLAYING and not paused:
        if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN:
            # Spawn bullet at player position
            bullets.append({
                'x': player_x,
                'y': player_y,
                'z': player_z - 5 # Start slightly ahead
            })

def keyboard(key, x, y):
    """Keyboard callback"""
    global game_state, selected_level, current_level, paused, keys_pressed
    
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
    
    elif key == b' ':  # SPACE
        if game_state == MENU:
            game_state = LEVEL_SELECT
            selected_level = 0
        elif game_state == PLAYING and paused:
            game_state = LEVEL_SELECT
            paused = False
    
    elif key == b'\r':  # ENTER
        if game_state == LEVEL_SELECT:
            current_level = selected_level
            game_state = PLAYING
            paused = False
            
    # Track WASD for movement
    if key == b'w': keys_pressed['w'] = True
    if key == b'a': keys_pressed['a'] = True
    if key == b's': keys_pressed['s'] = True
    if key == b'd': keys_pressed['d'] = True


def keyboard_up(key, x, y):
    """Keyboard release callback"""
    global keys_pressed
    key = key.lower()
    if key == b'w': keys_pressed['w'] = False
    if key == b'a': keys_pressed['a'] = False
    if key == b's': keys_pressed['s'] = False
    if key == b'd': keys_pressed['d'] = False


def special(key, x, y):
    """Special keys callback (arrows)"""
    global selected_level
    
    if game_state == LEVEL_SELECT:
        if key == GLUT_KEY_LEFT:
            selected_level = max(0, selected_level - 1)
        elif key == GLUT_KEY_RIGHT:
            selected_level = min(4, selected_level + 1)


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
    global player_hp, elapsed_time, last_time
    
    # We need delta_time for consistent movement
    # But update_game_logic is called from idle(), which doesn't pass delta.
    # We'll trust the global frame timing or just use a fixed per-frame move for now
    # to match the visual ground scroll which is time-based.
    
    # Ideally: move_amount = GAME_SPEED * 20 * delta_time
    # But currently ground moves by (elapsed_time * GAME_SPEED * 20)
    # So obstacles must move at that same rate.
    
    # Let's standardise: 
    # Movement per frame = (Change in elapsed_time) * Speed_Factor
    # We can't easily get 'Change in elapsed_time' inside this function without passing it.
    
    # FIX: We will just move them by a fixed amount that 'looks' right for now,
    # OR better, update obstacle Z based on creation time? No, that's complex for collisions.
    
    # Let's use a small fixed value that approximates the visual speed.
    move_speed = 3.0 # Experimentally adjusted
    
    for obs in obstacles:
        if obs['active']:
            obs['z'] += move_speed 
            
            # Collision Detection
            dx = player_x - obs['x']
            dy = player_y - obs['y']
            dz = player_z - obs['z']
            distance = math.sqrt(dx*dx + dy*dy + dz*dz) # 3D distance
            
            # For "Ground" objects, we mostly care about X/Z distance if Y is close enough
            # But full 3D check is fine if player can fly over them.
            
            if distance < (obs['radius'] + 5):
                obs['active'] = False
                player_hp -= 10
                print(f"Collision! HP: {player_hp}")
            
            # Despawn
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
    if random.random() < 0.02: # 2% chance per frame
        # Types: 'standard', 'fast', 'heavy'
        e_type = random.choice(['standard', 'fast', 'heavy'])
        
        x_pos = random.uniform(-60, 60)
        y_pos = random.uniform(-40, 40) # Enemies fly in the air
        
        hp = 3
        if e_type == 'fast': hp = 1
        elif e_type == 'heavy': hp = 7
        
        enemies.append({
            'x': x_pos,
            'y': y_pos,
            'z': ENEMY_SPAWN_Z,
            'type': e_type,
            'hp': hp,
            'active': True,
            'radius': 6
        })

def update_enemies():
    """Move enemies and check bullet collisions"""
    global player_hp
    
    for e in enemies:
        if not e['active']: continue
        
        # Movement
        speed = 2.0
        if e['type'] == 'fast': speed = 3.5
        elif e['type'] == 'heavy': speed = 1.0
        
        e['z'] += speed # Move towards player
        
        # Basic tracking (move x/y towards player)
        if e['type'] != 'heavy': # Heavy just moves straight
            dx = player_x - e['x']
            dy = player_y - e['y']
            e['x'] += dx * 0.01
            e['y'] += dy * 0.01
            
        # Collision with Player
        dx = player_x - e['x']
        dy = player_y - e['y']
        dz = player_z - e['z']
        dist = math.sqrt(dx*dx + dy*dy + dz*dz)
        
        if dist < (e['radius'] + 5):
            e['active'] = False
            player_hp -= 10
            print("Crashed into enemy!")
            
        # Collision with Bullets
        for b in bullets:
            bdx = b['x'] - e['x']
            bdy = b['y'] - e['y']
            bdz = b['z'] - e['z']
            b_dist = math.sqrt(bdx*bdx + bdy*bdy + bdz*bdz)
            
            if b_dist < e['radius'] + 2:
                e['hp'] -= 1
                b['z'] = BULLET_MAX_DIST - 100 # Remove bullet effectively
                if e['hp'] <= 0:
                    e['active'] = False
                    print("Enemy Destroyed!")

    # Cleanup
    enemies[:] = [e for e in enemies if e['active'] and e['z'] < 50]


def draw_enemies():
    """Render enemies"""
    for e in enemies:
        glPushMatrix()
        glTranslatef(e['x'], e['y'], e['z'])
        
        if e['type'] == 'standard':
            glColor3f(1.0, 0.0, 0.0) # Red Cube
            draw_cube(8)
        elif e['type'] == 'fast':
            glColor3f(1.0, 1.0, 0.0) # Yellow Triangle/Cone
            glutSolidCone(5, 10, 10, 10)
        elif e['type'] == 'heavy':
            glColor3f(0.5, 0.0, 0.5) # Purple Large Cube
            draw_cube(12)
            
        glPopMatrix()


def update_bullets():
    """Move bullets and check cleanup"""
    for b in bullets:
        b['z'] -= BULLET_SPEED * 20 # Move forward fast
    
    # Remove far bullets
    bullets[:] = [b for b in bullets if b['z'] > BULLET_MAX_DIST]

def draw_bullets():
    """Render bullets"""
    glColor3f(1.0, 1.0, 0.0) # Yellow tracers
    glBegin(GL_LINES)
    for b in bullets:
        glVertex3f(b['x'], b['y'], b['z'])
        glVertex3f(b['x'], b['y'], b['z'] + 10) # Trail
    glEnd()

def update_game_logic():
    """Update movement and game state logic"""
    global player_x, player_y, player_z
    
    if game_state == PLAYING and not paused:
        # Move player
        if keys_pressed['w']: player_y += player_speed
        if keys_pressed['s']: player_y -= player_speed
        if keys_pressed['a']: player_x -= player_speed
        if keys_pressed['d']: player_x += player_speed
        
        # Keep player within bounds
        player_x = max(-player_bounds_x, min(player_bounds_x, player_x))
        player_y = max(-player_bounds_y, min(player_bounds_y, player_y))
        
        # Update World
        spawn_obstacle()
        update_obstacles()
        
        spawn_enemy()
        update_enemies()
        
        update_bullets()


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
    glutKeyboardUpFunc(keyboard_up)
    glutSpecialFunc(special)
    glutMouseFunc(mouse)
    glutIdleFunc(idle)
    
    glutMainLoop()


if __name__ == "__main__":
    main()
