import pygame
import random
import os
import sys

# --- INICIALIZAÇÃO ---
pygame.init()
pygame.joystick.init()
pygame.font.init()

# Detectar Joysticks conectados
joysticks = [pygame.joystick.Joystick(x) for x in range(pygame.joystick.get_count())]
for j in joysticks:
    j.init()

# CONFIGURAÇÕES DE TELA
LARGURA_TELA = 1000
ALTURA_TELA = 750
BLOCK_SIZE = 30
PLAY_WIDTH = 300
PLAY_HEIGHT = 600

# GLOBAIS DE SISTEMA
FULLSCREEN = False
VELOCIDADE_NIVEL = 3  # 1 a 5 estrelas
FALL_SPEEDS = {1: 0.45, 2: 0.35, 3: 0.25, 4: 0.15, 5: 0.08}
SCORE_FILE = "recordes_tetris.txt"

# CORES
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
CINZA = (30, 30, 30)
CINZA_CLARO = (128, 128, 128)
VERMELHO = (255, 0, 0)
VERDE_NEON = (57, 255, 20)
AZUL_NEON = (0, 255, 255)
AMARELO = (255, 255, 0)
ROSA_CHOQUE = (255, 20, 147)

# FORMAS (S, Z, I, O, J, L, T)
FORMAS = [
    [['.....', '.....', '..00.', '.00..', '.....'], ['.....', '..0..', '..00.', '...0.', '.....']], # S
    [['.....', '.....', '.00..', '..00.', '.....'], ['.....', '..0..', '.00..', '.0...', '.....']], # Z
    [['..0..', '..0..', '..0..', '..0..', '.....'], ['.....', '0000.', '.....', '.....', '.....']], # I
    [['.....', '.....', '.00..', '.00..', '.....']], # O
    [['.....', '.0...', '.000.', '.....', '.....'], ['.....', '..00.', '..0..', '..0..', '.....'], ['.....', '.....', '.000.', '...0.', '.....'], ['.....', '..0..', '..0..', '.00..', '.....']], # J
    [['.....', '...0.', '.000.', '.....', '.....'], ['.....', '..0..', '..0..', '..00.', '.....'], ['.....', '.....', '.000.', '.0...', '.....'], ['.....', '..0..', '..0..', '.00..', '.....']], # L
    [['.....', '..0..', '.000.', '.....', '.....'], ['.....', '..0..', '..00.', '..0..', '.....'], ['.....', '.....', '.000.', '..0..', '.....'], ['.....', '..0..', '.00..', '..0..', '.....']]  # T
]
CORES_FORMAS = [VERDE_NEON, VERMELHO, AZUL_NEON, AMARELO, (255, 165, 0), (0, 0, 255), (128, 0, 128)]

# --- CLASSES ---

class Peca:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = CORES_FORMAS[FORMAS.index(shape)]
        self.rotation = 0

class TetrisGame:
    def __init__(self, offset_x, player_id):
        self.offset_x = offset_x
        self.offset_y = 80
        self.grid = [[(0,0,0) for _ in range(10)] for _ in range(20)]
        self.current_piece = self.get_shape()
        self.next_piece = self.get_shape()
        self.change_piece = False
        self.score = 0
        self.player_id = player_id
        self.is_flashing = False

    def get_shape(self):
        return Peca(5, 0, random.choice(FORMAS))

    def create_grid(self, locked_pos={}):
        grid = [[(0,0,0) for _ in range(10)] for _ in range(20)]
        for (j, i), color in locked_pos.items():
            if i >= 0: grid[i][j] = color
        return grid

    def valid_space(self, shape, grid):
        accepted_pos = [[(j, i) for j in range(10) if grid[i][j] == (0,0,0)] for i in range(20)]
        accepted_pos = [j for sub in accepted_pos for j in sub]
        formatted = self.convert_shape_format(shape)
        for pos in formatted:
            if pos not in accepted_pos:
                if pos[1] > -1: return False
        return True

    def convert_shape_format(self, shape):
        positions = []
        format = shape.shape[shape.rotation % len(shape.shape)]
        for i, line in enumerate(format):
            for j, column in enumerate(list(line)):
                if column == '0':
                    positions.append((shape.x + j - 2, shape.y + i - 4))
        return positions

    def clear_rows(self, grid, locked):
        inc = 0
        for i in range(len(grid)-1, -1, -1):
            if (0,0,0) not in grid[i]:
                inc += 1
                for j in range(len(grid[i])):
                    if (j, i) in locked: del locked[(j, i)]
        if inc > 0:
            for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
                x, y = key
                if y < i:
                    locked[(x, y + inc)] = locked.pop(key)
        self.score += inc * 10
        return inc

    def draw_window(self, surface, grid):
        pygame.draw.rect(surface, (10,10,10), (self.offset_x, self.offset_y, PLAY_WIDTH, PLAY_HEIGHT))
        for i in range(len(grid)):
            for j in range(len(grid[i])):
                if grid[i][j] != (0,0,0):
                    pygame.draw.rect(surface, grid[i][j], (self.offset_x + j*BLOCK_SIZE, self.offset_y + i*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
        
        # Alerta de perigo (Pisca borda se chegar no topo)
        color_border = BRANCO
        self.is_flashing = any(grid[i][j] != (0,0,0) for i in range(3) for j in range(10))
        if self.is_flashing and (pygame.time.get_ticks() // 250) % 2 == 0:
            color_border = VERMELHO
        pygame.draw.rect(surface, color_border, (self.offset_x, self.offset_y, PLAY_WIDTH, PLAY_HEIGHT), 3)

# --- SISTEMA DE RECORDE ---

def get_max_score():
    if not os.path.exists(SCORE_FILE): return "0"
    with open(SCORE_FILE, 'r') as f:
        lines = f.readlines()
        return lines[0].strip() if lines else "0"

def update_score(nscore):
    score = get_max_score()
    with open(SCORE_FILE, 'w') as f:
        if int(score) > nscore: f.write(str(score))
        else: f.write(str(nscore))

# --- SISTEMA DE TELAS E ARTES ---

def draw_text(win, text, size, color, x, y, center=True):
    font = pygame.font.SysFont("consolas", size, bold=True)
    label = font.render(text, 1, color)
    if center: win.blit(label, (x - label.get_width()//2, y))
    else: win.blit(label, (x, y))

def menu_pausa(win):
    pausado = True
    while pausado:
        pygame.draw.rect(win, PRETO, (300, 250, 400, 200))
        pygame.draw.rect(win, AZUL_NEON, (300, 250, 400, 200), 2)
        draw_text(win, "PAUSADO", 50, AMARELO, 500, 280)
        draw_text(win, "Pressione P ou 'START' para Voltar", 20, BRANCO, 500, 360)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN and event.key == pygame.K_p: pausado = False
            if event.type == pygame.JOYBUTTONDOWN: pausado = False

def tela_abertura(win):
    intro_art = [
        "__  _  _  ____  _    _     __     _    ____ ",
        "|  || || ||__  || |  | |   /  \   | |  |  _ \ ",
        "|  || || |  / / | |  | |  / /\ \  | |  | |_) |",
        "|__||_||_| /_/  |_|  |_| /_/  \_\ |_|  |____/ ",
        "        4 W A L L L A B   G A M E S             "
    ]
    win.fill(PRETO)
    for i, line in enumerate(intro_art):
        draw_text(win, line, 20, VERDE_NEON, LARGURA_TELA//2, 200 + i*25)
    pygame.display.update()
    pygame.time.delay(2000)

    win.fill(PRETO)
    draw_text(win, "Jogo pra meu Amoooo", 50, ROSA_CHOQUE, LARGURA_TELA//2, 300)
    draw_text(win, "APRESENTA", 20, BRANCO, LARGURA_TELA//2, 380)
    pygame.display.update()
    pygame.time.delay(1500)

    esperando = True
    while esperando:
        win.fill(PRETO)
        draw_text(win, "TETRIS ULTRA BATTLE", 70, AZUL_NEON, LARGURA_TELA//2, 250)
        if (pygame.time.get_ticks() // 500) % 2 == 0:
            draw_text(win, "PRESSIONE QUALQUER BOTAO", 30, AMARELO, LARGURA_TELA//2, 500)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type in [pygame.KEYDOWN, pygame.JOYBUTTONDOWN]: esperando = False

def menu_controles(win):
    run = True
    while run:
        win.fill(PRETO)
        draw_text(win, "CONFIGURAR CONTROLES", 50, AZUL_NEON, LARGURA_TELA//2, 80)
        
        # Player 1
        pygame.draw.rect(win, CINZA, (100, 180, 350, 350), 2)
        draw_text(win, "PLAYER 1", 30, AZUL_NEON, 275, 200)
        draw_text(win, "TECLADO: WASD", 20, BRANCO, 275, 250)
        draw_text(win, "Girar: W", 18, CINZA_CLARO, 275, 280)
        p1_joy = "Joy: DESCONECTADO"
        if pygame.joystick.get_count() > 0: p1_joy = f"Joy: OK ({pygame.joystick.Joystick(0).get_name()[:10]})"
        draw_text(win, p1_joy, 18, VERDE_NEON, 275, 350)

        # Player 2
        pygame.draw.rect(win, CINZA, (550, 180, 350, 350), 2)
        draw_text(win, "PLAYER 2", 30, ROSA_CHOQUE, 725, 200)
        draw_text(win, "TECLADO: SETAS", 20, BRANCO, 725, 250)
        draw_text(win, "Girar: SETA CIMA", 18, CINZA_CLARO, 725, 280)
        p2_joy = "Joy: DESCONECTADO"
        if pygame.joystick.get_count() > 1: p2_joy = f"Joy: OK ({pygame.joystick.Joystick(1).get_name()[:10]})"
        draw_text(win, p2_joy, 18, VERDE_NEON, 725, 350)

        draw_text(win, "Pressione ESPAÇO ou BOTAO 'A' para voltar", 25, AMARELO, LARGURA_TELA//2, 600)
        pygame.display.update()
        for event in pygame.event.get():
            if (event.type == pygame.KEYDOWN and event.key == pygame.K_SPACE) or event.type == pygame.JOYBUTTONDOWN:
                run = False
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()

def game_loop(win, mode):
    global VELOCIDADE_NIVEL
    locked_p1, locked_p2 = {}, {}
    game1 = TetrisGame(50 if mode == 2 else 350, 1)
    game2 = TetrisGame(650, 2) if mode == 2 else None
    
    clock = pygame.time.Clock()
    fall_time = 0
    fall_speed = FALL_SPEEDS[VELOCIDADE_NIVEL]
    run = True

    while run:
        grid_p1 = game1.create_grid(locked_p1)
        grid_p2 = game2.create_grid(locked_p2) if mode == 2 else None
        
        fall_time += clock.get_rawtime()
        clock.tick()

        if fall_time/1000 > fall_speed:
            fall_time = 0
            game1.current_piece.y += 1
            if not game1.valid_space(game1.current_piece, grid_p1):
                game1.current_piece.y -= 1
                game1.change_piece = True
            
            if mode == 2:
                game2.current_piece.y += 1
                if not game2.valid_space(game2.current_piece, grid_p2):
                    game2.current_piece.y -= 1
                    game2.change_piece = True

        for event in pygame.event.get():
            if event.type == pygame.QUIT: run = False
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p: menu_pausa(win)
                # Player 1 (WASD)
                if event.key == pygame.K_a:
                    game1.current_piece.x -= 1
                    if not game1.valid_space(game1.current_piece, grid_p1): game1.current_piece.x += 1
                if event.key == pygame.K_d:
                    game1.current_piece.x += 1
                    if not game1.valid_space(game1.current_piece, grid_p1): game1.current_piece.x -= 1
                if event.key == pygame.K_s:
                    game1.current_piece.y += 1
                    if not game1.valid_space(game1.current_piece, grid_p1): game1.current_piece.y -= 1
                if event.key == pygame.K_w:
                    game1.current_piece.rotation += 1
                    if not game1.valid_space(game1.current_piece, grid_p1): game1.current_piece.rotation -= 1
                
                # Player 2 (Setas)
                if mode == 2:
                    if event.key == pygame.K_LEFT:
                        game2.current_piece.x -= 1
                        if not game2.valid_space(game2.current_piece, grid_p2): game2.current_piece.x += 1
                    if event.key == pygame.K_RIGHT:
                        game2.current_piece.x += 1
                        if not game2.valid_space(game2.current_piece, grid_p2): game2.current_piece.x -= 1
                    if event.key == pygame.K_DOWN:
                        game2.current_piece.y += 1
                        if not game2.valid_space(game2.current_piece, grid_p2): game2.current_piece.y -= 1
                    if event.key == pygame.K_UP:
                        game2.current_piece.rotation += 1
                        if not game2.valid_space(game2.current_piece, grid_p2): game2.current_piece.rotation -= 1

            # JOYSTICK LOGIC
            if event.type == pygame.JOYAXISMOTION:
                target_game = game1 if event.joy == 0 else game2
                target_grid = grid_p1 if event.joy == 0 else grid_p2
                if target_game:
                    if event.axis == 0: # Horizontal
                        if event.value < -0.5: 
                            target_game.current_piece.x -= 1
                            if not target_game.valid_space(target_game.current_piece, target_grid): target_game.current_piece.x += 1
                        elif event.value > 0.5:
                            target_game.current_piece.x += 1
                            if not target_game.valid_space(target_game.current_piece, target_grid): target_game.current_piece.x -= 1
                    if event.axis == 1 and event.value > 0.5: # Baixo
                        target_game.current_piece.y += 1
                        if not target_game.valid_space(target_game.current_piece, target_grid): target_game.current_piece.y -= 1

            if event.type == pygame.JOYBUTTONDOWN:
                target_game = game1 if event.joy == 0 else game2
                target_grid = grid_p1 if event.joy == 0 else grid_p2
                if target_game:
                    target_game.current_piece.rotation += 1
                    if not target_game.valid_space(target_game.current_piece, target_grid): target_game.current_piece.rotation -= 1

        # Lógica de Peças P1
        if game1.change_piece:
            for pos in game1.convert_shape_format(game1.current_piece):
                locked_p1[pos] = game1.current_piece.color
            game1.current_piece = game1.next_piece
            game1.next_piece = game1.get_shape()
            game1.change_piece = False
            game1.clear_rows(grid_p1, locked_p1)
            if not game1.valid_space(game1.current_piece, grid_p1): run = False

        # Lógica de Peças P2
        if mode == 2 and game2.change_piece:
            for pos in game2.convert_shape_format(game2.current_piece):
                locked_p2[pos] = game2.current_piece.color
            game2.current_piece = game2.next_piece
            game2.next_piece = game2.get_shape()
            game2.change_piece = False
            game2.clear_rows(grid_p2, locked_p2)
            if not game2.valid_space(game2.current_piece, grid_p2): run = False

        win.fill(PRETO)
        game1.draw_window(win, grid_p1)
        draw_text(win, f"Score: {game1.score}", 30, BRANCO, game1.offset_x + 150, 30)
        
        if mode == 2:
            game2.draw_window(win, grid_p2)
            draw_text(win, f"Score: {game2.score}", 30, BRANCO, game2.offset_x + 150, 30)
        
        pygame.display.update()
    
    update_score(game1.score)

def main_menu(win):
    global FULLSCREEN, VELOCIDADE_NIVEL
    run = True
    while run:
        win.fill(PRETO)
        draw_text(win, "TETRIS ULTRA BATTLE", 60, AZUL_NEON, LARGURA_TELA//2, 80)
        
        opcoes = [
            "1 - MODO SOLO",
            "2 - MODO VS (MULTIJOGADOR)",
            f"V - VELOCIDADE: {'★' * VELOCIDADE_NIVEL}{'☆' * (5-VELOCIDADE_NIVEL)}",
            "F - TELA CHEIA (ON/OFF)",
            "C - CONFIGURAR CONTROLES",
            "ESC - SAIR"
        ]
        
        for i, texto in enumerate(opcoes):
            cor = AMARELO if texto.startswith("V") else BRANCO
            draw_text(win, texto, 30, cor, LARGURA_TELA//2, 220 + i*60)

        max_s = get_max_score()
        draw_text(win, f"RECORDE ATUAL: {max_s}", 20, VERDE_NEON, LARGURA_TELA//2, 650)
        draw_text(win, "4wallLab Studio - 2026", 15, CINZA_CLARO, LARGURA_TELA//2, 710)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1: game_loop(win, 1)
                if event.key == pygame.K_2: game_loop(win, 2)
                if event.key == pygame.K_c: menu_controles(win)
                if event.key == pygame.K_v:
                    VELOCIDADE_NIVEL = VELOCIDADE_NIVEL + 1 if VELOCIDADE_NIVEL < 5 else 1
                if event.key == pygame.K_f:
                    FULLSCREEN = not FULLSCREEN
                    win = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.FULLSCREEN if FULLSCREEN else 0)
                if event.key == pygame.K_ESCAPE: pygame.quit(); sys.exit()

# EXECUÇÃO
win = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("TETRIS ULTRA BATTLE - 4wallLab")
tela_abertura(win)
main_menu(win)