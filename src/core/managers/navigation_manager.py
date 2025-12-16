import pygame as pg
from src.utils import GameSettings
from src.entities.pathfinding import Pathfinder

class NavigationManager:
    def __init__(self, player, game_manager):
        self.player = player
        self.game_manager = game_manager
        self.pathfinder = Pathfinder(game_manager)

        self.current_path = []
        self.is_navigating = False
        self.tile = GameSettings.TILE_SIZE
        
        # ★ 跨地圖導航支援
        self.target_map = None
        self.target_tile_x = None
        self.target_tile_y = None

    def _player_tile_center(self):
        tx = int(self.player.position.x // self.tile)
        ty = int(self.player.position.y // self.tile)
        return (
            tx * self.tile + self.tile // 2,
            ty * self.tile + self.tile // 2
        )

    def start_navigation(self, tile_x, tile_y, target_map=None):
        """
        開始導航
        - 如果 target_map 為 None，則在當前地圖尋路
        - 否則記錄目標，等待地圖切換後繼續
        """
        self.target_map = target_map
        self.target_tile_x = tile_x
        self.target_tile_y = tile_y
        
        if target_map and target_map != self.game_manager.current_map_key:
            # ★ 跨地圖導航：先找到最近的傳送點
            self._navigate_to_teleporter(target_map)
        else:
            # ★ 同地圖導航
            self._calculate_path(tile_x, tile_y)

    def _navigate_to_teleporter(self, target_map):
        """找到通往目標地圖的傳送點"""
        for tp in self.game_manager.current_teleporter:
            if tp.destination == target_map:
                # 導航到這個傳送點
                tp_tile_x = tp.pos.x // self.tile
                tp_tile_y = tp.pos.y // self.tile
                self._calculate_path(tp_tile_x, tp_tile_y)
                return
        
        # 找不到傳送點
        print(f"無法找到通往 {target_map} 的傳送點")
        self.cancel_navigation()

    def _calculate_path(self, tile_x, tile_y):
        """計算路徑"""
        goal_px = tile_x * self.tile + self.tile // 2
        goal_py = tile_y * self.tile + self.tile // 2

        start_px, start_py = self._player_tile_center()

        self.current_path = self.pathfinder.find_path(start_px, start_py, goal_px, goal_py)
        self.is_navigating = bool(self.current_path)

    def cancel_navigation(self):
        self.current_path = []
        self.is_navigating = False
        self.target_map = None
        self.target_tile_x = None
        self.target_tile_y = None

    def update(self, dt):
        if not self.is_navigating or not self.current_path:
            return

        # 下一個 tile 的像素中心目標
        target_x, target_y = self.current_path[0]

        # 玩家目前位置
        px, py = self.player.position.x, self.player.position.y

        # 移動方向
        dx, dy = target_x - px, target_y - py
        dist = (dx*dx + dy*dy)**0.5

        # 到了 tile 中心
        if dist < 2:
            self.current_path.pop(0)
            if not self.current_path:
                self.cancel_navigation()
            return

        # 正規化
        dx /= dist
        dy /= dist

        # 用玩家基礎速度前進
        speed = self.player.speed * dt
        new_x = px + dx * speed
        new_y = py + dy * speed

        # ★ 不用 pixel 碰撞，因為 tile A* 已經避免了所有障礙
        self.player.position.x = new_x
        self.player.position.y = new_y
