import pygame
import random
import json
import os
import copy

# ==============================================================================
# 1. CONFIGURAÇÕES E CONSTANTES
# ==============================================================================

# Cores (R, G, B)
PRETO = (0, 0, 0)
BRANCO = (255, 255, 255)
CINZA = (128, 128, 128)
CINZA_ESCURO = (50, 50, 50)
VERMELHO_UI = (220, 20, 60)
VERDE_UI = (50, 205, 50)
AZUL_UI = (30, 144, 255)

# Cores das Peças
CORES_PECAS = [
    (0, 255, 255),   # I - Ciano
    (255, 215, 0),   # O - Amarelo
    (128, 0, 128),   # T - Roxo
    (0, 255, 0),     # S - Verde
    (255, 0, 0),     # Z - Vermelho
    (0, 0, 255),     # J - Azul
    (255, 165, 0)    # L - Laranja
]

# Dimensões
LARGURA_TELA = 800
ALTURA_TELA = 650
TAM_BLOCO = 25
COLS = 10
LINHAS = 20
LARGURA_PLAY = COLS * TAM_BLOCO
ALTURA_PLAY = LINHAS * TAM_BLOCO

# Formatos das Peças (Matrizes 0 e 1)
FORMATOS = [
    [[1, 1, 1, 1]], # I
    [[1, 1], [1, 1]], # O
    [[0, 1, 0], [1, 1, 1]], # T
    [[0, 1, 1], [1, 1, 0]], # S
    [[1, 1, 0], [0, 1, 1]], # Z
    [[1, 0, 0], [1, 1, 1]], # J
    [[0, 0, 1], [1, 1, 1]]  # L
]

ARQUIVO_DADOS = "dados_tetris.json"

# ==============================================================================
# 2. SISTEMA DE DADOS (PERSISTÊNCIA)
# ==============================================================================

class GerenciadorDados:
    def __init__(self):
        self.dados = {
            "recorde_infinito": 0,
            "nivel_carreira": 1
        }
        self.carregar()

    def carregar(self):
        if os.path.exists(ARQUIVO_DADOS):
            try:
                with open(ARQUIVO_DADOS, 'r') as f:
                    self.dados = json.load(f)
            except:
                print("Erro ao carregar save. Criando novo.")

    def salvar(self):
        try:
            with open(ARQUIVO_DADOS, 'w') as f:
                json.dump(self.dados, f)
        except:
            print("Erro ao salvar dados.")

    def atualizar_recorde(self, pontuacao):
        if pontuacao > self.dados["recorde_infinito"]:
            self.dados["recorde_infinito"] = pontuacao
            self.salvar()
            return True
        return False

    def desbloquear_nivel(self, nivel_atual):
        if nivel_atual >= self.dados["nivel_carreira"]:
            self.dados["nivel_carreira"] = nivel_atual + 1
            self.salvar()

# ==============================================================================
# 3. CLASSES BÁSICAS (PEÇA E MOTOR)
# ==============================================================================

class Peca:
    def __init__(self, x, y, formato_idx):
        self.x = x
        self.y = y
        self.tipo = formato_idx
        self.cor = CORES_PECAS[formato_idx]
        self.rotacao = 0
        self.formato_base = FORMATOS[formato_idx]

    def imagem(self):
        """Retorna a matriz da peça na rotação atual"""
        matriz = self.formato_base
        for _ in range(self.rotacao):
            matriz = [list(row) for row in zip(*matriz[::-1])]
        return matriz

    def rotacionar(self):
        self.rotacao = (self.rotacao + 1) % 4

class MotorJogo:
    """Lógica Pura do Tetris (sem renderização)"""
    def __init__(self, dificuldade='MEDIO'):
        self.grid = [[(0,0,0) for _ in range(COLS)] for _ in range(LINHAS)]
        self.peca_atual = None
        self.prox_peca = None
        self.pontuacao = 0
        self.linhas_totais = 0
        self.combo = 0
        self.game_over = False
        self.dificuldade = dificuldade
        
        # Define velocidade base
        mult = {'FACIL': 1.0, 'MEDIO': 1.5, 'DIFICIL': 2.0}
        self.velocidade_base = mult.get(dificuldade, 1.0)
        
        self.nova_peca()

    def nova_peca(self):
        if self.prox_peca:
            self.peca_atual = self.prox_peca
        else:
            self.peca_atual = self._gerar_peca_aleatoria()
        
        self.prox_peca = self._gerar_peca_aleatoria()
        
        # Verifica Game Over logo no spawn
        if not self.validar_movimento(self.peca_atual, 0, 0, self.peca_atual.rotacao):
            self.game_over = True

    def _gerar_peca_aleatoria(self):
        return Peca(COLS // 2 - 2, 0, random.randint(0, len(FORMATOS) - 1))

    def validar_movimento(self, peca, dx, dy, rotacao_teste=None):
        rot = peca.rotacao if rotacao_teste is None else rotacao_teste
        
        # Simula rotação localmente para teste
        forma_original = peca.formato_base
        matriz_teste = forma_original
        for _ in range(rot):
            matriz_teste = [list(row) for row in zip(*matriz_teste[::-1])]

        for i, linha in enumerate(matriz_teste):
            for j, valor in enumerate(linha):
                if valor:
                    novo_x = peca.x + j + dx
                    novo_y = peca.y + i + dy
                    
                    if novo_x < 0 or novo_x >= COLS or novo_y >= LINHAS:
                        return False
                    if novo_y >= 0: # Ignora colisão acima da tela
                        if self.grid[novo_y][novo_x] != (0,0,0):
                            return False
        return True

    def travar_peca(self):
        matriz = self.peca_atual.imagem()
        for i, linha in enumerate(matriz):
            for j, valor in enumerate(linha):
                if valor:
                    py = self.peca_atual.y + i
                    px = self.peca_atual.x + j
                    if py >= 0:
                        self.grid[py][px] = self.peca_atual.cor
        
        linhas_limpas = self.verificar_linhas()
        self.nova_peca()
        return linhas_limpas

    def verificar_linhas(self):
        linhas_para_limpar = []
        for i in range(LINHAS):
            if (0,0,0) not in self.grid[i]:
                linhas_para_limpar.append(i)
        
        qtd = len(linhas_para_limpar)
        if qtd > 0:
            self.combo += 1
            # Remove linhas e adiciona novas no topo
            for idx in linhas_para_limpar:
                del self.grid[idx]
                self.grid.insert(0, [(0,0,0) for _ in range(COLS)])
            
            # Pontuação
            base = [0, 100, 300, 500, 800] # 0, 1, 2, 3, 4 linhas
            pontos = base[qtd] * (1 + (self.combo * 0.1)) * self.velocidade_base
            self.pontuacao += int(pontos)
            self.linhas_totais += qtd
        else:
            self.combo = 0
            
        return qtd

    def adicionar_lixo(self, qtd):
        """Adiciona linhas cinzas por baixo (modo VS)"""
        for _ in range(qtd):
            self.grid.pop(0)
            nova_linha = [CINZA_ESCURO] * COLS
            buraco = random.randint(0, COLS-1)
            nova_linha[buraco] = (0,0,0)
            self.grid.append(nova_linha)

# ==============================================================================
# 4. INTELIGÊNCIA ARTIFICIAL
# ==============================================================================

class TetrisIA:
    def __init__(self, motor_jogo):
        self.motor = motor_jogo
        self.timer_movimento = 0
        self.intervalo_movimento = 200 if motor_jogo.dificuldade == 'FACIL' else 100 # ms
        self.alvo_x = None
        self.alvo_rot = None

    def pensar(self):
        """Calcula o melhor movimento para a peça atual"""
        melhor_score = -float('inf')
        melhor_x = self.motor.peca_atual.x
        melhor_rot = self.motor.peca_atual.rotacao
        
        peca = self.motor.peca_atual
        
        # Tenta todas as rotações (0-3)
        for r in range(4):
            # Tenta todas as posições X (-2 a 10 aprox)
            for x in range(-2, COLS):
                if not self.motor.validar_movimento(peca, x - peca.x, 0, r):
                    continue
                
                # Simula queda (Hard Drop)
                dy = 0
                while self.motor.validar_movimento(peca, x - peca.x, dy + 1, r):
                    dy += 1
                
                # Avalia o Grid resultante
                score = self._avaliar_grid_simulado(x, peca.y + dy, r)
                if score > melhor_score:
                    melhor_score = score
                    melhor_x = x
                    melhor_rot = r
        
        self.alvo_x = melhor_x
        self.alvo_rot = melhor_rot

    def _avaliar_grid_simulado(self, tx, ty, rot):
        # Cria cópia simplificada do grid
        grid_temp = [row[:] for row in self.motor.grid]
        peca = self.motor.peca_atual
        
        # Insere peça no grid temporário
        matriz = peca.formato_base
        for _ in range(rot):
            matriz = [list(row) for row in zip(*matriz[::-1])]
            
        for i, linha in enumerate(matriz):
            for j, val in enumerate(linha):
                if val:
                    if 0 <= ty+i < LINHAS and 0 <= tx+j < COLS:
                        grid_temp[ty+i][tx+j] = (1,1,1) # Marca como ocupado

        # Heurísticas
        altura_agregada = 0
        buracos = 0
        linhas_completas = 0
        irregularidade = 0
        
        col_alturas = [0] * COLS
        
        for c in range(COLS):
            for r in range(LINHAS):
                if grid_temp[r][c] != (0,0,0):
                    col_alturas[c] = LINHAS - r
                    break
            altura_agregada += col_alturas[c]
        
        # Conta buracos
        for c in range(COLS):
            bloqueio = False
            for r in range(LINHAS):
                if grid_temp[r][c] != (0,0,0):
                    bloqueio = True
                elif bloqueio and grid_temp[r][c] == (0,0,0):
                    buracos += 1
        
        # Conta linhas completas
        for r in range(LINHAS):
            if (0,0,0) not in grid_temp[r]:
                linhas_completas += 1
                
        # Irregularidade (diferença entre colunas vizinhas)
        for c in range(COLS - 1):
            irregularidade += abs(col_alturas[c] - col_alturas[c+1])

        # Pesos (ajustar para melhorar IA)
        score = (-0.51 * altura_agregada) + (0.76 * linhas_completas) + (-0.36 * buracos) + (-0.18 * irregularidade)
        return score

    def executar_movimento(self, dt):
        """Move a peça em direção ao alvo"""
        if self.alvo_x is None:
            self.pensar()
            return

        self.timer_movimento += dt
        if self.timer_movimento > self.intervalo_movimento:
            self.timer_movimento = 0
            
            # Rotação
            if self.motor.peca_atual.rotacao != self.alvo_rot:
                self.motor.peca_atual.rotacionar()
                if not self.motor.validar_movimento(self.motor.peca_atual, 0, 0):
                     # Se rotação falhar, desfaz
                    for _ in range(3): self.motor.peca_atual.rotacionar()
            
            # Movimento Horizontal
            elif self.motor.peca_atual.x < self.alvo_x:
                if self.motor.validar_movimento(self.motor.peca_atual, 1, 0):
                    self.motor.peca_atual.x += 1
            elif self.motor.peca_atual.x > self.alvo_x:
                if self.motor.validar_movimento(self.motor.peca_atual, -1, 0):
                    self.motor.peca_atual.x -= 1
            
            # Se alinhado, pode dropar (opcional: IA rápida usa hard drop)
            # Aqui deixamos a gravidade natural atuar ou aceleramos levemente

# ==============================================================================
# 5. APLICAÇÃO PRINCIPAL (UI E LOOPS)
# ==============================================================================

class JogoTetrisApp:
    def __init__(self):
        pygame.init()
        self.tela = pygame.display.set_mode((LARGURA_TELA, ALTURA_TELA))
        pygame.display.set_caption("Tetris Master Python")
        self.clock = pygame.time.Clock()
        self.fonte = pygame.font.SysFont('Arial', 20, bold=True)
        self.fonte_grande = pygame.font.SysFont('Arial', 50, bold=True)
        
        self.dados = GerenciadorDados()
        self.estado = 'MENU' # MENU, JOGO_SOLO, JOGO_VS, JOGO_CARREIRA, GAMEOVER
        self.modo_atual = None # 'INFINITO', 'CARREIRA', 'VS'
        
        self.motor_p1 = None
        self.motor_cpu = None
        self.ia_cpu = None
        
        self.tempo_queda = 0
        self.velocidade_queda = 500 # ms
        
        # Níveis da Carreira
        self.niveis_carreira = {
            1: {'obj': 'pontos', 'meta': 2000, 'desc': 'Faca 2.000 Pontos'},
            2: {'obj': 'linhas', 'meta': 10, 'desc': 'Limpe 10 Linhas'},
            3: {'obj': 'combo', 'meta': 3, 'desc': 'Faca um Combo x3'} # Difícil
        }

    def desenhar_texto(self, texto, x, y, cor=BRANCO, center=False, grande=False):
        font = self.fonte_grande if grande else self.fonte
        surf = font.render(texto, True, cor)
        rect = surf.get_rect()
        if center:
            rect.center = (x, y)
        else:
            rect.topleft = (x, y)
        self.tela.blit(surf, rect)

    def desenhar_grid(self, motor, offset_x, offset_y):
        # Borda
        pygame.draw.rect(self.tela, BRANCO, (offset_x - 2, offset_y - 2, LARGURA_PLAY + 4, ALTURA_PLAY + 4), 2)
        
        # Grid Estático
        for y in range(LINHAS):
            for x in range(COLS):
                cor = motor.grid[y][x]
                if cor != (0,0,0):
                    rect = (offset_x + x * TAM_BLOCO, offset_y + y * TAM_BLOCO, TAM_BLOCO - 1, TAM_BLOCO - 1)
                    pygame.draw.rect(self.tela, cor, rect)
        
        # Peça em movimento
        if motor.peca_atual:
            matriz = motor.peca_atual.imagem()
            for i, linha in enumerate(matriz):
                for j, valor in enumerate(linha):
                    if valor:
                        px = offset_x + (motor.peca_atual.x + j) * TAM_BLOCO
                        py = offset_y + (motor.peca_atual.y + i) * TAM_BLOCO
                        if py >= offset_y:
                            pygame.draw.rect(self.tela, motor.peca_atual.cor, (px, py, TAM_BLOCO - 1, TAM_BLOCO - 1))

    def resetar_jogo(self, modo, dificuldade):
        self.modo_atual = modo
        self.motor_p1 = MotorJogo(dificuldade)
        self.tempo_queda = 0
        
        if modo == 'VS':
            self.motor_cpu = MotorJogo(dificuldade)
            self.ia_cpu = TetrisIA(self.motor_cpu)
            # Reposicionar para tela dividida é visual, lógica é igual
            
        self.estado = 'JOGANDO'

    def logica_jogo(self, dt):
        # Controle de Queda Player 1
        velocidade = self.velocidade_queda / (1 + (self.motor_p1.pontuacao / 5000))
        self.tempo_queda += dt
        
        if self.tempo_queda > velocidade:
            self.tempo_queda = 0
            if self.motor_p1.validar_movimento(self.motor_p1.peca_atual, 0, 1):
                self.motor_p1.peca_atual.y += 1
            else:
                linhas = self.motor_p1.travar_peca()
                # VS Mode Attack
                if self.modo_atual == 'VS' and linhas >= 2:
                    self.motor_cpu.adicionar_lixo(linhas - 1)

        # Lógica Específica dos Modos
        if self.modo_atual == 'CARREIRA':
            nivel = self.dados.dados['nivel_carreira']
            meta = self.niveis_carreira.get(nivel, None)
            if meta:
                concluiu = False
                if meta['obj'] == 'pontos' and self.motor_p1.pontuacao >= meta['meta']: concluiu = True
                if meta['obj'] == 'linhas' and self.motor_p1.linhas_totais >= meta['meta']: concluiu = True
                if meta['obj'] == 'combo' and self.motor_p1.combo >= meta['meta']: concluiu = True
                
                if concluiu:
                    self.dados.desbloquear_nivel(nivel)
                    self.estado = 'VITORIA_NIVEL'

        # Lógica VS (CPU)
        if self.modo_atual == 'VS':
            # Gravidade CPU
            if self.motor_cpu.validar_movimento(self.motor_cpu.peca_atual, 0, 1):
                # Queda lenta normal
                pass 
            else:
                linhas_cpu = self.motor_cpu.travar_peca()
                if linhas_cpu >= 2:
                    self.motor_p1.adicionar_lixo(linhas_cpu - 1)
            
            # IA Pensa e Move
            self.ia_cpu.executar_movimento(dt)
            # Força queda IA de vez em quando para não ficar parada
            if random.randint(0, 100) < 5: 
                if self.motor_cpu.validar_movimento(self.motor_cpu.peca_atual, 0, 1):
                     self.motor_cpu.peca_atual.y += 1

        # Verificar Derrota
        if self.motor_p1.game_over:
            if self.modo_atual == 'INFINITO':
                self.dados.atualizar_recorde(self.motor_p1.pontuacao)
            self.estado = 'GAMEOVER'
            
        if self.modo_atual == 'VS' and self.motor_cpu.game_over:
            self.estado = 'VITORIA_VS'

    def input_jogo(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_LEFT:
                if self.motor_p1.validar_movimento(self.motor_p1.peca_atual, -1, 0):
                    self.motor_p1.peca_atual.x -= 1
            elif event.key == pygame.K_RIGHT:
                if self.motor_p1.validar_movimento(self.motor_p1.peca_atual, 1, 0):
                    self.motor_p1.peca_atual.x += 1
            elif event.key == pygame.K_DOWN:
                if self.motor_p1.validar_movimento(self.motor_p1.peca_atual, 0, 1):
                    self.motor_p1.peca_atual.y += 1
            elif event.key == pygame.K_UP:
                # Tenta rotacionar
                self.motor_p1.peca_atual.rotacionar()
                if not self.motor_p1.validar_movimento(self.motor_p1.peca_atual, 0, 0):
                    # Wall kick simples (tenta empurrar se bater na parede)
                    if self.motor_p1.validar_movimento(self.motor_p1.peca_atual, -1, 0):
                        self.motor_p1.peca_atual.x -= 1
                    elif self.motor_p1.validar_movimento(self.motor_p1.peca_atual, 1, 0):
                        self.motor_p1.peca_atual.x += 1
                    else:
                        # Se não der, desfaz
                        for _ in range(3): self.motor_p1.peca_atual.rotacionar()
            elif event.key == pygame.K_SPACE:
                # Hard drop
                while self.motor_p1.validar_movimento(self.motor_p1.peca_atual, 0, 1):
                    self.motor_p1.peca_atual.y += 1
                linhas = self.motor_p1.travar_peca()
                if self.modo_atual == 'VS' and linhas >= 2:
                    self.motor_cpu.adicionar_lixo(linhas - 1)
            elif event.key == pygame.K_ESCAPE:
                self.estado = 'MENU'

    def loop_principal(self):
        rodando = True
        while rodando:
            dt = self.clock.tick(60) # 60 FPS
            self.tela.fill(CINZA_ESCURO)
            
            # Eventos Globais
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    rodando = False
                
                if self.estado == 'MENU':
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_1: self.resetar_jogo('INFINITO', 'MEDIO')
                        if event.key == pygame.K_2: self.resetar_jogo('CARREIRA', 'MEDIO')
                        if event.key == pygame.K_3: self.resetar_jogo('VS', 'MEDIO')
                        if event.key == pygame.K_q: rodando = False
                
                elif self.estado == 'JOGANDO':
                    self.input_jogo(event)
                
                elif self.estado in ['GAMEOVER', 'VITORIA_NIVEL', 'VITORIA_VS']:
                    if event.type == pygame.KEYDOWN:
                        if event.key == pygame.K_ENTER: self.estado = 'MENU'

            # Renderização e Updates por Estado
            if self.estado == 'MENU':
                self.desenhar_texto("TETRIS MASTER", LARGURA_TELA//2, 100, AZUL_UI, True, True)
                self.desenhar_texto("1. Modo Infinito", LARGURA_TELA//2, 250, BRANCO, True)
                self.desenhar_texto("2. Modo Carreira", LARGURA_TELA//2, 300, BRANCO, True)
                self.desenhar_texto("3. VS Computador", LARGURA_TELA//2, 350, BRANCO, True)
                self.desenhar_texto("Q. Sair", LARGURA_TELA//2, 450, VERMELHO_UI, True)
                self.desenhar_texto(f"Recorde Infinito: {self.dados.dados['recorde_infinito']}", LARGURA_TELA//2, 550, (255,255,0), True)
            
            elif self.estado == 'JOGANDO':
                self.logica_jogo(dt)
                
                # Desenha Tela (Split ou Solo)
                if self.modo_atual == 'VS':
                    self.desenhar_grid(self.motor_p1, 50, 50)
                    self.desenhar_texto("VOCÊ", 150, 20, BRANCO, True)
                    self.desenhar_texto(f"Score: {self.motor_p1.pontuacao}", 50, 560)
                    
                    self.desenhar_grid(self.motor_cpu, 450, 50)
                    self.desenhar_texto("CPU (IA)", 550, 20, VERMELHO_UI, True)
                    self.desenhar_texto(f"Score: {self.motor_cpu.pontuacao}", 450, 560)
                
                else:
                    # Single Player (Centro)
                    offset_x = (LARGURA_TELA - LARGURA_PLAY) // 2
                    self.desenhar_grid(self.motor_p1, offset_x, 50)
                    
                    # HUD Lateral
                    self.desenhar_texto("Score", 50, 100, AZUL_UI)
                    self.desenhar_texto(str(self.motor_p1.pontuacao), 50, 130)
                    
                    self.desenhar_texto("Linhas", 50, 200, AZUL_UI)
                    self.desenhar_texto(str(self.motor_p1.linhas_totais), 50, 230)

                    self.desenhar_texto("Combo", 50, 300, VERDE_UI)
                    self.desenhar_texto(str(self.motor_p1.combo), 50, 330)
                    
                    if self.modo_atual == 'CARREIRA':
                        nivel = self.dados.dados['nivel_carreira']
                        desc = self.niveis_carreira.get(nivel, {'desc': 'FIM DA CARREIRA'})['desc']
                        self.desenhar_texto(f"NIVEL {nivel}", 600, 100, (255,215,0))
                        self.desenhar_texto(desc, 600, 140, BRANCO)

            elif self.estado == 'GAMEOVER':
                self.desenhar_texto("GAME OVER", LARGURA_TELA//2, 250, VERMELHO_UI, True, True)
                self.desenhar_texto(f"Pontuação Final: {self.motor_p1.pontuacao}", LARGURA_TELA//2, 350, BRANCO, True)
                self.desenhar_texto("Pressione ENTER para voltar", LARGURA_TELA//2, 450, CINZA, True)

            elif self.estado == 'VITORIA_NIVEL':
                self.desenhar_texto("NIVEL COMPLETADO!", LARGURA_TELA//2, 250, VERDE_UI, True, True)
                self.desenhar_texto("Pressione ENTER para continuar", LARGURA_TELA//2, 350, BRANCO, True)
                
            elif self.estado == 'VITORIA_VS':
                self.desenhar_texto("VOCE VENCEU A IA!", LARGURA_TELA//2, 250, (255,215,0), True, True)
                self.desenhar_texto("Pressione ENTER para voltar", LARGURA_TELA//2, 350, BRANCO, True)

            pygame.display.update()
        
        pygame.quit()

if __name__ == "__main__":
    app = JogoTetrisApp()
    app.loop_principal()