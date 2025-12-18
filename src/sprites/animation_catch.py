import pygame as pg
import random
from .sprite import Sprite

from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.core import GameManager
from src.utils import Logger, GameSettings
from src.utils.definition import Monster
from src.core.services import scene_manager, sound_manager
from src.interface.components import Button
from typing import override
# --- 假設新增的 PokeballSprite 類 (用於動畫) ---
class PokeballSprite(Sprite):
    def __init__(self, start_pos, target_pos):
        super().__init__("ingame_ui/ball.png")
        # 替換成您的 Pokeball 圖片路徑
        self.original_image = pg.image.load("assets/images/ingame_ui/ball.png").convert_alpha() 
        self.original_image = pg.transform.scale(self.original_image, (40, 40))
        self.image = self.original_image
        self.rect = self.image.get_rect(center=start_pos)
        
        self.start_pos = pg.Vector2(start_pos)
        self.target_pos = pg.Vector2(target_pos)
        self.pos = self.start_pos
        
        self.travel_time = 0.5 # 投擲持續時間
        self.elapsed_time = 0.0
        self.toss_height = 100 # 拋物線高度
        
        self.is_shaking = False
        self.shake_time = 0.0
        self.max_shake_count = 3 # 晃動次數
        self.current_shake_count = 0
        self.shake_duration = 0.5 # 每次晃動時長

    def update(self, dt):
        if not self.is_shaking:
            # 投擲動畫 (拋物線)
            self.elapsed_time += dt
            t = self.elapsed_time / self.travel_time
            
            if t >= 1.0:
                # 投擲完成，進入捕捉狀態
                t = 1.0
                return True # 返回 True 通知場景進入下一個狀態
            
            # 線性插值 (Lerp)
            new_x = self.start_pos.x + (self.target_pos.x - self.start_pos.x) * t
            new_y = self.start_pos.y + (self.target_pos.y - self.start_pos.y) * t
            
            # 拋物線高度計算 (使用二次函數)
            parabolic_offset = 4 * self.toss_height * t * (1 - t)
            self.pos = pg.Vector2(new_x, new_y - parabolic_offset)
            self.rect.center = (int(self.pos.x), int(self.pos.y))
            
            # 旋轉效果
            self.image = pg.transform.rotate(self.original_image, -t * 720) # 旋轉 2 圈
            self.rect = self.image.get_rect(center=self.rect.center)
            
            return False
        
        else:
            # 晃動動畫
            if self.current_shake_count < self.max_shake_count:
                self.shake_time += dt
                if self.shake_time >= self.shake_duration:
                    self.shake_time = 0.0
                    self.current_shake_count += 1
                    # 每次晃動結束播放音效（假設寶可夢掙脫的聲音）
                    #sound_manager.play_sfx("pokeball_shake.wav") 
                    
                # 晃動視覺效果：左右平移
                offset = 5 if int(self.shake_time * 10) % 2 == 0 else -5
                self.rect.x = int(self.target_pos.x - 20) + offset 
                self.rect.y = int(self.target_pos.y) # 寶貝球固定在地面
                
                return False
            else:
                # 晃動結束，最終判定結果
                return True # 返回 True 通知場景進行最終判定

# --- 假設新增的 TargetSprite 類 (用於瞄準) ---
class TargetSprite(Sprite):
    def __init__(self, frames_paths, center_pos, size):
        super().__init__("UI/raw/UI_Flat_Select01a_4.png")
        self.frames = []
        for path in frames_paths:
            
            frame = pg.image.load(path).convert_alpha()
            self.frames.append(pg.transform.scale(frame, size))
            
        self.image = self.frames[0]
        self.rect = self.image.get_rect(center=center_pos)
        
        self.animation_timer = 0.0
        self.animation_speed = 0.1 # 每 0.1 秒換一幀
        self.frame_index = 0
        self.is_active = True
        
    def update(self, dt):
        if not self.is_active:
            return

        self.animation_timer += dt
        if self.animation_timer >= self.animation_speed:
            self.animation_timer = 0.0
            self.frame_index = (self.frame_index + 1) % len(self.frames)
            self.image = self.frames[self.frame_index]

    def draw(self, screen):
        if self.is_active:
            screen.blit(self.image, self.rect)