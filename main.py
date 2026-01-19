import pygame
import random
import os

# --- CONFIGURAÇÕES GERAIS ---
pygame.init()
pygame.font.init()

LARGURA_TELA = 1000  # Aumentei um pouco para caber os menus laterais
ALTURA_TELA = 750
BLOCK_SIZE = 30
PLAY_WIDTH = 300  # 10 * 30
PLAY_HEIGHT = 600 # 20 * 30

# ARQUIVO DE SAVE
SCORE_FILE = "recordes_tetris.txt"

# CORES (Neon / Cyberpunk)
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
CINZA = (30, 30, 30)
CINZA_CLARO = (128, 128, 128)
VERMELHO = (255, 0, 0)
VERMELHO_ALERTA = (255, 0, 0, 100) # Com transparência
VERDE_NEON = (57, 255, 20)
AZUL_NEON = (0, 255, 255)
AMARELO = (255, 255, 0)
ROXO = (128, 0, 128)
ROSA_CHOQUE = (255, 20, 147) # Para os corações

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

# --- CLASSES ---

class Peca:
    def __init__(self, x, y, shape):
        self.x = x
        self.y = y
        self.shape = shape
        self.color = CORES_FORMAS[FORMAS.index(shape)]
        self.rotation = 0

class ItemMagico:
    def __init__(self, play_x, play_y):
        self.x = random.randint(0, 9) # Posição na grid (0 a 9)
        self.y = -2 # Começa acima da tela
        self.play_offset_x = play_x
        self.play_offset_y = play_y
        self.active = True
        self.tipo = "coracao" # Pode expandir para outros tipos
    
    def move(self):
        self.y += 0.1 # Cai mais devagar que as peças
    
    def draw(self, surface):
        if self.active:
            # Desenhar um coração simples
            cx = self.play_offset_x + (self.x * BLOCK_SIZE) + BLOCK_SIZE//2
            cy = self.play_offset_y + (int(self.y) * BLOCK_SIZE) + BLOCK_SIZE//2
            
            # Triangulo invertido + 2 circulos = coração
            pygame.draw.circle(surface, ROSA_CHOQUE, (int(cx - 5), int(cy - 5)), 7)
            pygame.draw.circle(surface, ROSA_CHOQUE, (int(cx + 5), int(cy - 5)), 7)
            pygame.draw.polygon(surface, ROSA_CHOQUE, [(cx-10, cy-2), (cx+10, cy-2), (cx, cy+10)])

class TetrisGame:
    def __init__(self, offset_x, player_id):
        self.offset_x = offset_x
        self.offset_y = (ALTURA_TELA - PLAY_HEIGHT) // 2 + 20
        self.grid = [[(0,0,0) for _ in range(10)] for _ in range(20)]
        self.current_piece = self.get_shape()
        self.next_piece = self.get_shape()
        self.change_piece = False
        self.score = 0
        self.game_over = False
        self.player_id = player_id # 1 ou 2
        
        # Modo Mágico
        self.magic_items = [] 
        self.magic_mode = False

        # Visual de Alerta
        self.is_flashing = False
        self.flash_timer = 0

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

    def check_magic_collision(self):
        # Verifica se a peça atual tocou num item magico
        formatted = self.convert_shape_format(self.current_piece)
        for item in self.magic_items:
            if item.active:
                # Se qualquer bloco da peça estiver na mesma coordenada (arredondada) do item
                for pos in formatted:
                    px, py = pos
                    if px == item.x and py == int(item.y):
                        item.active = False
                        self.score += 50 # Bonus por pegar o coração
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
        # Fundo do Grid
        pygame.draw.rect(surface, (0,0,0), (self.offset_x, self.offset_y, PLAY_WIDTH, PLAY_HEIGHT))
        
        # Grid Blocks
        for i in range(len(grid)):
            for j in range(len(grid[i])):
                if grid[i][j] != (0,0,0):
                    pygame.draw.rect(surface, grid[i][j], (self.offset_x + j*BLOCK_SIZE, self.offset_y + i*BLOCK_SIZE, BLOCK_SIZE, BLOCK_SIZE), 0)

        # Borda
        color_border = BRANCO
        if self.is_flashing:
             # Efeito pisca-pisca
            if (pygame.time.get_ticks() // 200) % 2 == 0:
                color_border = VERMELHO
                # Overlay Vermelho Transparente
                s = pygame.Surface((PLAY_WIDTH, PLAY_HEIGHT), pygame.SRCALPHA)
                s.fill((255, 0, 0, 50))
                surface.blit(s, (self.offset_x, self.offset_y))
        
        pygame.draw.rect(surface, color_border, (self.offset_x, self.offset_y, PLAY_WIDTH, PLAY_HEIGHT), 2)

        # Linhas fracas
        for i in range(len(grid)):
            pygame.draw.line(surface, (20,20,20), (self.offset_x, self.offset_y + i*BLOCK_SIZE), (self.offset_x+PLAY_WIDTH, self.offset_y+ i*BLOCK_SIZE))
            for j in range(len(grid[i])):
                pygame.draw.line(surface, (20,20,20), (self.offset_x + j*BLOCK_SIZE, self.offset_y), (self.offset_x + j*BLOCK_SIZE, self.offset_y + PLAY_HEIGHT))
        
        # Score e Info
        font = pygame.font.SysFont('comicsans', 30)
        label = font.render(f'Score: {self.score}', 1, BRANCO)
        surface.blit(label, (self.offset_x + 10, self.offset_y - 30))
        
        # Itens Mágicos
        if self.magic_mode:
            for item in self.magic_items:
                item.draw(surface)

        # Controles na tela
        font_ctrl = pygame.font.SysFont('consolas', 14)
        if self.player_id == 1:
            ctrls = ["W: Girar", "A: Esq", "D: Dir", "S: Descer"]
            for idx, txt in enumerate(ctrls):
                l = font_ctrl.render(txt, 1, CINZA_CLARO)
                surface.blit(l, (self.offset_x - 80, self.offset_y + 50 + idx*20))
        else:
            ctrls = ["Cima: Girar", "Esq: Esq", "Dir: Dir", "Baixo: Descer"]
            for idx, txt in enumerate(ctrls):
                l = font_ctrl.render(txt, 1, CINZA_CLARO)
                surface.blit(l, (self.offset_x + PLAY_WIDTH + 10, self.offset_y + 50 + idx*20))


# --- FUNÇÕES DE SISTEMA ---

def salvar_recorde(nome, pontuacao):
    try:
        if not os.path.exists(SCORE_FILE):
            with open(SCORE_FILE, "w") as f: f.write("")
        
        with open(SCORE_FILE, "a") as f:
            f.write(f"{nome},{pontuacao}\n")
    except:
        print("Erro ao salvar")

def ler_recordes():
    scores = []
    if os.path.exists(SCORE_FILE):
        with open(SCORE_FILE, "r") as f:
            for line in f:
                parts = line.strip().split(',')
                if len(parts) == 2:
                    scores.append((parts[0], int(parts[1])))
    scores.sort(key=lambda x: x[1], reverse=True)
    return scores[:5] # Retorna top 5

def draw_text_middle(surface, text, size, color, y_offset=0):
    font = pygame.font.SysFont("comicsans", size, bold=True)
    label = font.render(text, 1, color)
    surface.blit(label, (LARGURA_TELA/2 - label.get_width()/2, ALTURA_TELA/2 - label.get_height()/2 + y_offset))

def input_nome(win, score):
    # Tela para inserir 3 letras
    nome = ""
    run = True
    font = pygame.font.SysFont("comicsans", 60)
    
    while run:
        win.fill(PRETO)
        draw_text_middle(win, "NOVO RECORDE!", 50, VERDE_NEON, -100)
        draw_text_middle(win, f"Score: {score}", 40, BRANCO, -40)
        draw_text_middle(win, "Digite suas iniciais (3 letras):", 30, CINZA_CLARO, 20)
        
        lbl_nome = font.render(nome + "_"*(3-len(nome)), 1, AMARELO)
        win.blit(lbl_nome, (LARGURA_TELA/2 - lbl_nome.get_width()/2, ALTURA_TELA/2 + 80))
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "AAA"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RETURN:
                    if len(nome) > 0: run = False
                elif event.key == pygame.K_BACKSPACE:
                    nome = nome[:-1]
                else:
                    if len(nome) < 3 and event.unicode.isalpha():
                        nome += event.unicode.upper()
    return nome

def menu_controles(win):
    run = True
    while run:
        win.fill(PRETO)
        draw_text_middle(win, "CONECTAR CONTROLES", 50, AZUL_NEON, -200)
        
        # Info P1
        pygame.draw.rect(win, CINZA, (100, 200, 300, 300), 2)
        font = pygame.font.SysFont('comicsans', 30)
        win.blit(font.render("PLAYER 1", 1, BRANCO), (180, 220))
        win.blit(font.render("Teclado (WASD)", 1, VERDE_NEON), (150, 270))
        win.blit(font.render("Status: CONECTADO", 1, BRANCO), (150, 350))

        # Info P2
        pygame.draw.rect(win, CINZA, (600, 200, 300, 300), 2)
        win.blit(font.render("PLAYER 2", 1, BRANCO), (680, 220))
        win.blit(font.render("Teclado (Setas)", 1, VERDE_NEON), (650, 270))
        win.blit(font.render("Status: AGUARDANDO...", 1, BRANCO), (630, 350))
        win.blit(font.render("Pressione qualquer SETA", 1, CINZA_CLARO), (620, 390))

        draw_text_middle(win, "Pressione ESPAÇO para confirmar e voltar", 30, AMARELO, 250)
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    run = False
                if event.key in [pygame.K_UP, pygame.K_DOWN, pygame.K_LEFT, pygame.K_RIGHT]:
                     # Simulação de conexão visual
                     pygame.draw.rect(win, PRETO, (620, 340, 250, 100))
                     win.blit(font.render("Status: CONECTADO!", 1, AZUL_NEON), (630, 350))
                     pygame.display.update()
                     pygame.time.delay(500)
                     run = False

def menu_melhores(win):
    run = True
    scores = ler_recordes()
    while run:
        win.fill(PRETO)
        draw_text_middle(win, "MELHORES JOGADORES", 60, OURO if 'OURO' in globals() else AMARELO, -200)
        
        y = -100
        for idx, (nome, pontos) in enumerate(scores):
            txt = f"{idx+1}. {nome}  -  {pontos}"
            draw_text_middle(win, txt, 40, BRANCO, y)
            y += 50
            
        draw_text_middle(win, "Pressione ESC para voltar", 30, CINZA_CLARO, 250)
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT or (event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE):
                run = False

def pause_menu(win):
    paused = True
    while paused:
        # Overlay escuro
        s = pygame.Surface((LARGURA_TELA, ALTURA_TELA))
        s.set_alpha(10)
        s.fill(PRETO)
        win.blit(s, (0,0))
        
        draw_text_middle(win, "PAUSADO", 80, BRANCO, -50)
        draw_text_middle(win, "P - Voltar ao Jogo", 40, VERDE_NEON, 50)
        draw_text_middle(win, "Q - Sair para Menu", 40, VERMELHO, 100)
        pygame.display.update()

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                return "quit"
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    paused = False
                if event.key == pygame.K_q:
                    return "menu"
    return "resume"

# --- GAME LOOP PRINCIPAL ---

def game_loop(win, mode, magic=False):
    # Setup
    locked_positions_p1 = {}
    locked_positions_p2 = {}
    
    offset_p1 = (LARGURA_TELA - PLAY_WIDTH) // 2 if mode == 1 else 50
    offset_p2 = LARGURA_TELA - PLAY_WIDTH - 50
    
    game1 = TetrisGame(offset_p1, 1)
    game2 = TetrisGame(offset_p2, 2) if mode == 2 else None
    
    if magic:
        game1.magic_mode = True
        if game2: game2.magic_mode = True
    
    clock = pygame.time.Clock()
    start_ticks = pygame.time.get_ticks()
    run = True
    fall_time = 0
    fall_speed = 0.27
    magic_timer = 0
    
    # Diferença de pontos para derrota (Knockout)
    LIMIT_DIFF = 100 
    WARN_DIFF = 30

    while run:
        grid_p1 = game1.create_grid(locked_positions_p1)
        grid_p2 = game2.create_grid(locked_positions_p2) if mode == 2 else None
        
        dt = clock.tick()
        fall_time += dt
        magic_timer += dt

        # --- Modo Mágico (Spawn Itens) ---
        if magic and magic_timer > 5000: # A cada 5 segundos
            magic_timer = 0
            game1.magic_items.append(ItemMagico(game1.offset_x, game1.offset_y))
            if mode == 2:
                game2.magic_items.append(ItemMagico(game2.offset_x, game2.offset_y))

        # --- Queda Automática ---
        if fall_time/1000 > fall_speed:
            fall_time = 0
            # P1
            game1.current_piece.y += 1
            if not(game1.valid_space(game1.current_piece, grid_p1)) and game1.current_piece.y > 0:
                game1.current_piece.y -= 1
                game1.change_piece = True
            
            # P2
            if mode == 2:
                game2.current_piece.y += 1
                if not(game2.valid_space(game2.current_piece, grid_p2)) and game2.current_piece.y > 0:
                    game2.current_piece.y -= 1
                    game2.change_piece = True
            
            # Move Itens Mágicos
            if magic:
                for item in game1.magic_items: item.move()
                if mode == 2:
                    for item in game2.magic_items: item.move()

        # --- INPUTS ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
                return

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_p:
                    acao = pause_menu(win)
                    if acao == "menu": return
                    if acao == "quit": 
                        pygame.quit()
                        quit()

                # P1 (WASD)
                if event.key == pygame.K_a:
                    game1.current_piece.x -= 1
                    if not(game1.valid_space(game1.current_piece, grid_p1)): game1.current_piece.x += 1
                elif event.key == pygame.K_d:
                    game1.current_piece.x += 1
                    if not(game1.valid_space(game1.current_piece, grid_p1)): game1.current_piece.x -= 1
                elif event.key == pygame.K_s:
                    game1.current_piece.y += 1
                    if not(game1.valid_space(game1.current_piece, grid_p1)): game1.current_piece.y -= 1
                elif event.key == pygame.K_w:
                    game1.current_piece.rotation += 1
                    if not(game1.valid_space(game1.current_piece, grid_p1)): game1.current_piece.rotation -= 1

                # P2 (Setas)
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
                    elif event.key == pygame.K_UP:
                        game2.current_piece.rotation += 1
                        if not(game2.valid_space(game2.current_piece, grid_p2)): game2.current_piece.rotation -= 1
        
        # --- ATUALIZAÇÃO DO GRID ---
        shape_pos_p1 = game1.convert_shape_format(game1.current_piece)
        for i in range(len(shape_pos_p1)):
            x, y = shape_pos_p1[i]
            if y > -1: grid_p1[y][x] = game1.current_piece.color

        if mode == 2:
            shape_pos_p2 = game2.convert_shape_format(game2.current_piece)
            for i in range(len(shape_pos_p2)):
                x, y = shape_pos_p2[i]
                if y > -1: grid_p2[y][x] = game2.current_piece.color

        # --- LÓGICA MÁGICA ---
        if magic:
            game1.check_magic_collision()
            if mode == 2: game2.check_magic_collision()

        # --- FINALIZAR JOGADA ---
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

        # --- LÓGICA COMPETITIVA (VS) ---
        perdedor = None
        if mode == 2:
            diff = game1.score - game2.score
            
            # Reset
            game1.is_flashing = False
            game2.is_flashing = False
            
            # P2 está ganhando muito
            if diff < -WARN_DIFF: 
                game1.is_flashing = True # P1 Perigo
            # P1 está ganhando muito
            if diff > WARN_DIFF: 
                game2.is_flashing = True # P2 Perigo
            
            # Knockout
            if diff < -LIMIT_DIFF: perdedor = "P1"
            if diff > LIMIT_DIFF: perdedor = "P2"

        # --- DESENHO ---
        win.fill(PRETO)
        
        seconds = (pygame.time.get_ticks() - start_ticks) // 1000
        m, s = divmod(seconds, 60)
        timer_text = f'{m:02d}:{s:02d}'
        font_time = pygame.font.SysFont('consolas', 40, bold=True)
        lbl_time = font_time.render(timer_text, 1, AMARELO)
        win.blit(lbl_time, (LARGURA_TELA/2 - lbl_time.get_width()/2, 10))

        game1.draw_window(win, grid_p1)
        if mode == 1:
            draw_text_middle(win, "Player 1", 30, BRANCO, -340)
        
        if mode == 2:
            game2.draw_window(win, grid_p2)
            # HUD VS
            f_vs = pygame.font.SysFont('comicsans', 20)
            win.blit(f_vs.render(f"P1: {game1.score}", 1, AZUL_NEON), (50, 20))
            win.blit(f_vs.render(f"P2: {game2.score}", 1, VERDE_NEON), (LARGURA_TELA - 150, 20))

        pygame.display.update()

        # --- GAME OVER CONDITIONS ---
        msg_fim = ""
        if perdedor:
            msg_fim = f"KNOCKOUT! {perdedor} Perdeu feio!"
            run = False
        elif game1.check_lost(locked_positions_p1):
            msg_fim = "P1 PERDEU (Topo)!"
            run = False
        elif mode == 2 and game2.check_lost(locked_positions_p2):
            msg_fim = "P2 PERDEU (Topo)!"
            run = False
        
        if not run:
            draw_text_middle(win, msg_fim, 60, VERMELHO)
            pygame.display.update()
            pygame.time.delay(3000)
            
            # Salvar Scores
            if mode == 1:
                nome = input_nome(win, game1.score)
                salvar_recorde(nome, game1.score)
            elif mode == 2:
                # Salva o vencedor
                if game1.score > game2.score:
                    nome = input_nome(win, game1.score)
                    salvar_recorde(f"P1-{nome}", game1.score)
                else:
                    nome = input_nome(win, game2.score)
                    salvar_recorde(f"P2-{nome}", game2.score)

def main_menu(win):
    run = True
    while run:
        win.fill(PRETO)
        
        # Branding
        font_brand = pygame.font.SysFont('arial', 15)
        lbl_prod = font_brand.render("Produção: 4wallLab", 1, CINZA_CLARO)
        lbl_dedic = font_brand.render("Jogo pra meu Amoooo", 1, ROSA_CHOQUE)
        win.blit(lbl_prod, (10, ALTURA_TELA - 30))
        win.blit(lbl_dedic, (LARGURA_TELA - 180, ALTURA_TELA - 30))

        # Título
        draw_text_middle(win, "TETRIS ULTRA", 80, AZUL_NEON, -150)
        
        # Opções
        opts = [
            "1 - Single Player",
            "2 - VS Mode (Normal)",
            "3 - VS Dinâmico Mágico (Corações)",
            "4 - Conectar Controles",
            "5 - Ver Melhores (Salvos)",
            "Q - Sair"
        ]
        
        start_y = 0
        for opt in opts:
            color = BRANCO
            if "Mágico" in opt: color = ROSA_CHOQUE
            draw_text_middle(win, opt, 30, color, start_y)
            start_y += 40
        
        pygame.display.update()
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                run = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_1:
                    game_loop(win, mode=1, magic=False)
                if event.key == pygame.K_2:
                    game_loop(win, mode=2, magic=False)
                if event.key == pygame.K_3:
                    game_loop(win, mode=2, magic=True)
                if event.key == pygame.K_4:
                    menu_controles(win)
                if event.key == pygame.K_5:
                    menu_melhores(win)
                if event.key == pygame.K_q:
                    run = False
    pygame.quit()

win = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
pygame.display.set_caption("Tetris Battle - 4wallLab")
main_menu(win)