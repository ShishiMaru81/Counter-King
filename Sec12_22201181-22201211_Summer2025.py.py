
# Sec12_22201181-22201211_Summer2025.py




#Importing  necessary libraries


from OpenGL.GL import *
from OpenGL.GLUT import *
from OpenGL.GLU import *
import sys
import math
import random
import time







# Environment toggles/state
environment = {
    'is_daytime': True,
    'rain_enabled': False,
    'fog_enabled': False,
    # Each particle: [x, y, z, vx, vy, vz]
    'rain_particles': [],
    'max_rain_particles': 500,
    'rain_wind': 0.6,
    'rain_speed_z': 18.0,
    'fog_density': 0.0025,
}




# Backwards-compatible bindings for existing code that uses the old names
is_daytime = environment['is_daytime']
rain_enabled = environment['rain_enabled']
fog_enabled = environment['fog_enabled']
rain_particles = environment['rain_particles']
max_rain_particles = environment['max_rain_particles']
rain_wind = environment['rain_wind']
rain_speed_z = environment['rain_speed_z']
fog_density = environment['fog_density']



# Setup the main game configuration dictionary



#Main


game_config = {
    # World settings
    'world': {
        'battlefield_size': 1500,
        'controlled_territory': 600,
        'fortress_zone': 250,
        'fortress_radius': 60
    },
    
    # Camera system
    'camera': {
        'position': (0, 600, 600),
        'angle': 0,
        'distance': 600,
        'height': 550,
        'min_height': 400,
        'max_height': 1400
    },
    
    # Game state flags
    'flags': {
        'cheat_mode': False,
        'crosshair_enabled': False,
        'game_over': False,
        'round_paused': False,
        'choice_made': False,
        'first_person_active': False
    },
    
    # Player data
    'player': {
        'coordinates': [0, 0, 0],
        'movement_speed': 12,
        'score': 0,
        'health': 100,
        'max_health': 100,
        'rotation_speed': 4
    },
    


    # Weapon system
    'weapon': {
        'rotation_angle': 180,
        'position': [30, 15, 80],
        'projectiles': [],
        'missed_shots': 0,
        'miss_limit': 50
    },
    
    # Enemy system


    'enemies': {
        'active_targets': [],
        'spawn_count': 5,
        'movement_speed': 0.029,
        'pulse_scale': 1.0,
        'pulse_timer': 0,
        'count_per_round': [5, 7, 9, 11, 13, 15, 17, 19, 21],
        'projectiles': [],
        'shot_timers': {},
        'shot_damage': 1,
        'shot_cooldown': 301
    },
    
    # Tower defense system
    'towers': {
        'structures': [],
        'projectiles': [],
        'shot_timers': {},
        'firing_range': 600,
        'shot_damage': 3,
        'shot_cooldown': 201
    },
    
    # Health system
    'health_packs': {
        'items': [],  # Each: [x, y, z]
        'heal_amount': 60,
        'max_active': 1,
        'spawn_timer': 900,
        'spawn_interval_min': 300,
        'spawn_interval_max': 600,
        'pulse_timer': 0.0
    },
    
    # Round progression
    'progression': {
        'current_round': 1,
        'enemies_eliminated': 0,
        'kills_required': 10
    }
}

# --- sync game_config into module globals (keeps compatibility) ---
# World
GRID_LENGTH = game_config['world']['battlefield_size']
region = game_config['world']['controlled_territory']
castle_region = game_config['world']['fortress_zone']
castle_radius = game_config['world']['fortress_radius']

# Camera
camera_position = game_config['camera']['position']
camera_angle = game_config['camera']['angle']
camera_distance = game_config['camera']['distance']
camera_height = game_config['camera']['height']
camera_min_height = game_config['camera']['min_height']
camera_max_height = game_config['camera']['max_height']

# Flags
flags = game_config['flags']
cheat = flags['cheat_mode']
v_enable = flags['crosshair_enabled']
game_end = flags['game_over']
round_pause = flags['round_paused']
round_choice_made = flags['choice_made']
first_person_view = flags['first_person_active']

# Player
player = game_config['player']
player_coords = player['coordinates']
player_speed = player['movement_speed']
player_score = player['score']
player_health = player['health']
player_max_health = player['max_health']
player_turn_speed = player['rotation_speed']

# Weapon
weapon = game_config['weapon']
gun_rotation = weapon['rotation_angle']
gun_position = weapon['position']
shots = weapon['projectiles']
failed_shots = weapon['missed_shots']
max_miss = weapon['miss_limit']

# Enemies
enemies = game_config['enemies']
targets = enemies['active_targets']
target_number = enemies['spawn_count']
target_speed = enemies['movement_speed']
target_pulse = enemies['pulse_scale']
target_pulse_t = enemies['pulse_timer']
enemy_count_per_round = enemies['count_per_round']
enemy_shots = enemies['projectiles']
enemy_shot_timer = enemies['shot_timers']
enemy_shot_damage = enemies['shot_damage']
enemy_shot_cooldown = enemies['shot_cooldown']

# Towers
towers_cfg = game_config['towers']
towers = towers_cfg['structures']
tower_shots = towers_cfg['projectiles']
tower_shot_timers = towers_cfg['shot_timers']
tower_shot_range = towers_cfg['firing_range']
tower_shot_damage = towers_cfg['shot_damage']
tower_shot_cooldown = towers_cfg['shot_cooldown']

# Health packs
hp_cfg = game_config['health_packs']
health_packs = hp_cfg['items']
health_pack_heal = hp_cfg['heal_amount']
max_health_packs = hp_cfg['max_active']
health_pack_spawn_timer = hp_cfg['spawn_timer']
health_pack_spawn_interval_min = hp_cfg['spawn_interval_min']
health_pack_spawn_interval_max = hp_cfg['spawn_interval_max']
health_pack_pulse_t = hp_cfg['pulse_timer']

# Progression
progress = game_config['progression']
current_round = progress['current_round']
enemies_killed = progress['enemies_eliminated']
kills_to_advance = progress['kills_required']

tower_placement_mode = False
placement_marker_position = [400, 400]
try:
    DEFAULT_FONT = GLUT_BITMAP_HELVETICA_18
except NameError:
    DEFAULT_FONT = None
tree_count = 0

def render_text(x, y, text, font=None, color=(1, 1, 1)):
    if font is None:
        font = DEFAULT_FONT
    # Draw a subtle drop-shadow and slightly brighten the main color
    def _clamp(v):
        return max(0.0, min(1.0, v))

    # brightness boost for better visibility
    boosted = (_clamp(color[0] + 0.06), _clamp(color[1] + 0.06), _clamp(color[2] + 0.06))

    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 800, 0, 650)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    # Shadow (draw first, slightly offset)
    glColor3f(0.05, 0.05, 0.05)
    glRasterPos2f(x + 1, y - 1)
    for character in text:
        glutBitmapCharacter(font, ord(character))

    # Main text
    glColor3f(boosted[0], boosted[1], boosted[2])
    glRasterPos2f(x, y)
    for character in text:
        glutBitmapCharacter(font, ord(character))

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)


def draw_scene():
    # Consolidated scene draw entry
    draw_terrain_grid()
    draw_castle_and_tower()
    draw_trees()
    draw_health_packs()
    for tx, ty in towers:
        glPushMatrix()
        glTranslatef(tx, ty, 10)

        # Base Cylinder Tower
        glColor3f(0.5, 0.5, 0.5)
        gluCylinder(gluNewQuadric(), 40, 45, 180, 20, 20)

        # Top Battlements
        glTranslatef(0, 0, 180)
        for i in range(8):
            angle = i * 45
            x = 50 * math.cos(math.radians(angle))
            y = 50 * math.sin(math.radians(angle))
            glPushMatrix()
            glTranslatef(x, y, 0)
            glRotatef(angle, 0, 0, 1)
            glColor3f(0.4, 0.4, 0.4)
            glScalef(1, 1, 1.5)
            glutSolidCube(15)
            glPopMatrix()

        # Flagpole
        glColor3f(0.6, 0.3, 0.1)
        gluCylinder(gluNewQuadric(), 1.5, 1.5, 40, 10, 10)

        # Flag
        glTranslatef(0, 0, 40)
        glColor3f(1, 0, 0)
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, 0)
        glVertex3f(20, 8, 0)
        glVertex3f(0, 16, 0)
        glEnd()
        glPopMatrix()

    if not game_end:
        for t in targets:
            draw_enemy_unit(*t)
        for s in shots:
            draw_player_projectile(s[0], s[1], s[2])
        for es in enemy_shots:
            draw_enemy_projectile(es[0], es[1], es[2])
        for ts in tower_shots:
            draw_tower_projectile(ts[0], ts[1], ts[2])

def draw_terrain_grid():
    # Draw arena floor (natural grass tones)
    glBegin(GL_QUADS)
    for i in range(-GRID_LENGTH, GRID_LENGTH + 1, 100):
        for j in range(-GRID_LENGTH, GRID_LENGTH + 1, 100):
            if (i + j) % 200 == 0:
                glColor3f(0.18, 0.35, 0.18)  # darker grass patch
            else:
                glColor3f(0.20, 0.40, 0.20)  # lighter grass patch
            glVertex3f(i, j, 0)
            glVertex3f(i + 100, j, 0)
            glVertex3f(i + 100, j + 100, 0)
            glVertex3f(i, j + 100, 0)
    glEnd()

    # Draw conquered region (slightly richer grass)
    glBegin(GL_QUADS)
    for i in range(-region, region + 1, 100):
        for j in range(-region, region + 1, 100):
            if (i + j) % 200 == 0:
                glColor3f(0.22, 0.45, 0.22)
            else:
                glColor3f(0.25, 0.50, 0.25)
            glVertex3f(i, j, 2)
            glVertex3f(i + 100, j, 2)
            glVertex3f(i + 100, j + 100, 2)
            glVertex3f(i, j + 100, 2)
    glEnd()

    # Draw castle region (stone tiles instead of bright white)
    glBegin(GL_QUADS)
    for i in range(-castle_region, castle_region, 100):
        for j in range(-castle_region, castle_region, 100):
            if (i + j) % 200 == 0:
                glColor3f(0.65, 0.65, 0.65)  # darker stone
            else:
                glColor3f(0.72, 0.72, 0.72)  # lighter stone
            glVertex3f(i, j, 9)
            glVertex3f(i + 100, j, 9)
            glVertex3f(i + 100, j + 100, 9)
            glVertex3f(i, j + 100, 9)
    glEnd()
    # Boundary

    glBegin(GL_QUADS)
    glColor3f(0, 0, 0)

    glVertex3f(-region, -region, 0)
    glVertex3f(-region, region + 100, 0)
    glVertex3f(-region, region + 100, 30)
    glVertex3f(-region, -region, 30)

    glVertex3f(region + 100, -region, 0)
    glVertex3f(region + 100, region + 100, 0)
    glVertex3f(region + 100, region + 100, 30)
    glVertex3f(region + 100, -region, 30)

    glVertex3f(-region, region + 100, 0)
    glVertex3f(region + 100, region + 100, 0)
    glVertex3f(region + 100, region + 100, 30)
    glVertex3f(-region, region + 100, 30)

    glVertex3f(-region, -region, 0)
    glVertex3f(region + 100, -region, 0)
    glVertex3f(region + 100, -region, 30)
    glVertex3f(-region, -region, 30)
    glEnd()
    glBegin(GL_QUADS)
    glColor3f(0.25, 0.25, 0.27)  # outer walls in rock-like gray

    # Walls
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH + 100, 0)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH + 100, 100)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 100)

    glVertex3f(GRID_LENGTH + 100, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH + 100, GRID_LENGTH + 100, 0)
    glVertex3f(GRID_LENGTH + 100, GRID_LENGTH + 100, 100)
    glVertex3f(GRID_LENGTH + 100, -GRID_LENGTH, 100)

    glVertex3f(-GRID_LENGTH, GRID_LENGTH + 100, 0)
    glVertex3f(GRID_LENGTH + 100, GRID_LENGTH + 100, 0)
    glVertex3f(GRID_LENGTH + 100, GRID_LENGTH + 100, 100)
    glVertex3f(-GRID_LENGTH, GRID_LENGTH + 100, 100)

    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH + 100, -GRID_LENGTH, 0)
    glVertex3f(GRID_LENGTH + 100, -GRID_LENGTH, 100)
    glVertex3f(-GRID_LENGTH, -GRID_LENGTH, 100)
    glEnd()

def draw_trees():
    rng = random.Random(42)
    tree_count = 70
    for i in range(tree_count):
        x = rng.randint(-GRID_LENGTH + 200, GRID_LENGTH - 200)
        y = rng.randint(-GRID_LENGTH + 200, GRID_LENGTH - 200)
        if math.sqrt(x**2 + y**2) >= 500:
            glPushMatrix()
            glTranslatef(x, y, 0)
            glColor3f(0.4*i/70, 0.2*i/70, 0.1)
            gluCylinder(gluNewQuadric(), 12, 12, 70, 10, 10)
            glTranslatef(0, 0, 70)
            glColor3f(0.0, 0.6*i/70, 0.0)
            gluSphere(gluNewQuadric(), 40, 15, 15)
            glPopMatrix()

def draw_castle_and_tower():
    glPushMatrix()
    glColor3f(0.55, 0.56, 0.58)  # main stone towers (cool gray)
    for dx, dy in [(-60, -60), (60, -60), (-60, 60), (60, 60)]:
        glPushMatrix()
        glTranslatef(dx, dy, 0)
        glScalef(1, 1, 2)
        glutSolidCube(100)
        glPopMatrix()
    glPopMatrix()
    glColor3f(0.50, 0.51, 0.53)
    for dx, dy in [(-100, 0), (100, 0), (0, -100), (0, 100)]:
        glPushMatrix()
        glTranslatef(dx, dy, 50)
        glScalef(1.2, 1.2, 2.2)
        glutSolidCube(60)
        glPopMatrix()
        glPushMatrix()
        glTranslatef(dx, dy, 120)
        for i in range(8):
            angle = i * 45
            x = 35 * math.cos(math.radians(angle))
            y = 35 * math.sin(math.radians(angle))
            glPushMatrix()
            glTranslatef(x, y, 0)
            glColor3f(0.42, 0.43, 0.45)
            glutSolidCube(12)
            glPopMatrix()
        glPopMatrix()
    glColor3f(0.85, 0.1, 0.1)  # deep red flags
    for dx, dy in [(-100, 0), (100, 0), (0, -100), (0, 100)]:
        glPushMatrix()
        glTranslatef(dx, dy, 150)
        # Flag pole
        glColor3f(0.6, 0.3, 0.1)
        gluCylinder(gluNewQuadric(), 1.5, 1.5, 40, 10, 10)
        # Flag
        glTranslatef(0, 0, 40)
        glColor3f(1, 0, 0)
        glBegin(GL_TRIANGLES)
        glVertex3f(0, 0, 0)
        glVertex3f(25, 10, 0)
        glVertex3f(0, 20, 0)
        glEnd()
        glPopMatrix()
    glPushMatrix()
    glTranslatef(0, 0, 0)
    glColor3f(0.35, 0.36, 0.40)  # King tower base in stone gray
    gluCylinder(gluNewQuadric(), 40, 50, 200, 20, 20)
    glTranslatef(0, 0, 200)
    for i in range(12):
        angle = i * 30
        x = 50 * math.cos(math.radians(angle))
        y = 50 * math.sin(math.radians(angle))
        glPushMatrix()
        glTranslatef(x, y, 0)
        glColor3f(0.55, 0.56, 0.60)
        glutSolidCube(12)
        glPopMatrix()
    glPopMatrix()
    glPushMatrix()
    glTranslatef(0,0,200)
    glRotatef(gun_rotation, 0, 0, 1)
    # Legs (steel)
    glTranslatef(0, 0, 0)
    glColor3f(0.30, 0.34, 0.40)
    gluCylinder(gluNewQuadric(), 6, 12, 45, 10, 10)
    glTranslatef(30, 0, 0)
    glColor3f(0.30, 0.34, 0.40)
    gluCylinder(gluNewQuadric(), 6, 12, 45, 10, 10)
    # Body (leather/cloth)
    glTranslatef(-15, 0, 70)
    glColor3f(0.55, 0.46, 0.25)
    glutSolidCube(40)
    # Head (skin tone)
    glTranslatef(0, 0, 40)
    glColor3f(0.95, 0.85, 0.75)
    gluSphere(gluNewQuadric(), 20, 12, 12)
    # Arms (skin tone)
    glTranslatef(20, -60, -30)
    glRotatef(-90, 1, 0, 0)
    glColor3f(0.95, 0.85, 0.75)
    gluCylinder(gluNewQuadric(), 4, 8, 50, 10, 10)
    glRotatef(90, 1, 0, 0)
    glTranslatef(-45, 60, -40)
    glRotatef(0, 1, 0, 0)
    glColor3f(0.95, 0.85, 0.75)
    gluCylinder(gluNewQuadric(), 4, 8, 50, 10, 10)
    # Hat (golden accent)
    glColor3f(0.90, 0.78, 0.28)
    glTranslatef(25, 0, 87)
    glutSolidCone(12, 40, 16, 16)  # Base radius = 12, height = 40
    glTranslatef(-10, -15, -17)
    glColor3f(0.05, 0.05, 0.05)
    gluSphere(gluNewQuadric(), 5, 12, 12)
    glTranslatef(20, 0, 0)
    glColor3f(0.05, 0.05, 0.05)
    gluSphere(gluNewQuadric(), 5, 12, 12)
    glPopMatrix()

def spawn_tower():
    while True:
        x = random.randint(-region + 100, region - 100)
        y = random.randint(-region + 100, region - 100)
        if math.sqrt(x**2 + y**2) > 200:  # Avoid center
            return (x, y)

def draw_enemy_unit(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z + 35)
    if not round_pause:
        glScalef(target_pulse, target_pulse, target_pulse)
    # Lower Body (Upside-down Cone)
    glColor3f(0, 0, abs(target_pulse))
    glPushMatrix()
    glTranslatef(0,0,35)
    glRotatef(180, 1, 0, 0)  # Rotate the cone upside down
    glutSolidCone(25, 70, 16, 16)  # Base radius = 35, height = 50
    glPopMatrix()
    # Head
    glTranslatef(0, 0, 50)
    glColor3f(0, 0, 0)  # Black color for the head
    gluSphere(gluNewQuadric(), 15, 12, 12)
    # Hat
    glPushMatrix()
    glColor3f(0.5, 0, 0)  # Red color for the hat
    glTranslatef(0, 0, 20)
    glutSolidCone(12, 40, 16, 16)  # Base radius = 12, height = 40
    glPopMatrix()
    glPopMatrix()

def draw_player_projectile(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(-90, 1, 0, 0)
    glColor3f(1, 0.5, 0)
    glutSolidCube(8)
    glPopMatrix()

def draw_tower_projectile(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(-90, 1, 0, 0)
    glColor3f(0, 0.7, 1)  # Blue color for tower bullets
    glutSolidCone(4, 12, 8, 8)  # Cone shape for tower bullets
    glPopMatrix()

def draw_enemy_projectile(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(-90, 1, 0, 0)
    glColor3f(1, 0, 0)  # Red color for enemy bullets
    glutSolidSphere(5, 8, 8)  # Sphere for enemy bullets
    glPopMatrix()

def fire_player_weapon():
    global shots
    if first_person_view:
        ang = math.radians(gun_rotation + 45)
        x = player_coords[0] + (gun_position[0] + 5) * \
            math.sin(ang) - gun_position[1] * math.cos(ang)
        y = player_coords[1] - (gun_position[0] + 5) * \
            math.cos(ang) - gun_position[1] * math.sin(ang)
        z = player_coords[2] + gun_position[2]
        shot = [x, y, z, gun_rotation]
    else:
        ang = math.radians(gun_rotation - 90)
        off_x = gun_position[0] * \
            math.cos(ang) - gun_position[1] * math.sin(ang)
        off_y = gun_position[0] * \
            math.sin(ang) + gun_position[1] * math.cos(ang)
        x = player_coords[0] + off_x
        y = player_coords[1] + off_y
        z = player_coords[2] + gun_position[2]
        shot = [x, y, z, gun_rotation]
    shots.append(shot)

def update_player_projectiles():
    global shots, failed_shots, targets, game_end
    if round_pause:
        return
    to_remove = []
    for s in shots:
        ang = math.radians(s[3] - 90)
        s[0] += 2 * math.cos(ang)
        s[1] += 2 * math.sin(ang)
        if (s[0] > region + 100 or s[0] < -region or
                s[1] > region + 100 or s[1] < -region):
            to_remove.append(s)
            if not cheat:
                failed_shots += 1
    for s in to_remove:
        if s in shots:
            shots.remove(s)
    if failed_shots >= max_miss:
        game_end = True

def spawn_enemy_projectile(x, y, z):
    global enemy_shots
    dx = player_coords[0] - x
    dy = player_coords[1] - y
    ang = math.atan2(dy, dx)
    ang += random.uniform(-0.1, 0.1)
    enemy_shots.append([x, y, z + 70, ang])

def update_enemies():
    global targets, player_health, game_end, target_speed, enemy_shot_timer
    if round_pause:
        return
    for t in targets:
        enemy_id = id(t)
        if enemy_id not in enemy_shot_timer:
            enemy_shot_timer[enemy_id] = random.randint(
                60, enemy_shot_cooldown)
    for t in targets[:]:
        dx = player_coords[0] - t[0]
        dy = player_coords[1] - t[1]
        dist = math.sqrt(dx*dx + dy*dy)
        enemy_id = id(t)
        if enemy_id in enemy_shot_timer:
            enemy_shot_timer[enemy_id] -= 1
            if enemy_shot_timer[enemy_id] <= 0 and not cheat:
                spawn_enemy_projectile(t[0], t[1], t[2])
                enemy_shot_timer[enemy_id] = enemy_shot_cooldown + \
                    random.randint(-30, 30)
        if dist < 50:
            if not cheat:
                player_health -= 5
                if player_health <= 0:
                    game_end = True
                    targets.clear()
                    shots.clear()
                    enemy_shots.clear()
                    break
            if t in targets:
                targets.remove(t)
                if enemy_id in enemy_shot_timer:
                    del enemy_shot_timer[enemy_id]
            spawn_enemies(1)
        else:
            ang = math.atan2(dy, dx)
            t[0] += target_speed * math.cos(ang)
            t[1] += target_speed * math.sin(ang)
    timer_keys = list(enemy_shot_timer.keys())
    for enemy_id in timer_keys:
        if not any(id(t) == enemy_id for t in targets):
            del enemy_shot_timer[enemy_id]
    if not targets:
        next_round()

def detect_target_hits():
    global shots, targets, player_score, enemies_killed
    if round_pause:
        return
    for s in shots[:]:
        s_x, s_y = s[0], s[1]
        for t in targets[:]:
            t_x, t_y = t[0], t[1]
            dx, dy = s_x - t_x, s_y - t_y
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= 70:
                player_score += 1
                enemies_killed += 1
                if s in shots:
                    shots.remove(s)
                if t in targets:
                    targets.remove(t)
                max_enemies = (
                    enemy_count_per_round[current_round-1]
                    if current_round <= len(enemy_count_per_round)
                    else enemy_count_per_round[-1] + 2 * (current_round - len(enemy_count_per_round))
                )
                if enemies_killed >= kills_to_advance:
                    next_round()
                elif len(targets) < max_enemies:
                    spawn_enemies(1)
                break
        # Check health pack collection via shot
        for hp in health_packs[:]:
            dx = s_x - hp[0]
            dy = s_y - hp[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist <= 50:
                if s in shots:
                    shots.remove(s)
                collect_health_pack(hp)
                break

def tower_shoot(tower_idx, tx, ty):
    global tower_shots, targets
    closest_enemy = None
    min_dist = tower_shot_range
    for t in targets:
        dx = tx - t[0]
        dy = ty - t[1]
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < min_dist:
            min_dist = dist
            closest_enemy = t
    if closest_enemy:
        ex, ey, _ = closest_enemy
        dx = ex - tx
        dy = ey - ty
        ang = math.atan2(dy, dx)
        ang += random.uniform(-0.05, 0.05)
        tower_shots.append([tx, ty, 160, ang])
        return True
    return False

def update_towers():
    global tower_shot_timers, towers
    if round_pause:
        return
    for i, (tx, ty) in enumerate(towers):
        if i in tower_shot_timers:
            tower_shot_timers[i] -= 1
            if tower_shot_timers[i] <= 0:
                if tower_shoot(i, tx, ty):
                    tower_shot_timers[i] = tower_shot_cooldown
                else:
                    tower_shot_timers[i] = 60
        else:
            tower_shot_timers[i] = random.randint(60, tower_shot_cooldown)

def update_tower_shots():
    global tower_shots, targets, player_score, enemies_killed
    if round_pause:
        return
    to_remove_shots = []
    to_remove_targets = []
    for shot in tower_shots:
        shot[0] += 3 * math.cos(shot[3])
        shot[1] += 3 * math.sin(shot[3])
        if (shot[0] > region + 100 or shot[0] < -region or
                shot[1] > region + 100 or shot[1] < -region):
            to_remove_shots.append(shot)
            continue
        for t in targets:
            if t in to_remove_targets:
                continue
            dx = shot[0] - t[0]
            dy = shot[1] - t[1]
            dist = math.sqrt(dx*dx + dy*dy)
            if dist < 40:
                player_score += 1
                enemies_killed += 1
                to_remove_shots.append(shot)
                to_remove_targets.append(t)
                break
    for shot in to_remove_shots:
        if shot in tower_shots:
            tower_shots.remove(shot)
    for t in to_remove_targets:
        if t in targets:
            targets.remove(t)
            if enemies_killed >= kills_to_advance:
                next_round()
            else:
                max_enemies = (
                    enemy_count_per_round[current_round-1]
                    if current_round <= len(enemy_count_per_round)
                    else enemy_count_per_round[-1] + 2 * (current_round - len(enemy_count_per_round))
                )
                if len(targets) < max_enemies:
                    spawn_enemies(1)

def enemy_pulse():
    global target_pulse_t, target_pulse
    target_pulse_t += 0.01
    target_pulse = 1.0 + 0.4 * math.cos(target_pulse_t)

def health_pack_pulse():
    global health_pack_pulse_t
    health_pack_pulse_t += 0.05

def enemy_angle():
    angles = []
    for t in targets:
        dx, dy = player_coords[0] - t[0], player_coords[1] - t[1]
        ang = math.degrees(math.atan2(dy, dx)) - 90
        angles.append((ang + 360) % 360)
    return angles

def crosshair_position():
    if v_enable:
        glMatrixMode(GL_PROJECTION)
        glPushMatrix()
        glLoadIdentity()
        gluOrtho2D(0, 800, 0, 650)
        glMatrixMode(GL_MODELVIEW)
        glPushMatrix()
        glLoadIdentity()
        glColor3f(0, 0, 0)
        glBegin(GL_LINES)
        glVertex2f(400, 340)
        glVertex2f(400, 310)
        glVertex2f(380, 325)
        glVertex2f(400, 340)
        glVertex2f(420, 325)
        glVertex2f(400, 340)
        glEnd()
        glPopMatrix()
        glMatrixMode(GL_PROJECTION)
        glPopMatrix()
        glMatrixMode(GL_MODELVIEW)

def spawn_enemies(count=target_number):
    global targets, n
    max_enemies = enemy_count_per_round[current_round - 1] if current_round <= len(enemy_count_per_round) else 15
    if len(targets) + count > max_enemies:
        count = max(0, max_enemies - len(targets))
    if current_round < 4:
        n = current_round
    for _ in range(count):
        x = random.uniform(-region + 50, region - 50)
        y = random.uniform(-region + 50, region - 50)
        z = random.uniform(0, 10)
        while abs(x) < 200:
            x = random.uniform(-region + (100*n), region - 100)
        while abs(y) < 200:
            y = random.uniform(-region + (100*n), region - 100)
        targets.append([x, y, z])

def spawn_health_pack():
    if len(health_packs) >= max_health_packs:
        return
    # Spawn within a visible ring not far from center, outside castle tiles
    angle = random.uniform(0, 2 * math.pi)
    radius = random.uniform(max(castle_region + 50, 250), 380)
    x = radius * math.cos(angle)
    y = radius * math.sin(angle)
    z = 12
    health_packs.append([x, y, z])

def draw_health_packs():
    # Pulsing beacon cross + cylinder cap + additive glow billboard
    for hp in health_packs:
        glPushMatrix()
        glTranslatef(hp[0], hp[1], hp[2])
        s = 1.0 + 0.15 * math.sin(health_pack_pulse_t)
        glScalef(s, s, s)
        glColor3f(0.9, 0.1, 0.1)
        # Vertical cylinder (bigger)
        gluCylinder(gluNewQuadric(), 12, 12, 30, 12, 2)
        glTranslatef(0, 0, 30)
        glColor3f(1.0, 0.2, 0.2)
        gluSphere(gluNewQuadric(), 14, 12, 12)
        # Cross sign billboarded (approx)
        glColor3f(1.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glVertex3f(-8, -3, 8)
        glVertex3f( 8, -3, 8)
        glVertex3f( 8,  3, 8)
        glVertex3f(-8,  3, 8)
        glVertex3f(-3, -8, 8)
        glVertex3f( 3, -8, 8)
        glVertex3f( 3,  8, 8)
        glVertex3f(-3,  8, 8)
        glEnd()
        glPopMatrix()

        # Always-visible glow billboard
        glDisable(GL_DEPTH_TEST)
        glEnable(GL_BLEND)
        glBlendFunc(GL_SRC_ALPHA, GL_ONE)
        glColor4f(1.0, 0.2, 0.2, 0.12)
        glBegin(GL_QUADS)
        glVertex3f(hp[0]-40, hp[1]-40, hp[2]+35)
        glVertex3f(hp[0]+40, hp[1]-40, hp[2]+35)
        glVertex3f(hp[0]+40, hp[1]+40, hp[2]+35)
        glVertex3f(hp[0]-40, hp[1]+40, hp[2]+35)
        glEnd()
        glDisable(GL_BLEND)
        glEnable(GL_DEPTH_TEST)

def collect_health_pack(hp):
    global player_health
    if hp in health_packs:
        health_packs.remove(hp)
        player_health = min(player_health + health_pack_heal, player_max_health)

def update_enemy_shots():
    global enemy_shots, player_health, game_end
    if round_pause:
        return
    to_remove = []
    for shot in enemy_shots:
        shot[0] += 1.5 * math.cos(shot[3])
        shot[1] += 1.5 * math.sin(shot[3])
        if (shot[0] > GRID_LENGTH + 100 or shot[0] < -GRID_LENGTH or shot[1] > GRID_LENGTH + 100 or shot[1] < -GRID_LENGTH):
            to_remove.append(shot)
            continue
        dx = player_coords[0] - shot[0]
        dy = player_coords[1] - shot[1]
        dist = math.sqrt(dx*dx + dy*dy)
        if dist < castle_radius:
            if not cheat:
                player_health -= enemy_shot_damage
                if player_health <= 0:
                    game_end = True
                    targets.clear()
                    shots.clear()
                    enemy_shots.clear()
            to_remove.append(shot)
    for shot in to_remove:
        if shot in enemy_shots:
            enemy_shots.remove(shot)

def update_health_packs():
    global health_pack_spawn_timer
    health_pack_pulse()
    if round_pause or game_end:
        return
    health_pack_spawn_timer -= 1
    if health_pack_spawn_timer <= 0:
        spawn_health_pack()
        health_pack_spawn_timer = random.randint(
            health_pack_spawn_interval_min, health_pack_spawn_interval_max
        )

def next_round():
    global current_round, castle_radius, target_number, enemies_killed, region, round_pause, target_speed
    global player_health, player_max_health, kills_to_advance
    current_round += 1
    enemies_killed = 0
    target_speed += 0.25
    round_pause = True
    kills_to_advance += 10
    player_health = player_max_health
    if current_round < 5:
        castle_radius += 20
        region += 300
    if current_round <= len(enemy_count_per_round):
        target_number = enemy_count_per_round[current_round-1]
    else:
        target_number = enemy_count_per_round[-1] + 2 * (current_round - len(enemy_count_per_round))

def reset_game():
    global game_end, first_person_view, cheat, v_enable, failed_shots, region, towers, target_speed, current_round
    global player_health, player_max_health, player_score, player_coords, gun_rotation, castle_radius
    global tower_shots, tower_shot_timers, round_pause, round_choice_made, kills_to_advance, enemies_killed
    global health_packs, health_pack_spawn_timer, health_pack_pulse_t
    game_end, first_person_view = False, False
    cheat, v_enable, round_pause, round_choice_made = False, False, False, False
    player_coords = [0, 0, 0]
    towers = []
    region = 600
    player_max_health = 100
    target_speed = 0.025
    current_round = 1
    enemies_killed = 0
    castle_radius = 60
    kills_to_advance  = 10
    gun_rotation, player_health, player_max_health, player_score, failed_shots = 180, 100, 100, 0, 0
    shots.clear()
    targets.clear()
    tower_shots.clear()
    tower_shot_timers.clear()
    health_packs.clear()
    health_pack_spawn_timer = random.randint(health_pack_spawn_interval_min, health_pack_spawn_interval_max)
    health_pack_pulse_t = 0.0
    spawn_enemies()

def keyboardListener(key, x, y):
    global cheat, first_person_view, game_end, v_enable, gun_rotation, camera_position, camera_angle
    global player_coords, player_speed, player_turn_speed, player_health, player_max_health, player_score, failed_shots
    global round_pause, round_choice_made, towers, tower_shot_timers, tower_placement_mode, placement_marker_position
    global is_daytime, rain_enabled, fog_enabled
    # Global toggles always available
    if key == b'n':
        is_daytime = not is_daytime
        return
    if key == b't':
        rain_enabled = not rain_enabled
        if rain_enabled:
            ensure_rain_particles()
        return
    if key == b'f':
        fog_enabled = not fog_enabled
        return
    if key == b'h':
        # Force-spawn a health pack for testing
        spawn_health_pack()
        return
    if round_pause:
        if tower_placement_mode:
            if key == b's' and placement_marker_position[1] < region - 50:
                placement_marker_position[1] += 50
            elif key == b'w' and placement_marker_position[1] > -region + 50:
                placement_marker_position[1] -= 50
            elif key == b'd' and placement_marker_position[0] > -region + 50:
                placement_marker_position[0] -= 50
            elif key == b'a' and placement_marker_position[0] < region - 50:
                placement_marker_position[0] += 50
            elif key == b'\r':
                if (abs(placement_marker_position[0]) > castle_region or
                        abs(placement_marker_position[1]) > castle_region):
                    if len(towers) < 5:
                        towers.append(tuple(placement_marker_position))
                        tower_shot_timers[len(towers)-1] = random.randint(60, tower_shot_cooldown)
                    tower_placement_mode = False
                    round_pause = False
                    round_choice_made = True
                    first_person_view = not first_person_view
                    v_enable = first_person_view
                    player_turn_speed = 2.5 if first_person_view else 5
                    spawn_enemies(target_number)
                    
            return

        if key == b'1':
            spawn_enemies(target_number)
            player_max_health += 100
            player_health = player_max_health
            round_pause = False
            round_choice_made = True
            return
        elif key == b'2':
            if current_round > 4:
                round_choice_made = True
                return
            tower_placement_mode = True
            placement_marker_position = [400, 400]
            first_person_view = False
            v_enable = False
            player_turn_speed = 2.5 if first_person_view else 5
            camera_position, camera_angle = (0, 600, 600), 0
            return
        return

    if game_end and key != b'r':
        return
    elif key == b'c' and cheat == True:
        shots.clear()
        cheat = False
    elif key == b'v':
        if first_person_view and cheat:
            v_enable = not v_enable
    elif key == b'r' and game_end:
        reset_game()
    elif key == b'q' and game_end:
        sys.exit(0)
    if key == b'p':
        player_health = 1000
    gun_rotation %= 360
    if key == b'd':
        gun_rotation -= player_turn_speed
    if key == b'a':
        gun_rotation += player_turn_speed

def specialKeyListener(key, x, y):
    global camera_angle, camera_distance, camera_height, camera_min_height, camera_max_height
    if not game_end:
        if key == GLUT_KEY_UP:
            if camera_height > camera_min_height:
                camera_height -= 20
        elif key == GLUT_KEY_DOWN:
            if camera_height < camera_max_height:
                camera_height += 20
        elif key == GLUT_KEY_LEFT:
            camera_angle -= 5
        elif key == GLUT_KEY_RIGHT:
            camera_angle += 5

def mouseListener(button, state, x, y):
    global first_person_view, player_turn_speed, v_enable, game_end
    if game_end:
        return
    if button == GLUT_LEFT_BUTTON and state == GLUT_DOWN and cheat == False:
        fire_player_weapon()
    elif button == GLUT_RIGHT_BUTTON and state == GLUT_DOWN:
        first_person_view = not first_person_view
        v_enable = first_person_view
        player_turn_speed = 2.5 if first_person_view else 5

def configure_camera():
    """Simplified camera setup: first-person follows the gun, otherwise orbit around origin."""
    global camera_angle, camera_distance, camera_height
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(100, 1.25, 0.3, 2700)
    glMatrixMode(GL_MODELVIEW)
    glLoadIdentity()
    if first_person_view:
        angle = math.radians(gun_rotation)
        eye_x = player_coords[0] + (gun_position[0] * 1.2 * math.sin(angle)) - (gun_position[1] * 0.6 * math.cos(angle))
        eye_y = player_coords[1] - (gun_position[0] * 1.2 * math.cos(angle)) - (gun_position[1] * 0.6 * math.sin(angle))
        eye_z = player_coords[2] + gun_position[2] + 200
        cen_x = eye_x - math.sin(-angle) * 100
        cen_y = eye_y - math.cos(-angle) * 100
        cen_z = eye_z
        gluLookAt(eye_x, eye_y, eye_z + 50, cen_x, cen_y, cen_z - 30, 0, 0, 1)
    else:
        angle = math.radians(camera_angle)
        x = camera_distance * math.sin(angle)
        y = camera_distance * math.cos(angle)
        z = camera_height
        gluLookAt(x, y, z, 0, 0, 0, 0, 0, 1)

def idle():
    global player_score
    enemy_pulse()
    if rain_enabled:
        ensure_rain_particles()
        update_rain()
    update_health_packs()
    if round_pause:
        targets.clear()
        glutPostRedisplay()
        return
    if not game_end:
        update_enemies()
        update_enemy_shots()
        update_towers()
        update_tower_shots()
        update_player_projectiles()
        detect_target_hits()
    glutPostRedisplay()

def draw_gradient_background():
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, 800, 0, 650)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()
    glBegin(GL_QUADS)
    # Sky gradient depends on day/night
    if is_daytime:
        glColor3f(0.63, 0.81, 0.98)  # light sky blue
    else:
        glColor3f(0.03, 0.05, 0.10)  # dark night sky
    glVertex2f(0, 650)
    glVertex2f(800, 650)
    if is_daytime:
        glColor3f(0.07, 0.11, 0.21)  # horizon darker
    else:
        glColor3f(0.0, 0.0, 0.02)    # near-black horizon
    glVertex2f(800, 0)
    glVertex2f(0, 0)
    glEnd()
    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)

def ensure_rain_particles():
    while len(rain_particles) < max_rain_particles:
        x = random.uniform(-region - 200, region + 200)
        y = random.uniform(-region - 200, region + 200)
        z = random.uniform(300, 1200)
        vx = rain_wind + random.uniform(-0.3, 0.3)
        vy = random.uniform(-0.2, 0.2)
        vz = -rain_speed_z * random.uniform(0.8, 1.2)
        rain_particles.append([x, y, z, vx, vy, vz])

def update_rain():
    if not rain_enabled:
        return
    for p in rain_particles:
        p[0] += p[3]
        p[1] += p[4]
        p[2] += p[5]
        if p[2] < 0 or abs(p[0]) > GRID_LENGTH + 400 or abs(p[1]) > GRID_LENGTH + 400:
            p[0] = random.uniform(-region - 200, region + 200)
            p[1] = random.uniform(-region - 200, region + 200)
            p[2] = random.uniform(600, 1400)
            p[3] = rain_wind + random.uniform(-0.3, 0.3)
            p[4] = random.uniform(-0.2, 0.2)
            p[5] = -rain_speed_z * random.uniform(0.8, 1.2)

def draw_rain():
    if not rain_enabled or not rain_particles:
        return
    glDisable(GL_LIGHTING)
    glColor3f(0.6, 0.7, 0.9)
    glBegin(GL_LINES)
    for x, y, z, vx, vy, vz in rain_particles:
        glVertex3f(x, y, z)
        glVertex3f(x - vx * 0.6, y - vy * 0.6, z - vz * 0.6)
    glEnd()

def showScreen():
    global game_end, player_health, player_max_health, player_score, failed_shots, round_pause, tower_placement_mode
    glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
    glLoadIdentity()
    glViewport(0, 0, 800, 650)
    draw_gradient_background()
    configure_camera()

    # Fog setup
    if fog_enabled:
        glEnable(GL_FOG)
        fog_color = [0.63, 0.81, 0.98, 1.0] if is_daytime else [0.07, 0.11, 0.21, 1.0]
        glFogfv(GL_FOG_COLOR, (GLfloat * 4)(*fog_color))
        glFogi(GL_FOG_MODE, GL_EXP2)
        glFogf(GL_FOG_DENSITY, fog_density)
        glHint(GL_FOG_HINT, GL_NICEST)
    else:
        glDisable(GL_FOG)

    draw_scene()
    if rain_enabled:
        draw_rain()
    if v_enable:
        crosshair_position()

    # UI overlays
    if round_pause:
        if tower_placement_mode:
            glPushMatrix()
            glTranslatef(placement_marker_position[0], placement_marker_position[1], 10)
            glScalef(target_pulse, target_pulse, target_pulse)
            glColor3f(0, 1, 1)
            glutSolidSphere(20, 16, 16)
            glPopMatrix()
            render_text(200, 400, "Use W, A, S, D to move the marker", color=(1, 1, 0))
            render_text(200, 350, "Press Enter to place the tower (Can't place on white tiles)", color=(0, 1, 0))
        else:
            if current_round < 5:
                render_text(200, 400, f"Round {current_round-1} Completed! More region conquered and health restored.", color=(1, 1, 0))
                render_text(200, 350, "Choose your reward:", color=(1, 0.7, 0.2))
                render_text(200, 300, "Press [1] to increase base castle health by 100%", color=(0, 1, 0))
                render_text(200, 250, "Press [2] to add an archer tower in your arena ! ", color=(1, 0.7, 1))
                render_text(200, 200, "A new wave of enemies are coming & they are too faster !!", color=(1, 1, 0))
            else:
                render_text(200, 400, f"Round {current_round-1} Completed! Max health increased by 100%", color=(1, 1, 0))
                render_text(200, 300, "Press [1] to continue", color=(0, 1, 1))
                render_text(200, 250, "A new wave of enemies  are coming and they are too faster!!!", color=(1, 0, 0))
    elif not game_end:
        # HUD
        render_text(10, 650 - 25, f"Castle Health: {player_health}/{player_max_health}", color=(0, 0, 0))
        render_text(10, 650 - 55, f"Player Score: {player_score}")
        render_text(10, 650 - 85, f"Shots Missed: {failed_shots}")
        render_text(350, 625, f"Round {current_round}", color=(0, 0, 0))
        remaining = kills_to_advance - enemies_killed
        color = (1, 0, 0) if remaining > 5 else (1, 0.5, 0) if remaining > 2 else (0, 1, 0)
        render_text(580, 650 - 25, f"Enemies to Kill: {remaining}", color=(0, 0, 0))
        render_text(580, 650 - 55, f"Total Enemies: {len(targets)}")
        if health_packs:
            render_text(580, 650 - 85, "Health Pack: AVAILABLE (shoot it)", color=(0, 0.6, 0))
        else:
            render_text(580, 650 - 85, "Health Pack: searching... [[H to spawn]]", color=(0.4, 0.4, 0.4))
    else:
        # Game over screen
        render_text(10, 650 - 25, f"Game is Over :)... Your Score is {player_score}")
        render_text(10, 650 - 55, 'Press "R" to RESTART the Game!')
        render_text(10, 650 - 85, 'Press "Q" to QUIT the Game!')
        render_text(10, 650 - 145, 'Press "F" to toggle Fog! while playing')
        render_text(10, 650 - 175, 'Press "T" to toggle Rain! while playing')
        render_text(10, 650 - 205, 'Press "N" to toggle Day/Night! while playing')
        render_text(10, 650 - 235, 'Press "V" to toggle Crosshair! while playing')
        render_text(10, 650 - 265, 'Press "C" to toggle Camera! while playing')
        render_text(10, 650 - 295, 'Press "G" to toggle Gun! while playing')
        render_text(10, 650 - 325, 'Developed by - Anindya Paul & Nabib Azad Jisan')

    glutSwapBuffers()

    # if  game_end!=None  and not round_pause:
    #     time.sleep(0.01)



glutInit()
glutInitDisplayMode(GLUT_DOUBLE | GLUT_RGB | GLUT_DEPTH)
glutInitWindowSize(800, 650)
glutCreateWindow(b"Counter_king")
spawn_enemies()
glutDisplayFunc(showScreen)
glutIdleFunc(idle)
glutKeyboardFunc(keyboardListener)
glutSpecialFunc(specialKeyListener)
glutMouseFunc(mouseListener)
glutMainLoop()