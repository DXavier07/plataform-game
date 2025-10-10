import pgzrun
import sys

# --- CONFIGURAÇÕES ---
WIDTH = 800
HEIGHT = 400
TITLE = "Plataforma com Menu - Estilo Mario"

# --- ÁUDIO ---
music_volume = 0.5
music_playing = False

# --- ESTADOS DO JOGO ---
game_state = "menu"

# --- JOGADOR ---
player = Actor('player_idle', anchor=(0.5, 1))
player.vx = 0
player.scale = 3

# --- ANIMAÇÃO ---
player_frames = {
    "idle": ["player_idle"],
    "run": ["player_run1", "player_run2", "player_run3"],
    "jump": ["player_jump"]
}
player_frame_index = 0
player_frame_timer = 0
player_state = "idle"
facing_right = True

# --- MOVIMENTO ---
player_vy = 0
player_speed = 4
jump_power = -10
gravity = 0.5
can_jump = True  # evita duplo pulo pra corrigir bug de morte

# --- MUNDO ---
camera_x = 0
WORLD_LENGTH = 3000

# --- LISTAS ---
platforms = []
coins = []
enemies = []
enemy_speeds = []

# --- CONTROLE ---
on_ground = False
score = 0
menu_camera_x = 0
menu_speed = 0.5
use_wasd = False
settings_options = ["Volume +", "Volume -", "Trocar Controles (Setas/WASD)"]
selected_setting = 0
selected_option = 0
menu_options = ["Começar Jogo", "Configurações", "Sair"]

# --- FUNÇÕES ---
def build_level():
    platforms.clear()
    coins.clear()

    # Chão
    for i in range(100):
        platforms.append(Actor('chao', topleft=(i * 32, 370)))

    # Plataformas
    platform_positions = [
        (300, 300), (600, 250), (900, 320), (1200, 270),
        (1600, 230), (2000, 300), (2400, 250), (2700, 200)
    ]
    for pos in platform_positions:
        platforms.append(Actor('platform', topleft=pos))

    # Moedas
    coin_positions = [
        (320, 270), (620, 220), (1250, 240), (1650, 200),
        (2050, 270), (2450, 220), (2750, 170)
    ]
    for pos in coin_positions:
        coins.append(Actor('coin', topleft=pos))


def restart_game():
    global player_vy, score, camera_x, player_frame_index, player_frame_timer, player_state, facing_right, can_jump

    build_level()

    player.bottom = 370
    player.x = 80
    player_vy = 0
    score = 0
    camera_x = 0
    facing_right = True
    can_jump = True

    enemies.clear()
    enemy_speeds.clear()

    # --- CRIAÇÃO DOS INIMIGOS ---
    enemy_positions = [800, 1500, 2300]
    enemy_directions = [2, -2, 1.5]
    for pos, speed in zip(enemy_positions, enemy_directions):
        enemy = Actor("enemy_run2", topleft=(pos, 360))
        enemy.frame_timer = 0
        enemy.frame_index = 0
        enemy.frames = ["enemy_run2", "enemy_run3"]
        enemy.scale = 3
        enemies.append(enemy)
        enemy_speeds.append(speed)

    player_frame_index = 0
    player_frame_timer = 0
    player_state = "idle"


def start_music():
    global music_playing
    if not music_playing:
        music.play('bg.wav')
        music.set_volume(music_volume)
        music_playing = True


# --- FUNÇÃO PARA DESENHAR O FUNDO ---
def draw_background(offset=0):
    bg_width = images.background.get_width()
    bg_height = images.background.get_height()
    parallax_offset = int(offset * 0.5) % bg_width

    for x in range(-bg_width, WIDTH + bg_width, bg_width):
        for y in range(0, HEIGHT, bg_height):
            screen.blit("background", (x - parallax_offset, y))


def handle_menu_input():
    global game_state
    if keyboard.RETURN:
        option = menu_options[selected_option]
        if option == "Começar Jogo":
            restart_game()
            game_state = "playing"
        elif option == "Configurações":
            game_state = "settings"
        elif option == "Sair":
            sys.exit()


def handle_settings_input():
    global music_volume, use_wasd, game_state
    if keyboard.RETURN:
        option = settings_options[selected_setting]
        if option == "Volume +":
            music_volume = min(1.0, music_volume + 0.1)
            music.set_volume(music_volume)
        elif option == "Volume -":
            music_volume = max(0.0, music_volume - 0.1)
            music.set_volume(music_volume)
        elif option == "Trocar Controles (Setas/WASD)":
            use_wasd = not use_wasd
    if keyboard.escape or keyboard.space:
        game_state = "menu"


def handle_gameplay():
    global player_vy, on_ground, camera_x, score, game_state, can_jump
    global player_frame_index, player_frame_timer, player_state, facing_right

    if keyboard.escape:
        game_state = "menu"
        return

    moving = False
    if use_wasd:
        left, right, jump = keyboard.a, keyboard.d, keyboard.w
    else:
        left, right, jump = keyboard.left, keyboard.right, keyboard.space

    if left:
        player.x -= player_speed
        moving = True
        facing_right = False
    if right:
        player.x += player_speed
        moving = True
        facing_right = True
    if jump and can_jump and on_ground:
        player_vy = jump_power
        can_jump = False  # impede duplo pulo

    player_vy += gravity
    player.y += player_vy
    on_ground = False

    # --- COLISÕES COM PLATAFORMAS ---
    for plat in platforms:
        if player.colliderect(plat):
            # Verifica se colidiu por cima (chão)
            if player_vy >= 0 and player.bottom > plat.top and player.bottom - plat.top < 25:
                player.bottom = plat.top
                player_vy = 0
                on_ground = True
                can_jump = True

    # --- NÃO CAIA PELO CHÃO ---
    if player.bottom > HEIGHT:
        player.bottom = HEIGHT
        player_vy = 0
        on_ground = True
        can_jump = True

    # --- INIMIGOS ---
    for i in range(len(enemies) - 1, -1, -1):
        enemy = enemies[i]
        enemy.x += enemy_speeds[i]

        # Limites do mundo
        if enemy.left <= 0 or enemy.right >= WORLD_LENGTH:
            enemy_speeds[i] *= -1

        # --- ANIMAÇÃO DOS INIMIGOS ---
        enemy.frame_timer += 1
        if enemy.frame_timer > 15:
            enemy.frame_index = (enemy.frame_index + 1) % len(enemy.frames)
            enemy.image = enemy.frames[enemy.frame_index]
            enemy.frame_timer = 0

        # --- COLISÃO COM JOGADOR ---
        if player.colliderect(enemy):
            # jogador mata inimigo pular na cabeça dele
            if player_vy > 0 and player.bottom - enemy.top < 30:
                enemies.pop(i)
                enemy_speeds.pop(i)
                player_vy = jump_power / 1.5
                score += 50
            else:
                game_state = "game_over"
                return

    # --- MOEDAS ---
    for coin in coins[:]:
        if player.colliderect(coin):
            coins.remove(coin)
            score += 10

    # --- CONDIÇÕES DE DERROTA/VITÓRIA ---
    if player.top > HEIGHT:
        game_state = "game_over"
    if player.x >= WORLD_LENGTH - 100:
        game_state = "win"

    # --- CÂMERA ---
    camera_x = max(0, min(player.x - WIDTH // 2, WORLD_LENGTH - WIDTH))

    # --- ANIMAÇÃO DO JOGADOR ---
    if not on_ground:
        player_state = "jump"
    elif moving:
        player_state = "run"
    else:
        player_state = "idle"

    player_frame_timer += 1
    if player_frame_timer > 5:
        player_frame_index = (player_frame_index + 1) % len(player_frames[player_state])
        frame_name = player_frames[player_state][player_frame_index]
        if not facing_right:
            frame_name += "_left"
        player.image = frame_name
        player_frame_timer = 0


def on_key_down(key):
    global selected_option, selected_setting
    if game_state == "menu":
        if key == keys.UP:
            selected_option = (selected_option - 1) % len(menu_options)
        if key == keys.DOWN:
            selected_option = (selected_option + 1) % len(menu_options)
    elif game_state == "settings":
        if key == keys.UP:
            selected_setting = (selected_setting - 1) % len(settings_options)
        if key == keys.DOWN:
            selected_setting = (selected_setting + 1) % len(settings_options)


# --- DESENHO ---
def draw():
    screen.fill((0, 0, 0))
    if game_state == "menu":
        draw_menu()
    elif game_state == "settings":
        draw_settings()
    elif game_state == "playing":
        start_music()
        draw_game()
    elif game_state == "game_over":
        draw_game()
        screen.draw.text("GAME OVER", center=(WIDTH / 2, HEIGHT / 2 - 20), fontsize=60, color="red")
        screen.draw.text("Pressione ESPAÇO para voltar ao menu", center=(WIDTH / 2, HEIGHT / 2 + 30), fontsize=30, color="black")
    elif game_state == "win":
        draw_game()
        screen.draw.text("VOCÊ VENCEU!", center=(WIDTH / 2, HEIGHT / 2 - 20), fontsize=60, color="gold")
        screen.draw.text("Pressione ESPAÇO para voltar ao menu", center=(WIDTH / 2, HEIGHT / 2 + 30), fontsize=30, color="black")


def draw_menu():
    draw_background(menu_camera_x)
    for plat in platforms:
        plat.x -= menu_camera_x
        plat.draw()
        plat.x += menu_camera_x

    for coin in coins:
        coin.x -= menu_camera_x
        coin.draw()
        coin.x += menu_camera_x

    for enemy in enemies:
        enemy.x -= menu_camera_x
        enemy.draw()
        enemy.x += menu_camera_x

    screen.draw.text("PLATAFORMA AVENTURA", center=(WIDTH / 2, 100), fontsize=50, color="black")
    for i, option in enumerate(menu_options):
        color = "yellow" if i == selected_option else "white"
        screen.draw.text(option, center=(WIDTH / 2, 200 + i * 50), fontsize=40, color=color)
    screen.draw.text("Use ↑ ↓ para navegar | ENTER para selecionar", center=(WIDTH / 2, HEIGHT - 40), fontsize=25, color="darkblue")


def draw_settings():
    screen.fill((30, 30, 60))
    screen.draw.text("CONFIGURAÇÕES", center=(WIDTH / 2, 100), fontsize=50, color="white")
    for i, option in enumerate(settings_options):
        color = "yellow" if i == selected_setting else "white"
        screen.draw.text(option, center=(WIDTH / 2, 200 + i * 50), fontsize=35, color=color)
    screen.draw.text(f"Volume atual: {int(music_volume * 100)}%", center=(WIDTH / 2, HEIGHT - 80), fontsize=25, color="lightgray")
    screen.draw.text(f"Controles: {'WASD' if use_wasd else 'Setas'}", center=(WIDTH / 2, HEIGHT - 50), fontsize=25, color="lightgray")
    screen.draw.text("Use ↑ ↓ para navegar | ENTER selecionar | ESC/ESPACO voltar", center=(WIDTH / 2, HEIGHT - 20), fontsize=20, color="lightgray")


def draw_game():
    draw_background(camera_x)

    for plat in platforms:
        plat.x -= camera_x
        plat.draw()
        plat.x += camera_x

    for coin in coins:
        coin.x -= camera_x
        coin.draw()
        coin.x += camera_x

    for enemy in enemies:
        enemy.x -= camera_x
        enemy.draw()
        enemy.x += camera_x

    player.x -= camera_x
    player.draw()
    player.x += camera_x

    screen.draw.text(f"PONTOS: {score}", (10, 10), fontsize=30, color="black")


def update():
    global game_state, menu_camera_x
    if game_state == "menu":
        menu_camera_x += menu_speed
        if menu_camera_x > WORLD_LENGTH - WIDTH:
            menu_camera_x = 0
        handle_menu_input()
    elif game_state == "settings":
        handle_settings_input()
    elif game_state == "playing":
        start_music()
        handle_gameplay()
    elif game_state in ["game_over", "win"]:
        if keyboard.space:
            restart_game()
            game_state = "menu"


# --- INICIALIZAÇÃO ---
restart_game()
pgzrun.go()
