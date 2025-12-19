import pygame
from src.core import GameManager

from src.scenes.scene import Scene
from src.interface.components import Button
from src.utils import GameSettings, Logger
from src.utils.definition import Item
from src.core.services import input_manager, scene_manager


class ShopScene(Scene):
    def __init__(self, game_manager: GameManager = None):
        super().__init__()
        self.game_manager = game_manager
        self.bag = game_manager.bag

        # --- 寶可夢風格 UI 設定 (1280x720) ---
        self.SCREEN_WIDTH = 1280
        self.SCREEN_HEIGHT = 720
        self.CARD_WIDTH = 700
        self.CARD_HEIGHT = 100
        self.ITEM_SPACING = 130
        
        # 調整：將整個商店面板往下移，為頂部標題留出更多空間
        self.PANEL_TOP_Y = 150
        self.START_Y = self.PANEL_TOP_Y + 70 # 商品列表起始Y座標
        
        self.BUY_BUTTON_SIZE = 60 

        self.items_for_sale = [
            {"name": "Potion", "price": 5, "sprite": "ingame_ui/potion.png"},
            {"name": "Pokeball", "price": 8, "sprite": "ingame_ui/ball.png"},
            {"name": "Strength Potion", "price": 12, "sprite": "ingame_ui/options1.png"}
        ]

        # --- 按鈕初始化與位置調整 ---
        self.buttons = []
        center_x = self.SCREEN_WIDTH // 2
        
        # 購買按鈕 X 座標：位於面板右側邊緣內縮
        buy_button_x = center_x + self.CARD_WIDTH // 2 - self.BUY_BUTTON_SIZE // 2 - 60

        for i, item in enumerate(self.items_for_sale):
            btn = Button(
                img_path="UI/button_shop.png",
                img_hovered_path="UI/button_shop_hover.png",
                x=buy_button_x,
                y=self.START_Y + i * self.ITEM_SPACING + (self.CARD_HEIGHT - self.BUY_BUTTON_SIZE) // 2,
                width=self.BUY_BUTTON_SIZE, 
                height=self.BUY_BUTTON_SIZE,
                on_click=lambda idx=i: self.buy_item(idx)
            )
            self.buttons.append(btn)

        # 關閉按鈕 (返回鍵)
        self.CLOSE_BUTTON_SIZE = 48 # 縮小返回鍵
        # 調整：將返回鍵放在**主面板左上角**，遠離 Money 顯示
        self.close_button = Button(
            img_path="UI/button_back.png",
            img_hovered_path="UI/button_back_hover.png",
            x=center_x - (self.CARD_WIDTH // 2 + 50) + 15, # 靠近面板左側邊框
            y=self.PANEL_TOP_Y + 15, # 靠近面板頂部邊框
            width=self.CLOSE_BUTTON_SIZE, 
            height=self.CLOSE_BUTTON_SIZE,
            on_click=self.close_shop
        )

        # --- 字體和 UI 顏色設定 ---
        self.font_title = pygame.font.Font("assets/fonts/Minecraft.ttf", 52) 
        self.font_money = pygame.font.Font("assets/fonts/Minecraft.ttf", 36) 
        self.font_item = pygame.font.Font("assets/fonts/Minecraft.ttf", 30) 

        # 顏色定義
        self.COLOR_BG = (180, 220, 255)       
        self.COLOR_PANEL = (230, 240, 255)    
        self.COLOR_FRAME = (50, 50, 100)      
        self.COLOR_CARD_BG = (255, 255, 255)  
        self.COLOR_HIGHLIGHT = (255, 215, 0)  

        # 載入商品圖片
        self.item_sprites = {}
        for item in self.items_for_sale:
            try:
                # 修正：使用正確的 assets/images/ 前綴
                img = pygame.image.load("assets/images/" + item["sprite"]).convert_alpha()
                self.item_sprites[item["name"]] = pygame.transform.scale(img, (64, 64))
            except pygame.error:
                Logger.error(f"Failed to load sprite: {item['sprite']}")
                self.item_sprites[item["name"]] = pygame.Surface((64, 64), pygame.SRCALPHA) 


    def buy_item(self, idx):
        # 邏輯不變
        item = self.items_for_sale[idx]
        price = item["price"]

        if not self.bag.spend_money(price):
            Logger.warning("Not enough money!")
            return

        for it in self.bag._items_data:
            if it.name == item["name"]:
                it.count += 1
                Logger.info(f"Bought {item['name']}")
                return

        self.bag._items_data.append(
            Item(item["name"], item["sprite"], 1)
        )
        Logger.info(f"Bought {item['name']}")

    def close_shop(self):
        scene_manager.change_scene("game")

    def update(self, dt):
        for b in self.buttons:
            b.update(dt)
        
        self.close_button.update(dt)

        if input_manager.key_pressed(pygame.K_ESCAPE):
            self.close_shop()

    def draw(self, screen):
        """
        繪製精緻寶可夢風格商店介面
        """
        center_x = self.SCREEN_WIDTH // 2
        
        # --- 1. 背景 ---
        screen.fill(self.COLOR_BG) 
        pygame.draw.rect(screen, (150, 190, 220), (0, self.SCREEN_HEIGHT // 2, self.SCREEN_WIDTH, self.SCREEN_HEIGHT // 2))

        # --- 2. 主面板框架 ---
        PANEL_RECT = pygame.Rect(
            center_x - self.CARD_WIDTH // 2 - 50, 
            self.PANEL_TOP_Y, # 使用調整後的 Y 座標
            self.CARD_WIDTH + 100, 
            self.SCREEN_HEIGHT - self.PANEL_TOP_Y - 50
        )
        
        pygame.draw.rect(screen, self.COLOR_FRAME, PANEL_RECT, border_radius=15)
        INNER_RECT = PANEL_RECT.inflate(-10, -10)
        pygame.draw.rect(screen, self.COLOR_PANEL, INNER_RECT, border_radius=10)
        
        # --- 3. 標題與金錢 ---
        
        # 標題 (位於面板**中間頂部**，不會被金錢和返回鍵擋住)
        title_text = "POKEMON SHOP"
        title_surface = self.font_title.render(title_text, True, self.COLOR_FRAME)
        shadow_surface = self.font_title.render(title_text, True, (0, 0, 0))
        
        title_y = PANEL_RECT.top - title_surface.get_height() // 2 # 讓標題位於面板邊界上
        
        # 繪製標題
        screen.blit(shadow_surface, (center_x - title_surface.get_width() // 2 + 3, title_y + 3))
        screen.blit(title_surface, (center_x - title_surface.get_width() // 2, title_y))
        
        # 金錢區塊 (位於面板**右上角**)
        money_text_content = f"Money: {self.bag._money} G"
        money_text_surface = self.font_money.render(money_text_content, True, self.COLOR_FRAME)
        
        MONEY_RECT_W = money_text_surface.get_width() + 40
        MONEY_RECT = pygame.Rect(
            INNER_RECT.right - MONEY_RECT_W - 10, 
            INNER_RECT.top + 10, # 靠近主面板的右邊和頂邊
            MONEY_RECT_W, 
            money_text_surface.get_height() + 10
        )
        
        pygame.draw.rect(screen, self.COLOR_HIGHLIGHT, MONEY_RECT, border_radius=8) 
        pygame.draw.rect(screen, (255, 255, 200), MONEY_RECT.inflate(-4, -4), border_radius=6) 
        
        screen.blit(money_text_surface, (
            MONEY_RECT.centerx - money_text_surface.get_width() // 2, 
            MONEY_RECT.centery - money_text_surface.get_height() // 2
        ))
        
        # --- 4. 商品列表 (卡片化) ---
        
        for i, item in enumerate(self.items_for_sale):
            card_y = self.START_Y + i * self.ITEM_SPACING
            
            card_rect = pygame.Rect(
                center_x - self.CARD_WIDTH // 2, 
                card_y, 
                self.CARD_WIDTH, 
                self.CARD_HEIGHT
            )
            
            pygame.draw.rect(screen, self.COLOR_CARD_BG, card_rect, border_radius=10)
            pygame.draw.rect(screen, self.COLOR_FRAME, card_rect, 3, border_radius=10)
            
            # 載入和繪製商品圖標
            sprite = self.item_sprites.get(item["name"])
            if sprite:
                sprite_x = card_rect.x + 20
                sprite_y = card_rect.centery - sprite.get_height() // 2
                screen.blit(sprite, (sprite_x, sprite_y))

            # 商品名稱和價格文字
            name_price_text = f"{item['name']} - {item['price']} G"
            text_surface = self.font_item.render(name_price_text, True, (0, 0, 0))
            
            text_x = card_rect.x + 20 + 64 + 20 
            text_y = card_rect.centery - text_surface.get_height() // 2
            screen.blit(text_surface, (text_x, text_y))

        # --- 5. 按鈕繪製 ---
        
        # 購買按鈕
        for b in self.buttons:
            b.draw(screen)
        
        # 返回鍵 (已調整到左上角)
        self.close_button.draw(screen)