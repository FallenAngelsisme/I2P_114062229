import random
import pygame as pg
from src.utils import GameSettings, Direction, Position, PositionCamera
from src.core import GameManager
from src.sprites.animation import Animation
from src.entities.entity import Entity
from src.sprites.sprite import Sprite
from src.core.services import input_manager, scene_manager


class TalkNPC(Entity):
    detected: bool

    def __init__(
        self,
        x,
        y,
        game_manager: GameManager,
        dialogues: list[str],
        facing: Direction = Direction.DOWN
    ):
        super().__init__(x, y, game_manager)

        self.dialogues = dialogues
        self.facing = facing
        self.detected = False
        self.type = "talk"
        # 角色動畫（站立）
        self.animation = Animation(
            "character/ow4.png",
            ["down", "left", "right", "up"],
            4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE),
        )
        self._set_direction(facing)

        # 驚嘆號
        self.warning_sign = Sprite(
            "exclamation.png",
            (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2)
        )

    # 偵測範圍
    def _get_interact_rect(self):
        size = GameSettings.TILE_SIZE
        return pg.Rect(
            self.position.x - size,
            self.position.y - size,
            size * 3,
            size * 3
        )

    def _set_direction(self, direction: Direction):
        self.direction = direction
        self.animation.switch(direction.name.lower())

    def update(self, dt: float):
        self.animation.accumulator = 0

        player = self.game_manager.player
        if not player:
            self.detected = False
            return

        player_rect = pg.Rect(
            player.position.x,
            player.position.y,
            GameSettings.TILE_SIZE,
            GameSettings.TILE_SIZE
        )

        self.detected = self._get_interact_rect().colliderect(player_rect)

        if self.detected:
            self.warning_sign.update_pos(Position(
                self.position.x + GameSettings.TILE_SIZE // 4,
                self.position.y - GameSettings.TILE_SIZE // 2
            ))

            # ⭐ 互動鍵（E 或 SPACE）
            if input_manager.key_pressed(pg.K_e):
                self.talk()

        self.animation.update_pos(self.position)

    def talk(self):
        text = random.choice(self.dialogues)

        # 使用你專案裡的對話場景 / 對話框
        scene_manager.change_scene(
            "dialog",
            text=text
        )

    def draw(self, screen, camera: PositionCamera):
        self.animation.draw(screen, camera)

        if self.detected:
            self.warning_sign.draw(screen, camera)

        if GameSettings.DRAW_HITBOXES:
            pg.draw.rect(
                screen,
                (0, 255, 255),
                camera.transform_rect(self._get_interact_rect()),
                2
            )

    @classmethod
    def from_dict(cls, data, game_manager: GameManager):
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            data.get("dialogues", ["Hello there!"]),
            Direction[data.get("facing", "DOWN")]
        )

    def to_dict(self):
        base = super().to_dict()
        base["type"] = "talk"
        base["dialogues"] = self.dialogues
        base["facing"] = self.direction.name
        return base
