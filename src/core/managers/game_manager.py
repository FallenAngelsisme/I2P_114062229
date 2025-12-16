from __future__ import annotations
from src.utils import Logger, GameSettings, Position, Teleport
import json, os
import pygame as pg
from typing import TYPE_CHECKING
from src.data.evolution import EvolutionManager
from src.core.services import scene_manager
if TYPE_CHECKING:
    from src.maps.map import Map
    from src.entities.player import Player
    from src.entities.enemy_trainer import EnemyTrainer
    from src.data.bag import Bag


class GameManager:
    # Entities
    player: Player | None #Player 物件
    enemy_trainers: dict[str, list[EnemyTrainer]]
    bag: "Bag" #class bag
    
    # Map properties
    current_map_key: str
    maps: dict[str, Map] #字典
    
    # Changing Scene properties
    should_change_scene: bool
    next_map: str

    
    

    def __init__(self, maps: dict[str, Map], start_map: str, 
                 player: Player | None,
                 enemy_trainers: dict[str, list[EnemyTrainer]], 
                 bag: Bag | None = None):
              #外部（ GameManager.from_dict 或遊戲啟動時）傳入初始資料。
        self.last_teleport_position = None
        self.current_map_key = start_map       
        from src.data.bag import Bag
        # Game Properties
        self.maps = maps   #map 集合 
        self.player = player # class player
        self.enemy_trainers = enemy_trainers
        self.bag = bag if bag is not None else Bag([], [])
        self.npcs = {}
        # ★ NEW: 初始化 EvolutionManager
        self.evolution_manager = EvolutionManager()
        self.bag.set_game_manager(self) # 將 GameManager 傳給 Bag
        # ...
        # Check If you should change scene
        self.should_change_scene = False
        self.next_map = ""
        #bug
        self.next_player_position: Position | None = None
    @property
    def current_map(self) -> Map:
        return self.maps[self.current_map_key]
    #方便呼叫 ex:game_manager.current_map
        
    @property
    def current_enemy_trainers(self) -> list[EnemyTrainer]:
        return self.enemy_trainers[self.current_map_key]
    
    @property
    def current_npcs(self):
        return self.npcs.get(self.current_map_key, [])
        
    @property
    def current_teleporter(self) -> list[Teleport]:
        return self.maps[self.current_map_key].teleporters
    #傳送點列表，確保 Map.from_dict 把 teleport 轉成class Teleport形式，而不是 dict(像json)
                                                #(我的class)Teleport(x=5, y=10, destination="house1")
                                                #但尷尬的是我用的很混亂，我一開始沒發現defintion裡面有class teleport
    
    #switch_map 設置下次更新時需要切換地圖的旗標 (self.should_change_scene = True) 和目標地圖名稱 (self.next_map)。try_switch_map 則在旗標為 True 時，實際切換 current_map_key 並將玩家移動到新地圖的出生點 (spawn)。
    def switch_map(self, target: str, spawn_pos: Position | None = None) -> None:
        if target not in self.maps:
            Logger.warning(f"Map '{target}' not loaded; cannot switch.")
            return
    
        self.next_map = target
        self.next_player_position = spawn_pos #bug
        self.should_change_scene = True
            
    def try_switch_map(self) -> None:
        if self.should_change_scene:
            self.current_map_key = self.next_map
            self.next_map = ""
            self.should_change_scene = False
            if self.player:                                            #Spawn 是 Map 的出生位置
                if self.next_player_position is not None:
                # 直接設為 pixel 座標
                    self.player.position = self.next_player_position
                    # clear it afterwards
                    self.next_player_position = None
                    self.player._teleport_cooldown_timer = 0.5
                else:
                    self.player.position = self.maps[self.current_map_key].spawn
            
    def check_collision(self, rect: pg.Rect) -> bool:
        if self.maps[self.current_map_key].check_collision(rect):
            return True
        for entity in self.enemy_trainers[self.current_map_key]:
            if rect.colliderect(entity.animation.rect):
                return True
        
        return False
        
    def save(self, path: str) -> None:
        try:
            with open(path, "w") as f:
                #self.to_dict() 的結果 dump 成 JSON 檔案
                json.dump(self.to_dict(), f, indent=2)
            Logger.info(f"Game saved to {path}")
        except Exception as e:
            Logger.warning(f"Failed to save game: {e}")
             
    @classmethod
    def load(cls, path: str) -> "GameManager | None":
        if not os.path.exists(path):
            Logger.error(f"No file found: {path}, ignoring load function")
            return None

        with open(path, "r") as f:
            data = json.load(f)

        #讀檔並交由 from_dict 建構 GameManager
        return cls.from_dict(data)


    #把物變成"可以存進 JSON!!!! 的" 所以在save上面!我有用到
    def to_dict(self) -> dict[str, object]:

        #列表 = 用來裝所有地圖的存檔
        map_blocks: list[dict[str, object]] = []
        # "map1.json": Map物件
        for key, m in self.maps.items():
            block = m.to_dict() #便可存json的格式
            '''{
            "path": "maps/route1.tmx",
            "teleport": [...],
            "player": {"x": 10, "y": 5}
            }'''
            #所有敵人 trainer也是
            block["enemy_trainers"] = [t.to_dict() for t in self.enemy_trainers.get(key, [])]
            block["npcs"] = [npc.to_dict() for npc in self.npcs.get(key, [])]

            '''"map": [
                {
                    "path": "maps/route1.json",
                    "teleport": [...],
                    "enemy_trainers": [...],
                    "player": {...}
                },.....
                ]'''
            
            map_blocks.append(block)
        return {
            "map": map_blocks,
            "current_map": self.current_map_key,
            "player": self.player.to_dict() if self.player is not None else None,
            "bag": self.bag.to_dict(),
        }


    #把存檔讀出來的dict轉回"可用class" 所以load要return時有用到
    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "GameManager":
        from src.maps.map import Map
        from src.entities.player import Player
        from src.entities.enemy_trainer import EnemyTrainer
        from src.data.bag import Bag
        
        Logger.info("Loading maps")
        maps_data = data["map"]
        maps: dict[str, Map] = {}
        player_spawns: dict[str, Position] = {}
        trainers: dict[str, list[EnemyTrainer]] = {}

        for entry in maps_data:
            path = entry["path"]
                            #建 map 物
            maps[path] = Map.from_dict(entry)
            sp = entry.get("player")
            if sp:
                player_spawns[path] = Position(
                    sp["x"] * GameSettings.TILE_SIZE,
                    sp["y"] * GameSettings.TILE_SIZE
                )
        current_map = data["current_map"]
        gm = cls(
            maps, current_map,
            None, # Player
            trainers,
            bag=None
        )
        gm.current_map_key = current_map
        
        Logger.info("Loading enemy trainers")
        for m in data["map"]:
            raw_data = m["enemy_trainers"]       #還原敵人物件並存入
            gm.enemy_trainers[m["path"]] = [EnemyTrainer.from_dict(t, gm) for t in raw_data]

            gm.npcs[m["path"]] = []

            for npc_data in m.get("npcs", []):
                if npc_data["type"] == "shop":
                    from src.entities.shop_npc import ShopNPC
                    npc = ShopNPC.from_dict(npc_data, gm)
                    gm.npcs[m["path"]].append(npc)

                '''elif npc_data["type"] == "talk":
                    from src.entities.talk_npc import TalkNPC
                    npc = TalkNPC.from_dict(npc_data, gm)
                    gm.npcs[m["path"]].append(npc)'''
                        
        Logger.info("Loading Player")
        player_data = data.get("player")

        if player_data:
            # 先讀 tile 座標
            px = player_data["x"]
            py = player_data["y"]

            # 讓 Player 根據存檔資料建立
            gm.player = Player.from_dict(player_data, gm)

            # 存起 tile 座標（後面 GameScene.load_game 會用）
            gm.player.raw_x = px
            gm.player.raw_y = py
        Logger.info("Loading bag")
        from src.data.bag import Bag as _Bag
        gm.bag = Bag.from_dict(data.get("bag", {})) if data.get("bag") else _Bag([], [])

        gm.bag.set_game_manager(gm)

        return gm
    
    