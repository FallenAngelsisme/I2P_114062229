"""
進化系統數據配置
Evolution System Data Configuration

使用方式 / How to use:
1. 在這裡定義每個怪獸的進化鏈
2. 設定進化所需等級
3. 指定進化後的圖片路徑
4. 設定能力加成

Evolution Chain Example:
Charmander (Lv.16) -> Charmeleon (Lv.36) -> Charizard
"""
from src.utils import Logger
from src.utils.definition import Monster
'''
{
        "name": "Charmander",
        "hp": 60,
        "max_hp": 60,
        "level": 6,
        "sprite_path": "menu_sprites/menusprite7.png",
        "element": "Fire"
      },
{
        "name": "Charmeleon",
        "hp": 60,
        "max_hp": 60,
        "level": 6,
        "sprite_path": "menu_sprites/menusprite8.png",
        "element": "Fire"
      },
{
        "name": "Charizard",
        "hp": 60,
        "max_hp": 60,
        "level": 6,
        "sprite_path": "menu_sprites/menusprite9.png",
        "element": "Fire"
      },
{
        "name": "Rat",
        "hp": 60,
        "max_hp": 60,
        "level": 6,
        "sprite_path": "menu_sprites/menusprite10.png",
        "element": "Grass"
      },
{
        "name": "Rat_snack",
        "hp": 60,
        "max_hp": 60,
        "level": 6,
        "sprite_path": "menu_sprites/menusprite11.png",
        "element": "Grass"
      },
{
        "name": "Pidgey",
        "hp": 60,
        "max_hp": 60,
        "level": 6,
        "sprite_path": "menu_sprites/menusprite12.png",
        "element": "Water"
      },
{
        "name": "Pidgeotto",
        "hp": 60,
        "max_hp": 60,
        "level": 6,
        "sprite_path": "menu_sprites/menusprite13.png",
        "element": "Water"
      },
{
        "name": "Pidgeot",
        "hp": 60,
        "max_hp": 60,
        "level": 6,
        "sprite_path": "menu_sprites/menusprite14.png",
        "element": "Water"
      },
{
        "name": "Bulbasaur",
        "hp": 60,
        "max_hp": 60,
        "level": 6,
        "sprite_path": "menu_sprites/menusprite15.png",
        "element": "Grass"
      },
{
        "name": "Ivysaur",
        "hp": 60,
        "max_hp": 60,
        "level": 6,
        "sprite_path": "menu_sprites/menusprite16.png",
        "element": "Grass"
      }

'''
# ==================== 進化數據表 ====================
# 格式說明:
# "原始名稱": {
#     "to": "進化後名稱",
#     "level": 進化所需等級,
#     "sprite": "進化後圖片路徑",
#     "stat_bonus": {"hp": HP加成, "attack": 攻擊力加成}
# }
from src.utils.definition import Monster
EVOLUTION_DATA = {
    # === 皮卡丘進化鏈 ===
    "Pikachu": {
        "to": "Charizard",
        "level": 10,
        "sprite": "menu_sprites/menusprite2.png",
        "stat_bonus": {"hp": 40, "attack": 20, "defense": 15}
    },

    "Charizard": {
        "to": "Blastoise",
        "level": 10,
        "sprite": "menu_sprites/menusprite3.png",
        "stat_bonus": {"hp": 40, "attack": 20, "defense": 15}
    },
    # === 小火龍進化鏈 ===
    "Charmander": {
        "to": "Charmeleon",
        "level": 10,
        "sprite": "menu_sprites/menusprite8.png",
        "stat_bonus": {"hp": 20, "attack": 10, "defense": 15}
    },
    "Charmeleon": {
        "to": "chasaur",
        "level": 10,
        "sprite": "menu_sprites/menusprite9.png",
        "stat_bonus": {"hp": 50, "attack": 30, "defense": 15}
    },

    
    # === 妙蛙種子進化鏈 ===
    "Bulbasaur": {
        "to": "Ivysaur",
        "level": 10,
        "sprite": "menu_sprites/menusprite2.png",
        "stat_bonus": {"hp": 22, "attack": 9, "defense": 15}
    },
    "Ivysaur": {
        "to": "Venusaur",
        "level": 10,
        "sprite": "menu_sprites/menusprite3.png",
        "stat_bonus": {"hp": 48, "attack": 28, "defense": 15}
    },
    
    # === 波波進化鏈 ===
    "Pidgey": {
        "to": "Pidgeotto",
        "level": 10,
        "sprite": "menu_sprites/pidgeotto.png",
        "stat_bonus": {"hp": 15, "attack": 12, "defense": 15}
    },
    "Pidgeotto": {
        "to": "Pidgeot",
        "level": 10,
        "sprite": "menu_sprites/pidgeot.png",
        "stat_bonus": {"hp": 35, "attack": 25, "defense": 15}
    },
    
    # === 小拉達進化鏈 ===
    "Rattata": {
        "to": "Raticate",
        "level": 10,
        "sprite": "menu_sprites/raticate.png",
        "stat_bonus": {"hp": 30, "attack": 18, "defense": 15}
    },
    
    # === 烈雀進化鏈 ===
    "Spearow": {
        "to": "Fearow",
        "level": 10,
        "sprite": "menu_sprites/fearow.png",
        "stat_bonus": {"hp": 28, "attack": 22, "defense": 15}
    },
    
    # === 阿柏蛇進化鏈 ===
    "Ekans": {
        "to": "Arbok",
        "level": 102,
        "sprite": "menu_sprites/arbok.png",
        "stat_bonus": {"hp": 32, "attack": 20, "defense": 15}
    },
    
    
    
    
}


# ==================== 進化檢查函數 ====================

def can_evolve(monster):
    """判斷怪獸是否可進化"""
    Logger.info(f"=== can_evolve() Debug ===")
    Logger.info(f"Monster name: {monster.name}")
    Logger.info(f"Monster level: {monster.level}")
    Logger.info(f"Monster in EVOLUTION_DATA: {monster.name in EVOLUTION_DATA}")
    
    if monster.name not in EVOLUTION_DATA:
        Logger.info(f"Result: False (not in EVOLUTION_DATA)")
        return False
    
    required_level = EVOLUTION_DATA[monster.name].get("level", 999)
    Logger.info(f"Required level: {required_level}")
    Logger.info(f"Can evolve: {monster.level >= required_level}")
    
    return monster.level >= required_level
def apply_evolution(monster: Monster, evolution_data: dict) -> bool:
    """
    執行怪獸進化，並更新怪獸的屬性。
    Args:
        monster: 要進化的 Monster 物件。
        evolution_data: 進化目標的資料字典 (來自 EVOLUTION_DATA)。
    Returns:
        bool: 進化成功返回 True，否則返回 False。
    """
    if not evolution_data:
        return False

    evolve_to_name = evolution_data['to']
    sprite_path = evolution_data['sprite']
    stat_bonus = evolution_data['stat_bonus']
    
    # 1. 更新名稱和圖片路徑
    monster.name = evolve_to_name
    monster.sprite_path = sprite_path
    
    # 2. 更新屬性 (MaxHP 和當前HP)
    hp_bonus = stat_bonus.get('hp', 0)
    monster.max_hp += hp_bonus
    monster.hp += hp_bonus # 當前血量隨最大血量同步提升
    monster.hp = min(monster.hp, monster.max_hp) # 確保不超過最大值
    
    # 3. 更新攻擊力 (假設有 attack 屬性)
    # monster.attack += stat_bonus.get('attack', 0) 
    
    # 4. 更新進化鏈資料 (指向下一階)
    next_evolution = EVOLUTION_DATA.get(evolve_to_name)
    if next_evolution:
        monster.evolve_to = next_evolution.get('to')
        monster.evolve_level = next_evolution.get('level')
    else:
        monster.evolve_to = None
        monster.evolve_level = 0
    
    return True
def evolve(monster):
    """進化怪獸，回傳進化後的數據"""
    if not can_evolve(monster):
        return None
    
    evo = EVOLUTION_DATA[monster.name]
    old_name = monster.name
    monster.name = evo["to"]
    monster.sprite_path = evo["sprite"]
    monster.max_hp += evo["stat_bonus"].get("hp", 0)
    monster.hp = monster.max_hp
    monster.attack = getattr(monster, "attack", monster.level*2 + 20) + evo["stat_bonus"].get("attack", 0)
    return old_name, monster.name

class EvolutionManager:
    def can_evolve(self, monster: Monster) -> bool:
        """檢查怪獸是否可以進化 (是否有下一階數據)"""
        evo_data = EVOLUTION_DATA.get(monster.name)
        if evo_data and monster.level >= evo_data.get('level', 1000):
             return True
        return False

    def evolve_monster(self, monster: Monster) -> bool:
        if not self.can_evolve(monster):
            return False
            
        evo = EVOLUTION_DATA[monster.name]
        
        # 1. 更新名稱和圖片
        monster.name = evo["to"]
        monster.sprite_path = evo["sprite"]
        
        # 2. 更新血量 (HP/MaxHP)
        hp_bonus = evo["stat_bonus"].get("hp", 0)
        monster.max_hp += hp_bonus
        monster.hp = monster.max_hp # 進化後回滿血
        
        # 3. 更新 攻擊與防禦 (確保 Monster 物件有這兩個屬性，若無則初始化)
        # 參考 BattleScene 的基礎公式: level * 2 + 20
        if not hasattr(monster, 'attack'):
            monster.attack = monster.level * 2 + 20
        if not hasattr(monster, 'defense'):
            monster.defense = monster.level * 1.5 + 10
            
        monster.attack += evo["stat_bonus"].get("attack", 0)
        monster.defense += evo["stat_bonus"].get("defense", 0)
        
        Logger.info(f"{monster.name} evolved! Atk+{evo['stat_bonus'].get('attack', 0)}, Def+{evo['stat_bonus'].get('defense', 0)}")
        return True
    
    def get_next_name(self, monster_name: str) -> str | None:
        """
        根據當前寶可夢的名稱，查找下一個進化形態的名稱。
        """
        # 從 EVOLUTION_DATA 中獲取進化資訊
        evolution_info = EVOLUTION_DATA.get(monster_name)
        
        if evolution_info:
            # 返回 "to" 鍵對應的進化後名稱
            return evolution_info.get("to")
        else:
            # 如果沒有進化數據，則回傳 None
            return None