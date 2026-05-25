from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import math
import random
import time
#global variables
WINDOW_WIDTH, WINDOW_HEIGHT = 1200, 650
TEXT_HEIGHT = 120
OCEAN_HEIGHT = WINDOW_HEIGHT - TEXT_HEIGHT
#camera
camera_x, camera_y, camera_z = 0, 100, 550
angle = 0
submarine_x, submarine_y = 0, 50
submarine_speed = 7
#variables
life = 10
game_over = False
level = 1
level_complete = False
#fish
fish_list = []
fish_spawn_counter = 0
MAX_FISH = 2
fish_speed_base = 0.3
#bubble and ocean
bubble_positions = [(i * 15 - 150, -150 + j * 40, 0) for i in range(6) for j in range(5)]
bubble_offset = 0
seaweed_positions = [(120, -150, 0), (150, -150, 0), (-180, -150, -50), (-150, -150, -50)]

#key
target = 4
collected_keys = 0
missed_keys = 0
key_list = []
key_spawn_counter = 0
KEY_SPAWN_INTERVAL = 900

#diamond
diamond_list = []
diamond_spawn_counter = 0
DIAMOND_SPAWN_INTERVAL = 600
points = 0 
#enemy sub
enemy_sub_list = []
enemy_bullet_list = []
enemy_spawn_counter = 0
ENEMY_SPAWN_INTERVAL = 1500 
ENEMY_SHOOT_INTERVAL = 480 
bullet_hits = 0  
MAX_BULLET_HITS = 15  
bullet_speed = 1.2
#points and depth
collected_points = 0
base_depth = submarine_y  
current_depth = submarine_y


#oxygen
oxygen_bars = 15
start_time = time.time()
oxygen_decrease_rate = 3.0  
#mouse click
mouse_click_x = -1
mouse_click_y = -1
#cheat mode
cheat_mode = False
cheat_target = None  
cheat_state = "HUNTING"  #states: hunting, surfacing,descending
cheat_oxygen_threshold = 5 
cheat_surface_timer = 0  

# Quit/Pause Buttons
is_paused = False
BTN_WIDTH = 100
BTN_HEIGHT = 30
PAUSE_BTN_X = WINDOW_WIDTH - 250
PAUSE_BTN_Y = 10
QUIT_BTN_X = WINDOW_WIDTH - 130
QUIT_BTN_Y = 10

def calculate_display_depth(sub_y):
    depth_m = int(((150 - sub_y) / 300.0) * 1000)
    return max(0, min(1000, depth_m))

def update_oxygen_rate():
    global oxygen_decrease_rate

    if current_depth >= base_depth:
        oxygen_decrease_rate = 3.0
    elif current_depth >= base_depth - 50:
        oxygen_decrease_rate = 2.0 
    else:
        oxygen_decrease_rate = 1.0 



def spawn_fish():
    y = random.uniform(-100, 100)
    z = random.uniform(-100, 100)
    colors = [
        (1.0, 0.5, 0.0), (1.0, 0.0, 0.5), (1.0, 0.8, 0.0),
        (0.0, 0.8, 1.0), (0.5, 1.0, 0.0), (1.0, 0.3, 0.7), (0.3, 1.0, 0.8)
    ]
    r, g, b = random.choice(colors)
    speed = fish_speed_base
    fish_list.append([550, y, z, r, g, b, speed])

def spawn_key():
    y = random.uniform(-100, 100)
    z = 0 
    min_distance = 80
    attempts = 0
    while attempts < 10:
        valid_position = True
        for fish in fish_list:
            if abs(fish[1] - y) < min_distance:
                valid_position = False
                break
        if valid_position:
            break
        y = random.uniform(-100, 100)
        attempts += 1
    key_list.append([550, y, z])

def spawn_diamond():
    y = random.uniform(-100, 100)
    z = random.uniform(-50, 50) 
    diamond_list.append([550, y, z])

def spawn_enemy_submarine():
    y = random.uniform(-80, 80)
    z = random.uniform(-30, 30)
    shoot_timer = 0
    enemy_sub_list.append([550, y, z, shoot_timer])


def spawn_enemy_bullet(enemy_x, enemy_y, enemy_z):
    #calculate direction towards player submarine
    dx = submarine_x - enemy_x
    dy = submarine_y - enemy_y
    distance = math.sqrt(dx ** 2 + dy ** 2)
    if distance > 0:
        dir_x = dx / distance
        dir_y = dy / distance
    else:
        dir_x = -1
        dir_y = 0
    enemy_bullet_list.append([enemy_x, enemy_y, enemy_z, dir_x, dir_y])

def update_enemy_submarines():
    global enemy_sub_list, game_over, life
    if game_over or level_complete or level < 2:
        return
    enemies_to_remove = []
    for i, enemy in enumerate(enemy_sub_list):
        enemy_x, enemy_y, enemy_z, shoot_timer = enemy
        enemy[0] -= 0.7 # move left
        enemy[3] += 1
        
        # Shoot player
        if enemy[3] >= ENEMY_SHOOT_INTERVAL:
            spawn_enemy_bullet(enemy_x, enemy_y, enemy_z)
            enemy[3] = 0  # Reset time
        if not cheat_mode:
            enemy_left = enemy_x - 30
            enemy_right = enemy_x + 30
            enemy_top = enemy_y + 15
            enemy_bottom = enemy_y - 15
            sub_left = submarine_x - 42
            sub_right = submarine_x + 42
            sub_top = submarine_y + 21
            sub_bottom = submarine_y - 21
            if (enemy_right > sub_left and enemy_left < sub_right and
                    enemy_top > sub_bottom and enemy_bottom < sub_top and
                    abs(enemy_z) < 50):
                game_over = True
                
        if enemy_x < -550:
            enemies_to_remove.append(i)
    for i in sorted(enemies_to_remove, reverse=True):
        enemy_sub_list.pop(i)

def update_enemy_bullets():
    global enemy_bullet_list, bullet_hits, game_over, bullet_speed
    if game_over or level_complete:
        return
    bullets_to_remove = []
    for i, bullet in enumerate(enemy_bullet_list):
        bullet_x, bullet_y, bullet_z, dir_x, dir_y = bullet
        
        # Move bullet
        bullet[0] += dir_x * bullet_speed
        bullet[1] += dir_y * bullet_speed
        if not cheat_mode:
            bullet_radius = 3
            sub_left = submarine_x - 42
            sub_right = submarine_x + 42
            sub_top = submarine_y + 21
            sub_bottom = submarine_y - 21
            if (bullet_x + bullet_radius > sub_left and bullet_x - bullet_radius < sub_right and
                    bullet_y + bullet_radius > sub_bottom and bullet_y - bullet_radius < sub_top and
                    abs(bullet_z) < 50):
                bullet_hits += 1
                bullets_to_remove.append(i)
                
                if bullet_hits >= MAX_BULLET_HITS:
                    game_over = True
        
        if bullet_x < -400 or bullet_x > 400 or bullet_y < -200 or bullet_y > 200:
            bullets_to_remove.append(i)
    for i in sorted(bullets_to_remove, reverse=True):
        enemy_bullet_list.pop(i)

def check_collision():
    global life, game_over, fish_list
    if game_over or level_complete:
        return
    if cheat_mode:
        return
    sub_left = submarine_x - 42
    sub_right = submarine_x + 42
    sub_top = submarine_y + 21
    sub_bottom = submarine_y - 21
    fish_to_remove = []
    for i, fish in enumerate(fish_list):
        fish_x, fish_y, fish_z, r, g, b, speed = fish
        fish_left = fish_x - 10
        fish_right = fish_x + 10
        fish_top = fish_y + 10
        fish_bottom = fish_y - 10
        if fish_z > -50:
            if (fish_right > sub_left and fish_left < sub_right and
                    fish_top > sub_bottom and fish_bottom < sub_top):
                life -= 1
                fish_to_remove.append(i)
                if life <= 0:
                    game_over = True
                    print("GAME OVER!")
    for i in sorted(fish_to_remove, reverse=True):
        fish_list.pop(i)

def check_key_collection():
    global collected_keys, missed_keys, key_list, level_complete, game_over
    
    if game_over or level_complete:
        return
    sub_left = submarine_x - 42
    sub_right = submarine_x + 42
    sub_top = submarine_y + 21
    sub_bottom = submarine_y - 21
    keys_to_remove = []
    for i, key in enumerate(key_list):
        key_x, key_y, key_z = key
        key_left = key_x - 8
        key_right = key_x + 8
        key_top = key_y + 8
        key_bottom = key_y - 8
        if key_x < -550:
            missed_keys += 1
            keys_to_remove.append(i)
            if missed_keys >= 3 and not cheat_mode:
                game_over = True
        elif (key_right > sub_left and key_left < sub_right and
              key_top > sub_bottom and key_bottom < sub_top):
            collected_keys += 1
            keys_to_remove.append(i)
            if collected_keys >= target:
                level_complete = True
    for i in sorted(keys_to_remove, reverse=True):
        key_list.pop(i)

def check_diamond_collection():
    global points, diamond_list
    if game_over or level_complete:
        return
    sub_left = submarine_x - 42
    sub_right = submarine_x + 42
    sub_top = submarine_y + 21
    sub_bottom = submarine_y - 21
    diamonds_to_remove = []
    for i, diamond in enumerate(diamond_list):
        diamond_x, diamond_y, diamond_z = diamond
        diamond_left = diamond_x - 8
        diamond_right = diamond_x + 8
        diamond_top = diamond_y + 8
        diamond_bottom = diamond_y - 8
        
        if diamond_x < -550:
            diamonds_to_remove.append(i)
        elif (diamond_right > sub_left and diamond_left < sub_right and
              diamond_top > sub_bottom and diamond_bottom < sub_top):
            points += 1
            diamonds_to_remove.append(i)
    for i in sorted(diamonds_to_remove, reverse=True):
        diamond_list.pop(i)

def update_fish():
    global fish_list
    for fish in fish_list:
        fish[0] -= fish[6]
    check_collision()
    fish_list = [fish for fish in fish_list if fish[0] > -550]



def update_keys():
    for key in key_list:
        key[0] -= 0.5
    check_key_collection()

def update_diamonds():
    
    for diamond in diamond_list:
        diamond[0] -= 0.6 
    check_diamond_collection()

def find_nearest_target():
    global key_list, diamond_list
    nearest = None
    min_distance = float('inf')
    target_type = None
    for key in key_list:
        key_x, key_y, key_z = key
        distance = math.sqrt((key_x - submarine_x) ** 2 + (key_y - submarine_y) ** 2)
        if distance < min_distance:
            min_distance = distance
            nearest = key
            target_type = "key"
    if not key_list:
        for diamond in diamond_list:
            diamond_x, diamond_y, diamond_z = diamond
            distance = math.sqrt((diamond_x - submarine_x) ** 2 + (diamond_y - submarine_y) ** 2)
            if distance < min_distance:
                min_distance = distance
                nearest = diamond
                target_type = "diamond"
    return nearest, target_type

def avoid_fish():
    global submarine_y
    danger_zone = 60 
    avoidance_distance = 30
    for fish in fish_list:
        fish_x, fish_y, fish_z, r, g, b, speed = fish
        if fish_x > submarine_x - 50 and fish_x < submarine_x + 100 and fish_z > -50:
            distance = abs(fish_y - submarine_y)
            if distance < danger_zone:
                if fish_y > submarine_y:
                    submarine_y -= 2  #down
                else:
                    submarine_y += 2  #up
                return True
    return False

def avoid_enemy_bullets():
    global submarine_y, submarine_x
    if not enemy_bullet_list:
        return False
    danger_zone = 200  
    critical_zone = 100 
    
    for bullet in enemy_bullet_list:
        bullet_x, bullet_y, bullet_z, dir_x, dir_y = bullet
        distance = math.sqrt((bullet_x - submarine_x) ** 2 + (bullet_y - submarine_y) ** 2)
        if distance < danger_zone:
            # Calculate bullet
            future_x = bullet_x + dir_x * 60
            future_y = bullet_y + dir_y * 60
            future_dist = math.sqrt((future_x - submarine_x) ** 2 + (future_y - submarine_y) ** 2)
            if future_dist < distance or distance < critical_zone: #bullet close check
                evasion_speed = 7 if distance < critical_zone else 5
                if bullet_x > submarine_x: 
                    submarine_x -= evasion_speed    #move left
                else:
                    submarine_x += evasion_speed   #move right
                if bullet_y > submarine_y:
                    submarine_y -= evasion_speed  #move down
                else:
                    submarine_y += evasion_speed    #move up
                submarine_x += math.sin(angle * 10) * 3
                submarine_y += math.cos(angle * 10) * 3
                return True
    return False


def avoid_enemy_submarines():
    global submarine_y, submarine_x
    danger_zone = 120
    critical_zone = 70
    
    for enemy in enemy_sub_list:
        enemy_x, enemy_y, enemy_z, shoot_timer = enemy
        distance = math.sqrt((enemy_x - submarine_x) ** 2 + (enemy_y - submarine_y) ** 2)
        if distance < danger_zone:
            evasion_speed = 4 if distance < critical_zone else 3
            if enemy_y > submarine_y:
                submarine_y -= evasion_speed
            else:
                submarine_y += evasion_speed
            
            if enemy_x > submarine_x:
                submarine_x -= evasion_speed
            else:
                submarine_x += evasion_speed
            return True
    return False

def update_cheat_mode():
    global submarine_x, submarine_y, cheat_target, cheat_state, oxygen_bars
    global cheat_surface_timer
    if not cheat_mode or game_over or level_complete:
        return
    if oxygen_bars <= cheat_oxygen_threshold and cheat_state != "SURFACING":
        cheat_state = "SURFACING"
        cheat_surface_timer = 0
    if cheat_state == "SURFACING":
        
        submarine_y += submarine_speed * 1.5
        if submarine_y >= 140:
            submarine_y = 140
            cheat_surface_timer += 1
            if cheat_surface_timer >= 5:
                cheat_state = "DESCENDING"
        return
    elif cheat_state == "DESCENDING":
        target_depth = 50
        if submarine_y > target_depth:
            submarine_y -= submarine_speed * 0.5
            if submarine_y <= target_depth:
                submarine_y = target_depth
                cheat_state = "HUNTING"
        return
    if level >= 2:
        bullet_avoided = avoid_enemy_bullets()
        if bullet_avoided:
            submarine_y = max(-140, min(140, submarine_y))
            submarine_x = max(-180, min(180, submarine_x))
            cheat_state = "EVADING"
            return
    if level >= 2:
        enemy_avoided = avoid_enemy_submarines()
        if enemy_avoided:
            submarine_y = max(-140, min(140, submarine_y))
            submarine_x = max(-180, min(180, submarine_x))
            cheat_state = "EVADING"
            return
    
    if avoid_fish():
        submarine_y = max(-150, min(150, submarine_y))
        cheat_state = "DODGING"
        return
    cheat_state = "HUNTING"
    target, target_type = find_nearest_target()
    if target:
        target_x, target_y, target_z = target
        dx = target_x - submarine_x
        dy = target_y - submarine_y
        distance = math.sqrt(dx ** 2 + dy ** 2)
        if distance > 5:
            move_speed = submarine_speed * 0.1 if level >= 2 else submarine_speed * 0.2
            submarine_x += (dx / distance) * move_speed
            submarine_y += (dy / distance) * move_speed
        submarine_x = max(-200, min(200, submarine_x))
        submarine_y = max(-150, min(150, submarine_y))
    else:
        submarine_y += math.sin(angle * 2) * 1.5
        submarine_y = max(-100, min(100, submarine_y))


def draw_text(x, y, text):
    glColor3f(1.0, 1.0, 1.0)
    glRasterPos2f(x, y)
    for char in text:
        glutBitmapCharacter(GLUT_BITMAP_HELVETICA_18, ord(char))

def draw_submarine():
    
    glPushMatrix()
    glTranslatef(submarine_x, submarine_y, 0)
    if cheat_mode and level >= 2:
        glPushMatrix()
        glScalef(1.2, .7, 1.2)
        glColor3f(0.4, 1, 1.0)
        glutSolidSphere(65, 24, 24)
        glPopMatrix()
    
    glScalef(0.7, 0.7, 0.7)
    glPushMatrix()
    glColor3f(0.38, 0.40, 0.48)
    glScalef(2.8, 1.3, 1.3)
    glutSolidSphere(38, 24, 24)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-35, 0, 42)
    glColor3f(0.75, 0.90, 0.98)
    glutSolidSphere(13, 24, 24)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(35, 0, 42)
    glColor3f(0.75, 0.90, 0.98)
    glutSolidSphere(13, 24, 24)
    glPopMatrix()


    glPushMatrix()
    glTranslatef(-5, 50, 0)
    glColor3f(0.28, 0.30, 0.38)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 5, 5, 35, 16, 16)
    glTranslatef(0, 0, 35)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 5, 5, 22, 16, 16)
    glTranslatef(0, 0, 22)
    glColor3f(0.4, 0.42, 0.50)
    glutSolidSphere(7, 16, 16)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-30, 50, 0)
    glColor3f(0.28, 0.30, 0.38)
    glutSolidSphere(8, 12, 12)
    glPopMatrix()

    glPopMatrix()


def draw_enemy_submarine(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(0.5, 0.5, 0.5) 
    glRotatef(180, 0, 1, 0)  

    glPushMatrix()
    glColor3f(0.15, 0.15, 0.20)  # dark gray
    glScalef(2.8, 1.3, 1.3)
    glutSolidSphere(38, 24, 24)
    glPopMatrix()

    # Periscope
    glPushMatrix()
    glTranslatef(-5, 50, 0)
    glColor3f(0.10, 0.10, 0.15)
    glRotatef(-90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 5, 5, 35, 16, 16)
    glTranslatef(0, 0, 35)
    glRotatef(90, 0, 1, 0)
    gluCylinder(gluNewQuadric(), 5, 5, 22, 16, 16)
    glTranslatef(0, 0, 22)
    glColor3f(0.15, 0.15, 0.20)
    glutSolidSphere(7, 16, 16)
    glPopMatrix()

    glPopMatrix()


def draw_enemy_bullet(x, y, z):
    
    glPushMatrix()
    
    glTranslatef(x, y, z)

    glRotatef(angle * 100, 1, 0, 0)

    glColor3f(1.0, 0.2, 0.0)
    glPushMatrix()
    glScalef(2.0, 0.8, 0.8)
    glutSolidSphere(3, 12, 12)
    glPopMatrix()

    glPopMatrix()


def draw_simple_fish(x, y, z, r, g, b, scale=1.0):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(scale, scale, scale)
    glRotatef(math.sin(angle) * 10, 0, 1, 0)

    glColor3f(r, g, b)
    glPushMatrix()
    glScalef(1.5, 0.8, 0.6)
    glutSolidSphere(10, 20, 20)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(10, 3, 5)
    glColor3f(0.0, 0.0, 0.0)
    glutSolidSphere(1.5, 12, 12)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(9, 3, 5.5)
    glColor3f(1.0, 1.0, 1.0)
    glutSolidSphere(2, 12, 12)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(10, 3, 6.5)
    glColor3f(0.0, 0.0, 0.0)
    glutSolidSphere(1.2, 12, 12)
    glPopMatrix()

    glPopMatrix()

def draw_key(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    glScalef(0.6, 0.6, 0.6)

    # Key head
    glPushMatrix()
    glColor3f(1.0, 0.84, 0.0)  # Gold color
    glutSolidSphere(6, 16, 16)

    glPopMatrix()

    # Key shaft
    glPushMatrix()
    glTranslatef(0, -6, 0)
    glColor3f(1.0, 0.84, 0.0)
    glRotatef(90, 1, 0, 0)
    gluCylinder(gluNewQuadric(), 2, 2, 12, 12, 12)
    glPopMatrix()

    # Key teeth
    glColor3f(1.0, 0.84, 0.0)
    glPushMatrix()
    glTranslatef(-3, -16, 0)
    glutSolidCube(3)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(1, -14, 0)
    glutSolidCube(3)
    glPopMatrix()

    glPopMatrix()


def draw_diamond(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)

    glRotatef(angle * 50, 0, 1, 0)
    glRotatef(20, 1, 0, 0)

    glScalef(0.5, 0.5, 0.5)

    glColor3f(0.4, 0.8, 1.0)

    # Top pyramid
    glBegin(GL_TRIANGLES)
    # Front face
    glColor3f(0.6, 0.9, 1.0)
    glVertex3f(0, 12, 0) 
    glVertex3f(-8, 0, 8)  
    glVertex3f(8, 0, 8)  

    # Right face
    glColor3f(0.4, 0.85, 1.0)
    glVertex3f(0, 12, 0)
    glVertex3f(8, 0, 8)
    glVertex3f(8, 0, -8)

    # Back face
    glColor3f(0.5, 0.95, 1.0)
    glVertex3f(0, 12, 0)
    glVertex3f(8, 0, -8)
    glVertex3f(-8, 0, -8)

    # Left face
    glColor3f(0.3, 0.8, 0.95)
    glVertex3f(0, 12, 0)
    glVertex3f(-8, 0, -8)
    glVertex3f(-8, 0, 8)
    glEnd()

    # Bottom pyramid
    glBegin(GL_TRIANGLES)
    # Front face
    glColor3f(0.2, 0.7, 0.9)
    glVertex3f(0, -12, 0)
    glVertex3f(8, 0, 8)
    glVertex3f(-8, 0, 8)

    # Right face
    glColor3f(0.3, 0.75, 0.95)
    glVertex3f(0, -12, 0)
    glVertex3f(8, 0, -8)
    glVertex3f(8, 0, 8)

    # Back face
    glColor3f(0.25, 0.72, 0.92)
    glVertex3f(0, -12, 0)
    glVertex3f(-8, 0, -8)
    glVertex3f(8, 0, -8)
    
    # Left face
    glColor3f(0.35, 0.78, 0.96)
    glVertex3f(0, -12, 0)
    glVertex3f(-8, 0, 8)
    glVertex3f(-8, 0, -8)
    glEnd()

    glPopMatrix()


def draw_seaweed(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)

    for i in range(3):
        glPushMatrix()
        glTranslatef((i - 1) * 10, 0, 0)
        glColor3f(0.2, 0.6, 0.3)
        for j in range(8):
            glPushMatrix()
            offset = math.sin(angle * 2 + j * 0.5 + i) * 5
            glTranslatef(offset, j * 15, 0)
            glRotatef(offset * 2, 0, 0, 1)
            glScalef(0.4, 1.2, 0.2)
            glutSolidCube(8)
            glPopMatrix()
        glPopMatrix()

    glPopMatrix()

def draw_bubble(x, y, z, size=1.0):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(0.9, 0.95, 1.0)
    glutSolidSphere(size * 2.5, 8, 8)
    glPopMatrix()


def draw_ocean_floor():
    glColor3f(0.6, 0.6, 0.5)
    glBegin(GL_QUADS)
    glVertex3f(-750, -200, -200)
    glVertex3f(750, -200, -200)
    glVertex3f(750, -200, 200)
    glVertex3f(-750, -200, 200)
    glEnd()



def draw_button(x, y, width, height, text):
    glColor3f(0.6, 0.5, 0.9)

    glBegin(GL_QUADS)
    glVertex2f(x, y)
    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)
    glEnd()

    # Button border
    glColor3f(1.0, 1.0, 1.0)
    glLineWidth(2)
    glBegin(GL_LINES)
    glVertex2f(x, y)
    glVertex2f(x + width, y)

    glVertex2f(x + width, y + height)
    glVertex2f(x, y + height)

    glVertex2f(x, y)
    glVertex2f(x, y + height)

    glVertex2f(x + width, y)
    glVertex2f(x + width, y + height)


    glEnd()

    # Button text
    text_x = x + width // 2 - len(text) * 4
    text_y = y + height // 2 - 5
    draw_text(text_x, text_y, text)


def display():
    global angle, bubble_offset, mouse_click_x, mouse_click_y

    glClearColor(0.15, 0.5, 0.65, 1.0)
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)

    #ocean 3d
    glViewport(0, 0, WINDOW_WIDTH, OCEAN_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, WINDOW_WIDTH / OCEAN_HEIGHT, 0.1, 1000.0)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    gluLookAt(camera_x, camera_y, camera_z, 0, 0, 0, 0, 1, 0)
    glEnable(GL_DEPTH_TEST)
    draw_ocean_floor()
    draw_submarine()

    if level >= 2:
        for enemy in enemy_sub_list:
            x, y, z, shoot_timer = enemy
            draw_enemy_submarine(x, y, z)

        for bullet in enemy_bullet_list:
            x, y, z, dir_x, dir_y = bullet
            draw_enemy_bullet(x, y, z)

    for fish in fish_list:
        x, y, z, r, g, b, speed = fish
        draw_simple_fish(x, y, z, r, g, b, 0.8)

    for key in key_list:
        x, y, z = key
        draw_key(x, y, z)

    
    for diamond in diamond_list:
        x, y, z = diamond
        draw_diamond(x, y, z)

    for x, y, z in seaweed_positions:
        draw_seaweed(x, y, z)

    for i, (x, base_y, z) in enumerate(bubble_positions):
        y = base_y + bubble_offset + i * 8
        if y > 120:
            y = -150 + (y - 120) % 260
        size = 0.8 + math.sin(angle * 2 + i * 0.5) * 0.3
        draw_bubble(x, y, z, size)

    # water surface
    glBegin(GL_QUADS)
    glColor3f(.79, .77, .58)
    glVertex3f(-WINDOW_WIDTH, 120, 0)
    glVertex3f(WINDOW_WIDTH, 120, 0)
    glVertex3f(WINDOW_WIDTH, 120, -camera_z + 100)
    glVertex3f(-WINDOW_WIDTH, 120, -camera_z + 100)
    glEnd()

    # text part 2d
    glDisable(GL_DEPTH_TEST)
    glViewport(0, OCEAN_HEIGHT, WINDOW_WIDTH, TEXT_HEIGHT)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluOrtho2D(0, WINDOW_WIDTH, 0, TEXT_HEIGHT)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()

    glColor3f(0.5, 0.4, 0.9)
    glBegin(GL_QUADS)
    glVertex2f(0, 0)
    glVertex2f(WINDOW_WIDTH, 0)
    glVertex2f(WINDOW_WIDTH, TEXT_HEIGHT)
    glVertex2f(0, TEXT_HEIGHT)
    glEnd()

    if level_complete:
        draw_text(WINDOW_WIDTH // 2 - 100, 95, f"Level {level} Complete!")
        draw_text(WINDOW_WIDTH // 2 - 80, 75, f"Collected Keys: {collected_keys}/{target}")
        draw_text(WINDOW_WIDTH // 2 - 60, 55, f"Points: {points}")

        draw_button(WINDOW_WIDTH // 2 - 150, 20, 120, 30, "Replay")
        draw_button(WINDOW_WIDTH // 2 + 30, 20, 120, 30, "Next Level")
    elif not game_over:
        draw_text(20, 100, f"Life: {life}")
        draw_text(20, 75, f"Keys: {collected_keys}/{target}")
        draw_text(20, 50, f"Missed: {missed_keys}/3")
        
        draw_text(20, 25, f"O2:")
        
        glLineWidth(2)
        glBegin(GL_LINES)
        glColor3f(0, 0, 0)
        glVertex2f(55, 20)
        glVertex2f(535, 20)
        glVertex2f(55, 40)
        glVertex2f(535, 40)
        for i in range(16):
            glVertex2f(55 + 32 * i, 20)
            glVertex2f(55 + 32 * i, 40)
        glEnd()
        glBegin(GL_QUADS)
        glColor3f(1, 1, 1)
        for j in range(oxygen_bars):
            glVertex2f(57 + 32 * j, 22)
            glVertex2f(85 + 32 * j, 22)
            glVertex2f(85 + 32 * j, 38)
            glVertex2f(57 + 32 * j, 38)
        glEnd()
        
        draw_text(WINDOW_WIDTH // 2 - 80, 100, f"LEVEL: {level}")
        if cheat_mode:
            glColor3f(1.0, 1.0, 0.0)
            if level >= 2:
                draw_text(WINDOW_WIDTH // 2 - 100, 50, f"CHEAT: {cheat_state} [SHIELD ON]")
            else:
                draw_text(WINDOW_WIDTH // 2 - 80, 50, f"CHEAT: {cheat_state}")
        
        display_depth = calculate_display_depth(current_depth)
        draw_text(WINDOW_WIDTH - 250, 100, f"Depth: {display_depth}m")
        draw_text(WINDOW_WIDTH - 250, 75, f"Score: {points}")
        draw_text(WINDOW_WIDTH - 250, 50, f"Target: {target} keys")
        
        text_y = WINDOW_HEIGHT - mouse_click_y - OCEAN_HEIGHT
        
        pause_hover = (
                PAUSE_BTN_X <= mouse_click_x <= PAUSE_BTN_X + BTN_WIDTH and
                PAUSE_BTN_Y <= text_y <= PAUSE_BTN_Y + BTN_HEIGHT
        )

        quit_hover = (
                QUIT_BTN_X <= mouse_click_x <= QUIT_BTN_X + BTN_WIDTH and
                QUIT_BTN_Y <= text_y <= QUIT_BTN_Y + BTN_HEIGHT
        )

        pause_text = "Play" if is_paused else "Pause"

        draw_button(PAUSE_BTN_X, PAUSE_BTN_Y, BTN_WIDTH, BTN_HEIGHT, pause_text)
        draw_button(QUIT_BTN_X, QUIT_BTN_Y, BTN_WIDTH, BTN_HEIGHT, "Quit")

        if is_paused:
            draw_text(WINDOW_WIDTH // 2 -100, 0, "PAUSED")
        
        if level >= 2:
            draw_text(WINDOW_WIDTH - 650, 25,
                      f"Bullets: {bullet_hits}/{MAX_BULLET_HITS}  Enemies: {len(enemy_sub_list)}")
    elif missed_keys == 3 and oxygen_bars > 0:
        draw_text(WINDOW_WIDTH // 2 - 100, 90, "Missed keys: 3/3")
        draw_text(WINDOW_WIDTH // 2 - 80, 60, "Game Over !")
        draw_text(WINDOW_WIDTH // 2 - 100, 30, "Press R to Restart")
    elif oxygen_bars == 0 and missed_keys < 3:
        draw_text(WINDOW_WIDTH // 2 - 100, 90, "Out of Oxygen!")
        draw_text(WINDOW_WIDTH // 2 - 80, 60, "Game Over !")
        draw_text(WINDOW_WIDTH // 2 - 100, 30, "Press R to Restart")
    else:
        draw_text(WINDOW_WIDTH // 2 - 80, 60, "Game Over !")
        draw_text(WINDOW_WIDTH // 2 - 100, 30, "Press R to Restart")
    glutSwapBuffers()

def animate():
    global angle, bubble_offset, fish_spawn_counter, oxygen_bars, start_time, key_spawn_counter, diamond_spawn_counter, game_over, enemy_spawn_counter, is_paused
    angle += 0.03
    bubble_offset += 0.8
    if bubble_offset > 350:
        bubble_offset = 0
    if not game_over and not level_complete and not is_paused:
        if cheat_mode:
            update_cheat_mode()
        update_fish()
        update_keys()
        update_diamonds()
        update_oxygen_rate()
        if level >= 2:
            update_enemy_submarines()
            update_enemy_bullets()
            enemy_spawn_counter += 1
            if enemy_spawn_counter > ENEMY_SPAWN_INTERVAL:
                spawn_enemy_submarine()
                enemy_spawn_counter = 0
        fish_spawn_counter += 1
        if fish_spawn_counter > 60 and len(fish_list) < MAX_FISH:
            spawn_fish()
            fish_spawn_counter = 0
        key_spawn_counter += 1
        if key_spawn_counter > KEY_SPAWN_INTERVAL:
            spawn_key()
            key_spawn_counter = 0
        diamond_spawn_counter += 1
        if diamond_spawn_counter > DIAMOND_SPAWN_INTERVAL:
            spawn_diamond()
            diamond_spawn_counter = 0
        if submarine_y >= 140:
            oxygen_bars = 15
            start_time = time.time()
        else:
            present_time = time.time()
            delta_time = present_time - start_time
            if delta_time >= oxygen_decrease_rate:
                if oxygen_bars > 0:
                    oxygen_bars -= 1
                start_time = present_time
                if oxygen_bars <= 0:
                    game_over = True
    glutPostRedisplay()

def keyboard_listener(key, x, y):
    global camera_x, camera_y, camera_z, game_over, life, fish_list, submarine_x, submarine_y
    global oxygen_bars, start_time, collected_keys, missed_keys, level, target, key_list
    global level_complete, fish_speed_base, points, diamond_list, collected_points
    global cheat_mode, cheat_state, cheat_target, bullet_hits, enemy_sub_list, enemy_bullet_list
    if key == b'c' or key == b'C':
        cheat_mode = not cheat_mode
        if cheat_mode:
            cheat_state = "HUNTING"
            cheat_target = None

    elif key == b'r' or key == b'R':
        if game_over:
            game_over = False
            cheat_mode = False
            life = 10
            level = 1
            target = 4
            collected_keys = 0
            missed_keys = 0
            collected_points = 0
            points = 0
            bullet_hits = 0 
            fish_list = []
            key_list = []
            diamond_list = []
            enemy_sub_list = []  
            enemy_bullet_list = []  
            submarine_x = 0
            submarine_y = 50
            oxygen_bars = 15
            start_time = time.time()
            fish_speed_base = 0.4
            for i in range(3):
                spawn_fish()
    elif key == b'a': #zoom out
        camera_z -= 15
    elif key == b's':  # zoom in
        camera_z += 15
    elif key == b'd': #camera left
        camera_x -= 15
    elif key == b'f':#camera right
        camera_x += 15
    elif key == b'g': # camera up
        camera_y += 15
    elif key == b'h':   # camera down
        camera_y -= 15
    glutPostRedisplay()


def special_key_listener(key, x, y):
    global submarine_x, submarine_y, current_depth
    if game_over or level_complete or cheat_mode:
        return
    if key == GLUT_KEY_UP:
        submarine_y += submarine_speed
        if submarine_y > 150:
            submarine_y = 150
    elif key == GLUT_KEY_DOWN:
        submarine_y -= submarine_speed
        if submarine_y < -150:
            submarine_y = -150
    elif key == GLUT_KEY_LEFT:
        submarine_x -= submarine_speed
        if submarine_x < -435:
            submarine_x = -435
    elif key == GLUT_KEY_RIGHT:
        submarine_x += submarine_speed
        if submarine_x > 435:
            submarine_x = 435
    current_depth = submarine_y

    glutPostRedisplay()

def mouse_listener(button, state, x, y):
    global level_complete, level, target, collected_keys, missed_keys, fish_list, key_list
    global submarine_x, submarine_y, oxygen_bars, start_time, fish_speed_base, mouse_click_x, mouse_click_y
    global diamond_list, points, cheat_mode, bullet_hits, enemy_sub_list, enemy_bullet_list
    global is_paused, game_over
    mouse_click_x = x
    mouse_click_y = y
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and not level_complete:
        text_y = WINDOW_HEIGHT - y - OCEAN_HEIGHT

        if (PAUSE_BTN_X <= x <= PAUSE_BTN_X + BTN_WIDTH and
                PAUSE_BTN_Y <= text_y <= PAUSE_BTN_Y + BTN_HEIGHT):
            is_paused = not is_paused
            return

        if (QUIT_BTN_X <= x <= QUIT_BTN_X + BTN_WIDTH and
                QUIT_BTN_Y <= text_y <= QUIT_BTN_Y + BTN_HEIGHT):
            game_over = True
            is_paused = False
            return
    
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and level_complete:
        text_y = WINDOW_HEIGHT - y - OCEAN_HEIGHT # convert to text viewport
        if (WINDOW_WIDTH // 2 - 150 <= x <= WINDOW_WIDTH // 2 - 30 and
                20 <= text_y <= 60):
            
            cheat_mode = False  #reset cheat mode
            collected_keys = 0
            missed_keys = 0
            bullet_hits = 0
            fish_list = []
            key_list = []
            diamond_list = []
            enemy_sub_list = []  #reset enemy submarines
            enemy_bullet_list = []    #reset enemy bullets
            submarine_x = 0
            submarine_y = 50
            oxygen_bars = 15
            start_time = time.time()
            level_complete = False
            for i in range(3):
                spawn_fish()
        elif (WINDOW_WIDTH // 2 + 30 <= x <= WINDOW_WIDTH // 2 + 150 and
              20 <= text_y <= 60):
            cheat_mode = False 
            level += 1
            target += 1
            fish_speed_base += 0.1
            collected_keys = 0
            missed_keys = 0
            bullet_hits = 0
            fish_list = []
            key_list = []
            diamond_list = []
            enemy_sub_list = [] 
            enemy_bullet_list = []
            submarine_x = 0
            submarine_y = 50
            oxygen_bars = 15
            start_time = time.time()
            level_complete = False
            for i in range(3):
                spawn_fish()
            
    glutPostRedisplay()

def mouse_motion_listener(x, y):
    global mouse_click_x, mouse_click_y
    mouse_click_x = x
    mouse_click_y = y
    if level_complete:
        glutPostRedisplay()


def main():
    glutInit()
    glutInitDisplayMode(GLUT_RGBA | GLUT_DOUBLE | GLUT_DEPTH)
    glutInitWindowSize(WINDOW_WIDTH, WINDOW_HEIGHT)
    glutInitWindowPosition(0, 0)
    glutCreateWindow(b"Submarine Adventure")
    glutDisplayFunc(display)
    glutIdleFunc(animate)
    glutKeyboardFunc(keyboard_listener)
    glutSpecialFunc(special_key_listener)
    glutMouseFunc(mouse_listener)
    glutPassiveMotionFunc(mouse_motion_listener)
    for i in range(3):
        spawn_fish()
    glutMainLoop()
if __name__ == "__main__":
    main()