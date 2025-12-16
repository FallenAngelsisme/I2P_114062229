import pygame as pg
import math

# --- MonsterStaticSprite 類保持不變 ---
class MonsterStaticSprite:
    """只取 sprite sheet 的左格和右格作為正面與背面"""
    def __init__(self, path): # 移除 frame_width, frame_height 參數
        sheet = pg.image.load(path).convert_alpha()
        
        # --- 採用您的通用動畫切割邏輯 ---
        sheet_w, sheet_h = sheet.get_size()
        
        # 假設：Sprite Sheet 只有一行，但至少有兩幀（正面和背面）
        n_keyframes = 2 
        n_rows = 1 
        
        # 根據整個圖片的尺寸和預期的行/列數，計算單幀的寬高
        frame_w = sheet_w // n_keyframes
        frame_h = sheet_h // n_rows 
        
        # 檢查尺寸是否合理 (可選：增加錯誤處理)
        if frame_w == 0 or frame_h == 0:
            print("Error: Sprite sheet dimensions are too small or keyframes/rows are misconfigured.")
            # 可以拋出錯誤或使用預設值
            
        # -----------------------------------
        
        # 左邊格子 (正面): 位於 (0, 0)
        self.front = sheet.subsurface(pg.Rect(
            0 * frame_w, 0 * frame_h, 
            frame_w, frame_h
        ))
        
        # 右邊格子 (背面): 位於 (1 * frame_w, 0)
        self.back = sheet.subsurface(pg.Rect(
            1 * frame_w, 0 * frame_h, 
            frame_w, frame_h
        ))
    def draw_front(self, screen, x, y, scale=5, flip=True):
        frame = pg.transform.scale(
            self.front,
            (self.front.get_width() * scale, self.front.get_height() * scale)
        )

        if flip:
            frame = pg.transform.flip(frame, True, False)

        screen.blit(frame, (x, y))

    def draw_back(self, screen, x, y, scale=5, flip=True):
        frame = pg.transform.scale(
            self.back,
            (self.back.get_width() * scale, self.back.get_height() * scale)
        )

        if flip:
            frame = pg.transform.flip(frame, True, False)

        screen.blit(frame, (x, y))

    def update(self, dt):
        # 這裡原本有動畫邏輯，但 MonsterStaticSprite 似乎只用於靜態展示，故保留或移除依實際需求
        pass 
        
    def draw(self, screen, x, y, scale=3, flip=False):
        # 這裡原本是動畫邏輯，為避免混淆，暫時不使用
        pass
# --- 輔助函數：緩動 (Easing) ---

# 可以在進場和退場時提供更平滑、更有衝擊力的動畫效果
def ease_out_quart(t):
    """四次方緩動函數（從慢到快，然後急停）"""
    return 1 - (1 - t) ** 4

def ease_in_quart(t):
    """四次方緩動函數（從快到慢，然後急停）"""
    return t ** 4

# --- 新增的螢幕震動類 ---
class ScreenShake:
    def __init__(self, duration, magnitude=5):
        self.duration = duration  # 震動持續時間
        self.magnitude = magnitude  # 震動幅度
        self.timer = 0
        self.offset_x = 0
        self.offset_y = 0
    
    def update(self, dt):
        self.timer += dt
        if self.timer < self.duration:
            # 使用隨機數生成震動偏移
            # magnitude * (1 - t) 讓震動幅度隨時間衰減
            decay_factor = 1 - (self.timer / self.duration)
            self.offset_x = (pg.math.Vector2.from_polar((self.magnitude * decay_factor, pg.time.get_ticks() * 10)) * math.sin(self.timer * 50)).x 
            self.offset_y = (pg.math.Vector2.from_polar((self.magnitude * decay_factor, pg.time.get_ticks() * 10)) * math.cos(self.timer * 50)).y
        else:
            self.offset_x = 0
            self.offset_y = 0
            
    def get_offset(self):
        return (int(self.offset_x), int(self.offset_y))

# --- 加強後的 BattleIntroAnimation ---
class BattleIntroAnimation:
    def __init__(self, enemy_idle: MonsterStaticSprite, enable_shake: bool = True):
        self.enemy_idle = enemy_idle
        self.enable_shake = enable_shake

        self.time = 0
        self.stage = 0
        self.done = False

        # 螢幕尺寸
        self.screen_width = 1280
        self.screen_height = 720

        # 黑幕
        self.black_height = 200

        # 動畫時間
        self.intro_duration = 1.0
        self.hold_duration = 1.5
        self.outro_duration = 0.8

        # 黑幕最終位置
        self.END_Y_TOP = 0
        self.END_Y_BOTTOM = self.screen_height - self.black_height

        # 敵人固定位置
        self.left_x, self.left_y = 280, 140
        self.right_x, self.right_y = 750, 100

        # 震動
        self.shake = ScreenShake(duration=0.3, magnitude=10) if enable_shake else None

    # -------------------------
    # 斜切黑幕
    # -------------------------
    def draw_slanted_black(self, screen, y, flip=False):
        cut = 280
        over = 300

        if not flip:
            points = [
                (-over, y),                             # V1：左上角 (水平)
                (self.screen_width + over, y),          # V2：右上角 (水平)
                (self.screen_width + over, y + self.black_height), # V3：右下角 (垂直)
                (-over + cut, y + self.black_height)    # V4：左下角 (斜切)
            ]
        else:
            points = [
                (-over + cut, y),
                (self.screen_width + over, y),
                (self.screen_width + over, y + self.black_height),
                (-over, y + self.black_height)
            ]

        pg.draw.polygon(screen, (0, 0, 0), points)

    # -------------------------
    # Update
    # -------------------------
    def update(self, dt):
        if self.done:
            return

        self.time += dt

        if self.stage == 0:
            if self.time >= self.intro_duration:
                self.stage = 1
                self.time = 0
                if self.enable_shake:
                    self.shake = ScreenShake(duration=0.3, magnitude=10)

        elif self.stage == 1:
            if self.enable_shake and self.shake:
                self.shake.update(dt)

            if self.time >= self.hold_duration:
                self.stage = 2
                self.time = 0

        elif self.stage == 2:
            if self.time >= self.outro_duration:
                self.done = True
                self.stage = 3

    # -------------------------
    # Draw
    # -------------------------
    def draw(self, screen):
        # 震動偏移（安全）
        if self.enable_shake and self.shake:
            offset_x, offset_y = self.shake.get_offset()
        else:
            offset_x, offset_y = 0, 0

        if self.stage == 0:
            t = min(1, self.time / self.intro_duration)
            eased = ease_out_quart(t)

            top_y = -self.black_height + (self.black_height) * eased
            bottom_y = self.screen_height - (self.black_height) * eased

            self.draw_slanted_black(screen, top_y + offset_y, flip=False)

            if self.enemy_idle:
                self.enemy_idle.draw_front(screen, self.left_x, self.left_y, scale=5)
                self.enemy_idle.draw_back(screen, self.right_x, self.right_y, scale=5)
            
            self.draw_slanted_black(screen, bottom_y + offset_y, flip=True)
        elif self.stage == 1:
            
            self.draw_slanted_black(screen, self.END_Y_TOP + offset_y, flip=False)
            if self.enemy_idle:
                self.enemy_idle.draw_back(screen, self.right_x, self.right_y, scale=5)
                if self.time > 0.3 or int(self.time * 10) % 2 == 0:
                    self.enemy_idle.draw_front(screen, self.left_x, self.left_y, scale=5)
            
            self.draw_slanted_black(screen, self.END_Y_BOTTOM + offset_y, flip=True)
        elif self.stage == 2:
            t = min(1, self.time / self.outro_duration)
            eased = ease_in_quart(t)

            top_y = self.END_Y_TOP * (1 - eased) + (-self.black_height) * eased
            bottom_y = self.END_Y_BOTTOM * (1 - eased) + self.screen_height * eased

            
            self.draw_slanted_black(screen, top_y + offset_y, flip=False)
            if self.enemy_idle:
                self.enemy_idle.draw_front(screen, self.left_x, self.left_y, scale=5)
                self.enemy_idle.draw_back(screen, self.right_x, self.right_y, scale=5)
            
            self.draw_slanted_black(screen, bottom_y + offset_y, flip=True)