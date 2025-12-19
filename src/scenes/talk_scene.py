import pygame
from src.scenes.scene import Scene
from src.core.services import input_manager, scene_manager
from src.utils import Logger


class TalkScene(Scene):
    def __init__(self, text: str | list[str]):
        super().__init__()

        # ===== 對話資料 =====
        if isinstance(text, list):
            self.dialogues = text
            self.current_dialog_index = 0
            self.text = self.dialogues[0]
        else:
            self.dialogues = None
            self.current_dialog_index = 0
            self.text = text

        self.font = pygame.font.Font("assets/fonts/Minecraft.ttf", 36)
        self.hint_font = pygame.font.Font("assets/fonts/Minecraft.ttf", 22)

        self.screen_width = 1270
        self.screen_height = 720

        # ===== 背景圖 =====
        try:
            self.background = pygame.image.load(
                "assets/images/backgrounds/background1.png"
            ).convert()
            self.background = pygame.transform.scale(
                self.background,
                (self.screen_width, self.screen_height)
            )
        except Exception as e:
            Logger.error(f"Background load failed: {e}")
            self.background = None

        # ===== 人物第一格（鎖定）=====
        try:
            sheet = pygame.image.load(
                "assets/images/character/ow4.png"
            ).convert_alpha()

            tile = 32
            first_frame = sheet.subsurface((0, 0, tile, tile))
            self.character_img = pygame.transform.scale(first_frame, (700, 700))
        except Exception as e:
            Logger.error(f"Character image load failed: {e}")
            self.character_img = None

        # ===== SPACE 提示閃爍 =====
        self.hint_timer = 0
        self.show_hint = True

    def update(self, dt):
        # SPACE 提示閃爍
        self.hint_timer += dt
        if self.hint_timer > 0.5:
            self.show_hint = not self.show_hint
            self.hint_timer = 0

        if input_manager.key_pressed(pygame.K_SPACE):
            if self.dialogues:
                self.current_dialog_index += 1
                if self.current_dialog_index < len(self.dialogues):
                    self.text = self.dialogues[self.current_dialog_index]
                else:
                    scene_manager.change_scene("game")
            else:
                scene_manager.change_scene("game")

    def draw(self, screen):
        # ===== 背景 =====
        if self.background:
            screen.blit(self.background, (0, 0))
        else:
            screen.fill((40, 40, 60))

        # ===== 暗化遮罩（輕）=====
        overlay = pygame.Surface(screen.get_size(), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 70))
        screen.blit(overlay, (0, 0))

        # ===== 人物圖（中央）=====
        if self.character_img:
            x = (self.screen_width - 700) // 2
            y = (self.screen_height - 700) // 2 - 40
            screen.blit(self.character_img, (x, y))

        # ===== 對話框 =====
        box_rect = pygame.Rect(
            80,
            self.screen_height - 240,
            self.screen_width - 160,
            180
        )

        # 外框
        pygame.draw.rect(screen, (20, 20, 20), box_rect, border_radius=18)

        # 內框（半透明）
        inner = pygame.Surface((box_rect.width - 8, box_rect.height - 8), pygame.SRCALPHA)
        inner.fill((30, 30, 45, 220))
        screen.blit(inner, (box_rect.x + 4, box_rect.y + 4))

        # ===== 對話文字 =====
        text_surface = self.font.render(self.text, True, (235, 235, 235))
        screen.blit(
            text_surface,
            (box_rect.x + 40, box_rect.y + 45)
        )

        # ===== SPACE 提示 =====
        if self.show_hint:
            hint = self.hint_font.render("SPACE ▶", True, (200, 200, 200))
            screen.blit(
                hint,
                (box_rect.right - 140, box_rect.bottom - 40)
            )
