import pgzrun
import sys

# --- CONFIGURAÇÕES ---
WIDTH, HEIGHT = 800, 400
TITLE = "Plataforma dinâmica estilo Mario World"

# --- ÁUDIO ---
music_volume = 0.5
music_playing = False
music_muted = False

# --- ESTADOS ---
game_state = "menu"

# --- JOGADOR ---
player = Actor('player_idle', anchor=(0.5, 1))
player.vx = 0
player.scale = 3

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
can_jump = True

# --- MUNDO ---
camera_x = 0
WORLD_LENGTH = 3000

# --- OBJETOS ---
platforms, coins, enemies, enemy_speeds = [], [], [], []
on_ground, score = False, 0

# --- MENU ---
menu_camera_x, menu_speed = 0, 0.5
selected_option = 0
menu_options = ["Começar Jogo", "Mutar/Desmutar Som", "Sair do Jogo"]

# --- FUNÇÕES ---
def build_level():
    platforms.clear(), coins.clear()
    for i in range(100):
        platforms.append(Actor('chao', topleft=(i * 32, 370)))

    for pos in [(300, 300), (600, 250), (900, 320), (1200, 270),
                (1600, 230), (2000, 300), (2400, 250), (2700, 200)]:
        platforms.append(Actor('platform', topleft=pos))

    for pos in [(320, 270), (620, 220), (1250, 240), (1650, 200),
                (2050, 270), (2450, 220), (2750, 170)]:
        coins.append(Actor('coin', topleft=pos))


def restart_game():
    global player_vy, score, camera_x, player_frame_index, player_frame_timer
    global player_state, facing_right, can_jump

    build_level()
    player.bottom, player.x = 370, 80
    player_vy, camera_x, score = 0, 0, 0
    facing_right, can_jump = True, True
    enemies.clear(), enemy_speeds.clear()

    for pos, speed in zip([800, 1500, 2300], [2, -2, 1.5]):
        e = Actor("enemy_run2", topleft=(pos, 360))
        e.frames, e.frame_index, e.frame_timer, e.scale = ["enemy_run2", "enemy_run3"], 0, 0, 3
        enemies.append(e)
        enemy_speeds.append(speed)

    player_frame_index = player_frame_timer = 0
    player_state = "idle"


def start_music():
    global music_playing
    if not music_playing and not music_muted:
        music.play('bg.wav')
        music.set_volume(music_volume)
        music_playing = True


def toggle_music():
    global music_muted
    music_muted = not music_muted
    if music_muted:
        music.stop()
    else:
        music.play('bg.wav')
        music.set_volume(music_volume)


def draw_background(offset=0):
    bg_w, bg_h = images.background.get_width(), images.background.get_height()
    parallax = int(offset * 0.5) % bg_w
    for x in range(-bg_w, WIDTH + bg_w, bg_w):
        for y in range(0, HEIGHT, bg_h):
            screen.blit("background", (x - parallax, y))


def handle_menu_input():
    global game_state
    if keyboard.RETURN:
        opt = menu_options[selected_option]
        if opt == "Começar Jogo":
            restart_game()
            game_state = "playing"
        elif opt == "Mutar/Desmutar Som":
            toggle_music()
        elif opt == "Sair do Jogo":
            sys.exit()


def handle_gameplay():
    global player_vy, on_ground, camera_x, score, game_state, can_jump
    global player_frame_index, player_frame_timer, player_state, facing_right

    if keyboard.escape:
        game_state = "menu"
        return

    left, right, jump = keyboard.left, keyboard.right, keyboard.space
    moving = False
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
        can_jump = False

    player_vy += gravity
    player.y += player_vy
    on_ground = False

    for plat in platforms:
        if player.colliderect(plat) and player_vy >= 0 and player.bottom > plat.top and player.bottom - plat.top < 25:
            player.bottom, player_vy, on_ground, can_jump = plat.top, 0, True, True

    if player.bottom > HEIGHT:
        player.bottom, player_vy, on_ground, can_jump = HEIGHT, 0, True, True

    for i in range(len(enemies) - 1, -1, -1):
        e = enemies[i]
        e.x += enemy_speeds[i]
        if e.left <= 0 or e.right >= WORLD_LENGTH:
            enemy_speeds[i] *= -1
        e.frame_timer += 1
        if e.frame_timer > 15:
            e.frame_index = (e.frame_index + 1) % len(e.frames)
            e.image = e.frames[e.frame_index]
            e.frame_timer = 0

        if player.colliderect(e):
            if player_vy > 0 and player.bottom - e.top < 30:
                enemies.pop(i)
                enemy_speeds.pop(i)
                player_vy = jump_power / 1.5
                score += 50
            else:
                game_state = "game_over"
                return

    for c in coins[:]:
        if player.colliderect(c):
            coins.remove(c)
            score += 10

    if player.top > HEIGHT:
        game_state = "game_over"
    if player.x >= WORLD_LENGTH - 100:
        game_state = "win"

    camera_x = max(0, min(player.x - WIDTH // 2, WORLD_LENGTH - WIDTH))

    player_state = "jump" if not on_ground else "run" if moving else "idle"
    player_frame_timer += 1
    if player_frame_timer > 5:
        player_frame_index = (player_frame_index + 1) % len(player_frames[player_state])
        frame_name = player_frames[player_state][player_frame_index]
        player.image = frame_name + ("_left" if not facing_right else "")
        player_frame_timer = 0


def on_key_down(key):
    global selected_option
    if game_state == "menu":
        if key == keys.UP:
            selected_option = (selected_option - 1) % len(menu_options)
        if key == keys.DOWN:
            selected_option = (selected_option + 1) % len(menu_options)


# --- DESENHO ---
def draw():
    screen.fill((0, 0, 0))
    if game_state == "menu":
        draw_menu()
    elif game_state == "playing":
        start_music()
        draw_game()
    elif game_state == "game_over":
        draw_game()
        screen.draw.text("GAME OVER", center=(WIDTH/2, HEIGHT/2-20), fontsize=60, color="red")
        screen.draw.text("Pressione ESPAÇO para voltar ao menu", center=(WIDTH/2, HEIGHT/2+30), fontsize=30, color="black")
    elif game_state == "win":
        draw_game()
        screen.draw.text("VOCÊ VENCEU!", center=(WIDTH/2, HEIGHT/2-20), fontsize=60, color="gold")
        screen.draw.text("Pressione ESPAÇO para voltar ao menu", center=(WIDTH/2, HEIGHT/2+30), fontsize=30, color="black")


def draw_menu():
    draw_background(menu_camera_x)
    for lst in (platforms, coins, enemies):
        for obj in lst:
            obj.x -= menu_camera_x
            obj.draw()
            obj.x += menu_camera_x

    screen.draw.text("PLATAFORMA AVENTURA", center=(WIDTH/2, 100), fontsize=50, color="black")
    for i, opt in enumerate(menu_options):
        color = "yellow" if i == selected_option else "white"
        screen.draw.text(opt, center=(WIDTH/2, 200+i*50), fontsize=40, color=color)
    screen.draw.text("Use ↑ ↓ | ENTER selecionar", center=(WIDTH/2, HEIGHT-40), fontsize=25, color="darkblue")


def draw_game():
    draw_background(camera_x)
    for lst in (platforms, coins, enemies):
        for obj in lst:
            obj.x -= camera_x
            obj.draw()
            obj.x += camera_x
    player.x -= camera_x
    player.draw()
    player.x += camera_x
    screen.draw.text(f"PONTOS: {score}", (10, 10), fontsize=30, color="black")


def update():
    global game_state, menu_camera_x
    if game_state == "menu":
        menu_camera_x = (menu_camera_x + menu_speed) % (WORLD_LENGTH - WIDTH)
        handle_menu_input()
    elif game_state == "playing":
        start_music()
        handle_gameplay()
    elif game_state in ("game_over", "win"):
        if keyboard.space:
            restart_game()
            game_state = "menu"


# --- INICIALIZAÇÃO ---
restart_game()
pgzrun.go()
