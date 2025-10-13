import pgzrun
import sys
import random
from pygame import Rect

# --- CONFIGURAÇÕES ---
WIDTH, HEIGHT = 800, 400
TITLE = "Plataforma dinâmica estilo Mario World"

# --- ESTADOS ---
game_state = "menu"

# --- CONTROLE ---
score = 0
menu_camera_x = 0
menu_speed = 0.5
selected_option = 0
menu_options = ["Começar Jogo", "Mutar/Desmutar Música", "Sair"]

# --- ÁUDIO ---
music_volume = 0.5
music_playing = False
music_muted = False

# ========== CLASSES ==========

class AnimatedCharacter:
    """Classe base para personagens animados"""
    def __init__(self, x, y, frames_dict, scale=3):
        self.actor = Actor(frames_dict["idle"][0], anchor=(0.5, 1))
        self.actor.x = x
        self.actor.bottom = y
        self.actor.scale = scale
        
        self.frames = frames_dict
        self.current_state = "idle"
        self.frame_index = 0
        self.frame_timer = 0
        self.frame_speed = 5
        self.facing_right = True
    
    def update_animation(self):
        """Atualiza a animação do sprite"""
        self.frame_timer += 1
        if self.frame_timer > self.frame_speed:
            self.frame_timer = 0
            frames = self.frames[self.current_state]
            self.frame_index = (self.frame_index + 1) % len(frames)
            
            frame_name = frames[self.frame_index]
            if not self.facing_right and "_left" not in frame_name:
                frame_name += "_left"
            
            self.actor.image = frame_name
    
    def get_rect(self):
        """Retorna o Rect para detecção de colisão"""
        return Rect(self.actor.left, self.actor.top, self.actor.width, self.actor.height)
    
    def draw(self, camera_x=0):
        """Desenha o personagem ajustado pela câmera"""
        original_x = self.actor.x
        self.actor.x -= camera_x
        self.actor.draw()
        self.actor.x = original_x


class Player(AnimatedCharacter):
    """Classe do jogador com física e controles"""
    def __init__(self, x, y):
        frames = {
            "idle": ["player_idle", "player_idle2", "player_idle3"],
            "run": ["player_run1", "player_run2", "player_run3"],
            "jump": ["player_jumping", "player_jumping2", "player_jumping3"]
        }
        super().__init__(x, y, frames)
        
        self.vx = 0
        self.vy = 0
        self.speed = 4
        self.jump_power = -10
        self.gravity = 0.5
        self.on_ground = False
        self.can_jump = True
    
    def handle_input(self):
        """Processa entrada do jogador"""
        moving = False
        
        if keyboard.a:
            self.actor.x -= self.speed
            moving = True
            self.facing_right = False
        
        if keyboard.d:
            self.actor.x += self.speed
            moving = True
            self.facing_right = True
        
        if keyboard.space and self.can_jump and self.on_ground:
            self.vy = self.jump_power
            self.can_jump = False
            try:
                sounds.jump.play()
            except Exception:
                pass
        
        return moving
    
    def apply_physics(self, platforms, world_length, screen_height):
        """Aplica gravidade e colisões"""
        self.vy += self.gravity
        self.actor.y += self.vy
        self.on_ground = False
        
        # Colisão com plataformas
        for plat in platforms:
            if (self.actor.colliderect(plat) and self.vy >= 0 and 
                self.actor.bottom > plat.top and 
                self.actor.bottom - plat.top < 25):
                self.actor.bottom = plat.top
                self.vy = 0
                self.on_ground = True
                self.can_jump = True
        
        # Limite inferior
        if self.actor.bottom > screen_height:
            self.actor.bottom = screen_height
            self.vy = 0
            self.on_ground = True
            self.can_jump = True
        
        # Limites horizontais
        self.actor.x = max(0, min(self.actor.x, world_length))
    
    def update(self, platforms, world_length, screen_height):
        """Atualiza estado do jogador"""
        moving = self.handle_input()
        self.apply_physics(platforms, world_length, screen_height)
        
        # Define estado da animação
        if not self.on_ground:
            self.current_state = "jump"
        elif moving:
            self.current_state = "run"
        else:
            self.current_state = "idle"
        
        self.update_animation()
        
        return self.actor.top > screen_height  # retorna se caiu do mapa
    
    def reset(self, x, y):
        """Reseta posição e física do jogador"""
        self.actor.x = x
        self.actor.bottom = y
        self.vy = 0
        self.vx = 0
        self.on_ground = False
        self.can_jump = True
        self.facing_right = True
        self.current_state = "idle"
        self.frame_index = 0


class Enemy(AnimatedCharacter):
    """Classe dos inimigos com patrulha"""
    def __init__(self, x, y, speed):
        frames = {
            "idle": ["monster1_run", "monster1_run2"],
            "run": ["monster1_run", "monster1_run2", "monster1_run3", "monster1_run4"]
        }
        super().__init__(x, y, frames)
        
        self.speed = speed
        self.current_state = "run"
        self.frame_speed = 15
        self.world_length = 3000
    
    def update(self):
        """Atualiza movimento e animação do inimigo"""
        self.actor.x += self.speed
        
        # Inverte direção nos limites
        if self.actor.left <= 0 or self.actor.right >= self.world_length:
            self.speed *= -1
            self.facing_right = not self.facing_right
        
        self.update_animation()
    
    def check_collision(self, player):
        """Verifica colisão com o jogador"""
        if self.actor.colliderect(player.actor):
            # Jogador mata inimigo ao pular na cabeça
            if player.vy > 0 and player.actor.bottom - self.actor.top < 30:
                sounds.hit.play()
                return "kill_enemy"
            else:
                return "player_hit"
        return None


class Coin(AnimatedCharacter):
    """Classe para moedas coletáveis"""
    def __init__(self, x, y):
        frames = {
            "idle": ["coin_idle1", "coin_idle2", "coin_idle3", "coin_idle4"]
        }
        super().__init__(x, y, frames, scale=1)
        self.frame_speed = 10
        self.actor.scale = 1
    
    def update(self):
        """Atualiza animação da moeda"""
        self.update_animation()

# ========== GERENCIADOR DE JOGO ==========

class GameManager:
    """Gerencia o estado e lógica do jogo"""
    def __init__(self):
        self.player = None
        self.enemies = []
        self.coins = []
        self.platforms = []
        self.camera_x = 0
        self.score = 0
        self.world_length = 3000
        
    def build_level(self):
        """Constrói o nível com plataformas, moedas e inimigos"""
        self.platforms.clear()
        self.coins.clear()
        self.enemies.clear()
        
        # Chão
        for i in range(100):
            self.platforms.append(Actor('chao', topleft=(i * 32, 370)))
        
        # Plataformas
        platform_positions = [
            (300, 300), (310, 300), (600, 250), (610, 250),
            (900, 320), (1200, 270), (1600, 230), (2000, 300),
            (2400, 250), (2700, 200), (450, 270), (750, 220),
            (1050, 290), (1090, 290), (1350, 240), (1750, 200),
            (2150, 270), (2200, 270), (2550, 220), (2850, 170),
            (500, 180), (950, 150), (1400, 120), (1800, 100)
        ]
        
        for pos in platform_positions:
            self.platforms.append(Actor('platform', topleft=pos))
        
        # Moedas
        coin_positions = [
            (320, 270), (620, 220), (1250, 240), (1650, 200),
            (2050, 270), (2450, 220), (2750, 170)
        ]
        
        for pos in coin_positions:
            self.coins.append(Coin(pos[0], pos[1]))
        
        # Inimigos
        enemy_data = [(800, 366, 2), (1500, 366, -2), (2300, 366, 1.5)]
        for x, y, speed in enemy_data:
            self.enemies.append(Enemy(x, y, speed))
    
    def reset_game(self):
        """Reseta o jogo para o estado inicial"""
        self.build_level()
        self.player = Player(80, 370)
        self.camera_x = 0
        self.score = 0
    
    def update_camera(self):
        """Atualiza posição da câmera"""
        self.camera_x = max(0, min(self.player.actor.x - WIDTH // 2,self.world_length - WIDTH))
    
    def update(self):
        """Atualiza todos os elementos do jogo"""
        fell_off = self.player.update(self.platforms, self.world_length, HEIGHT)
        if fell_off:
            return "game_over"
        
        # Atualiza inimigos
        for enemy in self.enemies[:]:
            enemy.update()
            result = enemy.check_collision(self.player)
            
            if result == "kill_enemy":
                self.enemies.remove(enemy)
                self.player.vy = self.player.jump_power / 1.5
                self.score += 50
            elif result == "player_hit":
                return "game_over"
        
        # Atualiza e coleta moedas
        for coin in self.coins[:]:
            coin.update()
            if self.player.actor.colliderect(coin.actor):
                self.coins.remove(coin)
                self.score += 10
                sounds.coin.play()
        
        # Atualiza câmera
        self.update_camera()
        
        # Verifica vitória
        if self.player.actor.x >= self.world_length - 100:
            return "win"
        
        return "playing"
    
    def draw(self):
        """Desenha todos os elementos do jogo"""
        draw_background(self.camera_x)
        
        # Desenha plataformas
        for plat in self.platforms:
            plat.x -= self.camera_x
            plat.draw()
            plat.x += self.camera_x
        
        # Desenha moedas
        for coin in self.coins:
            coin.draw(self.camera_x)
        
        # Desenha inimigos
        for enemy in self.enemies:
            enemy.draw(self.camera_x)
        
        # Desenha jogador
        self.player.draw(self.camera_x)
        
        # HUD
        screen.draw.text(f"PONTOS: {self.score}", (10, 10), fontsize=30, color="black")

# ========== FUNÇÕES GLOBAIS ==========

game_manager = GameManager()

def start_music():
    global music_playing
    if not music_playing and not music_muted:
        music.play('bg.wav')
        music.set_volume(music_volume)
        music_playing = True

def toggle_music():
    global music_muted, music_playing
    music_muted = not music_muted
    if music_muted:
        music.stop()
    else:
        start_music()

def draw_background(offset=0):
    bg_w = images.background.get_width()
    bg_h = images.background.get_height()
    parallax = int(offset * 0.5) % bg_w
    for x in range(-bg_w, WIDTH + bg_w, bg_w):
        for y in range(0, HEIGHT, bg_h):
            screen.blit("background", (x - parallax, y))

def handle_menu_input():
    global game_state
    if keyboard.RETURN:
        opt = menu_options[selected_option]
        if opt == "Começar Jogo":
            game_manager.reset_game()
            game_state = "playing"
        elif opt == "Mutar/Desmutar Música":
            toggle_music()
        elif opt == "Sair":
            sys.exit()

def on_key_down(key):
    global selected_option
    if game_state == "menu":
        if key == keys.UP:
            selected_option = (selected_option - 1) % len(menu_options)
            sounds.select_effect.play()
        elif key == keys.DOWN:
            selected_option = (selected_option + 1) % len(menu_options)
            ounds.select_effect.play()
                


def draw():
    screen.fill((0, 0, 0))
    
    if game_state == "menu":
        draw_menu()
    elif game_state == "playing":
        start_music()
        game_manager.draw()
    elif game_state == "game_over":
        game_manager.draw()
        screen.draw.text("GAME OVER", center=(WIDTH/2, HEIGHT/2-20), fontsize=60, color="red")
        screen.draw.text("Pressione ESPAÇO para voltar ao menu", center=(WIDTH/2, HEIGHT/2+30), fontsize=30, color="black")
    elif game_state == "win":
        game_manager.draw()
        screen.draw.text("VOCÊ VENCEU!", center=(WIDTH/2, HEIGHT/2-20), fontsize=60, color="gold")
        screen.draw.text("Pressione ESPAÇO para voltar ao menu", center=(WIDTH/2, HEIGHT/2+30), fontsize=30, color="black")


def draw_menu():
    draw_background(menu_camera_x)
    
    # Desenha elementos do fundo animado
    for plat in game_manager.platforms:
        plat.x -= menu_camera_x
        plat.draw()
        plat.x += menu_camera_x
    
    for coin in game_manager.coins:
        coin.draw(menu_camera_x)
    
    for enemy in game_manager.enemies:
        enemy.draw(menu_camera_x)
    
    screen.draw.text("PLATAFORMA AVENTURA", center=(WIDTH/2, 100), fontsize=50, color="black")
    
    for i, opt in enumerate(menu_options):
        color = "yellow" if i == selected_option else "white" 
        screen.draw.text(opt, center=(WIDTH/2, 220+i*50), fontsize=40, color=color)
    
    screen.draw.text("Use ↑ ↓ | ENTER selecionar", center=(WIDTH/2, HEIGHT-40), fontsize=25, color="darkblue")


def update():
    global game_state, menu_camera_x
    
    if game_state == "menu":
        menu_camera_x = (menu_camera_x + menu_speed) % (3000 - WIDTH)
        handle_menu_input()
        
        # Atualiza animações do menu
        for coin in game_manager.coins:
            coin.update()
        for enemy in game_manager.enemies:
            enemy.update()
    
    elif game_state == "playing":
        start_music()
        if keyboard.escape:
            game_state = "menu"
            return
        
        result = game_manager.update()
        if result != "playing":
            game_state = result
    
    elif game_state in ("game_over", "win"):
        if keyboard.space:
            game_state = "menu"

game_manager.reset_game()
pgzrun.go()