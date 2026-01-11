# 👾 PyGame Platformer: Knight's Adventure

> Um estudo prático sobre desenvolvimento de jogos 2D, física e loop de eventos com Python.

![Python](https://img.shields.io/badge/Python-3.10%2B-blue)
![Pygame](https://img.shields.io/badge/Engine-Pygame-yellow)
![License](https://img.shields.io/badge/License-MIT-green)

## 📖 Sobre o Projeto

Este projeto é uma implementação de um jogo de plataforma side-scroller (estilo Mario/Metroidvania) construído do zero. O objetivo principal foi aplicar conceitos de **Programação Orientada a Objetos (POO)** na estruturação de entidades de jogo (Player, Inimigos, Cenário).

Diferente de engines prontas (Unity/Godot), aqui toda a lógica de gravidade, detecção de colisão e gerenciamento de estados foi escrita manualmente em Python.

---

## ⚙️ Destaques Técnicos

O que foi implementado no código:

* **Game Loop Customizado:** Controle manual de FPS e atualização de frames.
* **Sistema de Sprites:** Uso da classe `pygame.sprite.Sprite` para gerenciar animações e grupos de renderização.
* **Física de Pulo:** Implementação de vetores para simular gravidade e inércia do personagem.
* **Gerenciamento de Assets:** Carregamento modular de sons (`/sounds`), músicas (`/music`) e imagens (`/images`) para não sobrecarregar a memória.
* **Colisão Pixel-Perfect:** Lógica para interações precisas entre o Cavaleiro e os Slimes.

---

## 📂 Arquitetura de Arquivos

A organização do projeto segue o padrão MVC simplificado para jogos:

```text
plataform-game/
├── projeto.py      # ENTRY POINT: Contém o Loop Principal e Inicialização
├── sprites/        # Classes dos Personagens (Knight, Enemy) e Animações
├── images/         # Tilesets, Backgrounds e UI
├── sounds/         # SFX (Pulo, Hit, Game Over)
├── music/          # Trilha sonora em loop
└── fonts/          # Tipografia personalizada
