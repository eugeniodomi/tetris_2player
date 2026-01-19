import pygame
import random
import os
import sys

# --- INICIALIZAÇÃO ---
pygame.init()
pygame.joystick.init()
pygame.font.init()

# Detectar Joysticks
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
VELOCIDADE_NIVEL = 3  
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

# FORMAS
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

    def draw_window(self, surface, grid):
        pygame.draw.rect(surface, (10,10,10), (self.offset_x, self.offset_y, PLAY_WIDTH, PLAY_HEIGHT))
        for i in range(len(grid)):
            for j in range(len(grid[i])):
                if grid[i][j] != (0,0,0):
                    pygame.draw.rect(surface, grid[i][j], (self.offset_x + j*BLOCK_SIZE, self.offset_y + i*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
        
        is_danger = any(grid[i][j] != (0,0,0) for i in range(3) for j in range(10))
        color_border = VERMELHO if is_danger and (pygame.time.get_ticks() // 250) % 2 == 0 else BRANCO
        pygame.draw.rect(surface, color_border, (self.offset_x, self.offset_y, PLAY_WIDTH, PLAY_HEIGHT), 3)

# --- AUXILIARES ---

def draw_text(win, text, size, color, x, y, center=True):
    font = pygame.font.SysFont("consolas", size, bold=True)
    label = font.render(text, 1, color)
    if center: win.blit(label, (x - label.get_width()//2, y))
    else: win.blit(label, (x, y))

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

# --- TELAS ---

def tela_abertura(win):
    win.fill(PRETO)
    draw_text(win, "4WALL LAB GAMES", 40, VERDE_NEON, LARGURA_TELA//2, 300)
    pygame.display.update()
    pygame.time.delay(1500)
    win.fill(PRETO)
    draw_text(win, "Jogo pra meu Amoooo", 50, ROSA_CHOQUE, LARGURA_TELA//2, 300)
    draw_text(win, "APRESENTA", 20, BRANCO, LARGURA_TELA//2, 380)
    pygame.display.update()
    pygame.time.delay(1500)

def menu_controles(win):
    run = True
    while run:
        win.fill(PRETO)
        draw_text(win, "CONTROLES", 50, AZUL_NEON, LARGURA_TELA//2, 100)
        draw_text(win, "P1: WASD | P2: SETAS", 30, BRANCO, LARGURA_TELA//2, 250)
        draw_text(win, "JOYSTICK: ANALOGICO + BOTOES", 30, BRANCO, LARGURA_TELA//2, 320)
        draw_text(win, "ESC / BACKSPACE para Voltar", 20, AMARELO, LARGURA_TELA//2, 600)
        pygame.display.update()
        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]: run = False
            if event.type == pygame.JOYBUTTONDOWN:
                if event.button in [1, 6, 7]: run = False # Botão B ou Select/Start costumam ser 1, 6 ou 7

def game_loop(win, mode):
    global VELOCIDADE_NIVEL
    locked_p1, locked_p2 = {}, {}
    game1 = TetrisGame(50 if mode == 2 else 350, 1)
    game2 = TetrisGame(650, 2) if mode == 2 else None
    clock = pygame.time.Clock()
    fall_time = 0
    run = True

    while run:
        grid_p1 = game1.create_grid(locked_p1)
        grid_p2 = game2.create_grid(locked_p2) if mode == 2 else None
        fall_time += clock.get_rawtime()
        clock.tick()

        if fall_time/1000 > FALL_SPEEDS[VELOCIDADE_NIVEL]:
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
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE: run = False
                # P1
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
                # P2
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

            if event.type == pygame.JOYAXISMOTION:
                g = game1 if event.joy == 0 else game2
                gr = grid_p1 if event.joy == 0 else grid_p2
                if g:
                    if event.axis == 0:
                        if event.value < -0.5:
                            g.current_piece.x -= 1
                            if not g.valid_space(g.current_piece, gr): g.current_piece.x += 1
                        if event.value > 0.5:
                            g.current_piece.x += 1
                            if not g.valid_space(g.current_piece, gr): g.current_piece.x -= 1
                    if event.axis == 1 and event.value > 0.5:
                        g.current_piece.y += 1
                        if not g.valid_space(g.current_piece, gr): g.current_piece.y -= 1
            if event.type == pygame.JOYBUTTONDOWN:
                g = game1 if event.joy == 0 else game2
                gr = grid_p1 if event.joy == 0 else grid_p2
                if g:
                    g.current_piece.rotation += 1
                    if not g.valid_space(g.current_piece, gr): g.current_piece.rotation -= 1

        if game1.change_piece:
            for pos in game1.convert_shape_format(game1.current_piece):
                locked_p1[pos] = game1.current_piece.color
            game1.current_piece = game1.next_piece
            game1.next_piece = game1.get_shape()
            game1.change_piece = False
            game1.clear_rows(grid_p1, locked_p1)
            if not game1.valid_space(game1.current_piece, grid_p1): run = False

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
        if mode == 2: game2.draw_window(win, grid_p2)
        draw_text(win, f"P1: {game1.score}", 30, BRANCO, game1.offset_x + 150, 30)
        pygame.display.update()
    update_score(game1.score)

def main_menu(win):
    global FULLSCREEN, VELOCIDADE_NIVEL
    selected = 0
    run = True
    
    while run:
        win.fill(PRETO)
        draw_text(win, "TETRIS ULTRA BATTLE", 65, AZUL_NEON, LARGURA_TELA//2, 80)
        
        opcoes = [
            "MODO SOLO",
            "MODO VS (MULTIJOGADOR)",
            f"VELOCIDADE: {'★' * VELOCIDADE_NIVEL}{'☆' * (5-VELOCIDADE_NIVEL)}",
            "TELA CHEIA (ON/OFF)",
            "CONFIGURAR CONTROLES",
            "SAIR"
        ]

        for i, texto in enumerate(opcoes):
            cor = AZUL_NEON if i == selected else BRANCO
            prefixo = "> " if i == selected else "  "
            draw_text(win, prefixo + texto, 35, cor, LARGURA_TELA//2, 220 + i*65)

        draw_text(win, f"RECORDE: {get_max_score()}", 20, VERDE_NEON, LARGURA_TELA//2, 650)
        draw_text(win, "4wallLab Studio - 2026", 15, CINZA_CLARO, LARGURA_TELA//2, 710)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT: pygame.quit(); sys.exit()
            
            # --- LÓGICA DE NAVEGAÇÃO ---
            if event.type == pygame.KEYDOWN:
                # Setas e Numpad
                if event.key in [pygame.K_UP, pygame.K_KP8]: selected = (selected - 1) % len(opcoes)
                if event.key in [pygame.K_DOWN, pygame.K_KP2]: selected = (selected + 1) % len(opcoes)
                
                # Números (Teclado e Numpad)
                if event.key in [pygame.K_1, pygame.K_KP1]: game_loop(win, 1)
                if event.key in [pygame.K_2, pygame.K_KP2]: game_loop(win, 2)
                
                # Voltar
                if event.key in [pygame.K_ESCAPE, pygame.K_BACKSPACE]: pygame.quit(); sys.exit()

                # Confirmar Seleção (Enter / Space)
                if event.key in [pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE]:
                    if selected == 0: game_loop(win, 1)
                    if selected == 1: game_loop(win, 2)
                    if selected == 2: VELOCIDADE_NIVEL = (VELOCIDADE_NIVEL % 5) + 1
                    if selected == 3:
                        FULLSCREEN = not FULLSCREEN
                        win = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.FULLSCREEN if FULLSCREEN else 0)
                    if selected == 4: menu_controles(win)
                    if selected == 5: pygame.quit(); sys.exit()

            # --- LÓGICA DE CONTROLE (JOYSTICK) ---
            if event.type == pygame.JOYHATMOTION: # D-Pad
                if event.value[1] == 1: selected = (selected - 1) % len(opcoes)
                if event.value[1] == -1: selected = (selected + 1) % len(opcoes)
            
            if event.type == pygame.JOYAXISMOTION: # Analógico
                if event.axis == 1:
                    if event.value < -0.6: 
                        selected = (selected - 1) % len(opcoes)
                        pygame.time.delay(150) # Delay para não pular muitas opções
                    if event.value > 0.6: 
                        selected = (selected + 1) % len(opcoes)
                        pygame.time.delay(150)

            if event.type == pygame.JOYBUTTONDOWN:
                if event.button == 0: # Botão A (Confirmar)
                    if selected == 0: game_loop(win, 1)
                    if selected == 1: game_loop(win, 2)
                    if selected == 2: VELOCIDADE_NIVEL = (VELOCIDADE_NIVEL % 5) + 1
                    if selected == 3:
                        FULLSCREEN = not FULLSCREEN
                        win = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA), pygame.FULLSCREEN if FULLSCREEN else 0)
                    if selected == 4: menu_controles(win)
                    if selected == 5: pygame.quit(); sys.exit()
                if event.button == 1: # Botão B (Sair/Voltar)
                    pygame.quit(); sys.exit()

# INICIALIZAÇÃO FINAL
win = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("TETRIS ULTRA BATTLE - 4wallLab")
tela_abertura(win)
main_menu(win)