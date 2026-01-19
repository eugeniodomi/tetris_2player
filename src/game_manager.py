# src/game_manager.py
import pygame
from .config import *
from .input_handler import InputHandler
from .tetris_engine import TetrisGame

class GameManager:
    def __init__(self):
        self.state = "MENU" # Estados: MENU, GAME, GAME_OVER
        self.input_handler = InputHandler()
        # Inicializa um jogo Single Player
        self.game = None 
        
        # Fonts
        self.font_big = pygame.font.SysFont('Arial', 60, bold=True)
        self.font_small = pygame.font.SysFont('Arial', 30)

    def start_game(self):
        self.game = TetrisGame(player_id=0)
        # Mapeia teclado para player 0 se não houver
        if 0 not in self.input_handler.players_map:
            self.input_handler.map_player_to_device(0, 'keyboard')
        self.state = "GAME"

    def update(self, dt):
        # Captura inputs globais (ESC para sair/pause)
        keys = pygame.key.get_pressed()
        
        if self.state == "MENU":
            if keys[pygame.K_RETURN]:
                self.start_game()

        elif self.state == "GAME":
            # Inputs do jogo
            actions = self.input_handler.get_action(0) # Player 0
            
            # Pausa (Tecla P)
            if keys[pygame.K_p]:
                self.state = "PAUSE"
            
            # Atualiza o motor do Tetris
            self.game.update(actions, dt)
            
            if self.game.state == "GAME_OVER":
                self.state = "GAME_OVER"

        elif self.state == "GAME_OVER":
            if keys[pygame.K_RETURN]: # Reiniciar
                self.start_game()
            if keys[pygame.K_ESCAPE]: # Voltar ao Menu
                self.state = "MENU"
        
        elif self.state == "PAUSE":
            if keys[pygame.K_RETURN]: # Retornar ao jogo
                self.state = "GAME"

    def draw(self, screen):
        screen.fill(BLACK)
        
        if self.state == "MENU":
            title = self.font_big.render("TETRIS PYTHON", True, WHITE)
            msg = self.font_small.render("Pressione ENTER para jogar", True, GRAY)
            
            screen.blit(title, (SCREEN_WIDTH/2 - title.get_width()/2, 200))
            screen.blit(msg, (SCREEN_WIDTH/2 - msg.get_width()/2, 300))

        elif self.state == "GAME" or self.state == "PAUSE":
            # Desenha o jogo centralizado
            if self.game:
                self.game.draw(screen, TOP_LEFT_X, TOP_LEFT_Y)
            
            if self.state == "PAUSE":
                pause_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pause_surf.fill((0, 0, 0, 150)) # Overlay semi-transparente
                txt = self.font_big.render("PAUSE", True, WHITE)
                pause_surf.blit(txt, (SCREEN_WIDTH/2 - txt.get_width()/2, SCREEN_HEIGHT/2))
                screen.blit(pause_surf, (0,0))

        elif self.state == "GAME_OVER":
            # Desenha o jogo ao fundo congelado
            if self.game:
                self.game.draw(screen, TOP_LEFT_X, TOP_LEFT_Y)
            
            # Overlay
            overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 200))
            screen.blit(overlay, (0,0))
            
            txt_over = self.font_big.render("GAME OVER", True, RED)
            txt_score = self.font_small.render(f"Final Score: {self.game.score}", True, WHITE)
            txt_restart = self.font_small.render("ENTER para Reiniciar", True, GRAY)
            
            screen.blit(txt_over, (SCREEN_WIDTH/2 - txt_over.get_width()/2, 200))
            screen.blit(txt_score, (SCREEN_WIDTH/2 - txt_score.get_width()/2, 280))
            screen.blit(txt_restart, (SCREEN_WIDTH/2 - txt_restart.get_width()/2, 350))