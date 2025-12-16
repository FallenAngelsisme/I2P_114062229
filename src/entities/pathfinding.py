import pygame as pg
from heapq import heappush, heappop
from src.utils import GameSettings

class Pathfinder:
    def __init__(self, game_manager):
        self.game_manager = game_manager

    def heuristic(self, a, b):
        return abs(a[0]-b[0]) + abs(a[1]-b[1])

    def tile_is_teleporter(self, x, y):
        return self.game_manager.current_map.is_teleport_tile(x, y)

    def tile_has_entity(self, x, y):
        """檢查這格是否有 NPC 或 敵人"""
        tile = GameSettings.TILE_SIZE
        rect = pg.Rect(x * tile, y * tile, tile, tile)
        
        # 檢查敵人
        for enemy in self.game_manager.current_enemy_trainers:
            enemy_rect = pg.Rect(
                enemy.position.x, 
                enemy.position.y, 
                tile, tile
            )
            if rect.colliderect(enemy_rect):
                return True
        
        # 檢查 NPC
        for npc in self.game_manager.current_npcs:
            npc_rect = pg.Rect(
                npc.position.x,
                npc.position.y,
                tile, tile
            )
            if rect.colliderect(npc_rect):
                return True
        
        return False

    def find_path(self, start_px, start_py, goal_px, goal_py):
        tile = GameSettings.TILE_SIZE

        start = (start_px // tile, start_py // tile)
        goal = (goal_px // tile, goal_py // tile)

        open_set = []
        heappush(open_set, (0, start))
        came_from = {}
        g = {start: 0}

        while open_set:
            _, current = heappop(open_set)
            if current == goal:
                break

            cx, cy = current
            for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:
                nxt = (cx + dx, cy + dy)
                nx, ny = nxt

                # ★ 1. 傳送點要跳過（除非是終點）
                if self.tile_is_teleporter(nx, ny) and nxt != goal:
                    continue

                # ★ 2. 普通碰撞檢查
                rect = pg.Rect(nx*tile, ny*tile, tile, tile)
                if self.game_manager.current_map.check_collision(rect):
                    continue

                # ★ 3. 檢查是否有 NPC 或敵人（除非是終點）
                if self.tile_has_entity(nx, ny) and nxt != goal:
                    continue

                new_cost = g[current] + 1
                if nxt not in g or new_cost < g[nxt]:
                    g[nxt] = new_cost
                    priority = new_cost + self.heuristic(nxt, goal)
                    heappush(open_set, (priority, nxt))
                    came_from[nxt] = current

        # ---- 重建路徑 ----
        if goal not in came_from and goal != start:
            return []

        path = []
        node = goal
        while node != start:
            px = node[0]*tile + tile//2
            py = node[1]*tile + tile//2
            path.insert(0, (px, py))
            if node not in came_from:
                break
            node = came_from[node]

        return path