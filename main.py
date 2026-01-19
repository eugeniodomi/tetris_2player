import pygame
import random

# --- CONFIGURAÇÕES GERAIS ---
pygame.init()
LARGURA_TELA = 800
ALTURA_TELA = 700
BLOCK_SIZE = 30
PLAY_WIDTH = 300  # 10 blocos de largura * 30
PLAY_HEIGHT = 600 # 20 blocos de altura * 30

# CORES (Estilo Neon/Guitar Hero)
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
CINZA = (30, 30, 30)
VERMELHO = (255, 0, 0)
VERDE_NEON = (57, 255, 20)
AZUL_NEON = (0, 255, 255)
AMARELO = (255, 255, 0)
ROXO = (128, 0, 128)

# FORMAS (S, Z, I, O, J, L, T)
S = [['.....', '.....', '..00.', '.00..', '.....'], ['.....', '..0..', '..00.', '...0.', '.....']]
Z = [['.....', '.....', '.00..', '..00.', '.....'], ['.....', '..0..', '.00..', '.0...', '.....']]
I = [['..0..', '..0..', '..0..', '..0..', '.....'], ['.....', '0000.', '.....', '.....', '.....']]
O = [['.....', '.....', '.00..', '.00..', '.....']]
J = [['.....', '.0...', '.000.', '.....', '.....'], ['.....', '..00.', '..0..', '..0..', '.....'], ['.....', '.....', '.000.', '...0.', '.....'], ['.....', '..0..', '..0..', '.00..', '.....']]
L = [['.....', '...0.', '.000.', '.....', '.....'], ['.....', '..0..', '..0..', '..00.', '.....'], ['.....', '.....', '.000.', '.0...', '.....'], ['.....', '.00..', '..0..', '..0..', '.....']]
T = [['.....', '..0..', '.000.', '.....', '.....'], ['.....', '..0..', '..00.', '..0..', '.....'], ['.....', '.....', '.000.', '..0..', '.....'], ['.....', '..0..', '.00..', '..0..', '.....']]

FORMAS = [S, Z, I, O, J, L, T]
CORES_FORMAS = [VERDE_NEON, VERMELHO, AZUL_NEON, AMARELO, (255, 165, 0), (0, 0, 255), ROXO]

class Peca:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = CORES_FORMAS[FORMAS.index(shape)]
        self.rotation = 0

class TetrisGame:
    def __init__(self, offset_x):
        self.offset_x = offset_x
        self.offset_y = (ALTURA_TELA - PLAY_HEIGHT) // 2
        self.grid = [[(0,0,0) for _ in range(10)] for _ in range(20)]
        self.current_piece = self.get_shape()
        self.next_piece = self.get_shape()
        self.change_piece = False
        self.score = 0
        self.game_over = False

    def get_shape(self):
        return Peca(5, 0, random.choice(FORMAS))

    def create_grid(self, locked_pos={}):
        grid = [[(0,0,0) for _ in range(10)] for _ in range(20)]
        for i in range(len(grid)):
            for j in range(len(grid[i])):
                if (j, i) in locked_pos:
                    c = locked_pos[(j,i)]
                    grid[i][j] = c
        return grid

    def valid_space(self, shape, grid):
        accepted_pos = [[(j, i) for j in range(10) if grid[i][j] == (0,0,0)] for i in range(20)]
        accepted_pos = [j for sub in accepted_pos for j in sub]
        formatted = self.convert_shape_format(shape)
        for pos in formatted:
            if pos not in accepted_pos:
                if pos[1] > -1:
                    return False
        return True

    def convert_shape_format(self, shape):
        positions = []
        format = shape.shape[shape.rotation % len(shape.shape)]
        for i, line in enumerate(format):
            row = list(line)
            for j, column in enumerate(row):
                if column == '0':
                    positions.append((shape.x + j - 2, shape.y + i - 4))
        for i, pos in enumerate(positions):
            positions[i] = (pos[0], pos[1])
        return positions
    
    def check_lost(self, positions):
        for pos in positions:
            x, y = pos
            if y < 1:
                return True
        return False

    def clear_rows(self, grid, locked):
        inc = 0
        for i in range(len(grid)-1, -1, -1):
            row = grid[i]
            if (0,0,0) not in row:
                inc += 1
                ind = i
                for j in range(len(row)):
                    try:
                        del locked[(j,i)]
                    except:
                        continue
        if inc > 0:
            for key in sorted(list(locked), key=lambda x: x[1])[::-1]:
                x, y = key
                if y < ind:
                    newKey = (x, y + inc)
                    locked[newKey] = locked.pop(key)
            self.score += inc * 10

    def draw_window(self, surface, grid):
        # Desenha Borda
        pygame.draw.rect(surface, BRANCO, (self.offset_x, self.offset_y, PLAY_WIDTH, PLAY_HEIGHT), 2)
        
        # Desenha Grid
        for i in range(len(grid)):
            for j in range(len(grid[i])):
                pygame.draw.rect(surface, grid[i][j], (self.offset_x + j*BLOCK_SIZE, self.offset_y + i*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)

        # Desenha linhas da grade (opcional para estética)
        for i in range(len(grid)):
            pygame.draw.line(surface, CINZA, (self.offset_x, self.offset_y + i*BLOCK_SIZE), (self.offset_x+PLAY_WIDTH, self.offset_y+ i*BLOCK_SIZE))
            for j in range(len(grid[i])):
                pygame.draw.line(surface, CINZA, (self.offset_x + j*BLOCK_SIZE, self.offset_y), (self.offset_x + j*BLOCK_SIZE, self.offset_y + PLAY_HEIGHT))
        
        # Desenha Score
        font = pygame.font.SysFont('comicsans', 30)
        label = font.render(f'Score: {self.score}', 1, BRANCO)
        surface.blit(label, (self.offset_x + 10, self.offset_y - 30))

def draw_text_middle(surface, text, size, color, y_offset=0):
    font = pygame.font.SysFont("comicsans", size, bold=True)
    label = font.render(text, 1, color)
    surface.blit(label, (LARGURA_TELA/2 - label.get_width()/2, ALTURA_TELA/2 - label.get_height()/2 + y_offset))

def draw_timer(surface, start_ticks):
    seconds = (pygame.time.get_ticks() - start_ticks) // 1000
    m, s = divmod(seconds, 60)
    timer_text = f'{m:02d}:{s:02d}'
    
    font = pygame.font.SysFont('consolas', 40, bold=True)
    label = font.render(timer_text, 1, AMARELO)
    # Desenha no topo centralizado
    surface.blit(label, (LARGURA_TELA/2 - label.get_width()/2, 10))

def main_menu(win):
    run = True
    while run:
        win.fill(PRETO)
        draw_text_middle(win, "TETRIS BATTLE", 80, AZUL_NEON, -100)
        draw_text_middle(win, "1 - Single Player", 40, BRANCO, 0)
        draw_text_middle(win, "2 - VS Mode (2 Players)", 40, VERDE_NEON, 60)
        draw_text_middle(win, "Pressione a tecla para escolher", 20, CINZA, 150)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    game_loop(win, mode=1)
                if event.key == pygame.K_2:
                    game_loop(win, mode=2)
    pygame.quit()

def game_loop(win, mode):
    # Setup Inicial
    locked_positions_p1 = {}
    locked_positions_p2 = {}
    
    # Se for 1 jogador, centraliza. Se forem 2, divide a tela.
    offset_p1 = (LARGURA_TELA - PLAY_WIDTH) // 2 if mode == 1 else 50
    offset_p2 = LARGURA_TELA - PLAY_WIDTH - 50
    
    game1 = TetrisGame(offset_p1)
    game2 = TetrisGame(offset_p2) if mode == 2 else None
    
    clock = pygame.time.Clock()
    start_ticks = pygame.time.get_ticks()
    run = True
    fall_time = 0
    fall_speed = 0.27

    while run:
        grid_p1 = game1.create_grid(locked_positions_p1)
        grid_p2 = game2.create_grid(locked_positions_p2) if mode == 2 else None
        
        fall_time += clock.get_rawtime()
        clock.tick()

        # --- Lógica de Queda Automática ---
        if fall_time/1000 > fall_speed:
            fall_time = 0
            # Player 1 Fall
            game1.current_piece.y += 1
            if not(game1.valid_space(game1.current_piece, grid_p1)) and game1.current_piece.y > 0:
                game1.current_piece.y -= 1
                game1.change_piece = True
            
            # Player 2 Fall
            if mode == 2:
                game2.current_piece.y += 1
                if not(game2.valid_space(game2.current_piece, grid_p2)) and game2.current_piece.y > 0:
                    game2.current_piece.y -= 1
                    game2.change_piece = True

        # --- INPUTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                pygame.display.quit()
                quit()

            if event.type == pygame.KEYDOWN:
                # --- Controles Player 1 (WASD) ---
                if event.key == pygame.K_a:
                    game1.current_piece.x -= 1
                    if not(game1.valid_space(game1.current_piece, grid_p1)): game1.current_piece.x += 1
                elif event.key == pygame.K_d:
                    game1.current_piece.x += 1
                    if not(game1.valid_space(game1.current_piece, grid_p1)): game1.current_piece.x -= 1
                elif event.key == pygame.K_s:
                    game1.current_piece.y += 1
                    if not(game1.valid_space(game1.current_piece, grid_p1)): game1.current_piece.y -= 1
                elif event.key == pygame.K_w: # Rodar
                    game1.current_piece.rotation += 1
                    if not(game1.valid_space(game1.current_piece, grid_p1)): game1.current_piece.rotation -= 1

                # --- Controles Player 2 (Setas) ---
                if mode == 2:
                    if event.key == pygame.K_LEFT:
                        game2.current_piece.x -= 1
                        if not(game2.valid_space(game2.current_piece, grid_p2)): game2.current_piece.x += 1
                    elif event.key == pygame.K_RIGHT:
                        game2.current_piece.x += 1
                        if not(game2.valid_space(game2.current_piece, grid_p2)): game2.current_piece.x -= 1
                    elif event.key == pygame.K_DOWN:
                        game2.current_piece.y += 1
                        if not(game2.valid_space(game2.current_piece, grid_p2)): game2.current_piece.y -= 1
                    elif event.key == pygame.K_UP: # Rodar
                        game2.current_piece.rotation += 1
                        if not(game2.valid_space(game2.current_piece, grid_p2)): game2.current_piece.rotation -= 1
        
        # --- Atualizar Grid com Posições das Peças ---
        shape_pos_p1 = game1.convert_shape_format(game1.current_piece)
        for i in range(len(shape_pos_p1)):
            x, y = shape_pos_p1[i]
            if y > -1: grid_p1[y][x] = game1.current_piece.color

        if mode == 2:
            shape_pos_p2 = game2.convert_shape_format(game2.current_piece)
            for i in range(len(shape_pos_p2)):
                x, y = shape_pos_p2[i]
                if y > -1: grid_p2[y][x] = game2.current_piece.color

        # --- Checar se peça travou ---
        if game1.change_piece:
            for pos in shape_pos_p1:
                p = (pos[0], pos[1])
                locked_positions_p1[p] = game1.current_piece.color
            game1.current_piece = game1.next_piece
            game1.next_piece = game1.get_shape()
            game1.change_piece = False
            game1.clear_rows(grid_p1, locked_positions_p1)
        
        if mode == 2 and game2.change_piece:
            for pos in shape_pos_p2:
                p = (pos[0], pos[1])
                locked_positions_p2[p] = game2.current_piece.color
            game2.current_piece = game2.next_piece
            game2.next_piece = game2.get_shape()
            game2.change_piece = False
            game2.clear_rows(grid_p2, locked_positions_p2)

        # --- Desenhar na Tela ---
        win.fill(PRETO)
        
        # Desenha Timer
        draw_timer(win, start_ticks)

        # Desenha Jogo 1
        game1.draw_window(win, grid_p1)
        if mode == 1:
            draw_text_middle(win, "Player 1", 30, BRANCO, -320)
        
        # Desenha Jogo 2 (se houver)
        if mode == 2:
            game2.draw_window(win, grid_p2)
            # Labels VS
            font = pygame.font.SysFont('comicsans', 30)
            label_p1 = font.render("P1 (WASD)", 1, AZUL_NEON)
            label_p2 = font.render("P2 (Setas)", 1, VERDE_NEON)
            win.blit(label_p1, (50, 20))
            win.blit(label_p2, (LARGURA_TELA - 200, 20))

        pygame.display.update()

        # --- Game Over Check ---
        if game1.check_lost(locked_positions_p1) or (mode == 2 and game2.check_lost(locked_positions_p2)):
            draw_text_middle(win, "GAME OVER", 80, VERMELHO)
            pygame.display.update()
            pygame.time.delay(2000)
            run = False

win = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Tetris Battle")
main_menu(win)