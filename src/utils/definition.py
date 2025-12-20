from pygame import Rect
from .settings import GameSettings
from dataclasses import dataclass
from enum import Enum
from typing import overload, TypedDict, Protocol

MouseBtn = int
Key = int

Direction = Enum('Direction', ['UP', 'DOWN', 'LEFT', 'RIGHT', 'NONE'])

@dataclass
class Position:
    x: float
    y: float
    
    def copy(self):
        return Position(self.x, self.y)
        
    def distance_to(self, other: "Position") -> float:
        return ((self.x - other.x) ** 2 + (self.y - other.y) ** 2) ** 0.5
        
@dataclass
class PositionCamera:
    x: int
    y: int
    
    def copy(self):
        return PositionCamera(self.x, self.y)
        
    def to_tuple(self) -> tuple[int, int]:
        return (self.x, self.y)
        
    def transform_position(self, position: Position) -> tuple[int, int]:
        return (int(position.x) - self.x, int(position.y) - self.y)
        
    def transform_position_as_position(self, position: Position) -> Position:
        return Position(int(position.x) - self.x, int(position.y) - self.y)
        
    def transform_rect(self, rect: Rect) -> Rect:
        return Rect(rect.x - self.x, rect.y - self.y, rect.width, rect.height)

@dataclass
class Teleport:
    pos: Position
    destination: str
    exit_pos: Position | None = None
    @overload
    def __init__(self, x: int, y: int, destination: str, exit_x: int = None, exit_y: int = None) -> None: ...
    @overload
    def __init__(self, pos: Position, destination: str, exit_pos: Position = None) -> None: ...

    def __init__(self, *args, **kwargs):
        if isinstance(args[0], Position):
            self.pos = args[0]
            self.destination = args[1]
            self.exit_pos = args[2] if len(args) > 2 else None
        else:
            x, y, dest = args[0], args[1], args[2]
            self.pos = Position(x, y)
            self.destination = dest

        # ★ 處理 exit 座標
            if len(args) > 4:
                self.exit_pos = Position(args[3], args[4])
            else:
                self.exit_pos = None
    
    def to_dict(self):
        result = {
            "x": self.pos.x // GameSettings.TILE_SIZE,
            "y": self.pos.y // GameSettings.TILE_SIZE,
            "destination": self.destination
        }
        if self.exit_pos:
                result["exit_x"] = self.exit_pos.x // GameSettings.TILE_SIZE
                result["exit_y"] = self.exit_pos.y // GameSettings.TILE_SIZE
        return result
    
    @classmethod
    def from_dict(cls, data: dict):
        x = data["x"] * GameSettings.TILE_SIZE
        y = data["y"] * GameSettings.TILE_SIZE
        dest = data["destination"]

        # ★ 讀取 exit 座標
        if "exit_x" in data and "exit_y" in data:
            exit_x = data["exit_x"] * GameSettings.TILE_SIZE
            exit_y = data["exit_y"] * GameSettings.TILE_SIZE
            return cls(x, y, dest, exit_x, exit_y)
        else:
            return cls(x, y, dest)
        
class Monster: #(TypedDict)
    '''name: str
    hp: int
    max_hp: int
    level: int
    sprite_path: str'''


    def __init__(self, name: str, hp: int, max_hp: int, level: int, attack: int, defense: int, sprite_path: str,
        element: str = "Normal",
        evolve_to: str = None,
        evolve_level: int = None):
        self.name = name
        self.hp = hp
        self.max_hp = max_hp
        self.level = level
        self.attack = attack
        self.defense = defense
        self.sprite_path = sprite_path
        self.element = element #ch3
        self.evolve_to = evolve_to
        self.evolve_level = evolve_level

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "hp": self.hp,
            "max_hp": self.max_hp,
            "level": self.level,
            "attack": self.attack,
            "defense": self.defense,
            "sprite_path": self.sprite_path,
            "element": self.element,            # ★ 必須加
            "evolve_to": self.evolve_to,
            "evolve_level": self.evolve_level
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            hp=data["hp"],
            max_hp=data["max_hp"],
            level=data["level"],
            attack=data["attack"],
            defense=data["defense"],
            sprite_path=data["sprite_path"],
            element=data.get("element", "Normal"),      # ★ 必須加
            evolve_to=data.get("evolve_to"),
            evolve_level=data.get("evolve_level")
        )
class Item: #(TypedDict)
    '''name: str
    count: int
    sprite_path: str'''

    def __init__(self, name: str, count: int, sprite_path: str):
        self.name = name
        self.count = count
        self.sprite_path = sprite_path

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "count": self.count,
            "sprite_path": self.sprite_path
        }

    @classmethod
    def from_dict(cls, data: dict):
        return cls(
            name=data["name"],
            count=data["count"],
            sprite_path=data["sprite_path"]
        )