# main.py
import pygame
import sys
from src.config import *
from src.game_manager import GameManager

def main():
    pygame.init()
    screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
    pygame.display.set_caption("Tetris Python")
    clock = pygame.time.Clock()

    game_manager = GameManager()

    running = True
    while running:
        dt = clock.tick(FPS) / 1000.0  # Delta time em segundos

        # 1. Event Handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            
            if event.type == pygame.JOYDEVICEADDED or event.type == pygame.JOYDEVICEREMOVED:
                game_manager.input_handler._detect_joysticks()
            
            # Hack rápido para fechar com ESC no menu
            if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE and game_manager.state == "MENU":
                running = False

        # 2. Update (passando dt)
        game_manager.update(dt)

        # 3. Draw
        game_manager.draw(screen)

        pygame.display.flip()

    pygame.quit()
    sys.exit()

if __name__ == "__main__":
    main()