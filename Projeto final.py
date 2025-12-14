import pygame
from pygame.locals import *
from OpenGL.GL import *
from OpenGL.GLU import *
from PIL import Image
import math
import random
import os

WIDTH, HEIGHT = 1200, 800

# Traz a pasta onde está os arquivos
BASE_PATH = os.path.dirname(os.path.abspath(__file__))
TEXTURE_PATH = os.path.join(BASE_PATH, "pneuLogo.png")
MARLBORO_PATH = os.path.join(BASE_PATH, "marlboro.png")
SHELL_PATH = os.path.join(BASE_PATH, "Shell.png")
AUDIO_PATH = os.path.join(BASE_PATH, "Ferrari-F1.wav")

goodyear_texture_id = None
marlboro_texture_id = None
shell_texture_id = None

# Variáveis de Estado do Carro
car_x_position = 0.0
car_y_position = 0.0
car_roll_angle = 0.0
car_pitch_angle = 0.0
track_offset = 0.0
wheel_rotation = 0.0
speed = 0.0
drs_angle = 0.0
drs_active = False
steer_visual = 0.0
fire_particles = []
autopilot_active = False
autopilot_timer = 0.0

# Variáveis de Física/Loop
is_jumping = False
jump_velocity = 0.0
GRAVITY = -9.8
JUMP_STRENGTH = 6.0
is_looping = False
loop_progress = 0.0
LOOP_RATE = 180.0

# Câmeras
camera_mode = 0
cam_angle = 180.0
cam_zoom = 12.0
cam_height_orbital = 5.0

# Cores
COLOR_MP4_WHITE = (0.95, 0.95, 0.95)
COLOR_MP4_RED = (0.95, 0.1, 0.05)
COLOR_BLACK = (0.1, 0.1, 0.1)
COLOR_TIRE = (0.15, 0.15, 0.15)
COLOR_RIM = (0.3, 0.3, 0.3)
COLOR_NUT = (0.5, 0.5, 0.1)
COLOR_HUBCAP = (0.6, 0.6, 0.65)


def load_texture(filename):
    try:
        img = Image.open(filename)
        img = img.transpose(Image.FLIP_TOP_BOTTOM)
        if img.mode == 'RGBA':
            img_data = img.tobytes("raw", "RGBA", 0, -1)
            format = GL_RGBA
        else:
            img = img.convert('RGB')
            img_data = img.tobytes("raw", "RGB", 0, -1)
            format = GL_RGB

        width, height = img.size
        tex_id = glGenTextures(1)
        glBindTexture(GL_TEXTURE_2D, tex_id)

        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER,
                        GL_LINEAR_MIPMAP_LINEAR)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_S, GL_REPEAT)
        glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_WRAP_T, GL_CLAMP_TO_EDGE)

        gluBuild2DMipmaps(GL_TEXTURE_2D, format, width, height,
                          format, GL_UNSIGNED_BYTE, img_data)
        print(
            f"Sucesso: Textura carregada ({os.path.basename(filename)}). ID: {tex_id}")
        return tex_id

    except Exception as e:
        print(f"ERRO ao carregar textura ({filename}): {e}")
        return None


def init_gl():
    global goodyear_texture_id, marlboro_texture_id, shell_texture_id
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)
    glEnable(GL_LIGHT0)
    glEnable(GL_LIGHT1)
    glEnable(GL_COLOR_MATERIAL)
    glEnable(GL_NORMALIZE)

    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)

    glColorMaterial(GL_FRONT_AND_BACK, GL_AMBIENT_AND_DIFFUSE)
    glShadeModel(GL_SMOOTH)

    glLightfv(GL_LIGHT0, GL_POSITION, [10.0, 15.0, 5.0, 1.0])
    glLightfv(GL_LIGHT0, GL_AMBIENT, [0.3, 0.3, 0.4, 1.0])
    glLightfv(GL_LIGHT0, GL_DIFFUSE, [1.0, 1.0, 1.0, 1.0])
    glLightfv(GL_LIGHT0, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])

    glLightfv(GL_LIGHT1, GL_POSITION, [-50.0, 20.0, -50.0, 0.0])
    glLightfv(GL_LIGHT1, GL_DIFFUSE, [0.3, 0.3, 0.4, 1.0])

    glClearColor(0.4, 0.6, 0.9, 1.0)
    resize(WIDTH, HEIGHT)

    goodyear_texture_id = load_texture(TEXTURE_PATH)
    marlboro_texture_id = load_texture(MARLBORO_PATH)
    shell_texture_id = load_texture(SHELL_PATH)


def resize(width, height):
    if height == 0:
        height = 1
    glViewport(0, 0, width, height)
    glMatrixMode(GL_PROJECTION)
    glLoadIdentity()
    gluPerspective(45, width / height, 0.1, 500.0)
    glMatrixMode(GL_MODELVIEW)


def set_material_chrome():
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [1.0, 1.0, 1.0, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 120.0)


def set_material_rubber():
    glMaterialfv(GL_FRONT_AND_BACK, GL_SPECULAR, [0.1, 0.1, 0.1, 1.0])
    glMaterialf(GL_FRONT_AND_BACK, GL_SHININESS, 10.0)


# Inicio do carro - PRIMITIVAS DO DESENHO
def draw_solid_box_trapezoid_base(base_w, top_w, h, length, z_start, color_top, color_side, top_material="chrome", texture_id=None):
    if top_material == "chrome":
        set_material_chrome()
    else:
        set_material_rubber()

    bw, tw = base_w / 2, top_w / 2

    # topo
    if texture_id:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor3f(1.0, 1.0, 1.0)
    else:
        glDisable(GL_TEXTURE_2D)
        glColor3fv(color_top)

    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)

    if texture_id:
        glTexCoord2f(0.0, 1.0)
    glVertex3f(-tw, h, z_start)

    if texture_id:
        glTexCoord2f(0.0, 0.0)
    glVertex3f(-tw, h, z_start - length)

    if texture_id:
        glTexCoord2f(1.0, 0.0)
    glVertex3f(tw, h, z_start - length)

    if texture_id:
        glTexCoord2f(1.0, 1.0)
    glVertex3f(tw, h, z_start)
    glEnd()

    if texture_id:
        glDisable(GL_TEXTURE_2D)

    # Lados (Sem textura)
    glColor3fv(color_side)
    glBegin(GL_QUADS)

    # Esquerdo
    glNormal3f(-1, 0.5, 0)
    glVertex3f(-bw, 0, z_start)
    glVertex3f(-tw, h, z_start)
    glVertex3f(-tw, h, z_start - length)
    glVertex3f(-bw, 0, z_start - length)

    # Direito
    glNormal3f(1, 0.5, 0)
    glVertex3f(bw, 0, z_start)
    glVertex3f(bw, 0, z_start - length)
    glVertex3f(tw, h, z_start - length)
    glVertex3f(tw, h, z_start)

    # Frente e Trás
    glNormal3f(0, 0, 1)
    glVertex3f(-bw, 0, z_start)
    glVertex3f(bw, 0, z_start)
    glVertex3f(tw, h, z_start)
    glVertex3f(-tw, h, z_start)

    glNormal3f(0, 0, -1)
    glVertex3f(-bw, 0, z_start - length)
    glVertex3f(-tw, h, z_start - length)
    glVertex3f(tw, h, z_start - length)
    glVertex3f(bw, 0, z_start - length)
    glEnd()

    set_material_rubber()
    glBegin(GL_QUADS)
    glColor3fv(COLOR_BLACK)
    glNormal3f(0, -1, 0)
    glVertex3f(-bw, 0, z_start)
    glVertex3f(bw, 0, z_start)
    glVertex3f(bw, 0, z_start - length)
    glVertex3f(-bw, 0, z_start - length)
    glEnd()


def draw_solid_box_trapezoid(base_w, top_w, h, length, z_start, color_top, color_side, top_material="chrome", z_offset=0, texture_id=None):
    glPushMatrix()
    if z_offset != 0:
        glTranslatef(z_offset, 0, 0)
    draw_solid_box_trapezoid_base(
        base_w, top_w, h, length, z_start, color_top, color_side, top_material, texture_id)
    glPopMatrix()


def draw_solid_box_tapered(w_front, w_back, h_front, h_back, length, z_start, color_top, color_side, texture_id=None):
    wf, wb = w_front / 2, w_back / 2
    hf, hb = h_front, h_back
    z_end = z_start - length

    glBegin(GL_QUADS)
    # Topo
    glColor3fv(color_top)
    glNormal3f(0, 1, 0)
    glVertex3f(-wf, hf, z_start)
    glVertex3f(-wb, hb, z_end)
    glVertex3f(wb, hb, z_end)
    glVertex3f(wf, hf, z_start)

    # Base
    glColor3fv(COLOR_BLACK)
    glNormal3f(0, -1, 0)
    glVertex3f(-wf, 0, z_start)
    glVertex3f(wf, 0, z_start)
    glVertex3f(wb, 0, z_end)
    glVertex3f(-wb, 0, z_end)
    glEnd()

    # Lados com textura
    if texture_id:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, texture_id)
        glColor3f(1.0, 1.0, 1.0)
    else:
        glDisable(GL_TEXTURE_2D)
        glColor3fv(color_side)

    glBegin(GL_QUADS)

    # Lado Esquerdo
    glNormal3f(-1, 0, (wf-wb)/length)
    if texture_id:
        glTexCoord2f(0.0, 1.0)
    glVertex3f(-wf, 0, z_start)
    if texture_id:
        glTexCoord2f(0.0, 0.0)
    glVertex3f(-wf, hf, z_start)
    if texture_id:
        glTexCoord2f(1.0, 0.0)
    glVertex3f(-wb, hb, z_end)
    if texture_id:
        glTexCoord2f(1.0, 1.0)
    glVertex3f(-wb, 0, z_end)

    # Lado Direito
    glNormal3f(1, 0, (wf-wb)/length)
    if texture_id:
        glTexCoord2f(0.0, 1.0)
    glVertex3f(wf, 0, z_start)
    if texture_id:
        glTexCoord2f(1.0, 1.0)
    glVertex3f(wb, 0, z_end)
    if texture_id:
        glTexCoord2f(1.0, 0.0)
    glVertex3f(wb, hb, z_end)
    if texture_id:
        glTexCoord2f(0.0, 0.0)
    glVertex3f(wf, hf, z_start)

    glEnd()

    if texture_id:
        glDisable(GL_TEXTURE_2D)

    # Frente e Trás sem textura
    glColor3fv(color_side)
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glVertex3f(-wf, 0, z_start)
    glVertex3f(wf, 0, z_start)
    glVertex3f(wf, hf, z_start)
    glVertex3f(-wf, hf, z_start)

    glNormal3f(0, 0, -1)
    glVertex3f(-wb, 0, z_end)
    glVertex3f(-wb, hb, z_end)
    glVertex3f(wb, hb, z_end)
    glVertex3f(wb, 0, z_end)
    glEnd()

# Desenho da roda


def draw_wheel_solid_filled_both_sides(x, y, z, radius, width):
    slices = 32
    r_outer = radius
    r_inner = radius * 0.6
    rim_radius = r_inner - 0.01

    glPushMatrix()
    glTranslatef(x, y, z)
    glRotatef(90, 0, 1, 0)

    # Banda de rondagem
    set_material_rubber()
    glDisable(GL_TEXTURE_2D)
    glColor3fv(COLOR_TIRE)
    glBegin(GL_QUAD_STRIP)
    for i in range(slices + 1):
        a = 2 * math.pi * i / slices
        glNormal3f(math.cos(a), math.sin(a), 0)
        glVertex3f(radius * math.cos(a), radius * math.sin(a), -width / 2)
        glVertex3f(radius * math.cos(a), radius * math.sin(a), width / 2)
    glEnd()

    # Laterais do pneu com textura - Goodyear
    if goodyear_texture_id:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, goodyear_texture_id)
        glColor3f(1.0, 1.0, 1.0)
        set_material_rubber()

        for side in [1, -1]:
            glNormal3f(0, 0, side)
            glBegin(GL_QUAD_STRIP)
            for i in range(slices + 1):
                a = 2 * math.pi * i / slices
                u_coord = i / slices
                glTexCoord2f(u_coord, 0.0)
                glVertex3f(r_inner * math.cos(a), r_inner *
                           math.sin(a), side * width / 2)
                glTexCoord2f(u_coord, 1.0)
                glVertex3f(r_outer * math.cos(a), r_outer *
                           math.sin(a), side * width / 2)
            glEnd()
        glDisable(GL_TEXTURE_2D)
    else:
        glColor3fv(COLOR_TIRE)
        for side in [1, -1]:
            glNormal3f(0, 0, side)
            glBegin(GL_QUAD_STRIP)
            for i in range(slices + 1):
                a = 2 * math.pi * i / slices
                glVertex3f(r_inner * math.cos(a), r_inner *
                           math.sin(a), side * width / 2)
                glVertex3f(r_outer * math.cos(a), r_outer *
                           math.sin(a), side * width / 2)
            glEnd()

    # Aro e calota
    for side in [1, -1]:
        glNormal3f(0, 0, side)
        set_material_chrome()
        glColor3fv(COLOR_RIM)
        rim_offset = 0.005
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, 0, side * (width / 2 + rim_offset))
        for i in range(slices + 1):
            a = 2 * math.pi * i / slices
            glVertex3f(rim_radius * math.cos(a), rim_radius *
                       math.sin(a), side * (width / 2 + rim_offset))
        glEnd()

        glColor3fv(COLOR_HUBCAP)
        nut_radius = radius * 0.15
        nut_offset = rim_offset + 0.01
        glBegin(GL_TRIANGLE_FAN)
        glVertex3f(0, 0, side * (width / 2 + nut_offset + 0.02))
        for i in range(slices + 1):
            a = 2 * math.pi * i / slices
            glVertex3f(nut_radius * math.cos(a), nut_radius *
                       math.sin(a), side * (width / 2 + nut_offset))
        glEnd()

    glPopMatrix()

# Corpo do carro


def draw_mp4_6_body():
    global drs_angle, marlboro_texture_id, shell_texture_id
    set_material_rubber()
    glColor3fv(COLOR_BLACK)
    floor_h = 0.05

    # Assoalho
    glPushMatrix()
    glTranslatef(0, floor_h, 2.0)
    draw_solid_box_trapezoid(0.5, 0.5, 0.05, 3.8, 0,
                             COLOR_BLACK, COLOR_BLACK, "rubber")
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0, 0.13, 1.6)
    draw_solid_box_trapezoid(0.45, 0.35, 0.02, 0.6, 0,
                             COLOR_BLACK, COLOR_BLACK, "rubber")
    glPopMatrix()

    sp_z_start = 0.6
    sp_length = 1.7
    sp_width_front = 0.7
    sp_width_back = 0.35
    sp_offset_x = 0.35

    glPushMatrix()
    glTranslatef(-sp_offset_x, floor_h, sp_z_start)
    draw_solid_box_tapered(sp_width_front, sp_width_back,
                           0.04, 0.04, sp_length, 0, COLOR_BLACK, COLOR_BLACK)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(sp_offset_x, floor_h, sp_z_start)
    draw_solid_box_tapered(sp_width_front, sp_width_back,
                           0.04, 0.04, sp_length, 0, COLOR_BLACK, COLOR_BLACK)
    glPopMatrix()

    # Monocoque
    glPushMatrix()
    glTranslatef(0, 0.1, 0.8)
    draw_solid_box_tapered(0.62, 0.65, 0.45, 0.45, 1.6,
                           0, COLOR_MP4_WHITE, COLOR_MP4_WHITE)
    glTranslatef(0, 0.451, 0)
    draw_solid_box_trapezoid(0.60, 0.58, 0.02, 0.8, 0,
                             COLOR_MP4_RED, COLOR_MP4_RED, "rubber")

    glEnable(GL_BLEND)
    glColor4f(0.1, 0.1, 0.1, 0.7)
    glBegin(GL_QUAD_STRIP)
    for i in range(7):
        angle = math.radians(180 - i * 30)
        x = 0.28 * math.cos(angle)
        z = -0.1 + 0.1 * math.sin(angle)
        glVertex3f(x, 0, -0.1)
        glVertex3f(x, 0.1, z)
    glEnd()
    glDisable(GL_BLEND)
    glPopMatrix()

    # Bico Frontal
    glPushMatrix()
    glTranslatef(0, 0.1, 0.0)
    conn_w_back = 0.62 / 2
    conn_h_back = 0.47
    z_conn_start = 0.8
    conn_w_front = 0.45 / 2
    conn_h_front = 0.45
    z_conn_end = 1.6

    glBegin(GL_QUADS)
    glColor3fv(COLOR_MP4_WHITE)
    glNormal3f(-1, 0, 0)
    glVertex3f(-conn_w_back, 0.15, z_conn_start)
    glVertex3f(-conn_w_back, conn_h_back, z_conn_start)
    glVertex3f(-conn_w_front, conn_h_front, z_conn_end)
    glVertex3f(-conn_w_front, 0.15, z_conn_end)

    glNormal3f(1, 0, 0)
    glVertex3f(conn_w_back, 0.15, z_conn_start)
    glVertex3f(conn_w_back, conn_h_back, z_conn_start)
    glVertex3f(conn_w_front, conn_h_front, z_conn_end)
    glVertex3f(conn_w_front, 0.15, z_conn_end)

    glNormal3f(0, 0.5, 0)
    glVertex3f(-conn_w_back, conn_h_back, z_conn_start)
    glVertex3f(conn_w_back, conn_h_back, z_conn_start)
    glVertex3f(conn_w_front, conn_h_front, z_conn_end)
    glVertex3f(-conn_w_front, conn_h_front, z_conn_end)

    glColor3fv(COLOR_BLACK)
    glNormal3f(0, -1, 0)
    glVertex3f(-conn_w_back, 0.15, z_conn_start)
    glVertex3f(conn_w_back, 0.15, z_conn_start)
    glVertex3f(conn_w_front, 0.15, z_conn_end)
    glVertex3f(-conn_w_front, 0.15, z_conn_end)
    glEnd()

    # Ponta do Bico
    glPushMatrix()
    glTranslatef(0, 0, 1.6)
    base_w = 0.45 / 2
    base_h_top = 0.45
    base_h_bot = 0.15
    z_start = 0.0
    mid_w = 0.28 / 2
    mid_h_top = 0.35
    mid_h_bot = 0.15
    z_mid = 0.55
    tip_w = 0.10 / 2
    tip_h_top = 0.28
    tip_h_bot = 0.15
    z_end = 1.45

    # Desenha a base branca da parte superior do bico
    glBegin(GL_QUADS)
    glColor3fv(COLOR_MP4_WHITE)
    glNormal3f(0, 0.5, 0.2)
    glVertex3f(-mid_w, mid_h_top, z_mid)
    glVertex3f(mid_w, mid_h_top, z_mid)
    glVertex3f(tip_w, tip_h_top, z_end)
    glVertex3f(-tip_w, tip_h_top, z_end)
    glEnd()

    # Logo SHELL quadrado
    if shell_texture_id:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, shell_texture_id)
        glColor3f(1.0, 1.0, 1.0)

        y_offset = 0.001
        logo_size = 0.28
        z_center = 0.85

        t = (z_center - z_mid) / (z_end - z_mid)
        current_w = mid_w + t * (tip_w - mid_w)
        current_h = mid_h_top + t * (tip_h_top - mid_h_top)

        x_left = -logo_size / 2
        x_right = logo_size / 2
        z_back = z_center - logo_size / 2
        z_front = z_center + logo_size / 2

        t_back = (z_back - z_mid) / (z_end - z_mid)
        h_back = mid_h_top + t_back * (tip_h_top - mid_h_top) + y_offset

        t_front = (z_front - z_mid) / (z_end - z_mid)
        h_front = mid_h_top + t_front * (tip_h_top - mid_h_top) + y_offset

        glBegin(GL_QUADS)
        glNormal3f(0, 0.5, 0.2)
        glTexCoord2f(0.0, 0.0)
        glVertex3f(x_left, h_back, z_back)
        glTexCoord2f(1.0, 0.0)
        glVertex3f(x_right, h_back, z_back)
        glTexCoord2f(1.0, 1.0)
        glVertex3f(x_right, h_front, z_front)
        glTexCoord2f(0.0, 1.0)
        glVertex3f(x_left, h_front, z_front)
        glEnd()

        glDisable(GL_TEXTURE_2D)

    # Continua desenhando o resto do bico
    glBegin(GL_QUADS)
    glColor3fv(COLOR_MP4_WHITE)
    # Topo parte traseira
    glNormal3f(0, 0.5, 0)
    glVertex3f(-base_w, base_h_top, z_start)
    glVertex3f(base_w, base_h_top, z_start)
    glVertex3f(mid_w,  mid_h_top,  z_mid)
    glVertex3f(-mid_w,  mid_h_top,  z_mid)

    # Lados
    glNormal3f(-1, 0, 0)
    glVertex3f(-base_w, base_h_bot, z_start)
    glVertex3f(-base_w, base_h_top, z_start)
    glVertex3f(-mid_w,  mid_h_top,  z_mid)
    glVertex3f(-mid_w,  mid_h_bot,  z_mid)

    glNormal3f(1, 0, 0)
    glVertex3f(base_w, base_h_top, z_start)
    glVertex3f(base_w, base_h_bot, z_start)
    glVertex3f(mid_w,  mid_h_bot,  z_mid)
    glVertex3f(mid_w,  mid_h_top,  z_mid)

    # Lados da ponta
    glNormal3f(-1, 0, 0)
    glVertex3f(-mid_w, mid_h_bot, z_mid)
    glVertex3f(-mid_w, mid_h_top, z_mid)
    glVertex3f(-tip_w, tip_h_top, z_end)
    glVertex3f(-tip_w, tip_h_bot, z_end)

    glNormal3f(1, 0, 0)
    glVertex3f(mid_w, mid_h_top, z_mid)
    glVertex3f(mid_w, mid_h_bot, z_mid)
    glVertex3f(tip_w, tip_h_bot, z_end)
    glVertex3f(tip_w, tip_h_top, z_end)

    # Frente
    glNormal3f(0, 0, 1)
    glVertex3f(-tip_w, tip_h_bot, z_end)
    glVertex3f(tip_w, tip_h_bot, z_end)
    glVertex3f(tip_w, tip_h_top, z_end)
    glVertex3f(-tip_w, tip_h_top, z_end)

    # Fundo
    glColor3fv(COLOR_BLACK)
    glNormal3f(0, -1, 0)
    glVertex3f(-base_w, base_h_bot, z_start)
    glVertex3f(base_w, base_h_bot, z_start)
    glVertex3f(mid_w,  mid_h_bot,  z_mid)
    glVertex3f(-mid_w,  mid_h_bot,  z_mid)

    glNormal3f(0, -1, 0)
    glVertex3f(-mid_w, mid_h_bot, z_mid)
    glVertex3f(mid_w, mid_h_bot, z_mid)
    glVertex3f(tip_w, tip_h_bot, z_end)
    glVertex3f(-tip_w, tip_h_bot, z_end)
    glEnd()
    glPopMatrix()
    glPopMatrix()

    # Cockpit
    glPushMatrix()
    glTranslatef(0, 0.55, 0.3)
    set_material_rubber()
    glColor3fv(COLOR_BLACK)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-0.22, -0.2, 0.2)
    glVertex3f(0.22, -0.2, 0.2)
    glVertex3f(0.22, -0.2, -0.4)
    glVertex3f(-0.22, -0.2, -0.4)
    glNormal3f(0, 0.5, 1)
    glVertex3f(-0.22, -0.2, -0.4)
    glVertex3f(0.22, -0.2, -0.4)
    glVertex3f(0.22, 0.15, -0.55)
    glVertex3f(-0.22, 0.15, -0.55)
    glEnd()
    glPopMatrix()

    # Sidepods e engine cover
    glPushMatrix()
    glTranslatef(-0.45, 0.1, 0.4)
    draw_solid_box_tapered(0.55, 0.40, 0.35, 0.25, 1.8,
                           0, COLOR_MP4_WHITE, COLOR_MP4_WHITE)
    glTranslatef(0, 0.351, -0.1)
    draw_solid_box_tapered(0.53, 0.38, 0.02, 0.02, 1.6,
                           0, COLOR_MP4_RED, COLOR_MP4_RED)
    glPopMatrix()

    glPushMatrix()
    glTranslatef(0.45, 0.1, 0.4)
    draw_solid_box_tapered(0.55, 0.40, 0.35, 0.25, 1.8,
                           0, COLOR_MP4_WHITE, COLOR_MP4_WHITE)
    glTranslatef(0, 0.351, -0.1)
    draw_solid_box_tapered(0.53, 0.38, 0.02, 0.02, 1.6,
                           0, COLOR_MP4_RED, COLOR_MP4_RED)
    glPopMatrix()

    # Engine cover texturizada
    glPushMatrix()
    glTranslatef(0, 0.55, -0.2)

    if marlboro_texture_id:
        glEnable(GL_TEXTURE_2D)
        glBindTexture(GL_TEXTURE_2D, marlboro_texture_id)
        glColor3f(1.0, 1.0, 1.0)
    else:
        glColor3fv(COLOR_MP4_WHITE)

    glBegin(GL_QUADS)
    # Lado esquerdo
    glNormal3f(-0.5, 0.5, 0)
    if marlboro_texture_id:
        glTexCoord2f(1.0, 1.0)
    glVertex3f(-0.25, 0, 0)
    if marlboro_texture_id:
        glTexCoord2f(0.0, 1.0)
    glVertex3f(-0.1, -0.2, -1.6)
    if marlboro_texture_id:
        glTexCoord2f(0.0, 0.0)
    glVertex3f(-0.1, 0.1, -1.6)
    if marlboro_texture_id:
        glTexCoord2f(1.0, 0.0)
    glVertex3f(-0.25, 0.4, 0)

    # Lado direito
    glNormal3f(0.5, 0.5, 0)
    if marlboro_texture_id:
        glTexCoord2f(0.0, 1.0)
    glVertex3f(0.25, 0, 0)
    if marlboro_texture_id:
        glTexCoord2f(0.0, 0.0)
    glVertex3f(0.25, 0.4, 0)
    if marlboro_texture_id:
        glTexCoord2f(1.0, 0.0)
    glVertex3f(0.1, 0.1, -1.6)
    if marlboro_texture_id:
        glTexCoord2f(1.0, 1.0)
    glVertex3f(0.1, -0.2, -1.6)
    glEnd()

    if marlboro_texture_id:
        glDisable(GL_TEXTURE_2D)
        glColor3fv(COLOR_MP4_WHITE)

    # Topo da carenagem
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0.2)
    glVertex3f(-0.25, 0.4, 0)
    glVertex3f(0.25, 0.4, 0)
    glVertex3f(0.1, 0.1, -1.6)
    glVertex3f(-0.1, 0.1, -1.6)
    glEnd()

    glTranslatef(0, 0.35, 0.1)
    draw_solid_box_tapered(0.32, 0.22, 0.25, 0.15, 0.6,
                           0, COLOR_MP4_RED, COLOR_MP4_RED)

    glColor3fv(COLOR_BLACK)
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glVertex3f(-0.14, 0.02, 0.01)
    glVertex3f(0.14, 0.02, 0.01)
    glVertex3f(0.14, 0.23, 0.01)
    glVertex3f(-0.14, 0.23, 0.01)
    glEnd()
    glPopMatrix()

    # Asas
    glPushMatrix()
    glTranslatef(0, 0.15, 2.6)

    # Asa principal dianteira
    draw_solid_box_trapezoid(1.6, 1.6, 0.05, 0.4, 0,
                             COLOR_MP4_WHITE, COLOR_MP4_WHITE, "rubber")

    glTranslatef(0, 0.06, -0.1)
    draw_solid_box_trapezoid(1.4, 1.3, 0.02, 0.2, 0,
                             COLOR_MP4_WHITE, COLOR_MP4_WHITE, "rubber")
    for side in [1, -1]:
        glPushMatrix()
        glTranslatef(0.81 * side, -0.05, 0.1)
        glColor3fv(COLOR_MP4_WHITE)
        glBegin(GL_QUADS)
        glNormal3f(side, 0, 0)
        glVertex3f(0, 0, 0)
        glVertex3f(0, 0.3, 0)
        glVertex3f(0, 0.3, -0.45)
        glVertex3f(0, 0, -0.45)
        glEnd()
        glPopMatrix()
    glPopMatrix()

    # Asa traseira
    glPushMatrix()
    glTranslatef(0, 0.85, -1.6)
    glPushMatrix()
    glTranslatef(0, -0.45, 0.2)
    draw_solid_box_trapezoid(0.06, 0.06, 0.5, 0.3, 0,
                             COLOR_BLACK, COLOR_BLACK, "rubber")
    glPopMatrix()
    draw_solid_box_trapezoid(1.1, 1.1, 0.05, 0.4, 0,
                             COLOR_MP4_RED, COLOR_MP4_RED, "rubber")
    glPushMatrix()
    glTranslatef(0, 0.1, -0.05)
    glRotatef(drs_angle, 1, 0, 0)
    draw_solid_box_trapezoid(1.08, 1.08, 0.04, 0.35, 0,
                             COLOR_MP4_RED, COLOR_MP4_RED, "rubber")
    glPopMatrix()
    glTranslatef(0, -0.4, 0.1)
    draw_solid_box_trapezoid(1.0, 1.0, 0.05, 0.3, 0,
                             COLOR_MP4_WHITE, COLOR_MP4_WHITE, "rubber")
    glTranslatef(0, 0.4, -0.1)
    for side in [1, -1]:
        glPushMatrix()
        glTranslatef(0.56 * side, -0.3, 0.1)
        glColor3fv(COLOR_MP4_WHITE)
        glBegin(GL_QUADS)
        glNormal3f(side, 0, 0)
        glVertex3f(0, -0.1, 0)
        glVertex3f(0, 0.7, 0)
        glVertex3f(0, 0.7, -0.6)
        glVertex3f(0, -0.1, -0.6)
        glEnd()
        glPopMatrix()
    glPopMatrix()

    # Suspensão
    glLineWidth(6)
    glColor3f(0.15, 0.15, 0.15)
    wheel_y_front = 0.32
    wheel_z_front = 1.6
    wheel_x_front_offset = 0.85

    for side in [1, -1]:
        glBegin(GL_LINES)
        glVertex3f(0.22*side, 0.45, 1.2)
        glVertex3f(wheel_x_front_offset*side,
                   wheel_y_front + 0.05, wheel_z_front)

        glVertex3f(0.10*side, 0.38, 1.75)
        glVertex3f(wheel_x_front_offset*side,
                   wheel_y_front + 0.05, wheel_z_front)

        glVertex3f(0.22*side, 0.15, 1.2)
        glVertex3f(wheel_x_front_offset*side,
                   wheel_y_front - 0.05, wheel_z_front)

        glVertex3f(0.10*side, 0.15, 1.75)
        glVertex3f(wheel_x_front_offset*side,
                   wheel_y_front - 0.05, wheel_z_front)
        glEnd()

        glPushMatrix()
        glTranslatef(wheel_x_front_offset * side, wheel_y_front, wheel_z_front)
        if side == -1:
            glScalef(-1, 1, 1)

        hw, hh, hd = 0.05, 0.1, 0.1
        glBegin(GL_QUADS)
        glNormal3f(1, 0, 0)
        glVertex3f(hw, hh, -hd)
        glVertex3f(hw, -hh, -hd)
        glVertex3f(hw, -hh, hd)
        glVertex3f(hw, hh, hd)
        glNormal3f(-1, 0, 0)
        glVertex3f(-hw, hh, hd)
        glVertex3f(-hw, -hh, hd)
        glVertex3f(-hw, -hh, -hd)
        glVertex3f(-hw, hh, -hd)
        glNormal3f(0, 1, 0)
        glVertex3f(-hw, hh, -hd)
        glVertex3f(-hw, hh, hd)
        glVertex3f(hw, hh, hd)
        glVertex3f(hw, hh, -hd)
        glNormal3f(0, -1, 0)
        glVertex3f(hw, -hh, hd)
        glVertex3f(hw, -hh, -hd)
        glVertex3f(-hw, -hh, -hd)
        glVertex3f(-hw, -hh, hd)
        glNormal3f(0, 0, 1)
        glVertex3f(hw, hh, hd)
        glVertex3f(hw, -hh, hd)
        glVertex3f(-hw, -hh, hd)
        glVertex3f(-hw, hh, hd)
        glNormal3f(0, 0, -1)
        glVertex3f(hw, -hh, -hd)
        glVertex3f(hw, hh, -hd)
        glVertex3f(-hw, hh, -hd)
        glVertex3f(-hw, -hh, -hd)
        glEnd()
        glPopMatrix()

    wheel_y_rear = 0.42
    wheel_z_rear = -1.2
    wheel_x_rear_offset = 0.95

    for side in [1, -1]:
        glBegin(GL_LINES)
        glVertex3f(0.20*side, 0.40, -0.5)
        glVertex3f(wheel_x_rear_offset*side, wheel_y_rear + 0.05, wheel_z_rear)

        glVertex3f(0.20*side, 0.40, -0.9)
        glVertex3f(wheel_x_rear_offset*side, wheel_y_rear + 0.05, wheel_z_rear)

        glVertex3f(0.20*side, 0.15, -0.5)
        glVertex3f(wheel_x_rear_offset*side, wheel_y_rear - 0.05, wheel_z_rear)

        glVertex3f(0.20*side, 0.15, -0.9)
        glVertex3f(wheel_x_rear_offset*side, wheel_y_rear - 0.05, wheel_z_rear)
        glEnd()

        glPushMatrix()
        glTranslatef(wheel_x_rear_offset * side, wheel_y_rear, wheel_z_rear)
        if side == -1:
            glScalef(-1, 1, 1)

        hw, hh, hd = 0.05, 0.1, 0.1
        glBegin(GL_QUADS)
        glNormal3f(1, 0, 0)
        glVertex3f(hw, hh, -hd)
        glVertex3f(hw, -hh, -hd)
        glVertex3f(hw, -hh, hd)
        glVertex3f(hw, hh, hd)
        glNormal3f(-1, 0, 0)
        glVertex3f(-hw, hh, hd)
        glVertex3f(-hw, -hh, hd)
        glVertex3f(-hw, -hh, -hd)
        glVertex3f(-hw, hh, -hd)
        glNormal3f(0, 1, 0)
        glVertex3f(-hw, hh, -hd)
        glVertex3f(-hw, hh, hd)
        glVertex3f(hw, hh, hd)
        glVertex3f(hw, hh, -hd)
        glNormal3f(0, -1, 0)
        glVertex3f(hw, -hh, hd)
        glVertex3f(hw, -hh, -hd)
        glVertex3f(-hw, -hh, -hd)
        glVertex3f(-hw, -hh, hd)
        glNormal3f(0, 0, 1)
        glVertex3f(hw, hh, hd)
        glVertex3f(hw, -hh, hd)
        glVertex3f(-hw, -hh, hd)
        glVertex3f(-hw, hh, hd)
        glNormal3f(0, 0, -1)
        glVertex3f(hw, -hh, -hd)
        glVertex3f(hw, hh, -hd)
        glVertex3f(-hw, hh, -hd)
        glVertex3f(-hw, -hh, -hd)
        glEnd()
        glPopMatrix()
    glLineWidth(1)

# Texto e partículas


def draw_digit_segment(x, y, size, digit):
    th = size * 0.15
    s = size
    segments = {
        0: [1, 1, 1, 1, 1, 1, 0],
        1: [0, 1, 1, 0, 0, 0, 0],
        2: [1, 1, 0, 1, 1, 0, 1],
        3: [1, 1, 1, 1, 0, 0, 1],
        4: [0, 1, 1, 0, 0, 1, 1],
        5: [1, 0, 1, 1, 0, 1, 1],
        6: [1, 0, 1, 1, 1, 1, 1],
        7: [1, 1, 1, 0, 0, 0, 0],
        8: [1, 1, 1, 1, 1, 1, 1],
        9: [1, 1, 1, 1, 0, 1, 1]
    }
    act = segments.get(int(digit), [0] * 7)

    glBegin(GL_QUADS)
    if act[0]:
        glVertex3f(x, y + s, 0)
        glVertex3f(x + s, y + s, 0)
        glVertex3f(x + s, y + s - th, 0)
        glVertex3f(x, y + s - th, 0)
    if act[1]:
        glVertex3f(x + s - th, y + s, 0)
        glVertex3f(x + s, y + s, 0)
        glVertex3f(x + s, y + s / 2, 0)
        glVertex3f(x + s - th, y + s / 2, 0)
    if act[2]:
        glVertex3f(x + s - th, y + s / 2, 0)
        glVertex3f(x + s, y + s / 2, 0)
        glVertex3f(x + s, y, 0)
        glVertex3f(x + s - th, y, 0)
    if act[3]:
        glVertex3f(x, y + th, 0)
        glVertex3f(x + s, y + th, 0)
        glVertex3f(x + s, y, 0)
        glVertex3f(x, y, 0)
    if act[4]:
        glVertex3f(x, y + s / 2, 0)
        glVertex3f(x + th, y + s / 2, 0)
        glVertex3f(x + th, y, 0)
        glVertex3f(x, y, 0)
    if act[5]:
        glVertex3f(x, y + s, 0)
        glVertex3f(x + th, y + s, 0)
        glVertex3f(x + th, y + s / 2, 0)
        glVertex3f(x, y + s / 2, 0)
    if act[6]:
        glVertex3f(x, y + s / 2 + th / 2, 0)
        glVertex3f(x + s, y + s / 2 + th / 2, 0)
        glVertex3f(x + s, y + s / 2 - th / 2, 0)
        glVertex3f(x, y + s / 2 - th / 2, 0)
    glEnd()


def draw_controls_panel(w, h):
    panel_x_start = 20
    panel_y_start = 20
    panel_width = 450
    panel_height = 300
    x2 = panel_x_start + panel_width
    y2 = panel_y_start + panel_height

    glBegin(GL_QUADS)
    glColor4f(0.0, 0.0, 0.6, 0.7)
    glVertex2f(panel_x_start, panel_y_start)
    glVertex2f(x2, panel_y_start)
    glVertex2f(x2, y2)
    glVertex2f(panel_x_start, y2)
    glEnd()

    glLineWidth(3)
    glBegin(GL_LINE_LOOP)
    glColor3f(0.3, 0.3, 1.0)
    glVertex2f(panel_x_start, panel_y_start)
    glVertex2f(x2, panel_y_start)
    glVertex2f(x2, y2)
    glVertex2f(panel_x_start, y2)
    glEnd()

    glColor3f(1, 1, 1)
    draw_text_pygame(40, y2 - 50, "COMANDOS:", 35, (255, 255, 0))
    draw_text_pygame(40, y2 - 100, "Direção: Setas", 26)
    draw_text_pygame(40, y2 - 140, "Câmera: C", 26)
    draw_text_pygame(40, y2 - 180, "FLAPS: K", 26)

    col_right_x = 260
    draw_text_pygame(col_right_x, y2 - 100, "PULO: L", 26, (100, 255, 100))
    draw_text_pygame(col_right_x, y2 - 140, "ESPECIAL: X", 26, (255, 150, 255))
    draw_text_pygame(40, y2 - 230, "NITRO MANUAL: ESPAÇO", 24, (255, 100, 100))
    draw_text_pygame(40, y2 - 270, "PILOTO AUTO: P", 24, (0, 255, 255))


def draw_hud_primitives(w, h):
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glMatrixMode(GL_PROJECTION)
    glPushMatrix()
    glLoadIdentity()
    gluOrtho2D(0, w, 0, h)
    glMatrixMode(GL_MODELVIEW)
    glPushMatrix()
    glLoadIdentity()

    draw_controls_panel(w, h)

    speed_kmh = int(speed * 330)
    digits = [int(d) for d in str(speed_kmh).zfill(3)]

    glColor3f(1.0, 1.0, 1.0)
    draw_digit_segment(w - 170, 50, 45, digits[0])
    draw_digit_segment(w - 115, 50, 45, digits[1])
    draw_digit_segment(w - 60, 50, 45, digits[2])

    fill = 220 * speed
    glColor3f(0.2, 0.2, 0.2)
    glBegin(GL_QUADS)
    glVertex2f(w - 240, 30)
    glVertex2f(w - 20, 30)
    glVertex2f(w - 20, 40)
    glVertex2f(w - 240, 40)
    glEnd()

    glColor3f(0.0, 1.0, 0.0)
    glBegin(GL_QUADS)
    glVertex2f(w - 240, 30)
    glVertex2f(w - 240 + fill, 30)
    glVertex2f(w - 240 + fill, 40)
    glVertex2f(w - 240, 40)
    glEnd()

    if drs_active:
        glColor3f(0.0, 1.0, 0.0)
    else:
        glColor3f(0.5, 0.0, 0.0)

    glBegin(GL_QUADS)
    glVertex2f(w - 70, 130)
    glVertex2f(w - 20, 130)
    glVertex2f(w - 20, 170)
    glVertex2f(w - 70, 170)
    glEnd()

    if autopilot_active:
        glColor3f(0.0, 1.0, 1.0)
        glBegin(GL_QUADS)
        glVertex2f(w - 130, 130)
        glVertex2f(w - 80, 130)
        glVertex2f(w - 80, 170)
        glVertex2f(w - 130, 170)
        glEnd()

    glPopMatrix()
    glMatrixMode(GL_PROJECTION)
    glPopMatrix()
    glMatrixMode(GL_MODELVIEW)
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)


def update_particles(dt):
    global fire_particles
    for p in fire_particles:
        p['life'] -= dt * 2.5
        p['z'] += speed * 25.0 * dt
        p['y'] += random.uniform(0, 1) * dt
        p['size'] -= dt * 0.1
    fire_particles = [p for p in fire_particles if p['life'] > 0]


def draw_fire_particles():
    glDisable(GL_LIGHTING)
    glEnable(GL_BLEND)
    glBlendFunc(GL_SRC_ALPHA, GL_ONE)

    for p in fire_particles:
        life_ratio = p['life']
        if life_ratio > 0.7:
            glColor4f(1.0, 1.0, 0.5, life_ratio)
        elif life_ratio > 0.4:
            glColor4f(1.0, 0.5, 0.0, life_ratio)
        else:
            glColor4f(0.5, 0.0, 0.0, life_ratio)

        size = max(0.01, p['size'])
        glPushMatrix()
        glTranslatef(p['x'], p['y'], p['z'])
        glRotatef(p['life'] * 300, 1, 1, 1)

        glBegin(GL_QUADS)
        glVertex3f(-size, -size, 0)
        glVertex3f(size, -size, 0)
        glVertex3f(size, size, 0)
        glVertex3f(-size, size, 0)

        glVertex3f(0, -size, -size)
        glVertex3f(0, -size, size)
        glVertex3f(0, size, size)
        glVertex3f(0, size, -size)
        glEnd()
        glPopMatrix()

    glBlendFunc(GL_SRC_ALPHA, GL_ONE_MINUS_SRC_ALPHA)
    glEnable(GL_LIGHTING)


def draw_text_pygame(x, y, text, font_size=20, color=(255, 255, 255)):
    if not pygame.font.get_init():
        pygame.font.init()

    font = pygame.font.SysFont("Arial", font_size, bold=True)
    text_surface = font.render(text, True, color).convert_alpha()
    text_data = pygame.image.tostring(text_surface, "RGBA", True)
    w, h = text_surface.get_size()

    tex_id = glGenTextures(1)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MAG_FILTER, GL_LINEAR)
    glTexParameteri(GL_TEXTURE_2D, GL_TEXTURE_MIN_FILTER, GL_LINEAR)
    glTexImage2D(GL_TEXTURE_2D, 0, GL_RGBA, w, h, 0,
                 GL_RGBA, GL_UNSIGNED_BYTE, text_data)

    glEnable(GL_TEXTURE_2D)
    glBindTexture(GL_TEXTURE_2D, tex_id)
    glColor4f(1, 1, 1, 1)

    glBegin(GL_QUADS)
    glTexCoord2f(0, 0)
    glVertex2f(x, y)
    glTexCoord2f(1, 0)
    glVertex2f(x + w, y)
    glTexCoord2f(1, 1)
    glVertex2f(x + w, y + h)
    glTexCoord2f(0, 1)
    glVertex2f(x, y + h)
    glEnd()

    glDisable(GL_TEXTURE_2D)
    glDeleteTextures([tex_id])

# Pista


def draw_cube():
    glBegin(GL_QUADS)
    glNormal3f(0, 0, 1)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(-0.5, 0.5, 0.5)
    glVertex3f(-0.5, -0.5, 0.5)
    glVertex3f(0.5, -0.5, 0.5)
    glNormal3f(0, 0, -1)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(-0.5, 0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glNormal3f(0, 1, 0)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glVertex3f(-0.5, 0.5, -0.5)
    glVertex3f(-0.5, 0.5, 0.5)
    glNormal3f(0, -1, 0)
    glVertex3f(0.5, -0.5, 0.5)
    glVertex3f(-0.5, -0.5, 0.5)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(0.5, -0.5, -0.5)
    glNormal3f(1, 0, 0)
    glVertex3f(0.5, 0.5, 0.5)
    glVertex3f(0.5, -0.5, 0.5)
    glVertex3f(0.5, -0.5, -0.5)
    glVertex3f(0.5, 0.5, -0.5)
    glNormal3f(-1, 0, 0)
    glVertex3f(-0.5, 0.5, 0.5)
    glVertex3f(-0.5, 0.5, -0.5)
    glVertex3f(-0.5, -0.5, -0.5)
    glVertex3f(-0.5, -0.5, 0.5)
    glEnd()


def draw_cylinder(base, top, height, slices=12):
    quad = gluNewQuadric()
    gluQuadricNormals(quad, GLU_SMOOTH)
    gluCylinder(quad, base, top, height, slices, 1)
    gluDeleteQuadric(quad)


def draw_cloud_primitive(x, y, z):
    glPushMatrix()
    glTranslatef(x, y, z)
    glColor3f(1.0, 1.0, 1.0)

    glPushMatrix()
    glScalef(12, 4, 6)
    draw_cube()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(3, 2.5, 1)
    glScalef(8, 4, 5)
    draw_cube()
    glPopMatrix()

    glPushMatrix()
    glTranslatef(-5, 1, -1)
    glScalef(7, 3, 5)
    draw_cube()
    glPopMatrix()

    glPopMatrix()


def draw_tree_primitive():
    glColor3f(0.4, 0.2, 0.1)
    glPushMatrix()
    glRotatef(-90, 1, 0, 0)
    draw_cylinder(0.4, 0.4, 1.5, 8)
    glPopMatrix()

    glColor3f(0.1, 0.6, 0.1)
    glPushMatrix()
    glTranslatef(0, 1.2, 0)
    glRotatef(-90, 1, 0, 0)
    draw_cylinder(2.5, 0.0, 4.0, 8)
    glPopMatrix()


def draw_skybox_primitive():
    glDisable(GL_LIGHTING)
    glDisable(GL_DEPTH_TEST)
    glBegin(GL_QUADS)
    glColor3f(0.2, 0.4, 0.8)
    glVertex3f(-400, 200, -400)
    glVertex3f(400, 200, -400)
    glColor3f(0.5, 0.7, 1.0)
    glVertex3f(400, -50, -400)
    glVertex3f(-400, -50, -400)
    glEnd()
    glEnable(GL_DEPTH_TEST)
    glEnable(GL_LIGHTING)


def draw_track_primitives(track_offset):
    segment_len = 10.0
    num_segments = 50
    shift = track_offset % segment_len
    base_idx = int(track_offset // segment_len)

    glColor3f(0.2, 0.6, 0.2)
    glBegin(GL_QUADS)
    glNormal3f(0, 1, 0)
    glVertex3f(-500, -0.5, 50)
    glVertex3f(500, -0.5, 50)
    glVertex3f(500, -0.5, -600)
    glVertex3f(-500, -0.5, -600)
    glEnd()

    for i in range(num_segments):
        idx = base_idx + i
        z_start = 20 - (i * segment_len) + shift
        z_end = z_start - segment_len

        if idx % 2 == 0:
            c_asp, c_curb, c_wall = (
                0.3, 0.3, 0.35), (0.9, 0.1, 0.1), (0.7, 0.7, 0.7)
        else:
            c_asp, c_curb, c_wall = (
                0.25, 0.25, 0.3), (1.0, 1.0, 1.0), (0.6, 0.6, 0.6)

        glColor3fv(c_asp)
        glBegin(GL_QUADS)
        glNormal3f(0, 1, 0)
        glVertex3f(-6, 0, z_start)
        glVertex3f(6, 0, z_start)
        glVertex3f(6, 0, z_end)
        glVertex3f(-6, 0, z_end)
        glEnd()

        glColor3fv(c_curb)
        glBegin(GL_QUADS)
        glVertex3f(-7, 0.02, z_start)
        glVertex3f(-6, 0.02, z_start)
        glVertex3f(-6, 0.02, z_end)
        glVertex3f(-7, 0.02, z_end)
        glEnd()

        glBegin(GL_QUADS)
        glVertex3f(6, 0.02, z_start)
        glVertex3f(7, 0.02, z_start)
        glVertex3f(7, 0.02, z_end)
        glVertex3f(6, 0.02, z_end)
        glEnd()

        glColor3fv(c_wall)
        glBegin(GL_QUADS)
        glNormal3f(1, 0, 0)
        glVertex3f(-9, 0, z_start)
        glVertex3f(-9, 1.5, z_start)
        glVertex3f(-9, 1.5, z_end)
        glVertex3f(-9, 0, z_end)
        glEnd()

        glBegin(GL_QUADS)
        glNormal3f(-1, 0, 0)
        glVertex3f(9, 0, z_start)
        glVertex3f(9, 1.5, z_start)
        glVertex3f(9, 1.5, z_end)
        glVertex3f(9, 0, z_end)
        glEnd()

        if idx % 4 == 0:
            glPushMatrix()
            glTranslatef(-18, 0, (z_start + z_end) / 2)
            draw_tree_primitive()
            glPopMatrix()

            glPushMatrix()
            glTranslatef(18, 0, (z_start + z_end) / 2)
            draw_tree_primitive()
            glPopMatrix()

# Função principal


def main():
    global car_x_position, car_y_position, track_offset, wheel_rotation, cam_angle, cam_zoom, camera_mode
    global car_roll_angle, car_pitch_angle, speed, drs_angle, drs_active, steer_visual, WIDTH, HEIGHT
    global fire_particles, autopilot_active, autopilot_timer, is_jumping, jump_velocity
    global GRAVITY, JUMP_STRENGTH, is_looping, loop_progress, LOOP_RATE

    # Som do mixer
    pygame.mixer.init(frequency=44100, size=-16, channels=2, buffer=2048)
    pygame.init()

    if not pygame.font.get_init():
        pygame.font.init()

    engine_channel = None
    try:
        engine_sound = pygame.mixer.Sound(AUDIO_PATH)
        engine_channel = engine_sound.play(-1)
        engine_channel.set_volume(0.0)
    except Exception as e:
        print(
            f"ERRO DE AUDIO: Não foi possível carregar {AUDIO_PATH}. Erro: {e}")

    screen = pygame.display.set_mode(
        (WIDTH, HEIGHT), DOUBLEBUF | OPENGL | RESIZABLE)
    pygame.display.set_caption(
        "F1 McLaren MP4/6 - 1991 (Shell & Marlboro Edition)")

    init_gl()
    clock = pygame.time.Clock()
    running = True

    while running:
        dt = clock.tick(60) / 1000.0

        for event in pygame.event.get():
            if event.type == QUIT:
                running = False
            elif event.type == VIDEORESIZE:
                WIDTH, HEIGHT = event.w, event.h
                resize(WIDTH, HEIGHT)
            elif event.type == KEYDOWN:
                if event.key == K_ESCAPE:
                    running = False
                if event.key == K_c:
                    camera_mode = (camera_mode + 1) % 2
                if event.key == K_k:
                    drs_active = not drs_active
                if event.key == K_p:
                    autopilot_active = not autopilot_active
                    autopilot_timer = 0.0
                if event.key == K_l and not is_jumping and not is_looping:
                    is_jumping = True
                    jump_velocity = JUMP_STRENGTH
                if event.key == K_x and not is_looping and not is_jumping:
                    if speed > 0.3:
                        is_looping = True
                        loop_progress = 0.0
                    else:
                        print("Acelere mais para fazer o Loop!")

        keys = pygame.key.get_pressed()
        max_speed_limit = 1.0

        if autopilot_active:
            autopilot_timer += dt
            cycle_time = autopilot_timer % 6.0
            if cycle_time > 4.0:
                max_speed_limit = 1.8
                speed += 0.02
                for _ in range(5):
                    fire_particles.append(
                        {'x': car_x_position + random.uniform(-0.1, 0.1), 'y': 0.5, 'z': 2.0, 'life': 1.0, 'size': 0.3})
            else:
                max_speed_limit = 0.8
                speed += 0.01
        else:
            if keys[K_SPACE]:
                speed += 0.02
                max_speed_limit = 1.8
                for _ in range(5):
                    fire_particles.append(
                        {'x': car_x_position + random.uniform(-0.1, 0.1), 'y': 0.5, 'z': 2.0, 'life': 1.0, 'size': 0.3})
            else:
                if keys[K_UP]:
                    speed += 0.01
                elif keys[K_DOWN]:
                    speed -= 0.02
                else:
                    speed -= 0.005
                max_speed_limit = 1.3 if drs_active else 1.0

        speed = max(0.0, min(speed, max_speed_limit))

        if engine_channel:
            target_volume = min(1.0, speed / 1.5)
            if speed < 0.02:
                target_volume = 0.0
            engine_channel.set_volume(target_volume)

        if is_jumping:
            jump_velocity += GRAVITY * dt
            car_y_position += jump_velocity * dt

        if car_y_position <= 0.0:
            car_y_position = 0.0
            is_jumping = False
            jump_velocity = 0.0

        if is_looping:
            loop_progress += LOOP_RATE * dt
            loop_radius = 12.0
            rad = math.radians(loop_progress)
            car_y_position = loop_radius * (1.0 - math.cos(rad))
            car_pitch_angle = -loop_progress

        if loop_progress >= 360.0:
            is_looping = False
            loop_progress = 0.0
            car_pitch_angle = 0.0
            car_y_position = 0.0

        update_particles(dt)
        steering = 0.0

        if speed > 0.05 and not is_looping:
            if keys[K_LEFT]:
                steering = 1.0
            if keys[K_RIGHT]:
                steering = -1.0
            car_x_position += steering * 9.0 * speed * dt
            car_x_position = max(-8.5, min(8.5, car_x_position))

        if not is_looping:
            steer_visual += (steering * 20.0 - steer_visual) * 0.1
            car_roll_angle += (-steering * 3.0 - car_roll_angle) * 0.1
        else:
            car_roll_angle += (0.0 - car_roll_angle) * 0.1

        track_offset += speed * 70.0 * dt
        wheel_rotation += speed * 1200.0 * dt

        drs_target = 70.0 if drs_active else 0.0
        drs_angle += (drs_target - drs_angle) * 0.1

        if camera_mode == 1:
            if keys[K_a]:
                cam_angle -= 2
            if keys[K_d]:
                cam_angle += 2
            if keys[K_w]:
                cam_zoom = max(5.0, cam_zoom - 0.2)
            if keys[K_s]:
                cam_zoom = min(40.0, cam_zoom + 0.2)

        glClear(GL_COLOR_BUFFER_BIT | GL_DEPTH_BUFFER_BIT)
        glLoadIdentity()

        if camera_mode == 0:
            gluLookAt(car_x_position * 0.3, 4.5 + car_y_position * 0.5,
                      12.0, car_x_position, car_y_position, -10.0, 0, 1, 0)
        elif camera_mode == 1:
            cx = cam_zoom * math.sin(math.radians(cam_angle))
            cz = cam_zoom * math.cos(math.radians(cam_angle))
            gluLookAt(cx, cam_height_orbital, cz, 0,
                      0.5 + car_y_position, 0, 0, 1, 0)

        glPushMatrix()
        glTranslatef(car_x_position, 0, 0)
        draw_skybox_primitive()
        draw_cloud_primitive(-100, 120, -150)
        draw_cloud_primitive(0, 130, -200)
        draw_cloud_primitive(120, 115, -120)
        glPopMatrix()

        glPushMatrix()
        draw_track_primitives(track_offset)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(car_x_position, car_y_position, 0)
        glRotatef(180, 0, 1, 0)
        glRotatef(car_pitch_angle, 1, 0, 0)
        glRotatef(car_roll_angle, 0, 0, 1)

        draw_mp4_6_body()

        fw, rw = 0.25, 0.45
        glPushMatrix()
        glTranslatef(1.05, 0.42, -1.2)
        glRotatef(wheel_rotation, 1, 0, 0)
        draw_wheel_solid_filled_both_sides(0, 0, 0, 0.42, rw)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(-1.05, 0.42, -1.2)
        glRotatef(wheel_rotation, 1, 0, 0)
        draw_wheel_solid_filled_both_sides(0, 0, 0, 0.42, rw)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(0.9, 0.32, 1.6)
        glRotatef(steer_visual, 0, 1, 0)
        glRotatef(wheel_rotation, 1, 0, 0)
        draw_wheel_solid_filled_both_sides(0, 0, 0, 0.32, fw)
        glPopMatrix()

        glPushMatrix()
        glTranslatef(-0.9, 0.32, 1.6)
        glRotatef(steer_visual, 0, 1, 0)
        glRotatef(wheel_rotation, 1, 0, 0)
        draw_wheel_solid_filled_both_sides(0, 0, 0, 0.32, fw)
        glPopMatrix()
        glPopMatrix()

        draw_fire_particles()
        draw_hud_primitives(WIDTH, HEIGHT)
        pygame.display.flip()

    if engine_channel:
        engine_channel.stop()
    pygame.quit()


if __name__ == "__main__":
    main()
