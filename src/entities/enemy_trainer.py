from __future__ import annotations
import pygame
from enum import Enum
from dataclasses import dataclass
from typing import override

from .entity import Entity
from src.sprites import Sprite
from src.core import GameManager
from src.core.services import input_manager, scene_manager
from src.utils import GameSettings, Direction, Position, PositionCamera


class EnemyTrainerClassification(Enum):
    STATIONARY = "stationary" #固定不動的 NPC
    MOVING = "moving"
 
@dataclass
class IdleMovement: #????damnnn我可以加移動敵人，臣妾做不到
    def update(self, enemy, dt):
        return

@dataclass
class PatrolMovement:
    speed: float = 1.2 * GameSettings.TILE_SIZE   # 每秒移動速度
    direction: Direction = Direction.LEFT         # 初始方向
    distance: float = 0                           # 已走距離（像素）
    max_tiles: int = 2                            # 最大巡邏格數

    def update(self, enemy: "EnemyTrainer", dt: float) -> None:
        step = self.speed * dt
        enemy_rect = pygame.Rect(enemy.position.x, enemy.position.y,
                                 GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)

        # 水平巡邏
        if self.direction == Direction.LEFT:
            enemy.position.x -= step
            self.distance += step

            if self.distance >= self.max_tiles * GameSettings.TILE_SIZE:
                self.direction = Direction.RIGHT
                self.distance = 0
                enemy._set_direction(Direction.RIGHT)

        elif self.direction == Direction.RIGHT:
            enemy.position.x += step
            self.distance += step

            if self.distance >= self.max_tiles * GameSettings.TILE_SIZE:
                self.direction = Direction.LEFT
                self.distance = 0
                enemy._set_direction(Direction.LEFT)

        # 更新動作位置
        enemy.animation.update_pos(enemy.position)


class EnemyTrainer(Entity):
    classification: EnemyTrainerClassification
    max_tiles: int | None
    _movement: IdleMovement
    warning_sign: Sprite
    detected: bool
    los_direction: Direction #NPC視線方向

    @override
    def __init__(
        self,
        x: float,
        y: float,
        game_manager: GameManager,
        classification: EnemyTrainerClassification = EnemyTrainerClassification.STATIONARY,
        max_tiles: int | None = 2,
        facing: Direction | None = None,
    ) -> None:
        super().__init__(x, y, game_manager)
        self.warning_sign = Sprite(
            "exclamation.png",
            (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2)
        )
        self.warning_sign.update_pos(Position(
            x + GameSettings.TILE_SIZE // 4,
            y - GameSettings.TILE_SIZE // 2
        ))
        self.detected = False

        self.classification = classification
        self.max_tiles = max_tiles
        if classification == EnemyTrainerClassification.STATIONARY:
            self._movement = IdleMovement()
            if facing is None:
                raise ValueError("Idle EnemyTrainer requires a 'facing' Direction")
            self._set_direction(facing)
        
        elif classification == EnemyTrainerClassification.MOVING:
            # 巡邏預設左右往返
            self._movement = PatrolMovement(max_tiles=max_tiles)
            if facing is None:
                facing = Direction.LEFT
            self._set_direction(facing)

        else:
            raise ValueError("Invalid classification")

    @override
    def update(self, dt: float) -> None:
        if self.classification == EnemyTrainerClassification.MOVING:
            self._movement.update(self, dt)
        self._has_los_to_player()
        # detected or not ▲跟上面has los to player 有關
        '''if self.detected and input_manager.key_pressed(pygame.K_SPACE):
            #meet enemy
            from src.scenes.battle_scene import BattleScene
            scene_manager.change_scene(BattleScene(self.game_manager, self))
        self.animation.update_pos(self.position)'''

        if self.detected:
            
            # 更新警告標誌位置，讓它固定在 NPC 頭上
            self.warning_sign.update_pos(Position(
                self.position.x + GameSettings.TILE_SIZE // 4,
                self.position.y - GameSettings.TILE_SIZE // 2
            ))

        # 更新動畫位置
        self.animation.update_pos(self.position) #雖然不會動，但動畫需要更新方向
    @override
    def draw(self, screen: pygame.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        if self.detected:
            self.warning_sign.draw(screen, camera)
        if GameSettings.DRAW_HITBOXES:
            los_rect = self._get_los_rect()#視線矩正
            if los_rect is not None:
                pygame.draw.rect(screen, (255, 255, 0), camera.transform_rect(los_rect), 1)

    #設定NPC面向方向（同步動畫）
    def _set_direction(self, direction: Direction) -> None:
        self.direction = direction
        if direction == Direction.RIGHT: #啊哈，in definition裡面有定義，cooooool
            self.animation.switch("right")
        elif direction == Direction.LEFT:
            self.animation.switch("left")
        elif direction == Direction.DOWN:
            self.animation.switch("down")
        else:
            self.animation.switch("up")
        self.los_direction = self.direction

    def _get_los_rect(self) -> pygame.Rect | None:
        '''
        TODO: Create hitbox to detect line of sight of the enemies towards the player
        回傳一個敵人的矩形
        '''
        x, y = self.position.x, self.position.y
        size = GameSettings.TILE_SIZE

        if self.los_direction == Direction.UP:
            return pygame.Rect(x, y - size * self.max_tiles, size, size * self.max_tiles)
        elif self.los_direction == Direction.DOWN:
            return pygame.Rect(x, y + size, size, size * self.max_tiles)
        elif self.los_direction == Direction.LEFT:
            return pygame.Rect(x - size * self.max_tiles, y, size * self.max_tiles, size)
        else:  # RIGHT
            return pygame.Rect(x + size, y, size * self.max_tiles, size)

    def _has_los_to_player(self) -> None:
        '''判斷玩家是否進入(_get_los_rect)矩形'''
        player = self.game_manager.player
        if player is None:
            self.detected = False
            return
        
        los_rect = self._get_los_rect()
        player_rect = pygame.Rect(
            player.position.x,
            player.position.y,
            GameSettings.TILE_SIZE,
            GameSettings.TILE_SIZE
        )

        '''if los_rect is None:
            self.detected = False
            return
        '''
        '''
        TODO: Implement line of sight detection
        If it's detected, set self.detected to True
        '''
        self.detected = los_rect.colliderect(player_rect)

    @classmethod
    @override
    def from_dict(cls, data: dict, game_manager: GameManager) -> "EnemyTrainer":
        raw = data.get("classification", "stationary")

        try:
            classification = EnemyTrainerClassification(raw)
        except ValueError:
            classification = EnemyTrainerClassification.STATIONARY
        
        max_tiles = data.get("max_tiles", 2)

        facing_raw = data.get("facing", "DOWN")
        
        try:
            facing = Direction[facing_raw]
        except KeyError:
            facing = Direction.DOWN
            
        return cls(
            data["x"] * GameSettings.TILE_SIZE,
            data["y"] * GameSettings.TILE_SIZE,
            game_manager,
            classification,
            max_tiles,
            facing,
        )

    @override
    def to_dict(self) -> dict[str, object]:
        base: dict[str, object] = super().to_dict()
        base["classification"] = self.classification.value
        base["facing"] = self.direction.name
        base["max_tiles"] = self.max_tiles
        return base