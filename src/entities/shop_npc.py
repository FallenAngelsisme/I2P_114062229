import pygame as pg
from src.utils import GameSettings, Direction, Position, PositionCamera, Logger
from src.core import GameManager
from src.sprites.animation import Animation
from src.entities.entity import Entity
from src.core.services import input_manager, scene_manager
from src.sprites.sprite import Sprite


class ShopNPC(Entity):
    detected: bool
    def __init__(self, x, y, game_manager: GameManager, facing: Direction = Direction.DOWN):
        super().__init__(x, y, game_manager)
        self.facing = facing

        # 初始化動畫（四方向，但不播放步行）
        self.animation = Animation(
            "character/ow2.png",
            ["down", "left", "right", "up"],
            4,
           (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE),
        )

        self._set_direction(facing)  # ← 現在 animation 已存在，可以正確切方向

        # 警告符號
        self.warning_sign = Sprite(
            "exclamation.png",
            (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2)
        )
        self.warning_sign.update_pos(Position(
            x + GameSettings.TILE_SIZE // 4,
            y - GameSettings.TILE_SIZE // 2
        ))

        self.detected = False

    # ⭐ NPC 的偵測範圍（跟 enemy trainer 類似，2x2 tiles）
    def _get_interact_rect(self):
        size = GameSettings.TILE_SIZE
        return pg.Rect(
            self.position.x - size,
            self.position.y - size,
            size * 3,
            size * 3
        )

    def _set_direction(self, direction: Direction):
        """只切換站立方向，不播放走路動畫"""
        self.direction = direction

        if self.animation:
            # 依照方向切換 Sprite row
            if direction == Direction.DOWN:
                self.animation.switch("down")
            elif direction == Direction.LEFT:
                self.animation.switch("left")
            elif direction == Direction.RIGHT:
                self.animation.switch("right")
            else:
                self.animation.switch("up")

    def update(self, dt: float):
        # 玩家是否靠近
        self.animation.accumulator = 0

        player = self.game_manager.player
        if not player:
            self.detected = False
            return

        interact_rect = self._get_interact_rect()

        player_rect = pg.Rect(
            player.position.x,
            player.position.y,
            GameSettings.TILE_SIZE,
            GameSettings.TILE_SIZE
        )

        self.detected = interact_rect.colliderect(player_rect)


        if self.detected:
            self.warning_sign.update_pos(Position(
                self.position.x + GameSettings.TILE_SIZE // 4,
                self.position.y - GameSettings.TILE_SIZE // 2
            ))

        self.animation.update_pos(self.position)

    def draw(self, screen, camera: PositionCamera):
        self.animation.draw(screen, camera)

        if self.detected:
            self.warning_sign.draw(screen, camera)

        # debug：畫出偵測範圍
        if GameSettings.DRAW_HITBOXES:
            pg.draw.rect(
                screen,
                (255, 255, 0),
                camera.transform_rect(self._get_interact_rect()),
                2
            )


    @classmethod
    def from_dict(cls, data, game_manager: GameManager):
        facing = Direction[data.get("facing", "DOWN")]
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            facing
        )

    def to_dict(self):
        base = super().to_dict()
        base["type"] = "shop"
        base["facing"] = self.direction.name
        return base
