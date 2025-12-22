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


# ============ LEVEL RENDERING ============

def draw_level_1():
    """Level 1: Blue sky + green forest ground"""
    glLoadIdentity()
    
    # Draw far background quad - moves with parallax effect
    background_z = -600 + (elapsed_time * 80) % 80
    glBegin(GL_QUADS)
    glColor3f(0.5, 0.8, 0.6)
    glVertex3f(-600, -600, background_z)
    glVertex3f(600, -600, background_z)
    glVertex3f(600, 600, background_z)
    glVertex3f(-600, 600, background_z)
    glEnd()
    
    # Multiple ground planes at different depths for parallax effect
    for layer in range(-600, 600, 80):
        z_pos = layer + (elapsed_time * 80) % 80
        # Green forest ground
        draw_ground_plane(z_pos, (0.2, 0.6, 0.2), size=400, grid_spacing=35)
    
    # Draw sun in background (far away)
    glPushMatrix()
    glTranslatef(50, 80, -200)
    glColor3f(1.0, 1.0, 0.0)
    draw_sphere(15, slices=80, stacks=80)
    glPopMatrix()
    
    # Draw clouds
    for i in range(5):
        x_pos = -120 + i * 60
        draw_cloud(x_pos, 40, -150 + i * 40, scale=1.2)
    
    # Draw trees (moving)
    for i in range(12):
        z_offset = -150 + i * 50 + (elapsed_time * 80)
        x_pos = -100 + (i % 4) * 70
        glPushMatrix()
        glTranslatef(x_pos, -100, z_offset)
        glColor3f(0.4, 0.3, 0.1)
        draw_cylinder(3, 30, slices=60, stacks=60)
        glPopMatrix()
        
        # Tree top (foliage)
        glPushMatrix()
        glTranslatef(x_pos, -70, z_offset)
        glColor3f(0.2, 0.5, 0.1)
        draw_sphere(8, slices=70, stacks=70)
        glPopMatrix()


def draw_level_2():
    """Level 2: Sunset sky + dark blue ocean ground"""
    glLoadIdentity()
    # Draw sunset background - moves with parallax effect
    background_z = -600 + (elapsed_time * 85) % 80
    glBegin(GL_QUADS)
    glColor3f(1.0, 0.6, 0.3)
    glVertex3f(-600, -600, background_z)
    glVertex3f(600, -600, background_z)
    glVertex3f(600, 600, background_z)
    glVertex3f(-600, 600, background_z)
    glEnd()
    
    # Dark blue ocean ground
    for layer in range(-600, 600, 80):
        z_pos = layer + (elapsed_time * 85) % 80
        draw_ground_plane(z_pos, (0.1, 0.3, 0.6), size=400, grid_spacing=35)
    
    # Draw sun (orange/red)
    glPushMatrix()
    glTranslatef(-50, 60, -200)
    glColor3f(1.0, 0.5, 0.0)
    draw_sphere(20, slices=80, stacks=80)
    glPopMatrix()
    
    # Draw water waves as moving spheres
    for i in range(12):
        z_offset = -100 + i * 60 + (elapsed_time * 85)
        x_pos = -140 + (i % 5) * 70
        glPushMatrix()
        glTranslatef(x_pos, -95, z_offset)
        glColor3f(0.2, 0.5, 0.8)
        draw_sphere(6, slices=60, stacks=60)
        glPopMatrix()


def draw_level_3():
    """Level 3: Blue sky + orange desert ground"""
    glLoadIdentity()
    # Draw blue sky background - moves with parallax effect
    background_z = -600 + (elapsed_time * 82) % 80
    glBegin(GL_QUADS)
    glColor3f(0.4, 0.7, 1.0)
    glVertex3f(-600, -600, background_z)
    glVertex3f(600, -600, background_z)
    glVertex3f(600, 600, background_z)
    glVertex3f(-600, 600, background_z)
    glEnd()
    
    # Orange desert ground
    for layer in range(-600, 600, 80):
        z_pos = layer + (elapsed_time * 82) % 80
        draw_ground_plane(z_pos, (1.0, 0.7, 0.3), size=400, grid_spacing=35)
    
    # Draw clouds
    for i in range(5):
        x_pos = -100 + i * 50
        draw_cloud(x_pos, 50, -140 + i * 50, scale=1.1)
    
    # Draw sand dunes as rounded shapes
    for i in range(12):
        z_offset = -150 + i * 50 + (elapsed_time * 82)
        x_pos = -100 + (i % 4) * 70
        y_offset = 10 + (i % 2) * 15
        glPushMatrix()
        glTranslatef(x_pos, -100 - y_offset, z_offset)
        glColor3f(0.9, 0.8, 0.4)
        draw_sphere(12, slices=70, stacks=70)
        glPopMatrix()


def draw_level_4():
    """Level 4: Purple sunset + green forest ground"""
    glLoadIdentity()
    # Draw purple sky background - moves with parallax effect
    background_z = -600 + (elapsed_time * 78) % 80
    glBegin(GL_QUADS)
    glColor3f(0.6, 0.3, 0.8)
    glVertex3f(-600, -600, background_z)
    glVertex3f(600, -600, background_z)
    glVertex3f(600, 600, background_z)
    glVertex3f(-600, 600, background_z)
    glEnd()
    
    # Green forest ground
    for layer in range(-600, 600, 80):
        z_pos = layer + (elapsed_time * 78) % 80
        draw_ground_plane(z_pos, (0.3, 0.5, 0.2), size=400, grid_spacing=35)
    
    # Sun
    glPushMatrix()
    glTranslatef(60, 50, -200)
    glColor3f(1.0, 0.4, 0.2)
    draw_sphere(18, slices=80, stacks=80)
    glPopMatrix()
    
    # Draw clouds
    for i in range(6):
        x_pos = -120 + i * 50
        draw_cloud(x_pos, 45, -160 + i * 35, scale=1.1)
    
    # Draw trees
    for i in range(12):
        z_offset = -150 + i * 50 + (elapsed_time * 78)
        x_pos = -100 + (i % 4) * 70
        glPushMatrix()
        glTranslatef(x_pos, -100, z_offset)
        glColor3f(0.3, 0.2, 0.1)
        draw_cylinder(4, 35, slices=60, stacks=60)
        glPopMatrix()
        
        # Tree top (foliage)
        glPushMatrix()
        glTranslatef(x_pos, -65, z_offset)
        glColor3f(0.3, 0.6, 0.2)
        draw_sphere(10, slices=70, stacks=70)
        glPopMatrix()


def draw_level_5():
    """Level 5: Red sky (final boss level) + red volcanic ground"""
    glLoadIdentity()
    # Draw red sky background - moves with parallax effect
    background_z = -600 + (elapsed_time * 75) % 80
    glBegin(GL_QUADS)
    glColor3f(1.0, 0.3, 0.2)
    glVertex3f(-600, -600, background_z)
    glVertex3f(600, -600, background_z)
    glVertex3f(600, 600, background_z)
    glVertex3f(-600, 600, background_z)
    glEnd()
    
    # Red volcanic ground
    for layer in range(-600, 600, 80):
        z_pos = layer + (elapsed_time * 75) % 80
        draw_ground_plane(z_pos, (0.8, 0.2, 0.1), size=400, grid_spacing=35)
    
    # Large ominous sphere (boss indicator)
    glPushMatrix()
    glTranslatef(0, 0, -150)
    glColor3f(0.8, 0.0, 0.0)
    draw_sphere(25, slices=80, stacks=80)
    glPopMatrix()
    
    # Surrounding rocks (moving) - use spheres for smoother look
    for i in range(14):
        angle = (i / 14.0) * 2 * math.pi
        x = math.cos(angle) * 100
        y = math.sin(angle) * 70
        z_offset = -120 + (i % 4) * 50 + (elapsed_time * 75)
        glPushMatrix()
        glTranslatef(x, y - 100, z_offset)
        glColor3f(0.6, 0.3, 0.2)
        draw_sphere(10, slices=70, stacks=70)
        glPopMatrix()


def draw_current_level():
    """Draw the current level's visuals"""
    levels = [draw_level_1, draw_level_2, draw_level_3, draw_level_4, draw_level_5]
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    if 0 <= current_level < len(levels):
        levels[current_level]()


# ============ MENU RENDERING ============

def draw_menu():
    """Draw main menu"""
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    
    # Dark background
    glBegin(GL_QUADS)
    glColor3f(0.1, 0.1, 0.15)
    glVertex3f(-640, 0, -100)
    glVertex3f(640, 0, -100)
    glVertex3f(640, 720, -100)
    glVertex3f(-640, 720, -100)
    glEnd()
    
    # Title
    draw_text_2d("STRATO QUEST", WINDOW_WIDTH // 2, 150, 
                 color=(1.0, 1.0, 0.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    
    # Instructions
    draw_text_2d("Press SPACE to Start", WINDOW_WIDTH // 2, 350,
                 color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_2d("or ESC to Quit", WINDOW_WIDTH // 2, 420,
                 color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)


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
    glOrtho(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex3f(0, 0, -1)
    glVertex3f(WINDOW_WIDTH, 0, -1)
    glVertex3f(WINDOW_WIDTH, WINDOW_HEIGHT, -1)
    glVertex3f(0, WINDOW_HEIGHT, -1)
    glEnd()
    
    # Title
    draw_text_2d("SELECT LEVEL", WINDOW_WIDTH // 2, 80,
                 color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    
    # Draw level buttons - centered
    start_x = WINDOW_WIDTH // 2 - 400
    for i in range(5):
        x_pos = start_x + i * 200
        y_pos = 250
        
        # Highlight selected level
        if i == selected_level:
            draw_text_2d(f"LEVEL {i + 1}", x_pos, y_pos,
                        color=(1.0, 1.0, 0.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
        else:
            draw_text_2d(f"Level {i + 1}", x_pos, y_pos,
                        color=(0.7, 0.7, 0.7), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    
    # Instructions - centered
    draw_text_2d("LEFT/RIGHT arrows to select", WINDOW_WIDTH // 2, 450,
                 color=(0.8, 0.8, 0.8), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_2d("ENTER to play", WINDOW_WIDTH // 2, 520,
                 color=(0.8, 0.8, 0.8), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_2d("ESC to back to menu", WINDOW_WIDTH // 2, 590,
                 color=(0.8, 0.8, 0.8), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_pause_menu():
    """Draw pause menu overlay with semi-transparent background"""
    # Semi-transparent overlay (2D)
    glClear(GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    glOrtho(0, WINDOW_WIDTH, WINDOW_HEIGHT, 0, -1, 1)
    
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    
    glColor3f(0.0, 0.0, 0.0)
    glBegin(GL_QUADS)
    glVertex3f(0, 0, 0)
    glVertex3f(WINDOW_WIDTH, 0, 0)
    glVertex3f(WINDOW_WIDTH, WINDOW_HEIGHT, 0)
    glVertex3f(0, WINDOW_HEIGHT, 0)
    glEnd()
    
    # Text
    draw_text_2d("PAUSED", WINDOW_WIDTH // 2, 250,
                 color=(1.0, 1.0, 0.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_2d("Press ESC to continue", WINDOW_WIDTH // 2, 350,
                 color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    draw_text_2d("SPACE to go back to menu", WINDOW_WIDTH // 2, 420,
                 color=(1.0, 1.0, 1.0), font=GLUT_BITMAP_TIMES_ROMAN_24, centered=True)
    
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
    elapsed_time += delta_time
    
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, (WINDOW_WIDTH / WINDOW_HEIGHT), 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    
    if game_state == MENU:
        draw_menu()
    elif game_state == LEVEL_SELECT:
        draw_level_select()
    elif game_state == PLAYING:
        draw_current_level()
        if paused:
            draw_pause_menu()
    elif game_state == GAME_OVER:
        draw_menu()
    
    glutSwapBuffers()


def keyboard(key, x, y):
    """Keyboard callback"""
    global game_state, selected_level, current_level, paused
    
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
    
    glutPostRedisplay()


def special(key, x, y):
    """Special keys callback (arrows)"""
    global selected_level
    
    if game_state == LEVEL_SELECT:
        if key == GLUT_KEY_LEFT:
            selected_level = max(0, selected_level - 1)
        elif key == GLUT_KEY_RIGHT:
            selected_level = min(4, selected_level + 1)
        
        glutPostRedisplay()


def idle():
    """Idle callback for continuous rendering"""
    glutPostRedisplay()


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
    
    glutDisplayFunc(display)
    glutKeyboardFunc(keyboard)
    glutSpecialFunc(special)
    glutReshapeFunc(reshape)
    glutIdleFunc(idle)
    
    glutMainLoop()


if __name__ == "__main__":
    main()
