import pygame as pg
import pytmx

from src.utils import load_tmx, Position, GameSettings, PositionCamera, Teleport

class Map:
    # Map Properties
    path_name: str
    tmxdata: pytmx.TiledMap
    # Position Argument
    spawn: Position
    teleporters: list[Teleport]
    # Rendering Properties
    _surface: pg.Surface
    _collision_map: list[pg.Rect]

    def __init__(self, path: str, tp: list[Teleport], spawn: Position):
        self.path_name = path
        self.tmxdata = load_tmx(path)
        self.spawn = spawn
        self.teleporters = tp # 這裡就是傳送點列表!!
        self.npcs = []
        pixel_w = self.tmxdata.width * GameSettings.TILE_SIZE
        pixel_h = self.tmxdata.height * GameSettings.TILE_SIZE

        # Prebake the map
        self._surface = pg.Surface((pixel_w, pixel_h), pg.SRCALPHA)
        self._render_all_layers(self._surface)
        # Prebake the collision map
        self._collision_map = self._create_collision_map()
        # catch  the collision map
        self._bush_map = self._create_bush_map()
        

    def update(self, dt: float):
        return

    def draw(self, screen: pg.Surface, camera: PositionCamera):
        screen.blit(self._surface, camera.transform_position(Position(0, 0)))
        
        # Draw the hitboxes collision map
        if GameSettings.DRAW_HITBOXES:
            for rect in self._collision_map:
                pg.draw.rect(screen, (255, 0, 0), camera.transform_rect(rect), 1)
        
    def check_collision(self, rect: pg.Rect) -> bool:
        '''
        [TODO HACKATHON 4]
        Return True if collide if rect param collide with self._collision_map
        Hint: use API colliderect and iterate each rectangle to check
        '''

                     #self._collision_map遊戲物件碰撞區塊的list
        for crect in self._collision_map:
            #物品1.colliderect(物2) 是pygame裡的用法，檢查兩個矩形是否相交
            if rect.colliderect(crect):
                return True
        return False
        
    def check_teleport(self, pos: Position) -> Teleport | None:
        #檢查到傳送塊

        '''[TODO HACKATHON 6] 
        Teleportation: Player can enter a building by walking into certain tiles defined inside saves/*.json, and the map will be changed
        Hint: Maybe there is an way to switch the map using something from src/core/managers/game_manager.py called switch_... 
        負責檢查玩家的當前位置 (pos) 是否與地圖中定義的任何一個傳送點 (self.teleporters) 的矩形範圍相交。如果相交，則返回對應的 Teleport 物件。'''
        #玩家在地圖上的碰撞矩形                           #TILE_SIZE是格子大小
        player_rect = pg.Rect(pos.x, pos.y, GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
        
        # teleporters 現在是dicts  dict有x,y,destination
        #self.teleporters 是json讀取"teleport"
        for tp in self.teleporters:
            tp_rect = pg.Rect(
                tp.pos.x,
                tp.pos.y,
                GameSettings.TILE_SIZE,
                GameSettings.TILE_SIZE
            )
            if player_rect.colliderect(tp_rect):
                return tp  # 回傳整個dict，裡面有 destination
        return None

    def _render_all_layers(self, target: pg.Surface) -> None:
        #讓layer順序畫
        for layer in self.tmxdata.visible_layers:
            if isinstance(layer, pytmx.TiledTileLayer):
                self._render_tile_layer(target, layer)
            # elif isinstance(layer, pytmx.TiledImageLayer) and layer.image:
            #     target.blit(layer.image, (layer.x or 0, layer.y or 0)) 目前不顯示 image layer
 
    #把layer裡的每一格tile畫出來
    def _render_tile_layer(self, target: pg.Surface, layer: pytmx.TiledTileLayer) -> None:
        for x, y, gid in layer:
            if gid == 0:
                continue     #.tmx地圖檔中，取出某一格tile
            image = self.tmxdata.get_tile_image_by_gid(gid) #ID
            if image is None:
                continue

            image = pg.transform.scale(image, (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
            target.blit(image, (x * GameSettings.TILE_SIZE, y * GameSettings.TILE_SIZE))
    
    def _create_collision_map(self) -> list[pg.Rect]:
        rects = [] #存放地圖上的碰撞矩形
        for layer in self.tmxdata.visible_layers:#跑地圖中每一個可見圖層
               # 磚塊圖層 (TiledTileLayer)而非其他圖層        圖層名稱包含 "collision" 或 "house"的
            if isinstance(layer, pytmx.TiledTileLayer) and ("collision" in layer.name.lower() or "house" in layer.name.lower()):
                for x, y, gid in layer: #x, y 是磚塊在圖層中座標 gid是磚塊的圖ID
                    if gid != 0:
                        '''
                        [TODO HACKATHON 4]
                        rects.append(pg.Rect(...))
                        Append the collision rectangle to the rects[] array
                        Remember scale the rectangle with the TILE_SIZE from settings
                        '''
                        #建立一個pygame.Rect矩形 "Append the collision rectangle"
                        rect = pg.Rect(
                        x * GameSettings.TILE_SIZE,
                        y * GameSettings.TILE_SIZE,
                        GameSettings.TILE_SIZE,
                        GameSettings.TILE_SIZE
                        )
                        rects.append(rect)
                        pass
        return rects
    
    def _create_bush_map(self) -> list[pg.Rect]:
        rects = []
                        #tmxdata.visible_layers = 地圖裡所有「可見的」layer
        for layer in self.tmxdata.visible_layers:
                                #必須是一格一格的tile layer，而不是object&image layer。
            if isinstance(layer, pytmx.TiledTileLayer) and "bush" in layer.name.lower():
                for x, y, gid in layer: #gid:tile圖塊ID
                    if gid != 0:
                        rect = pg.Rect(
                            x * GameSettings.TILE_SIZE, #chang像素座標
                            y * GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE,
                            GameSettings.TILE_SIZE
                        )
                        rects.append(rect)
        return rects
    
   
    
    
    #
    @classmethod
    def from_dict(cls, data: dict) -> "Map":
        tp_raw = data.get("teleport", [])
        teleporters = [
            Teleport.from_dict(tp) for tp in tp_raw
        ]

        pos = Position(data["player"]["x"] * GameSettings.TILE_SIZE, data["player"]["y"] * GameSettings.TILE_SIZE)
        return cls(data["path"], teleporters, pos)

    def to_dict(self):
        # 處理 teleporters - 可能是 dict 或 Teleport #看我之後要不要多做功能，可能就需要class teleport，GameManager.py def current_teleporter(self) -> list[Teleport] 我現在丟了dic勉強能用，但可能...要改?
        teleport_list = [tp.to_dict() for tp in self.teleporters]        #但，....我一開始沒發現definition有class teleport
        
        return {
            "path": self.path_name,
            "teleport": teleport_list,
            "player": {
                "x": self.spawn.x // GameSettings.TILE_SIZE,
                "y": self.spawn.y // GameSettings.TILE_SIZE,
            }
        }
    
    def is_teleport_tile(self, tile_x, tile_y):
        # 假設 map.teleports 是你的傳送點列表，例如：
        # teleports = [{"x": 10, "y": 5, "to": "gym"}]
        px = tile_x * GameSettings.TILE_SIZE
        py = tile_y * GameSettings.TILE_SIZE

        for tp in self.teleporters:  # ← 正確名稱
            if tp.pos.x == px and tp.pos.y == py:
                return True
        return False