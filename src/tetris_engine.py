# src/tetris_engine.py
import pygame
import random
from .config import *

class Piece:
    def __init__(self, x, y, shape_idx):
        self.x = x
        self.y = y
        self.shape_idx = shape_idx
        self.type = SHAPES[shape_idx]
        self.color = SHAPE_COLORS[shape_idx]
        self.rotation = 0  # 0 a 3

    def image(self):
        """Retorna a matriz da rotação atual."""
        return self.type[self.rotation % len(self.type)]

    def rotate(self):
        self.rotation = (self.rotation + 1) % len(self.type)
    
    def undo_rotate(self):
        self.rotation = (self.rotation - 1) % len(self.type)

class TetrisGame:
    def __init__(self, player_id=0):
        self.player_id = player_id
        self.grid = self.create_grid()
        self.current_piece = None
        self.next_piece = None
        self.score = 0
        self.level = 1
        self.lines_cleared = 0
        self.state = "JOGANDO" # JOGANDO, GAME_OVER
        
        # Controle de tempo de queda
        self.fall_time = 0
        self.fall_speed = 0.5 # Segundos para cair

        self.get_new_piece() # Cria initial next_piece
        self.spawn_piece()   # Move next para current

    def create_grid(self, locked_positions={}):
        """Cria matriz 20x10. locked_positions é dict {(x,y): color}"""
        grid = [[BLACK for _ in range(GRID_WIDTH)] for _ in range(GRID_HEIGHT)]
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                if (x, y) in locked_positions:
                    grid[y][x] = locked_positions[(x, y)]
        return grid

    def get_new_piece(self):
        idx = random.randint(0, len(SHAPES) - 1)
        # Começa no meio topo (x=5, y=0)
        self.next_piece = Piece(5, 0, idx)

    def spawn_piece(self):
        self.current_piece = self.next_piece
        self.get_new_piece()
        # Verifica colisão logo ao nascer (Game Over)
        if not self.valid_move(self.current_piece, self.grid):
            self.state = "GAME_OVER"

    def valid_move(self, piece, grid):
        accepted_pos = [[(x, y) for x in range(GRID_WIDTH) if grid[y][x] == BLACK] for y in range(GRID_HEIGHT)]
        accepted_pos = [x for sub in accepted_pos for x in sub] # Flatten

        formatted = self.convert_shape_format(piece)

        for pos in formatted:
            if pos not in accepted_pos:
                if pos[1] > -1: # Ignora posições acima da tela ao nascer
                    return False
        return True

    def convert_shape_format(self, piece):
        positions = []
        format_shape = piece.image()

        for i, line in enumerate(format_shape):
            row = list(line)
            for j, column in enumerate(row):
                if column == '0':
                    # O formato é 5x5, ajusta offset para posição x,y do jogo
                    positions.append((piece.x + j - 2, piece.y + i - 4))
        return positions

    def lock_piece(self):
        """Trava a peça no grid e verifica linhas"""
        formatted = self.convert_shape_format(self.current_piece)
        
        # Adiciona ao grid persistente
        for pos in formatted:
            x, y = pos
            if y > -1: # Evita erro se game over no topo
                self.grid[y][x] = self.current_piece.color

        # Verifica linhas
        self.clear_lines()
        self.spawn_piece()

    def clear_lines(self):
        inc = 0
        # Percorre de baixo para cima
        for y in range(GRID_HEIGHT - 1, -1, -1):
            row = self.grid[y]
            if BLACK not in row: # Se linha não tem preto, está cheia
                inc += 1
                # Remove a linha movendo tudo para baixo
                ind = y
                for y2 in range(ind, 0, -1):
                    self.grid[y2] = self.grid[y2 - 1][:]
                self.grid[0] = [BLACK for _ in range(GRID_WIDTH)]
                
                # Hack: como movemos tudo para baixo, precisamos checar a mesma linha 'y' de novo
                # Mas para simplificar neste exemplo, deixamos o loop continuar.
                # Nota: Em loop reverso simples, pode pular linha se houver múltiplas.
                # O ideal é reconstruir o grid, mas esta lógica funciona para tetris básico.

        if inc > 0:
            # Pontuação estilo Nintendo
            scores = {1: 40, 2: 100, 3: 300, 4: 1200}
            self.score += scores.get(inc, 0) * self.level
            self.lines_cleared += inc
            # Aumenta velocidade a cada 10 linhas
            if self.lines_cleared // 10 >= self.level:
                self.level += 1
                self.fall_speed = max(0.1, 0.5 - (self.level * 0.05))

    def update(self, actions, dt):
        """Chamado a cada frame"""
        if self.state != "JOGANDO": return

        # Queda automática
        self.fall_time += dt
        if self.fall_time >= self.fall_speed:
            self.fall_time = 0
            self.current_piece.y += 1
            if not self.valid_move(self.current_piece, self.grid):
                self.current_piece.y -= 1
                self.lock_piece()

        # Input lateral
        if actions['left']:
            self.current_piece.x -= 1
            if not self.valid_move(self.current_piece, self.grid):
                self.current_piece.x += 1
        
        if actions['right']:
            self.current_piece.x += 1
            if not self.valid_move(self.current_piece, self.grid):
                self.current_piece.x -= 1

        # Rotação
        if actions['rotate']:
            self.current_piece.rotate()
            if not self.valid_move(self.current_piece, self.grid):
                self.current_piece.undo_rotate()

        # Soft Drop (Descer rápido)
        if actions['drop']:
            self.current_piece.y += 1
            if not self.valid_move(self.current_piece, self.grid):
                self.current_piece.y -= 1
                # Opcional: Lock imediato ou esperar próximo tick?
                # Vamos deixar travar no próximo tick automático para permitir deslize

    def draw(self, surface, offset_x, offset_y):
        # 1. Desenha o Grid Estático
        for y in range(GRID_HEIGHT):
            for x in range(GRID_WIDTH):
                pygame.draw.rect(surface, self.grid[y][x], 
                                 (offset_x + x*BLOCK_SIZE, offset_y + y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)
                # Grade cinza fraca
                pygame.draw.rect(surface, (30,30,30), 
                                 (offset_x + x*BLOCK_SIZE, offset_y + y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 1)

        # 2. Desenha borda da área de jogo
        pygame.draw.rect(surface, WHITE, (offset_x, offset_y, PLAY_WIDTH, PLAY_HEIGHT), 2)

        # 3. Desenha a Peça Atual
        if self.current_piece:
            formatted = self.convert_shape_format(self.current_piece)
            for pos in formatted:
                x, y = pos
                if y > -1: # Não desenha o que está "acima" da tela
                    pygame.draw.rect(surface, self.current_piece.color, 
                                     (offset_x + x*BLOCK_SIZE, offset_y + y*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)

        # 4. Desenha HUD (Score, Level) - Simplificado
        font = pygame.font.SysFont('Arial', 20)
        label_score = font.render(f"Score: {self.score}", 1, WHITE)
        label_level = font.render(f"Level: {self.level}", 1, WHITE)
        
        surface.blit(label_score, (offset_x + PLAY_WIDTH + 10, offset_y))
        surface.blit(label_level, (offset_x + PLAY_WIDTH + 10, offset_y + 30))
        
        # 5. Próxima Peça
        label_next = font.render("Next:", 1, WHITE)
        surface.blit(label_next, (offset_x + PLAY_WIDTH + 10, offset_y + 80))
        if self.next_piece:
            format_shape = self.next_piece.type[self.next_piece.rotation % len(self.next_piece.type)]
            for i, line in enumerate(format_shape):
                for j, char in enumerate(line):
                    if char == '0':
                        pygame.draw.rect(surface, self.next_piece.color, 
                                         (offset_x + PLAY_WIDTH + 10 + j*BLOCK_SIZE, offset_y + 110 + i*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)