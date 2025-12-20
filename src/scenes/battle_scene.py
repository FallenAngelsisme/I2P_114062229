import pygame as pg
import random
import os
import re
from typing import override
from src.data.evolution import EVOLUTION_DATA
from src.data.elements import compute_element_multiplier
from src.sprites.animation_sheet import AnimationSheet
from src.sprites.monster_attack_anim import MonsterStaticSprite, BattleIntroAnimation

from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.core import GameManager
from src.utils import Logger, GameSettings
from src.core.services import scene_manager, sound_manager
from src.interface.components import Button


class BattleScene(Scene):
    def __init__(self, game_manager: GameManager = None):
        super().__init__()
        
        #n
        self.intro_anim = None
        self.do_intro = True
        # Shake動畫
        self.enemy_shake_timer = 0
        self.player_shake_timer = 0

        self.game_manager = game_manager  # 儲存 game_manager 引用
        self.background = BackgroundSprite("backgrounds/background1.png")
        
        # 戰鬥狀態
        self.turn = "player"
        self.battle_state = "choose_monster"  # 先選擇怪獸
        self.message = "Choose your monster!"
        self.message_timer = 2.0

        
        # 保存原始數據
        self.original_player_data = None
        self.selected_monster_index = None  # 記錄玩家選的是哪一隻
        
        #
        self.player_is_attacking = False
        self.enemy_is_attacking = False
        self.player_attack_offset = 0
        self.enemy_attack_offset = 0
        # 當前戰鬥中的怪獸
        self.player_monster = None
        self.enemy_monster = None
        self.old_level = 0 #   NEW:

        # Buff系統
        self.player_attack_buff = 0
        self.player_defense_buff = 0
        
        # 字體
        self.font_small = pg.font.Font("assets/fonts/Minecraft.ttf", 20)
        self.font_medium = pg.font.Font("assets/fonts/Minecraft.ttf", 30)
        self.font_large = pg.font.Font("assets/fonts/Minecraft.ttf", 40)
        
        # 怪獸選擇按鈕（最多顯示6隻）
        self.monster_select_buttons = []
        
        
        # 戰鬥按鈕
        self.attack_button = Button(
            "UI/raw/UI_Flat_Button02a_3.png", "UI/raw/UI_Flat_Button02a_3.png",
            400, 580, 120, 40, self.player_attack
        )
        self.item_button = Button(
            "UI/raw/UI_Flat_Button02a_3.png", "UI/raw/UI_Flat_Button02a_3.png",
            550, 580, 120, 40, self.open_item_menu
        )
        self.run_button = Button(
            "UI/raw/UI_Flat_Button02a_3.png", "UI/raw/UI_Flat_Button02a_3.png",
            700, 580, 120, 40, self.run_away
        )

        # Item Menu
        self.item_menu_open = False
        self.item_buttons = [
            Button("UI/raw/UI_Flat_Button02a_3.png", "UI/raw/UI_Flat_Button02a_3.png",
                   450, 350, 220, 40, lambda: self.use_item("Potion")),
            Button("UI/raw/UI_Flat_Button02a_3.png", "UI/raw/UI_Flat_Button02a_3.png",
                   450, 400, 220, 40, lambda: self.use_item("Strength Potion")),
            Button("UI/raw/UI_Flat_Button02a_3.png", "UI/raw/UI_Flat_Button02a_3.png",
                   450, 450, 220, 40, lambda: self.use_item("Defense Potion")),
        ]
        
        # 攻擊動畫 - 根據屬性不同
        self.attack_animations = {
            "Fire": "assets/images/attack/attack4.png",
            "Water": "assets/images/attack/attack3.png",
            "Grass": "assets/images/attack/attack6.png",
            "Electric": "assets/images/attack/attack2.png",
            "Normal": "assets/images/attack/attack1.png",
            "Ice": "assets/images/attack/attack1.png",
            "Land": "assets/images/attack/attack7.png",
        }
        
        self.current_player_anim = None
        self.current_enemy_anim = None
        
        # 怪獸圖片緩存
        self.player_sprite = None
        self.enemy_sprite = None
        # Animated frames
        self.player_frames = []
        self.enemy_frames = []
        self.player_frame_index = 0
        self.enemy_frame_index = 0
        self.player_anim_timer = 0.0
        self.enemy_anim_timer = 0.0
        self.monster_anim_speed = 0.12
        
        # 野生怪獸池（用於隨機生成敵人）
        self.wild_monster_pool = [
            {"name": "Wild Charizard", "element": "Grass", "sprite": "sprites/sprite2_attack.png", "spriteenter": "sprites/sprite2.png", "base_hp": 40, "base_attack": 20},
            {"name": "Wild Blastoise", "element": "Water", "sprite": "sprites/sprite3_attack.png","spriteenter": "sprites/sprite3.png", "base_hp": 80, "base_attack": 25},
            {"name": "Wild Venusaur", "element": "Grass", "sprite": "sprites/sprite4_attack.png", "spriteenter": "sprites/sprite4.png","base_hp": 60, "base_attack": 28},
            {"name": "Wild Gengar", "element": "Electric", "sprite": "sprites/sprite5_attack.png", "spriteenter": "sprites/sprite5.png","base_hp": 80, "base_attack": 15},
            {"name": "Wild Charmander", "element": "Fire", "sprite": "sprites/sprite7_attack.png", "spriteenter": "sprites/sprite7.png","base_hp": 80, "base_attack": 15},
            {"name": "Wild Dragonite", "element": "Ice", "sprite": "sprites/sprite6_attack.png", "spriteenter": "sprites/sprite6.png","base_hp": 70, "base_attack": 20},
        ]
    def get_attack_anim(self, element):
        """每次攻擊都產生新的動畫物件避免卡住"""
        if element not in self.attack_animations:
            return None
        path = self.attack_animations[element]
        anim = AnimationSheet(path, 96, 96, 4)
        return anim

    def _load_animated_frames(self, rel_path: str, frame_w: int = 96, frame_h: int = 96, count: int = 4, scale=(150,150)):
        """嘗試把精靈表切成多幀；失敗時回退到單張圖。回傳 Surface list。"""
        frames = []
        try:
            # 檔案不存在就直接回傳空清單（避免大量噪音錯誤訊息）
            if not os.path.exists(rel_path):
                return []

            sheet = pg.image.load(rel_path).convert_alpha()
            sw, sh = sheet.get_size()
            # 如果 sheet 小於單幀尺寸或無法切割，視為單張圖
            if sw < frame_w or sh < frame_h:
                img = pg.transform.scale(sheet, scale)
                frames = [img]
                return frames

            # 如果 sheet 寬度明顯可以切割多幀，以 count 為準；否則用 sw//frame_w
            if sw >= frame_w * count:
                actual_count = count
            else:
                actual_count = max(1, sw // frame_w)

            for i in range(actual_count):
                surf = pg.Surface((frame_w, frame_h), pg.SRCALPHA)
                surf.blit(sheet, (0, 0), (i * frame_w, 0, frame_w, frame_h))
                surf = pg.transform.scale(surf, scale)
                frames.append(surf)

            if not frames:
                img = pg.transform.scale(sheet, scale)
                frames = [img]
        except Exception as e:
            # 只有在檔案存在但載入失敗時才記錄錯誤
            if os.path.exists(rel_path):
                Logger.error(f"Failed to load animated frames {rel_path}: {e}")
                try:
                    img = pg.image.load(rel_path).convert_alpha()
                    frames = [pg.transform.scale(img, scale)]
                except Exception:
                    frames = []
            else:
                frames = []

        return frames

    def generate_random_enemy(self):
        """隨機生成野生敵人"""
        template = random.choice(self.wild_monster_pool)
        level = random.randint(10, 20)
        
        self.enemy_monster = {
            "name": template["name"],
            "hp": template["base_hp"] + level * 2,
            "max_hp": template["base_hp"] + level * 2,
            "attack": template["base_attack"] + level* 0.4,
            "defense": level * 1.2,
            "level": level,
            "sprite_path": template["sprite"],
            "element": template["element"],
            "spriteenter": template["spriteenter"],
        }
        
        Logger.info(f"Wild {self.enemy_monster['name']} appeared! Lv.{level}")

    def select_monster(self, index):
        """玩家選擇怪獸"""
        if self.battle_state != "choose_monster":
            return
        
        bag = self.game_manager.bag
        
        if index >= len(bag._monsters_data):
            return
        
        # 記錄選擇的怪獸
        self.selected_monster_index = index
        selected_mon = bag._monsters_data[index]
        
        # 保存原始數據
        self.original_player_data = {
            "hp": selected_mon.hp,
            "max_hp": selected_mon.max_hp,
            "attack": selected_mon.attack if hasattr(selected_mon, "attack") else (selected_mon.level * 2 + 20),
            "defense": selected_mon.defense if hasattr(selected_mon, "defense") else (selected_mon.level * 1.5 + 10),
            "level": selected_mon.level,
            "name": selected_mon.name,
            "sprite_path": selected_mon.sprite_path,
            "element": selected_mon.element
        }
        
        # 創建戰鬥用的副本
        self.player_monster = self.original_player_data.copy()
        
        # 載入圖片
        self.load_sprites()
        # Player idle animation
        

        # 開始戰鬥
        self.battle_state = "choose_action"
        self.message = f"Go! {self.player_monster['name']}!"
        self.message_timer = 2.5
        
        Logger.info(f"Player selected: {self.player_monster['name']}")

    def load_sprites(self):
        """載入怪獸圖片"""
        try:
            path = "assets/images/" + self.player_monster["sprite_path"]
            self.player_frames = self._load_animated_frames(path, frame_w=96, frame_h=96, count=4, scale=(150,150))
            # If only a single frame was found, try to derive an *_attack variant (e.g. sprite.png -> sprite_attack.png)
            if len(self.player_frames) <= 1:
                base, ext = os.path.splitext(path)
                # Candidates to try for attack frames
                candidates = [base + "_attack" + ext]
                # If original is a menu_sprites menuspriteN, derive sprites/spriteN_attack
                m = re.search(r"menu_sprites/menusprite(\d+)", path)
                if m:
                    n = m.group(1)
                    candidates.append(os.path.join(os.path.dirname(path), "..", f"sprites/sprite{n}_attack{ext}"))
                    candidates.append(f"assets/images/sprites/sprite{n}_attack{ext}".replace('assets/images/',''))
                    # proper absolute candidate
                    candidates.append(f"assets/images/sprites/sprite{n}_attack{ext}")

                # normalize and try candidates until one yields multiple frames
                for cand in candidates:
                    attack_frames = self._load_animated_frames(cand, frame_w=96, frame_h=96, count=4, scale=(150,150))
                    if len(attack_frames) > 1:
                        self.player_frames = attack_frames
                        break

            if self.player_frames:
                self.player_frame_index = 0
                self.player_sprite = self.player_frames[0]
            else:
                # fallback single image
                self.player_sprite = pg.image.load(path).convert_alpha()
                self.player_sprite = pg.transform.scale(self.player_sprite, (150,150))
        except Exception as e:
            Logger.error(f"Failed to load player sprite: {e}")
            self.player_sprite = None
            
        try:
            path = "assets/images/" + self.enemy_monster["sprite_path"]
            self.enemy_frames = self._load_animated_frames(path, frame_w=96, frame_h=96, count=4, scale=(150,150))
            if len(self.enemy_frames) <= 1:
                base, ext = os.path.splitext(path)
                candidates = [base + "_attack" + ext]
                m = re.search(r"menu_sprites/menusprite(\d+)", path)
                if m:
                    n = m.group(1)
                    candidates.append(f"assets/images/sprites/sprite{n}_attack{ext}")

                for cand in candidates:
                    attack_frames = self._load_animated_frames(cand, frame_w=96, frame_h=96, count=4, scale=(150,150))
                    if len(attack_frames) > 1:
                        self.enemy_frames = attack_frames
                        break

            if self.enemy_frames:
                self.enemy_frame_index = 0
                self.enemy_sprite = self.enemy_frames[0]
            else:
                self.enemy_sprite = pg.image.load(path).convert_alpha()
                self.enemy_sprite = pg.transform.scale(self.enemy_sprite, (150,150))
        except Exception as e:
            Logger.error(f"Failed to load enemy sprite: {e}")
            self.enemy_sprite = None

    def restore_monsters(self):
        """戰鬥結束後恢復怪獸狀態"""
        if self.selected_monster_index is None:
            return
        
        bag = self.game_manager.bag
        
        # 恢復玩家怪獸的HP
        if self.selected_monster_index < len(bag._monsters_data):
            mon = bag._monsters_data[self.selected_monster_index]
            mon.hp = self.original_player_data["hp"]
        
        # 重置Buff
        self.player_attack_buff = 0
        self.player_defense_buff = 0
        
        Logger.info("Monster stats restored after battle")

    def player_attack(self):
        if self.turn != "player" or self.battle_state != "choose_action":
            return

        self.player_is_attacking = True
        self.player_frame_index = 0
        self.player_anim_timer = 0.0
        # 播玩家攻擊動畫效果（大畫面攻擊特效）
        self.current_player_anim = self.get_attack_anim(self.player_monster["element"])

        # 計算傷害
        mult = compute_element_multiplier(self.player_monster["element"], self.enemy_monster["element"])
        base_damage = self.player_monster["attack"] + self.player_attack_buff
        damage = int((base_damage + random.randint(1, 5)) * mult)
        self.enemy_monster["hp"] = max(0, self.enemy_monster["hp"]+self.enemy_monster["defense"] - damage)

        # 效果訊息
        if mult > 1:
            eff = "It's super effective!"
        elif mult < 1:
            eff = "Not very effective..."
        else:
            eff = ""

        self.message = f"{self.player_monster['name']} dealt {damage}! {eff}"
        self.message_timer = 2.0

        # 敵人震動效果
        self.enemy_shake_timer = 0.4

        self.battle_state = "player_anim"


    def enemy_attack(self):
        if self.enemy_monster["hp"] <= 0:
            return

        self.enemy_is_attacking = True
        self.enemy_frame_index = 0
        self.enemy_anim_timer = 0.0
        self.current_enemy_anim = self.get_attack_anim(self.enemy_monster["element"])

        mult = compute_element_multiplier(self.enemy_monster["element"], self.player_monster["element"])
        base_damage = self.enemy_monster["attack"]
        damage = int((base_damage + random.randint(1, 5)) * mult)
        damage = max(1, damage - self.player_defense_buff)

        self.player_monster["hp"] = max(0, self.player_monster["hp"]+ self.player_monster["defense"] - damage)

        # 效果訊息
        if mult > 1:
            eff = "It's super effective!"
        elif mult < 1:
            eff = "Not very effective..."
        else:
            eff = ""

        self.message = f"{self.enemy_monster['name']} dealt {damage}! {eff}"
        self.message_timer = 2.0

        # 玩家shake
        self.player_shake_timer = 0.4

        self.battle_state = "enemy_anim"

    def run_away(self):
        """逃跑"""
        if self.turn != "player" or self.battle_state != "choose_action":
            return
            
        if random.random() < 0.5:
            self.message = "Got away safely!"
            self.message_timer = 2.5
            self.battle_state = "game_over"
        else:
            self.message = "Can't escape!"
            self.message_timer = 2.0
            self.turn = "player"
            self.battle_state = "choose_action"

    def open_item_menu(self):
        """打開道具選單"""
        if self.turn == "player" and self.battle_state == "choose_action":
            self.item_menu_open = True

    def use_item(self, item_name):
        """使用道具"""
        if not self.item_menu_open:
            return
        
        # 檢查道具是否存在
        has_item = False
        for item in self.game_manager.bag._items_data:
            if item.name == item_name and item.count > 0:
                has_item = True
                break
        
        if not has_item:
            self.message = f"You don't have any {item_name}!"
            self.message_timer = 2.5
            self.item_menu_open = False
            return

        # 使用道具效果
        if item_name == "Potion":
            heal = 40
            self.player_monster["hp"] = min(
                self.player_monster["hp"] + heal,
                self.player_monster["max_hp"]
            )
            self.message = f"Recovered {heal} HP!"
            self.game_manager.bag.del_item("Potion")

        elif item_name == "Strength Potion":
            self.player_attack_buff += 10
            self.message_timer = 2.2
            self.message = f"{self.player_monster['name']}'s attack + 10!"
            self.game_manager.bag.del_item("Strength Potion")

        elif item_name == "Defense Potion":
            self.player_defense_buff += 10
            self.message_timer = 2.2
            self.message = f"{self.player_monster['name']}'s defense +10!"
            self.game_manager.bag.del_item("Defense Potion")

        self.item_menu_open = False
        self.message_timer = 2.2
        self.turn = "enemy"
        self.battle_state = "item_used"
           

    @override
    def enter(self) -> None:
        #n
        self.do_intro = True
        """進入戰鬥場景"""
        # 如果沒有 game_manager，嘗試從 GameScene 獲取
        if self.game_manager is None:
            from src.scenes.game_scene import GameScene
            # 直接從 scene_manager._scenes 獲取
            if "game" in scene_manager._scenes:
                game_scene = scene_manager._scenes["game"]
                if isinstance(game_scene, GameScene) and hasattr(game_scene, 'game_manager'):
                    self.game_manager = game_scene.game_manager
                    Logger.info("BattleScene: Got game_manager from GameScene")
        
        if self.game_manager is None:
            Logger.error("BattleScene: No game_manager available!")
            scene_manager.change_scene("game")
            return
        
        sound_manager.play_bgm("RBY 106 Rival Appears!.ogg")
        sound_manager.set_bgm_volume(GameSettings.AUDIO_VOLUME)
        
        # 重置戰鬥狀態
        self.turn = "player"
        self.battle_state = "choose_monster"
        self.message = "Choose your monster!"
        self.message_timer = 2.2
        self.player_attack_buff = 0
        self.player_defense_buff = 0
        self.item_menu_open = False
        self.selected_monster_index = None
        self.player_monster = None
        
        monsters = self.game_manager.bag._monsters_data
        self.monster_select_buttons.clear()

        for i in range(len(monsters)):
            row = i // 3
            col = i % 3
            btn = Button(
                "UI/raw/UI_Flat_Banner03a.png",
                "UI/raw/UI_Flat_Banner03a.png",
                300 + col * 250,
                200 + row * 120,
                220,
                100,
                lambda idx=i: self.select_monster(idx)
            )
            self.monster_select_buttons.append(btn)
        # 生成隨機敵人
        self.generate_random_enemy()
        self.load_enemy_sprite()
        #n
        

        self.enemy_idle_anim = MonsterStaticSprite(
            "assets/images/" + self.enemy_monster["spriteenter"]
        )
        self.intro_anim = BattleIntroAnimation(self.enemy_idle_anim, enable_shake=False)
        

    def load_enemy_sprite(self):
        """只載入敵人圖片"""
        try:
            path = "assets/images/" + self.enemy_monster["sprite_path"]
            self.enemy_frames = self._load_animated_frames(path, frame_w=96, frame_h=96, count=4, scale=(150,150))
            if self.enemy_frames:
                self.enemy_frame_index = 0
                self.enemy_sprite = self.enemy_frames[0]
            else:
                self.enemy_sprite = pg.image.load(path).convert_alpha()
                self.enemy_sprite = pg.transform.scale(self.enemy_sprite, (150,150))
        except Exception as e:
            Logger.error(f"Failed to load enemy sprite: {e}")
            self.enemy_sprite = None

    @override
    def exit(self) -> None:
        """離開戰鬥場景"""
        self.restore_monsters()

    @override
    def update(self, dt: float):
        """更新戰鬥邏輯"""
        ATTACK_MOVE_DISTANCE = 40
        ATTACK_MOVE_SPEED = 200 
        # Always update idle animations for monsters
        # player
        if self.player_is_attacking and self.player_frames and len(self.player_frames) > 1:
            self.player_anim_timer += dt
            if self.player_anim_timer >= self.monster_anim_speed:
                self.player_anim_timer = 0.0
                self.player_frame_index += 1

                if self.player_frame_index >= len(self.player_frames):
                    self.player_frame_index = 0
                    self.player_is_attacking = False

                self.player_sprite = self.player_frames[self.player_frame_index]
        else:
            # 沒攻擊 → 固定第一幀
            if self.player_frames:
                self.player_sprite = self.player_frames[0]
        
        # enemy
        if self.enemy_is_attacking and self.enemy_frames and len(self.enemy_frames) > 1:
            self.enemy_anim_timer += dt
            if self.enemy_anim_timer >= self.monster_anim_speed:
                self.enemy_anim_timer = 0.0
                self.enemy_frame_index += 1

                if self.enemy_frame_index >= len(self.enemy_frames):
                    self.enemy_frame_index = 0
                    self.enemy_is_attacking = False

                self.enemy_sprite = self.enemy_frames[self.enemy_frame_index]
        else:
            # 沒攻擊 → 固定第一幀
            if self.enemy_frames:
                self.enemy_sprite = self.enemy_frames[0]

        if self.player_is_attacking:
            self.player_attack_offset += ATTACK_MOVE_SPEED * dt
            if self.player_attack_offset >= ATTACK_MOVE_DISTANCE:
                self.player_attack_offset = ATTACK_MOVE_DISTANCE
        else:
            self.player_attack_offset = max(0, self.player_attack_offset - ATTACK_MOVE_SPEED * dt)

        if self.enemy_is_attacking:
            self.enemy_attack_offset -= ATTACK_MOVE_SPEED * dt
            if self.enemy_attack_offset <= -ATTACK_MOVE_DISTANCE:
                self.enemy_attack_offset = -ATTACK_MOVE_DISTANCE
        else:
            self.enemy_attack_offset = min(0, self.enemy_attack_offset + ATTACK_MOVE_SPEED * dt)

        # Shake timer
        if self.enemy_shake_timer > 0:
            self.enemy_shake_timer -= dt
        if self.player_shake_timer > 0:
            self.player_shake_timer -= dt
        
        #n
        if self.do_intro:
            self.intro_anim.update(dt)
            if self.intro_anim.done:
                self.do_intro = False
                self.battle_state = "choose_monster"
                sound_manager.play_bgm("RBY 107 Battle! (Trainer).ogg")
                sound_manager.set_bgm_volume(GameSettings.AUDIO_VOLUME)
            
        # 怪獸選擇階段
        if self.battle_state == "choose_monster":
            for i, btn in enumerate(self.monster_select_buttons):
                if i < len(self.game_manager.bag._monsters_data):
                    btn.update(dt)
            return
        
        # 更新訊息計時器
        if self.message_timer > 0:
            self.message_timer -= dt
            
            if self.message_timer > 0:
                pass   # 有文字時，不跑後續
            else:
                self.message = ""
        
        if self.battle_state == "item_used":
            if self.message_timer <= 0:
                self.battle_state = "enemy_attack_start"
            return
        
        if self.battle_state == "player_anim":
            if self.current_player_anim:
                self.current_player_anim.update(dt)
            if self.message_timer <= 0:
                # stop drawing the attack effect
                self.current_player_anim = None
                if self.enemy_monster["hp"] <= 0:

                    self._handle_win()
        
                else:
                    self.turn = "enemy"
                    self.battle_state = "enemy_attack_start"
            return

        if self.battle_state == "enemy_attack_start":
            self.enemy_attack()
            return

        if self.battle_state == "enemy_anim":
            if self.current_enemy_anim:
                self.current_enemy_anim.update(dt)
            if self.message_timer <= 0:
                # stop drawing the attack effect
                self.current_enemy_anim = None
                if self.player_monster["hp"] <= 0:
                    self.message = "You fainted!"
                    self.message_timer = 2.5
                    self.battle_state = "game_over"
                else:
                    self.turn = "player"
                    self.battle_state = "choose_action"
                    self.message = "What will you do?"

            return


        # 遊戲結束
        if self.battle_state == "game_over" and self.message_timer <= 0:
            
            scene_manager.change_scene("game")
        
        # 更新按鈕
        if self.battle_state == "choose_action":
            self.attack_button.update(dt)
            self.item_button.update(dt)
            self.run_button.update(dt)
            if self.item_menu_open:
                for btn in self.item_buttons:
                    btn.update(dt)
                return

    @override
    def draw(self, screen):
        if self.do_intro:
            self.background.draw(screen)
            self.intro_anim.draw(screen)
            return
        """繪製戰鬥畫面"""
        self.background.draw(screen)

        # 怪獸選擇畫面
        if self.battle_state == "choose_monster":
            self.draw_monster_selection(screen)
            return

        # 計算並繪製敵我精靈（一次 blit，含攻擊位移與 shake）
        enemy_base_offset = -5 if self.enemy_shake_timer > 0 else 0
        enemy_base_x = 900 + enemy_base_offset
        enemy_x = int(enemy_base_x + self.enemy_attack_offset)
        enemy_y = 100
        if self.enemy_sprite:
            screen.blit(self.enemy_sprite, (enemy_x, enemy_y))

        player_base_offset = -5 if self.player_shake_timer > 0 else 0
        player_base_x = 150 + player_base_offset
        player_x = int(player_base_x + self.player_attack_offset)
        player_y = 250
        player_spriteflipped = None
        if self.player_sprite:
            player_spriteflipped = pg.transform.flip(self.player_sprite, True, False)
            screen.blit(player_spriteflipped, (player_x, player_y))

        # 繪製攻擊特效（大畫面動畫）
        player_center_x = player_base_x - 75
        player_center_y = player_y - 75
        enemy_center_x = enemy_base_x - 75
        enemy_center_y = enemy_y - 75
        if self.current_enemy_anim:
            self.current_enemy_anim.draw(screen, player_center_x, player_center_y, scale=5)
        if self.current_player_anim:
            self.current_player_anim.draw(screen, enemy_center_x, enemy_center_y, scale=5, flip=True)

        # HP條
        self.draw_hp_bar(screen, 750, 280, 200, 20, 
                        self.enemy_monster["hp"]/self.enemy_monster["max_hp"])
        self.draw_hp_bar(screen, 100, 450, 200, 20, 
                        self.player_monster["hp"]/self.player_monster["max_hp"])

        # 怪獸資訊
        enemy_info = self.font_small.render(
            f"{self.enemy_monster['name']} Lv.{self.enemy_monster['level']} ({self.enemy_monster['element']})", 
            True, (255, 255, 255)
        )
        screen.blit(enemy_info, (750, 250))
        
        player_info = self.font_small.render(
            f"{self.player_monster['name']} Lv.{self.player_monster['level']} ({self.player_monster['element']})", 
            True, (255, 255, 255)
        )
        screen.blit(player_info, (100, 420))

        # 訊息框
        box = pg.Surface((1280, 200))
        box.set_alpha(180)
        box.fill((30, 30, 30))
        screen.blit(box, (0, 500))

        msg = self.font_medium.render(self.message, True, (255, 255, 255))
        screen.blit(msg, (80, 530))

        # UI按鈕
        if not self.item_menu_open:
            if self.turn == "player" and self.battle_state == "choose_action":
                self.attack_button.draw(screen)
                self.item_button.draw(screen)
                self.run_button.draw(screen)

                screen.blit(self.font_small.render("Attack", True, (0, 0, 0)), (430, 590))
                screen.blit(self.font_small.render("Items", True, (0, 0, 0)), (585, 590))
                screen.blit(self.font_small.render("Run", True, (0, 0, 0)), (735, 590))
        else:
            # --- 背景遮罩 ---
            overlay = pg.Surface((1280, 720), pg.SRCALPHA)
            overlay.fill((0, 0, 0, 180))
            screen.blit(overlay, (0, 0))

            # --- 菜單視窗 ---
            menu_w, menu_h = 450, 300
            menu_x = (1280 - menu_w) // 2
            menu_y = (720 - menu_h) // 2

            menu_bg = pg.Surface((menu_w, menu_h))
            menu_bg.fill((50, 50, 60))
            pg.draw.rect(menu_bg, (255, 255, 255), (0, 0, menu_w, menu_h), 4)
            screen.blit(menu_bg, (menu_x, menu_y))

            # --- 標題 ---
            title = self.font_medium.render("Choose an Item", True, (255, 255, 100))
            screen.blit(title, (menu_x + menu_w//2 - title.get_width()//2, menu_y + 20))

            # --- 更新按鈕位置（置中） ---
            btn_w, btn_h = 250, 50
            start_y = menu_y + 90

            for i, btn in enumerate(self.item_buttons):
                btn.rect.x = menu_x + (menu_w - btn_w)//2
                btn.rect.y = start_y + i * 70
                btn.rect.width = btn_w
                btn.rect.height = btn_h

                btn.draw(screen)

                txt = ["Potion", "Strength Potion", "Defense Potion"][i]
                label = self.font_small.render(txt, True, (0, 0, 0))
                screen.blit(label, (btn.rect.x + btn_w//2 - label.get_width()//2,
                                    btn.rect.y + btn_h//2 - label.get_height()//2))

    def draw_monster_selection(self, screen):
        """繪製怪獸選擇畫面"""
        # 半透明背景
        overlay = pg.Surface((1280, 720))
        overlay.set_alpha(200)
        overlay.fill((20, 20, 40))
        screen.blit(overlay, (0, 0))
        
        # 標題
        title = self.font_large.render("Choose Your Monster!", True, (255, 255, 100))
        screen.blit(title, (400, 80))
        
        # 敵人預覽
        enemy_text = self.font_medium.render(
            f"VS: {self.enemy_monster['name']} Lv.{self.enemy_monster['level']}", 
            True, (255, 100, 100)
        )
        screen.blit(enemy_text, (450, 130))
        
        monsters = self.game_manager.bag._monsters_data
        
        for i, btn in enumerate(self.monster_select_buttons):
            if i >= len(monsters):
                break
            
            mon = monsters[i]
            btn.draw(screen)
            
            # 怪獸圖片
            try:
                img = pg.image.load("assets/images/" + mon.sprite_path).convert_alpha()
                img = pg.transform.scale(img, (60, 60))
                screen.blit(img, (btn.rect.x + 10, btn.rect.y + 20))
            except:
                pass
            
            # 怪獸資訊
            name_text = self.font_small.render(mon.name, True, (0, 0, 0))
            screen.blit(name_text, (btn.rect.x + 80, btn.rect.y + 15))
            
            level_text = self.font_small.render(f"Lv.{mon.level}", True, (0, 0, 0))
            screen.blit(level_text, (btn.rect.x + 80, btn.rect.y + 40))
            
            element_text = self.font_small.render(mon.element, True, (0, 0, 0))
            screen.blit(element_text, (btn.rect.x + 80, btn.rect.y + 65))

    def draw_hp_bar(self, screen, x, y, w, h, ratio):
        """繪製HP條"""
        pg.draw.rect(screen, (200, 0, 0), (x, y, w, h))
        pg.draw.rect(screen, (0, 255, 0), (x, y, w * ratio, h))
        pg.draw.rect(screen, (255, 255, 255), (x, y, w, h), 2)


    #   NEW: 戰鬥勝利後的處理邏輯 (Requirement 1 & 2)
    def _handle_win(self):
        # 1. 處理戰鬥中的怪獸升級和回血
        if self.player_monster and self.selected_monster_index is not None:
            # 取得 Bag 中的怪獸實例，確保永久修改
            monster_in_bag = self.game_manager.bag._monsters_data[self.selected_monster_index]
            
            # 紀錄升級前等級
            self.old_level = monster_in_bag.level #  

            # 升級
            monster_in_bag.level += 1
            monster_in_bag.attack += 10
            monster_in_bag.defense += 10
            # 血量更新至生命最大值
            monster_in_bag.hp = monster_in_bag.max_hp
            
            Logger.info(f"{monster_in_bag.name} leveled up to Lv.{monster_in_bag.level} and was healed to max HP.")
            
            self.evolution_message = None
            if self.game_manager and self.game_manager.evolution_manager:
                if self.game_manager.evolution_manager.can_evolve(monster_in_bag):
                    #   NEW: 如果可以進化，則提示玩家
                    self.evolution_message = f"{monster_in_bag.name} is ready to Evolve!"
                    
            # 3. 處理金錢獎勵 (假設固定獎勵 25)
            money_reward = 25 
            if self.game_manager and self.game_manager.bag:
                self.game_manager.bag.add_money(money_reward)
            
            # 4. 設置勝利和升級訊息
            self.battle_state = "game_over" 
            
            #   MODIFIED: 顯示升級資訊，如果同時有進化提示則組合
            level_msg = f"{monster_in_bag.name} LV UP! ({self.old_level} -> {monster_in_bag.level}) Reward: {money_reward} Money."
            
            if self.evolution_message:
                # 如果有進化提示，則將升級訊息和進化提示組合起來
                self.message = level_msg + " " + self.evolution_message
            else:
                self.message = level_msg
                
            self.message_timer = 5.0
            
        else:
            self.battle_state = "game_over" 
            self.message = "Battle ended."
            self.message_timer = 3.0

    