from __future__ import annotations
import pygame as pg
from typing import override
from src.sprites import Animation
from src.utils import Position, PositionCamera, Direction, GameSettings
from src.core import GameManager
from src.utils import Logger

class Entity:
    animation: Animation
    direction: Direction
    position: Position
    game_manager: GameManager
    
    def __init__(self, x: float, y: float, game_manager: GameManager) -> None:
        ####self.camera = PositionCamera(0, 0)
        
        # Sprite is only for debug, need to change into animations
        self.animation = Animation(                             #每個方向的幀數
            "character/ow1.png", ["down", "left", "right", "up"], 4,
            (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        )
        
        self.position = Position(x, y)
        self.direction = Direction.DOWN
        self.animation.update_pos(self.position)
        self.game_manager = game_manager

    def update(self, dt: float) -> None:
        self.animation.update_pos(self.position)
        self.animation.update(dt)

        ####self.camera.update(self.position)
    def draw(self, screen: pg.Surface, camera: PositionCamera) -> None:
        self.animation.draw(screen, camera)
        if GameSettings.DRAW_HITBOXES:
            self.animation.draw_hitbox(screen, camera)
        
    @staticmethod
    def _snap_to_grid(value: float) -> int:
        return round(value / GameSettings.TILE_SIZE) * GameSettings.TILE_SIZE
    
    @property
    def camera(self) -> PositionCamera:
        '''
        [TODO HACKATHON 3]
        Implement the correct algorithm of player camera
        '''
        # 我要來設定螢幕中心座標
        screen_center_x = GameSettings.SCREEN_WIDTH // 2
        screen_center_y = GameSettings.SCREEN_HEIGHT // 2

        # 計算相機位置的方法 = 玩家位置 - 螢幕中心
        cam_x = int(self.position.x - screen_center_x)
        cam_y = int(self.position.y - screen_center_y)

        ####cam_x = max(0, cam_x)
        ####cam_y = max(0, cam_y)
        #可是會超出地圖還沒設
        ####
        '''if self.game_manager and self.game_manager.current_map:
            map_width = self.game_manager.current_map.width * GameSettings.TILE_SIZE
            map_height = self.game_manager.current_map.height * GameSettings.TILE_SIZE
            
            # 限制相機不超出地圖邊界
            cam_x = max(0, min(cam_x, map_width - GameSettings.SCREEN_WIDTH))
            cam_y = max(0, min(cam_y, map_height - GameSettings.SCREEN_HEIGHT))
        '''
            # 嘗試取得地圖邊界（如果有的話）
        try:
            current_map = self.game_manager.current_map
            
            # 方法 1: 如果 Map 有 width/height 屬性
            if hasattr(current_map, 'width') and hasattr(current_map, 'height'):
                map_width = current_map.width * GameSettings.TILE_SIZE
                map_height = current_map.height * GameSettings.TILE_SIZE
                
                # 限制相機不超出地圖邊界
                cam_x = max(0, min(cam_x, map_width - GameSettings.SCREEN_WIDTH))
                cam_y = max(0, min(cam_y, map_height - GameSettings.SCREEN_HEIGHT))
            
            # 方法 2: 如果 Map 有 tiles 或其他結構
            elif hasattr(current_map, 'tiles') and current_map.tiles:
                # 假設 tiles 是二維陣列
                map_height_tiles = len(current_map.tiles)
                map_width_tiles = len(current_map.tiles[0]) if map_height_tiles > 0 else 0
                
                map_width = map_width_tiles * GameSettings.TILE_SIZE
                map_height = map_height_tiles * GameSettings.TILE_SIZE
                
                # 限制相機不超出地圖邊界
                cam_x = max(0, min(cam_x, map_width - GameSettings.SCREEN_WIDTH))
                cam_y = max(0, min(cam_y, map_height - GameSettings.SCREEN_HEIGHT))
            
            # 如果都沒有，就不限制邊界（暫時的）
            else:
                # 至少確保相機不會是負數
                cam_x = max(0, cam_x)
                cam_y = max(0, cam_y)
                
        except Exception as e:
            # 如果出錯，就不限制邊界
            Logger.warning(f"Could not get map bounds for camera: {e}")
            cam_x = max(0, cam_x)
            cam_y = max(0, cam_y)
        return PositionCamera(cam_x, cam_y)
        
    def to_dict(self) -> dict[str, object]:
        return {
            "x": self.position.x / GameSettings.TILE_SIZE,
            "y": self.position.y / GameSettings.TILE_SIZE,
        }
        
    @classmethod
    def from_dict(cls, data: dict[str, float | int], game_manager: GameManager) -> Entity:
        x = float(data["x"])
        y = float(data["y"])
        return cls(x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE, game_manager)
         