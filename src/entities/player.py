from __future__ import annotations
import pygame as pg
from .entity import Entity
from src.core.services import input_manager
from src.utils import Position, PositionCamera, GameSettings, Logger, Direction
from src.core import GameManager
import math
from typing import override
from .enemy_trainer import EnemyTrainer

class Player(Entity):
    speed: float = 4.0 * GameSettings.TILE_SIZE
    game_manager: GameManager
    is_near_interactable_trainer: EnemyTrainer | None = None
    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        super().__init__(x, y, game_manager)
        self._last_teleport = None  # tuple (map_key, tile_x, tile_y) 或 None bug
        self._teleport_cooldown_timer = 0.0  # 秒bug
        self.is_moving = False #online
    @override
    def update(self, dt: float) -> None:
        
        #開頭每回合減少 cooldown bug
        if hasattr(self, "_teleport_cooldown_timer"):
            self._teleport_cooldown_timer = max(0.0, getattr(self, "_teleport_cooldown_timer") - dt)


        dis = Position(0, 0)
        '''
        [TODO HACKATHON 2]
        Calculate the distance change, and then normalize the distance
        
        [TODO HACKATHON 4]
        Check if there is collision, if so try to make the movement smooth
        Hint #1 : use entity.py _snap_to_grid function or create a similar function
        Hint #2 : Beware of glitchy teleportation, you must do
                    1. Update X
                    2. If collide, snap to grid
                    3. Update Y
                    4. If collide, snap to grid
                  instead of update both x, y, then snap to grid
        
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= ...
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += ...
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= ...
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += ...
        
        self.position = ...
        '''
        
        if input_manager.key_down(pg.K_LEFT) or input_manager.key_down(pg.K_a):
            dis.x -= 1
            self.direction = Direction.LEFT
            self.animation.switch("left")
        if input_manager.key_down(pg.K_RIGHT) or input_manager.key_down(pg.K_d):
            dis.x += 1
            self.direction = Direction.RIGHT
            self.animation.switch("right")  
        if input_manager.key_down(pg.K_UP) or input_manager.key_down(pg.K_w):
            dis.y -= 1
            self.direction = Direction.UP
            self.animation.switch("up")
        if input_manager.key_down(pg.K_DOWN) or input_manager.key_down(pg.K_s):
            dis.y += 1
            self.direction = Direction.DOWN
            self.animation.switch("down")
        
        
        #print(f"dis before normalize: {dis.x}, {dis.y}")
        #正規化向量
        magnitude = math.hypot(dis.x, dis.y)
        self.is_moving = magnitude > 0 #online

        #print(f"new position: {self.position.x}, {self.position.y}")
        if magnitude > 0:
            dis.x = dis.x / magnitude * self.speed * dt
            dis.y = dis.y / magnitude * self.speed * dt

        self.is_near_interactable_trainer = None # 預設為 None
         # move with collision handling
        # X方向移動
        self.position.x += dis.x
        player_rect = pg.Rect(self.position.x, self.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        collide = self.game_manager.current_map.check_collision(player_rect)
        
        for enemy in self.game_manager.current_enemy_trainers:
            enemy_rect = pg.Rect(enemy.position.x, enemy.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
            #一樣也是!!#物品1.colliderect(物2)
            if player_rect.colliderect(enemy_rect):
                collide = True
                break

        for npc in self.game_manager.current_npcs:
            npc_rect = pg.Rect(npc.position.x, npc.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
            if player_rect.colliderect(npc_rect):
                collide = True
                break

        if collide:
            self.position.x = self._snap_to_grid(self.position.x)

        # Y方向移動
        self.position.y += dis.y
        player_rect = pg.Rect(self.position.x, self.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        collide = self.game_manager.current_map.check_collision(player_rect)#用圖去判斷
        for enemy in self.game_manager.current_enemy_trainers:
            enemy_rect = pg.Rect(enemy.position.x, enemy.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
            #一樣也是!!#物品1.colliderect(物2)
            if player_rect.colliderect(enemy_rect):
                collide = True
                break

        for npc in self.game_manager.current_npcs:
            npc_rect = pg.Rect(npc.position.x, npc.position.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
            if player_rect.colliderect(npc_rect):
                collide = True
                break

        if collide:
            self.position.y = self._snap_to_grid(self.position.y)

        

        # Check teleportation 角色移動的更新迴圈，實際觸發傳送邏輯。它會呼叫 current_map.check_telepor
        tp = self.game_manager.current_map.check_teleport(self.position)
        
        if tp and self._teleport_cooldown_timer <= 0:
            #dest = tp.destination
            #self.game_manager.switch_map(dest)
                              #切地圖的入口開關
                                        # json裡面喔 tp["destination"]
            # 記錄這次是從哪裡傳
            tile_x = int(tp.pos.x // GameSettings.TILE_SIZE)
            tile_y = int(tp.pos.y // GameSettings.TILE_SIZE)
            tp_tile = (self.game_manager.current_map_key, tile_x, tile_y)

            # 設定冷卻避免重複傳送
            self._last_teleport = tp_tile
            self._teleport_cooldown_timer = 0.35
            spawn_pos = None
            if tp.exit_pos:
                # *** 重點：給 exit_pos 加一點 offset，避免重踩傳送 tile ***
                spawn_pos = Position(
                    tp.exit_pos.x ,
                    tp.exit_pos.y 
                )
            
            self.game_manager.switch_map(tp.destination, spawn_pos)
        super().update(dt)

    @override
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        super().draw(screen, camera)
        
    @override
    def to_dict(self) -> dict[str, object]:
        return super().to_dict()
    
    @classmethod
    @override
    def from_dict(cls, data: dict[str, object], game_manager: GameManager) -> Player:
        return cls(data["x"] * GameSettings.TILE_SIZE, data["y"] * GameSettings.TILE_SIZE, game_manager)

