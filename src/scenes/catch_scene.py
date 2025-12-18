import pygame as pg
import random
from src.sprites import BackgroundSprite
from src.sprites.animation_catch import TargetSprite, PokeballSprite

from src.scenes.scene import Scene
from src.core import GameManager
from src.utils import Logger, GameSettings
from src.utils.definition import Monster
from src.core.services import scene_manager, sound_manager
from src.interface.components import Button
from typing import override

# Constants for the Catch State Machine
class CatchState:
    WILD_APPEAR = 0       # 剛進入，顯示 'A wild X appeared!'
    WAITING_ACTION = 1    # 等待玩家按下 CATCH 或 RUN，瞄準遊戲啟動
    THROWING_BALL = 2     # 寶貝球在空中
    SHAKING = 3           # 寶貝球在晃動
    CAUGHT = 4            # 捕捉成功，顯示 'Gotcha!'
    FAILED = 5            # 捕捉失敗或逃跑，顯示結果
    TRANSITION = 6        # 訊息結束，準備切換場景


class CatchPokemonScene(Scene):
    def __init__(self, game_manager: GameManager):
        super().__init__()
        self.game_manager = game_manager
        
        # --- 寶可夢數據 ---
        self.wild_pokemon = self._generate_wild_pokemon()
        self.catch_attempts = 0
        self.max_attempts = 3
        self.base_catch_rate = 0.5
        
        # --- 狀態機 ---
        self.catch_state = CatchState.WILD_APPEAR
        
        # --- UI Elements ---
        self.background = BackgroundSprite("backgrounds/background1.png")
        self.font_small = pg.font.Font("assets/fonts/Minecraft.ttf", 20)
        self.font_medium = pg.font.Font("assets/fonts/Minecraft.ttf", 30)
        self.font_large = pg.font.Font("assets/fonts/Minecraft.ttf", 40)
        
        # --- 動畫/Sprite 載入 (新的方法) ---
        self._load_pokemon_sprite_sheet() # 新增：載入動畫幀
        self._setup_target_sprite()       # 新增：設置瞄準框
        self.pokeball_animation = None    # 用於投擲/晃動的 PokeballSprite 實例
        self.pokemon_animation_timer = 0.0
        self.pokemon_frame_index = 0
        
        # --- 訊息顯示 ---
        self.message = f"A wild {self.wild_pokemon['name']} appeared!"
        self.message_timer = 2.0
        
        # --- 按鈕 (維持原樣) ---
        self.catch_button = Button("UI/raw/UI_Flat_Button02a_3.png", "UI/raw/UI_Flat_Button02a_3.png",
                                   450, 500, 150, 50, self.start_catch_attempt) # 函數名稱變更
        self.run_button = Button("UI/raw/UI_Flat_Button02a_3.png", "UI/raw/UI_Flat_Button02a_3.png",
                                 650, 500, 150, 50, self.run_away)

    def _load_pokemon_sprite_sheet(self):
        """載入並切割寶可夢的 Sprite Sheet (1. 寶可夢動畫)"""
        try:
            path = "assets/images/" + self.wild_pokemon["sprite_path"]
            sheet = pg.image.load(path).convert_alpha()
            sheet_w, sheet_h = sheet.get_size()
            
            # 假設：sheet 只有一行，有 4 幀
            n_keyframes = 4 
            n_rows = 1 
            frame_w = sheet_w // n_keyframes
            frame_h = sheet_h // n_rows 
            
            self.pokemon_frames = []
            for i in range(n_keyframes):
                frame = pg.Surface((frame_w, frame_h), pg.SRCALPHA)
                frame.blit(sheet, (0, 0), (i * frame_w, 0, frame_w, frame_h))
                # 縮放至顯示大小
                self.pokemon_frames.append(pg.transform.scale(frame, (200, 200)))
                
            self.pokemon_sprite = self.pokemon_frames[0]
            self.pokemon_frame_rate = 0.2 # 每 0.2 秒換一幀
            
        except Exception as e:
            self.pokemon_sprite = None
            self.pokemon_frames = []
            Logger.warning(f"Could not load or process sprite sheet: {self.wild_pokemon['sprite_path']}. Error: {e}")

    def _setup_target_sprite(self):
        """設置瞄準框 Sprite (6. 瞄準遊戲機制)"""
        target_frames_paths = [
            "assets/images/UI/raw/UI_Flat_Select01a_1.png",
            "assets/images/UI/raw/UI_Flat_Select01a_2.png",
            "assets/images/UI/raw/UI_Flat_Select01a_3.png",
            "assets/images/UI/raw/UI_Flat_Select01a_4.png",
        ]
        
        # 讓瞄準框在寶可夢的中心位置
        target_center = (GameSettings.SCREEN_WIDTH // 2, 250)
        target_size = (100, 100)
        
        # 假設 TargetSprite 已如上方定義
        self.target_sprite = TargetSprite(target_frames_paths, target_center, target_size)
        
        # 瞄準判定屬性
        self.is_targeting = False
        self.target_success_rate_modifier = 0.0

    def get_pokeball_count(self) -> int:
        """獲取寶貝球數量"""
        for item in self.game_manager.bag._items_data:
            if item.name == "Pokeball":
                return item.count
        return 0
    
    def start_catch_attempt(self):
        """點擊 CATCH 按鈕時，啟動瞄準或立即進入投擲"""
        if self.catch_state != CatchState.WAITING_ACTION:
            return

        if self.get_pokeball_count() == 0:
            self.message = "No Pokeballs left!"
            self.message_timer = 1.5
            self.catch_state = CatchState.FAILED # 進入失敗狀態
            return
            
        # 6. 捕捉的方式：判斷瞄準
        mouse_x, mouse_y = pg.mouse.get_pos()
        target_rect = self.target_sprite.rect
        
        if target_rect.collidepoint(mouse_x, mouse_y):
            # 點擊成功，給予捕捉率加成
            self.target_success_rate_modifier = 0.3 # 成功瞄準 +30% 捕捉率
            sound_manager.play_bgm("RBY 119 Captured a Pokemon!.ogg") # 新增音效
            self.message = "Great throw! Prepare to catch..."
        else:
            self.target_success_rate_modifier = 0.0
            self.message = "Threw the Pokeball..."
            
        # 消耗寶貝球
        self.game_manager.bag.del_item("Pokeball")
        self.catch_attempts += 1
        
        # 啟動投擲動畫
        # 寶貝球起始位置 (畫面下方中央)
        start_pos = (GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT - 50)
        # 寶可夢位置 (中間平台)
        target_pos = (GameSettings.SCREEN_WIDTH // 2 - 20, 300) 
        
        # 2. 投擲寶貝球動畫
        self.pokeball_animation = PokeballSprite(start_pos, target_pos)
        #sound_manager.play_bgm("pokeball_throw.wav") # 新增音效
        self.catch_state = CatchState.THROWING_BALL
        self.message_timer = 0.5 # 訊息停留短暫時間，讓動畫接上

    def calculate_catch_success(self) -> bool:
        """計算並判定捕捉是否成功"""
        
        # 基礎率 + 嘗試次數加成 + 瞄準加成
        catch_rate = self.base_catch_rate + (self.catch_attempts * 0.15) + self.target_success_rate_modifier
        
        # 確保捕捉率不超過 1.0
        catch_rate = min(catch_rate, 1.0) 
        
        success = random.random() < catch_rate
        
        if success:
            # 5. 捕捉成功音效
            sound_manager.play_bgm("RBY 122 Obtained a Pokemon!.ogg") 
            self.message = f"Gotcha! {self.wild_pokemon['name']} was caught!"
            self.message_timer = 2.5
            
            # 新增寶可夢到背包
            level = self.wild_pokemon['level']
            max_hp = 30 + (level * 5)
            caught_monster = Monster(
                name=self.wild_pokemon['name'], hp=max_hp, max_hp=max_hp, level=level,
                sprite_path=self.wild_pokemon['sprite_path']
            )
            self.game_manager.bag.add_monster(caught_monster)
            return True
        else:
            # 捕捉失敗音效
            #sound_manager.play_bgm("catch_fail.wav") 
            self.message = f"Oh no! {self.wild_pokemon['name']} broke free!"
            self.message_timer = 2.5
            return False

    def run_away(self):
        """逃跑，直接進入失敗狀態"""
        if self.catch_state == CatchState.WAITING_ACTION:
            self.message = "Got away safely!"
            self.message_timer = 1.5
            self.catch_state = CatchState.FAILED
    
    def _generate_wild_pokemon(self):
        """Generate a random wild pokemon我先自己設"""
        pokemon_list = [
            {"name": "Pikachu", "level": random.randint(3, 7), "sprite_path": "menu_sprites/menusprite1.png"},
            {"name": "Charmander", "level": random.randint(3, 7), "sprite_path": "menu_sprites/menusprite2.png"},
            {"name": "Bulbasaur", "level": random.randint(3, 7), "sprite_path": "menu_sprites/menusprite3.png"},
            {"name": "Squirtle", "level": random.randint(3, 7), "sprite_path": "menu_sprites/menusprite4.png"},
        ]
        return random.choice(pokemon_list)
    @override
    def enter(self) -> None:
        # G. 寶可夢叫聲
        sound_manager.play_bgm("RBY 110 Battle! (Wild Pokemon).ogg")
        #sound_manager.play_bgm(f"{self.wild_pokemon['name'].lower()}_cry.wav") # 假設有叫聲檔案
        sound_manager.set_bgm_volume(GameSettings.AUDIO_VOLUME)
        self.catch_state = CatchState.WILD_APPEAR

    @override
    def update(self, dt: float):
        # 寶可夢動畫更新 (1. 寶可夢動畫)
        if self.catch_state not in [CatchState.THROWING_BALL, CatchState.SHAKING]:
            self.pokemon_animation_timer += dt
            if self.pokemon_animation_timer >= self.pokemon_frame_rate and self.pokemon_frames:
                self.pokemon_animation_timer = 0.0
                self.pokemon_frame_index = (self.pokemon_frame_index + 1) % len(self.pokemon_frames)
                self.pokemon_sprite = self.pokemon_frames[self.pokemon_frame_index]
        
        # 狀態機邏輯
        if self.catch_state == CatchState.WILD_APPEAR:
            # 等待初始訊息結束
            if self.message_timer > 0:
                self.message_timer -= dt
            else:
                self.message = "Select an action."
                self.catch_state = CatchState.WAITING_ACTION
                self.target_sprite.is_active = True # 瞄準框開始活動
                
        elif self.catch_state == CatchState.WAITING_ACTION:
            # 更新按鈕和瞄準框
            self.catch_button.update(dt)
            self.run_button.update(dt)
            self.target_sprite.update(dt)
            
        elif self.catch_state == CatchState.THROWING_BALL:
            # 投擲動畫 (2. 投擲寶貝球動畫)
            if self.pokeball_animation and self.pokeball_animation.update(dt):
                # 投擲完成，隱藏寶可夢，進入晃動狀態
                self.pokemon_sprite = None # 隱藏寶可夢，被收進球
                self.pokeball_animation.is_shaking = True
                self.catch_state = CatchState.SHAKING
                self.message = "Pokeball wiggles..."
        
        elif self.catch_state == CatchState.SHAKING:
            # 晃動動畫 (3. 捕捉成功/失敗動畫)
            if self.pokeball_animation and self.pokeball_animation.update(dt):
                # 晃動結束，進行最終判定
                is_caught = self.calculate_catch_success()
                
                if is_caught:
                    self.catch_state = CatchState.CAUGHT
                    self.pokeball_animation = None # 捕捉成功，球消失
                else:
                    self.catch_state = CatchState.FAILED
                    # 捕捉失敗，重新顯示寶可夢 sprite
                    self.pokemon_sprite = self.pokemon_frames[0] 
                    self.pokeball_animation = None # 球彈開消失
                    
                self.message_timer = 2.5 # 重設訊息計時器
                
        elif self.catch_state in [CatchState.CAUGHT, CatchState.FAILED]:
            # 等待結果訊息結束
            if self.message_timer > 0:
                self.message_timer -= dt
            else:
                self.catch_state = CatchState.TRANSITION
                
        elif self.catch_state == CatchState.TRANSITION:
            # 退出場景
            Logger.info("Returning to game scene")
            scene_manager.change_scene("game")

    @override
    def draw(self, screen: pg.Surface) -> None:
        # Draw background
        self.background.draw(screen)
        
        # Draw pokemon sprite (如果沒有在投擲或晃動狀態)
        if self.pokemon_sprite:
            sprite_x = GameSettings.SCREEN_WIDTH // 2 - 100
            sprite_y = 150
            screen.blit(self.pokemon_sprite, (sprite_x, sprite_y))
        
        # Draw pokemon info
        name_text = self.font_large.render(self.wild_pokemon["name"], True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, 100))
        screen.blit(name_text, name_rect)
        
        level_text = self.font_medium.render(f"Lv. {self.wild_pokemon['level']}", True, (255, 255, 0))
        level_rect = level_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, 380))
        screen.blit(level_text, level_rect)
        
        # 繪製瞄準框 (6. 瞄準遊戲機制)
        if self.catch_state == CatchState.WAITING_ACTION:
            self.target_sprite.draw(screen)
            
        # 繪製投擲中的寶貝球 (2. 投擲寶貝球動畫 & 3. 晃動動畫)
        if self.pokeball_animation:
            screen.blit(self.pokeball_animation.image, self.pokeball_animation.rect)
        
        # 繪製訊息框 (4. 訊息框風格)
        message_bg = pg.Surface((1280, 150))
        message_bg.set_alpha(240) # 稍微不透明一點
        message_bg.fill((30, 30, 30))
        # 加上寶可夢風格的邊框
        pg.draw.rect(message_bg, (50, 50, 200), (0, 0, 1280, 150), 5) 
        
        screen.blit(message_bg, (0, 450))
        
        # Draw message
        message_text = self.font_medium.render(self.message, True, (255, 255, 255))
        message_rect = message_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, 480))
        screen.blit(message_text, message_rect)
        
        # Draw buttons (只有在等待操作時顯示)
        if self.catch_state == CatchState.WAITING_ACTION:
            self.catch_button.draw(screen)
            catch_text = self.font_small.render("CATCH", True, (0, 0, 0))
            screen.blit(catch_text, (490, 510))
            
            self.run_button.draw(screen)
            run_text = self.font_small.render("RUN", True, (0, 0, 0))
            screen.blit(run_text, (695, 510))
            
            # Draw pokeball count
            pokeball_count = self.get_pokeball_count()
            attempts_text = self.font_small.render(
                f"Pokeballs: {pokeball_count}", 
                True, (255, 255, 255)
            )
            screen.blit(attempts_text, (550, 560))