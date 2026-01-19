# src/input_handler.py
import pygame

class InputHandler:
    def __init__(self):
        pygame.joystick.init()
        self.joysticks = {} # Map id_joystick -> objeto joystick
        self.players_map = {} # Map id_player (0-3) -> id_device (guid/id)
        
        # Detecta joysticks já conectados no boot
        self._detect_joysticks()

    def _detect_joysticks(self):
        """Reinicia e detecta controles conectados."""
        self.joysticks = {}
        count = pygame.joystick.get_count()
        for i in range(count):
            joy = pygame.joystick.Joystick(i)
            joy.init()
            self.joysticks[joy.get_instance_id()] = joy
            print(f"Joystick detectado: {joy.get_name()} (ID: {joy.get_instance_id()})")

    def map_player_to_device(self, player_id, device_id):
        """Associa um jogador a um dispositivo (Teclado ou Joystick ID)."""
        self.players_map[player_id] = device_id
        print(f"Player {player_id + 1} associado ao device {device_id}")

    def get_action(self, player_id):
        """
        Retorna um dicionário de ações para um jogador específico neste frame.
        Ex: {'left': True, 'rotate': False, ...}
        """
        actions = {'left': False, 'right': False, 'rotate': False, 'drop': False, 'start': False}
        device_id = self.players_map.get(player_id)

        if device_id is None:
            return actions

        keys = pygame.key.get_pressed()

        # Input via Teclado (Assumindo que 'keyboard' é o device_id)
        if device_id == 'keyboard':
            if keys[pygame.K_LEFT]: actions['left'] = True
            if keys[pygame.K_RIGHT]: actions['right'] = True
            if keys[pygame.K_UP]: actions['rotate'] = True
            if keys[pygame.K_DOWN]: actions['drop'] = True
            if keys[pygame.K_RETURN]: actions['start'] = True
        
        # Input via Joystick
        elif isinstance(device_id, int) and device_id in self.joysticks:
            joy = self.joysticks[device_id]
            # Mapeamento genérico (pode variar por controle, ideal configurar depois)
            # Eixos (D-PAD ou Analógico)
            if joy.get_axis(0) < -0.5: actions['left'] = True
            if joy.get_axis(0) > 0.5: actions['right'] = True
            # Botões
            if joy.get_button(0): actions['rotate'] = True # A / X
            if joy.get_button(1): actions['drop'] = True   # B / O
            if joy.get_button(7): actions['start'] = True  # Start
            
            # Hat (D-pad digital comum em alguns controles)
            if joy.get_numhats() > 0:
                hat = joy.get_hat(0)
                if hat[0] == -1: actions['left'] = True
                if hat[0] == 1: actions['right'] = True

        return actions