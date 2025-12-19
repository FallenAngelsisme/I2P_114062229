import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item
from src.utils import Logger
from src.interface.components import Button,ImageButton
import os

# ★ NEW: 為了進化功能，假設 Bag 實例可以拿到 GameManager 的引用
# 這樣才能呼叫 evolution_manager 和存取 money
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core import GameManager # 僅用於型別提示

class Bag:
    _monsters_data: list[Monster]
    _items_data: list[Item]
    _money: int # ★ NEW
    PAGE_SIZE = 4 #UI
    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None, money: int = 0): # ★ MODIFIED        
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []
        self._money = money # ★ NEW: 初始化金錢
        self.evolve_buttons = {}

        src = "assets/images/UI/raw/UI_Flat_ButtonPlay01a.png"
        dst = "assets/images/UI/raw/UI_Flat_ButtonPlay01a_left.png"

        if not os.path.exists(dst):
            img = pg.image.load(src).convert_alpha()
            flipped = pg.transform.flip(img, True, False)
            pg.image.save(flipped, dst)
            Logger.info(f"Generated flipped button: {dst}")

        # UI
        self.bg_img = pg.image.load("assets/images/UI/raw/UI_Flat_Frame03a.png").convert_alpha()
        self.bg_img = pg.transform.scale(self.bg_img, (800, 520))

        self.visible = False
        self.current_page = 0
        self.current_tab = "monster"

        self.monster_card_bg = pg.image.load("assets/images/UI/raw/UI_Flat_Banner03a.png").convert_alpha()
        self.monster_card_bg = pg.transform.scale(self.monster_card_bg, (310, 75))

        self.item_card_bg = pg.image.load("assets/images/UI/raw/UI_Flat_Banner03a.png").convert_alpha()
        self.item_card_bg = pg.transform.scale(self.item_card_bg, (310, 75))

        # 進化相關 UI
        self.evolve_dialog_open = False # ★ NEW: 進化對話框狀態
        self.evolve_target_index = -1       # ★ NEW: 儲存要進化的怪獸索引
        self.evolve_button_rects = {}       # ★ NEW: 儲存進化按鈕的 Rect

        # ★ NEW: 進化和金錢相關 UI
        self.game_manager = None # 稍後設定 (請確保在 GameManager 初始化後呼叫 set_game_manager)
        self.evolve_icon_img = pg.image.load("assets/images/ingame_ui/baricon4.png").convert_alpha()
        self.evolve_icon_img = pg.transform.scale(self.evolve_icon_img, (48, 48))
        self.coin_icon = pg.image.load("assets/images/ingame_ui/coin.png").convert_alpha()
        self.coin_icon = pg.transform.scale(self.coin_icon, (24, 24))
    

        self.font_small  = pg.font.Font("assets/fonts/Minecraft.ttf", 15)
        self.font_medium = pg.font.Font("assets/fonts/Minecraft.ttf", 24)
        self.font_large  = pg.font.Font("assets/fonts/Minecraft.ttf", 30)

         # Tab 按鈕
        #640
        self.btn_tab_mon = Button(
            img_path="UI/raw/UI_Flat_Banner02a.png", img_hovered_path="UI/raw/UI_Flat_Banner02a.png",
            x=460, y=140, width=140, height=35,
            on_click=lambda: self.switch_tab("monster")
        )
        self.btn_tab_item = Button(
            img_path="UI/raw/UI_Flat_Banner02a.png", img_hovered_path="UI/raw/UI_Flat_Banner02a.png",
            x=700, y=140, width=140, height=35,
            on_click=lambda: self.switch_tab("item")
        )

        # 分頁按鈕
        #640
        self.btn_prev = Button(
            img_path="UI/raw/UI_Flat_ButtonPlay01a_left.png", img_hovered_path="UI/raw/UI_Flat_ButtonPlay01a_left.png",
            x=500, y=560, width=50, height=30,
            on_click=self.prev_page
        )
        self.btn_next = Button(
            img_path="UI/raw/UI_Flat_ButtonPlay01a.png", img_hovered_path="UI/raw/UI_Flat_ButtonPlay01a.png",
            x=780, y=560, width=50, height=30,
            on_click=self.next_page
        )

        # 關閉按鈕（右上角）
        self.btn_close = Button(
            img_path="UI/button_x.png", img_hovered_path="UI/button_x_hover.png",
            x=950, y=140, width=40, height=40,
            on_click=self.toggle
        )

        # 對話框按鈕
        dialog_btn_y = GameSettings.SCREEN_HEIGHT // 2 + 50
        self.btn_yes = Button("UI/raw/UI_Flat_IconArrow01a.png"
                              , "UI/raw/UI_Flat_IconArrow01a.png", 
                              GameSettings.SCREEN_WIDTH // 2 - 120,
                                dialog_btn_y
                                , 40, 40, self.perform_evolution) # ★ NEW
        self.btn_no = Button("UI/button_x.png", "UI/button_x_hover.png", 
                             GameSettings.SCREEN_WIDTH // 2 + 20, dialog_btn_y, 40, 40, self._close_evolve_dialog) # ★ NEW


    # ★ NEW: Setter for GameManager (確保進化邏輯能呼叫 EvolutionManager)
    def set_game_manager(self, game_manager):
        self.game_manager = game_manager

    # ★ NEW: 金錢操作
    def add_money(self, amount: int):
        self._money += amount
    
    def spend_money(self, amount: int) -> bool:
        if self._money >= amount:
            self._money -= amount
            return True
        return False

    # ★ NEW: 進化對話框邏輯
    def _open_evolve_dialog(self, monster_index: int):
        self.evolve_target_index = monster_index
        self.evolve_dialog_open = True
        
    def _close_evolve_dialog(self):
        self.evolve_target_index = -1
        self.evolve_dialog_open = False
        
    def perform_evolution(self):
        """執行進化流程 (花費金錢並呼叫進化管理員)"""
        cost = 10
        if self.evolve_target_index == -1:
            Logger.warn("Evolution failed: Invalid target.")
            self._close_evolve_dialog()
            return

        if not self.spend_money(cost):
            Logger.warn("Evolution failed: Insufficient money.")
            self._close_evolve_dialog()
            return

        monster = self._monsters_data[self.evolve_target_index]

        # 呼叫 EvolutionManager 進行實際的進化數據更改
        if self.game_manager and self.game_manager.evolution_manager:
            success = self.game_manager.evolution_manager.evolve_monster(monster)
            if not success:
                self.add_money(cost)
            
        self._close_evolve_dialog()


    def _draw_evolve_dialog(self, screen: pg.Surface):
        """繪製進化確認對話框"""
        monster = self._monsters_data[self.evolve_target_index]
        
        # 對話框背景
        dialog_rect = pg.Rect(GameSettings.SCREEN_WIDTH // 2 - 200, GameSettings.SCREEN_HEIGHT // 2 - 100, 400, 200)
        pg.draw.rect(screen, (50, 50, 50), dialog_rect)
        pg.draw.rect(screen, (255, 255, 255), dialog_rect, 5)

        # 訊息文字
        cost = 10 # 進化費用
        message = f"Evolve {monster.name} to {self.game_manager.evolution_manager.get_next_name(monster.name)}?"
        message2 = f"Cost: {cost} Gold"
        
        
        text_surface = self.font_medium.render(message, True, (255, 255, 255))
        screen.blit(text_surface, (dialog_rect.x + 20, dialog_rect.y + 30))
        
        text_surface2 = self.font_medium.render(message2, True, (255, 255, 255))
        screen.blit(text_surface2, (dialog_rect.x + 20, dialog_rect.y + 70))

        # 按鈕
        self.btn_yes.draw(screen)
        self.btn_no.draw(screen)
        
    def handle_event(self, event):
        print("[Bag] Event:", event) 
        '''if not self.visible:
            return
        Logger.info(f"[Bag] got eventCCCCCCCCCCCCCC: {event}")
        if self.evolve_dialog_open:
            if event.type == pg.MOUSEMOTION:
                mouse_pos = event.pos
                # 手動更新 hover 狀態 (假設 Button 類別有 hover 屬性)
                self.btn_yes.hover = self.btn_yes.rect.collidepoint(mouse_pos)
                self.btn_no.hover = self.btn_no.rect.collidepoint(mouse_pos)
                return True # 處理 hover 事件，並阻止事件傳播至下層 UI
            elif event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
                mouse_pos = event.pos
                
                # 檢查 btn_yes
                if self.btn_yes.rect.collidepoint(mouse_pos):
                    self.btn_yes.on_click()
                    return True # 事件已處理

                # 檢查 btn_no
                if self.btn_no.rect.collidepoint(mouse_pos):
                    self.btn_no.on_click()
                    return True # 事件已處理

            return True'''
        # ★ NEW: 3. 處理怪物分頁中的進化按鈕點擊
        if self.current_tab == "monster":
            for btn in self.evolve_button_rects.values():
                if btn.handle_event(event):
                    return True
    
        self.btn_prev.handle_event(event)
        self.btn_next.handle_event(event)
        self.btn_close.handle_event(event)

        self.btn_tab_mon.handle_event(event)
        self.btn_tab_item.handle_event(event)

        return False 
                
    def prev_page(self):
        self.current_page = max(self.current_page - 1, 0)
        self.evolve_button_rects.clear()

    def next_page(self):
        max_p = self.get_max_pages()
        self.current_page = min(self.current_page + 1, max_p)
        self.evolve_button_rects.clear()

    def get_max_pages(self):
        total = len(self._monsters_data) if self.current_tab == "monster" else len(self._items_data)
        return max((total - 1) // Bag.PAGE_SIZE, 0)
    
    
    def switch_tab(self, tab):
        self.current_tab = tab
        self.current_page = 0
        self.evolve_button_rects.clear()

    def toggle(self):
        self.visible = not self.visible

    def update(self, dt: float):
        if not self.visible:
            return
        
        # --- 原本的按鈕更新 ---
        for button in self.evolve_buttons.values():
            button.update(dt)

        self.btn_prev.update(dt)
        self.btn_next.update(dt)
        self.btn_close.update(dt)
        self.btn_tab_mon.update(dt)
        self.btn_tab_item.update(dt)

        # --- 新增 yes/no 輪詢 ---
        if self.evolve_dialog_open:
            mouse_pos = pg.mouse.get_pos()
            mouse_pressed = pg.mouse.get_pressed()[0]  # 左鍵
            # hover
            self.btn_yes.hover = self.btn_yes.rect.collidepoint(mouse_pos)
            self.btn_no.hover = self.btn_no.rect.collidepoint(mouse_pos)
            # click
            if mouse_pressed:
                if self.btn_yes.rect.collidepoint(mouse_pos):
                    self.btn_yes.on_click()
                elif self.btn_no.rect.collidepoint(mouse_pos):
                    self.btn_no.on_click()
    def draw(self, screen: pg.Surface):
        if not self.visible:
            return
        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        overlay.set_alpha(150)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        screen.blit(self.bg_img, (250, 100))

        # Tabs
        self.draw_tabs(screen)

        # 分頁
        self.btn_prev.draw(screen)
        self.btn_next.draw(screen)

        # 關閉按鈕
        self.btn_close.draw(screen)

        # ★ NEW: 繪製金錢總數 (Requirement 2)
        coin_x = GameSettings.SCREEN_WIDTH // 2 + 300
        coin_y = 60
        screen.blit(self.coin_icon, (coin_x, coin_y))
        money_text = self.font_small.render(f"{self._money}", True, (255, 255, 255))
        screen.blit(money_text, (coin_x + 30, coin_y + 4))

        if self.current_tab == "monster":
            start_index = self.current_page * self.PAGE_SIZE
            end_index = min(start_index + self.PAGE_SIZE, len(self._monsters_data))
            
            x_start = 505  # 怪獸卡片 X 座標
            y = 180        # ★ FIX: 怪獸卡片起始 Y 座標 (從 100 改為 180)
            
            
            for i in range(start_index, end_index):
                mon = self._monsters_data[i]
                
                # --- START: 怪獸卡片繪製邏輯 (從 draw_monsters 合併過來) ---
                screen.blit(self.monster_card_bg, (x_start, y))

                # 怪獸圖片
                try:
                    img = pg.image.load("assets/images/" + mon.sprite_path).convert_alpha()
                    img = pg.transform.scale(img, (65, 65))
                    screen.blit(img, (x_start + 10, y + 5))
                except Exception as e:
                    # 處理圖片讀取失敗 (可選)
                    pass 

                # 名字和等級
                screen.blit(self.font_medium.render(mon.name, True, (0, 0, 0)), (x_start + 80, y + 10))
                screen.blit(self.font_small.render(f"Lv.{mon.level}", True, (0, 0, 0)), (x_start + 250, y + 10))

                # HP bar
                pg.draw.rect(screen, (40, 40, 40), (x_start + 80, y + 35, 200, 12))
                hp_ratio = mon.hp / mon.max_hp
                pg.draw.rect(screen, (0, 200, 0), (x_start + 80, y + 35, int(200 * hp_ratio), 12))

                hp_text = self.font_small.render(f"{mon.hp}/{mon.max_hp}", True, (0, 0, 0))
                screen.blit(hp_text, (x_start + 140, y + 50))
                # --- END: 怪獸卡片繪製邏輯 ---

                Logger.info(f"Checking evolution for {mon.name}:")
                Logger.info(f"  - game_manager exists: {self.game_manager is not None}")
                Logger.info(f"  - evolution_manager exists: {self.game_manager.evolution_manager is not None if self.game_manager else False}")
                Logger.info(f"  - evolve_icon loaded: {self.evolve_icon_img is not None}")

                
                if self.game_manager and self.game_manager.evolution_manager and self.evolve_icon_img:
                    can_evolve = self.game_manager.evolution_manager.can_evolve(mon)
                    Logger.info(f"  - can_evolve: {can_evolve}")
                    
                    if can_evolve:
                        # 若未建立按鈕 → 建立一次
                        if i not in self.evolve_buttons:
                            self.evolve_buttons[i] = ImageButton(
                                img=self.evolve_icon_img,
                                x=x_start + 380,
                                y=y+10 ,
                                width=48,
                                height=48,
                                on_click=lambda idx=i: self._open_evolve_dialog(idx)
                            )

                        # 更新按鈕位置（如果 layout 會動）
                        btn = self.evolve_buttons[i]
                        btn.rect.topleft = (x_start + 380, y+10 )

                        self.evolve_button_rects[i] = btn
                        btn.draw(screen)
                        Logger.info(f"  ✓ Drew evolution button at ({x_start + 380}, {y + 10})")
                
                y += 90
            
            
            # ★ NEW: 繪製進化對話框
            if self.evolve_dialog_open:
                self._draw_evolve_dialog(screen)
        else:
            self.draw_items(screen)

        
    def draw_tabs(self, screen):
        self.btn_tab_mon.draw(screen)
        self.btn_tab_item.draw(screen)

        txt1 = self.font_small.render("Monsters", True, (0, 0, 0))
        txt2 = self.font_small.render("Items", True, (0, 0, 0))

        screen.blit(txt1, (490, 148))
        screen.blit(txt2, (730, 148))

   
    #Item UI
    def draw_items(self, screen):
        start = self.current_page * Bag.PAGE_SIZE
        items = self._items_data[start:start + Bag.PAGE_SIZE]

        x = 505
        y = 180

        for item in items:
            screen.blit(self.item_card_bg, (x, y))

            img = pg.image.load("assets/images/" + item.sprite_path).convert_alpha()
            img = pg.transform.scale(img, (45, 45))
            screen.blit(img, (x + 10, y + 15))

            screen.blit(self.font_medium.render(item.name, True, (0, 0, 0)), (x + 70, y + 10))
            screen.blit(self.font_small.render(f"x{item.count}", True, (0, 0, 0)), (x + 250, y + 40))

            y += 90
    
    def to_dict(self) -> dict[str, object]:
        '''
        return {
            "monsters": list(self._monsters_data),
            "items": list(self._items_data)
        }
        '''
        return {
            "monsters": [m.to_dict() for m in self._monsters_data],
            "items": [i.to_dict() for i in self._items_data],
            "money": self._money # ★ MODIFIED: 儲存金錢
        }

    @classmethod
    def from_dict(cls, data: dict[str, object]) -> "Bag":
        '''monsters = data.get("monsters") or []
        items = data.get("items") or []
        bag = cls(monsters, items)
        return bag'''

        monsters = [Monster.from_dict(m) for m in data.get("monsters", [])]
        items = [Item.from_dict(i) for i in data.get("items", [])]
        money = data.get("money", 0) # ★ MODIFIED: 讀取金錢
        return cls(monsters, items, money) # ★ MODIFIED
    
    def add_monster(self, monster_data):
        """添加寶可夢到背包"""
        self._monsters_data.append(monster_data)
        Logger.info(f"Added {monster_data.name} to bag")
    def del_item(self, item_name):
        for item in self._items_data:
            if item.name == item_name:
                item.count -= 1
                Logger.info(f"Used {item.name}, remaining: {item.count}")
                
                # 如果數量為 0，從背包中移除
                if item.count <= 0:
                    self._items_data.remove(item)
                    Logger.info(f"Removed {item.name} from bag (count reached 0)")
                return True
        
        Logger.warning(f"Item {item_name} not found in bag")
        return False

    
