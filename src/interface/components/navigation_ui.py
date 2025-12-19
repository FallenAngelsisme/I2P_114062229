import pygame as pg
from src.interface.components.button import Button
from src.utils import GameSettings

# 假設這是您的 Button 類別，它需要支援文字渲染
# 注意：為了在按鈕上渲染文字，您需要確保您的 Button 類別能處理 `text` 參數
# 這裡我們主要在 NavigationUI 的 draw 方法中手動渲染文字
# 如果您不想修改 Button 類別，下面的 draw 方法將包含手動渲染邏輯

class NavigationUI:
    def __init__(self, nav_manager, font_big, font_medium):
        self.nav_manager = nav_manager
        self.font_big = font_big
        self.font_medium = font_medium

        self.is_open = False
        self.font_title  = pg.font.Font("assets/fonts/Pokemon Solid.ttf", 80)
        # 載入寶可夢風格的橫幅圖片 (作為目的地按鈕底圖)
        # 必須確保路徑正確，並根據您的需求縮放
        try:
            # 假設原始圖片很大，我們將它縮放為適合按鈕的大小
            self.BANNER_WIDTH = 250
            self.BANNER_HEIGHT = 50
            # 增加懸停效果：稍微變亮
        except pg.error as e:
            print(f"無法載入橫幅圖片: {e}")
            self.banner_img = pg.Surface((250, 50))
            self.banner_img.fill((100, 100, 255))
            self.banner_hover_img = self.banner_img # 如果載入失敗，使用預設藍色

        # 地點列表
        self.places = [
            {"name": "Gym", "x": 24, "y": 24},
            {"name": "Hospital", "x": 55, "y": 15},
            {"name": "Poke Center", "x": 16, "y": 28},
            
        ]
        
        # UI 尺寸定義 (用於面板居中)
        self.PANEL_WIDTH = 500
        self.PANEL_HEIGHT = 450
        self.PANEL_X = (GameSettings.SCREEN_WIDTH - self.PANEL_WIDTH) // 2
        self.PANEL_Y = (GameSettings.SCREEN_HEIGHT - self.PANEL_HEIGHT) // 2


        # 導航開關按鈕 (保持不變)
        self.nav_button = Button(
            "UI/button_play.png", "UI/button_play_hover.png",
            GameSettings.SCREEN_WIDTH - 240, 20,
            60, 60,
            self.toggle
        )
        # 停止導航按鈕 (保持不變)
        self.stop_nav_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            GameSettings.SCREEN_WIDTH - 320, 20,
            60, 60,
            self.stop_navigation
        )
        
        # 新增導航面板的關閉按鈕
        self.close_panel_button = Button(
            "UI/button_x.png", "UI/button_x_hover.png",
            self.PANEL_X + self.PANEL_WIDTH - 60, self.PANEL_Y + 15, # 放在面板右上角
            40, 40,
            self.toggle # 點擊它也是關閉面板
        )


        # 目的地選擇按鈕列表 (使用橫幅圖片作為視覺元素)
        self.place_buttons = []
        start_y = self.PANEL_Y + 120
        # 計算按鈕的 X 座標使其居中於面板
        button_x = self.PANEL_X + (self.PANEL_WIDTH - self.BANNER_WIDTH) // 2

        for i, p in enumerate(self.places):
            btn = Button(
                "UI/raw/UI_Flat_Banner02a.png",
                "UI/raw/UI_Flat_Banner02a.png",
                button_x, start_y + i * (self.BANNER_HEIGHT + 10),
                self.BANNER_WIDTH, self.BANNER_HEIGHT,
                lambda place=p: self.select_place(place)
            )
            btn.text = p["name"] # 儲存名稱供 draw 方法渲染
            self.place_buttons.append(btn)
    
    # 開/關 UI (保持不變)
    def toggle(self):
        self.is_open = not self.is_open

    # 點地點 (保持不變)
    def select_place(self, place):
        self.nav_manager.start_navigation(place["x"], place["y"])
        self.is_open = False

    def stop_navigation(self):
        self.nav_manager.cancel_navigation()

    def update(self, dt):
        if getattr(self, "block_input", False):
            return
        self.nav_button.update(dt)
        self.stop_nav_button.update(dt)
        if self.is_open:
            self.close_panel_button.update(dt) # 更新關閉按鈕
            for btn in self.place_buttons:
                btn.update(dt)

    # 畫 UI
    def draw(self, screen, camera):
        # 繪製主要導航按鈕和停止導航按鈕 (在遊戲世界頂部)
        self.nav_button.draw(screen)
        if self.nav_manager.is_navigating:
            self.stop_nav_button.draw(screen)
            
        if not self.is_open:
            return

        # ------------------- 寶可夢風格導航面板 -------------------
        
        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
                #alpha是指 整體透明度
        overlay.set_alpha(180)
                #填上顏色
        overlay.fill((0, 0, 0))
                #貼到主畫上
        screen.blit(overlay, (0, 0))

        # 2. 面板 (模擬寶可夢對話框的邊框和顏色)
        panel_rect = pg.Rect(self.PANEL_X, self.PANEL_Y, self.PANEL_WIDTH, self.PANEL_HEIGHT)
        
        # 畫主要背景 (白色/淺灰色)
        pg.draw.rect(screen, (220, 220, 220), panel_rect)
        # 畫邊框 (寶可夢經典的深藍色/黑色邊框)
        pg.draw.rect(screen, (0, 0, 0), panel_rect, 5) # 黑色粗邊框
        
        # 3. 標題
        title_text = self.font_title.render("Navigation", True, (0, 0, 0))
        title_rect = title_text.get_rect(center=(self.PANEL_X + self.PANEL_WIDTH // 2, self.PANEL_Y + 60))
        screen.blit(title_text, title_rect)

        # 4. 目的地按鈕
        for btn in self.place_buttons:
            btn.draw(screen) # 繪製圖片按鈕
            
            # 手動在按鈕圖片上渲染文字
            # 渲染地點名稱
            place_text = self.font_medium.render(btn.text, True, (0,0,0)) # 白色文字
            text_rect = place_text.get_rect(center=(btn.rect.centerx, btn.rect.centery))
            screen.blit(place_text, text_rect)
            
            # **關於按鈕判斷被擋住的問題：**
            # 這是 **不會** 發生擋住判斷的。因為 Pygame 的按鈕判斷 (`btn.update(dt)`) 是基於滑鼠點擊時的座標是否落入按鈕的矩形區域 (`btn.rect`) 內。渲染文字只是在畫面上畫像素，不會改變按鈕的矩形區域或阻擋點擊事件。

        # 5. 關閉按鈕 (放在最後繪製以確保它在最上層)
        self.close_panel_button.draw(screen)