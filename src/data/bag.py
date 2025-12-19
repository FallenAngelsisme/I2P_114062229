import pygame as pg
import json
from src.utils import GameSettings
from src.utils.definition import Monster, Item
from src.utils import Logger
from src.interface.components import Button, ImageButton
import os

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from src.core import GameManager 

class Bag:
    _monsters_data: list[Monster]
    _items_data: list[Item]
    _money: int 
    PAGE_SIZE = 4 

    def __init__(self, monsters_data: list[Monster] | None = None, items_data: list[Item] | None = None, money: int = 0):        
        self._monsters_data = monsters_data if monsters_data else []
        self._items_data = items_data if items_data else []
        self._money = money 
        self.evolve_buttons = {}
        self.info_buttons = {} # ★ NEW: 儲存資訊按鈕

        # UI 資源加載
        src = "assets/images/UI/raw/UI_Flat_ButtonPlay01a.png"
        dst = "assets/images/UI/raw/UI_Flat_ButtonPlay01a_left.png"
        if not os.path.exists(dst):
            img = pg.image.load(src).convert_alpha()
            flipped = pg.transform.flip(img, True, False)
            pg.image.save(flipped, dst)

        self.bg_img = pg.image.load("assets/images/UI/raw/UI_Flat_Frame03a.png").convert_alpha()
        self.bg_img = pg.transform.scale(self.bg_img, (800, 520))

        self.visible = False
        self.current_page = 0
        self.current_tab = "monster"

        self.monster_card_bg = pg.image.load("assets/images/UI/raw/UI_Flat_Banner03a.png").convert_alpha()
        self.monster_card_bg = pg.transform.scale(self.monster_card_bg, (310, 75))

        self.item_card_bg = pg.image.load("assets/images/UI/raw/UI_Flat_Banner03a.png").convert_alpha()
        self.item_card_bg = pg.transform.scale(self.item_card_bg, (310, 75))

        # 進化與資訊 UI 狀態
        self.evolve_dialog_open = False 
        self.evolve_target_index = -1       
        self.info_dialog_open = False   # ★ NEW: 詳細資訊對話框狀態
        self.info_target_index = -1     # ★ NEW: 儲存要查看的怪獸索引
        
        self.evolve_button_rects = {}       
        self.info_button_rects = {}     # ★ NEW

        self.game_manager = None 
        self.evolve_icon_img = pg.image.load("assets/images/ingame_ui/baricon4.png").convert_alpha()
        self.evolve_icon_img = pg.transform.scale(self.evolve_icon_img, (48, 48))
        
        # ★ NEW: 詳細資訊圖標
        self.info_icon_img = pg.image.load("assets/images/ingame_ui/baricon3.png").convert_alpha()
        self.info_icon_img = pg.transform.scale(self.info_icon_img, (48, 48))

        self.coin_icon = pg.image.load("assets/images/ingame_ui/coin.png").convert_alpha()
        self.coin_icon = pg.transform.scale(self.coin_icon, (24, 24))

        self.font_small  = pg.font.Font("assets/fonts/Minecraft.ttf", 15)
        self.font_medium = pg.font.Font("assets/fonts/Minecraft.ttf", 24)
        self.font_large  = pg.font.Font("assets/fonts/Minecraft.ttf", 30)

        # 按鈕初始化 (Tab, Prev, Next, Close)
        self._init_base_buttons()

    def _init_base_buttons(self):
        self.btn_tab_mon = Button("UI/raw/UI_Flat_Banner02a.png", "UI/raw/UI_Flat_Banner02a.png", 460, 140, 140, 35, lambda: self.switch_tab("monster"))
        self.btn_tab_item = Button("UI/raw/UI_Flat_Banner02a.png", "UI/raw/UI_Flat_Banner02a.png", 700, 140, 140, 35, lambda: self.switch_tab("item"))
        self.btn_prev = Button("UI/raw/UI_Flat_ButtonPlay01a_left.png", "UI/raw/UI_Flat_ButtonPlay01a_left.png", 500, 560, 50, 30, self.prev_page)
        self.btn_next = Button("UI/raw/UI_Flat_ButtonPlay01a.png", "UI/raw/UI_Flat_ButtonPlay01a.png", 780, 560, 50, 30, self.next_page)
        self.btn_close = Button("UI/button_x.png", "UI/button_x_hover.png", 950, 140, 40, 40, self.toggle)
        
        # 進化確認按鈕
        dialog_btn_y = GameSettings.SCREEN_HEIGHT // 2 + 50
        self.btn_yes = Button("UI/raw/UI_Flat_IconArrow01a.png", "UI/raw/UI_Flat_IconArrow01a.png", GameSettings.SCREEN_WIDTH // 2 - 120, dialog_btn_y, 40, 40, self.perform_evolution)
        self.btn_no = Button("UI/button_x.png", "UI/button_x_hover.png", GameSettings.SCREEN_WIDTH // 2 + 20, dialog_btn_y, 40, 40, self._close_evolve_dialog)
        
        # ★ NEW: 資訊關閉按鈕
        self.btn_info_close = Button("UI/button_x.png", "UI/button_x_hover.png", GameSettings.SCREEN_WIDTH // 2 + 150, GameSettings.SCREEN_HEIGHT // 2 - 140, 30, 30, self._close_info_dialog)

    def set_game_manager(self, game_manager):
        self.game_manager = game_manager

    # --- 資訊對話框邏輯 ---
    def _open_info_dialog(self, monster_index: int):
        self.info_target_index = monster_index
        self.info_dialog_open = True
        
    def _close_info_dialog(self):
        self.info_target_index = -1
        self.info_dialog_open = False

    def _get_monster_stats(self, mon):
        """參考 BattleScene 的計算邏輯"""
        base_atk = mon.level * 2 + 20
        base_def = mon.level * 1.5 + 10
        atk = getattr(mon, 'attack', base_atk)
        dfn = getattr(mon, 'defense', base_def)
        return int(atk), int(dfn)

    def _draw_monster_detail(self, screen: pg.Surface):
        """繪製怪獸詳細資訊頁面"""
        mon = self._monsters_data[self.info_target_index]
        atk, dfn = self._get_monster_stats(mon)
        
        # 半透明背景遮罩
        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        overlay.set_alpha(180)
        overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))

        # 詳情框背景
        rect = pg.Rect(GameSettings.SCREEN_WIDTH // 2 - 200, GameSettings.SCREEN_HEIGHT // 2 - 150, 400, 300)
        pg.draw.rect(screen, (40, 40, 50), rect)
        pg.draw.rect(screen, (255, 255, 255), rect, 3)

        # 怪獸大圖
        try:
            img = pg.image.load("assets/images/" + mon.sprite_path).convert_alpha()
            img = pg.transform.scale(img, (120, 120))
            screen.blit(img, (rect.x + 20, rect.y + 50))
        except: pass

        # 文字資訊
        title = self.font_large.render(mon.name, True, (255, 215, 0))
        screen.blit(title, (rect.x + 160, rect.y + 30))
        
        stats = [
            f"Type: {mon.element}",
            f"Level: {mon.level}",
            f"HP: {mon.hp}/{mon.max_hp}",
            f"Attack: {atk}",
            f"Defense: {dfn}"
        ]
        
        for i, text in enumerate(stats):
            surf = self.font_medium.render(text, True, (255, 255, 255))
            screen.blit(surf, (rect.x + 160, rect.y + 80 + i * 35))

        self.btn_info_close.draw(screen)

    # --- 原有進化邏輯 ---
    def add_money(self, amount: int): self._money += amount
    def spend_money(self, amount: int) -> bool:
        if self._money >= amount:
            self._money -= amount
            return True
        return False

    def _open_evolve_dialog(self, monster_index: int):
        self.evolve_target_index = monster_index
        self.evolve_dialog_open = True
    def _close_evolve_dialog(self):
        self.evolve_target_index = -1
        self.evolve_dialog_open = False
        
    def perform_evolution(self):
        cost = 10
        if self.evolve_target_index == -1: return
        if not self.spend_money(cost): return
        monster = self._monsters_data[self.evolve_target_index]
        if self.game_manager and self.game_manager.evolution_manager:
            success = self.game_manager.evolution_manager.evolve_monster(monster)
            if not success: self.add_money(cost)
        self._close_evolve_dialog()

    def _draw_evolve_dialog(self, screen: pg.Surface):
        monster = self._monsters_data[self.evolve_target_index]
        dialog_rect = pg.Rect(GameSettings.SCREEN_WIDTH // 2 - 200, GameSettings.SCREEN_HEIGHT // 2 - 100, 400, 200)
        pg.draw.rect(screen, (50, 50, 50), dialog_rect)
        pg.draw.rect(screen, (255, 255, 255), dialog_rect, 5)
        
        cost = 10 
        message = f"Evolve {monster.name}?"
        message2 = f"Cost: {cost} Gold"
        
        screen.blit(self.font_medium.render(message, True, (255, 255, 255)), (dialog_rect.x + 20, dialog_rect.y + 30))
        screen.blit(self.font_medium.render(message2, True, (255, 255, 255)), (dialog_rect.x + 20, dialog_rect.y + 70))
        self.btn_yes.draw(screen)
        self.btn_no.draw(screen)

    def handle_event(self, event):
        if not self.visible: return False

        # 如果資訊頁面打開，優先處理其關閉按鈕
        if self.info_dialog_open:
            if self.btn_info_close.handle_event(event): return True
            return True

        if self.evolve_dialog_open:
            # 這裡簡化處理，原本 update 有處理點擊
            return True

        if self.current_tab == "monster":
            # 處理列表中的所有按鈕
            for btn in self.evolve_button_rects.values():
                if btn.handle_event(event): return True
            for btn in self.info_button_rects.values():
                if btn.handle_event(event): return True
    
        self.btn_prev.handle_event(event)
        self.btn_next.handle_event(event)
        self.btn_close.handle_event(event)
        self.btn_tab_mon.handle_event(event)
        self.btn_tab_item.handle_event(event)
        return False 

    def update(self, dt: float):
        if not self.visible: return
        
        if self.info_dialog_open:
            self.btn_info_close.update(dt)
            return

        for button in self.evolve_buttons.values(): button.update(dt)
        for button in self.info_buttons.values(): button.update(dt) # ★ NEW

        self.btn_prev.update(dt)
        self.btn_next.update(dt)
        self.btn_close.update(dt)
        self.btn_tab_mon.update(dt)
        self.btn_tab_item.update(dt)

        if self.evolve_dialog_open:
            mouse_pos = pg.mouse.get_pos()
            mouse_pressed = pg.mouse.get_pressed()[0]
            self.btn_yes.hover = self.btn_yes.rect.collidepoint(mouse_pos)
            self.btn_no.hover = self.btn_no.rect.collidepoint(mouse_pos)
            if mouse_pressed:
                if self.btn_yes.rect.collidepoint(mouse_pos): self.btn_yes.on_click()
                elif self.btn_no.rect.collidepoint(mouse_pos): self.btn_no.on_click()

    def draw(self, screen: pg.Surface):
        if not self.visible: return
        
        overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        overlay.set_alpha(150); overlay.fill((0, 0, 0))
        screen.blit(overlay, (0, 0))
        screen.blit(self.bg_img, (250, 100))

        self.draw_tabs(screen)
        self.btn_prev.draw(screen); self.btn_next.draw(screen); self.btn_close.draw(screen)

        # 繪製金錢
        coin_x, coin_y = GameSettings.SCREEN_WIDTH // 2 + 300, 60
        screen.blit(self.coin_icon, (coin_x, coin_y))
        screen.blit(self.font_small.render(f"{self._money}", True, (255, 255, 255)), (coin_x + 30, coin_y + 4))

        if self.current_tab == "monster":
            start_index = self.current_page * self.PAGE_SIZE
            end_index = min(start_index + self.PAGE_SIZE, len(self._monsters_data))
            x_start, y = 505, 180
            
            for i in range(start_index, end_index):
                mon = self._monsters_data[i]
                screen.blit(self.monster_card_bg, (x_start, y))

                # 怪獸簡要資訊
                try:
                    img = pg.image.load("assets/images/" + mon.sprite_path).convert_alpha()
                    img = pg.transform.scale(img, (65, 65))
                    screen.blit(img, (x_start + 10, y + 5))
                except: pass

                screen.blit(self.font_medium.render(mon.name, True, (0, 0, 0)), (x_start + 80, y + 10))
                screen.blit(self.font_small.render(f"Lv.{mon.level}", True, (0, 0, 0)), (x_start + 250, y + 10))
                
                # HP Bar
                pg.draw.rect(screen, (40, 40, 40), (x_start + 80, y + 35, 200, 12))
                hp_ratio = mon.hp / mon.max_hp
                pg.draw.rect(screen, (0, 200, 0), (x_start + 80, y + 35, int(200 * hp_ratio), 12))

                # ★ NEW: 詳細資訊按鈕 (baricon3)
                if i not in self.info_buttons:
                    self.info_buttons[i] = ImageButton(self.info_icon_img, x_start + 325, y + 10, 48, 48, lambda idx=i: self._open_info_dialog(idx))
                info_btn = self.info_buttons[i]
                info_btn.rect.topleft = (x_start + 325, y + 10)
                self.info_button_rects[i] = info_btn
                info_btn.draw(screen)

                # ★ 進化按鈕 (baricon4)
                if self.game_manager and self.game_manager.evolution_manager:
                    if self.game_manager.evolution_manager.can_evolve(mon):
                        if i not in self.evolve_buttons:
                            self.evolve_buttons[i] = ImageButton(self.evolve_icon_img, x_start + 380, y + 10, 48, 48, lambda idx=i: self._open_evolve_dialog(idx))
                        btn = self.evolve_buttons[i]
                        btn.rect.topleft = (x_start + 380, y + 10)
                        self.evolve_button_rects[i] = btn
                        btn.draw(screen)
                
                y += 90

            if self.evolve_dialog_open: self._draw_evolve_dialog(screen)
            if self.info_dialog_open: self._draw_monster_detail(screen) # ★ NEW
        else:
            self.draw_items(screen)

    def draw_tabs(self, screen):
        self.btn_tab_mon.draw(screen); self.btn_tab_item.draw(screen)
        screen.blit(self.font_small.render("Monsters", True, (0, 0, 0)), (490, 148))
        screen.blit(self.font_small.render("Items", True, (0, 0, 0)), (730, 148))

    def draw_items(self, screen):
        start = self.current_page * Bag.PAGE_SIZE
        items = self._items_data[start:start + Bag.PAGE_SIZE]
        x, y = 505, 180
        for item in items:
            screen.blit(self.item_card_bg, (x, y))
            try:
                img = pg.image.load("assets/images/" + item.sprite_path).convert_alpha()
                img = pg.transform.scale(img, (45, 45))
                screen.blit(img, (x + 10, y + 15))
            except: pass
            screen.blit(self.font_medium.render(item.name, True, (0, 0, 0)), (x + 70, y + 10))
            screen.blit(self.font_small.render(f"x{item.count}", True, (0, 0, 0)), (x + 250, y + 40))
            y += 90
    
    def switch_tab(self, tab):
        self.current_tab = tab
        self.current_page = 0
        self.evolve_button_rects.clear()
        self.info_button_rects.clear()

    def prev_page(self):
        self.current_page = max(self.current_page - 1, 0)
        self.evolve_button_rects.clear()
        self.info_button_rects.clear()

    def next_page(self):
        self.current_page = min(self.current_page + 1, self.get_max_pages())
        self.evolve_button_rects.clear()
        self.info_button_rects.clear()

    def get_max_pages(self):
        total = len(self._monsters_data) if self.current_tab == "monster" else len(self._items_data)
        return max((total - 1) // Bag.PAGE_SIZE, 0)

    def toggle(self): self.visible = not self.visible

    def to_dict(self) -> dict:
        return {
            "monsters": [m.to_dict() for m in self._monsters_data],
            "items": [i.to_dict() for i in self._items_data],
            "money": self._money 
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Bag":
        monsters = [Monster.from_dict(m) for m in data.get("monsters", [])]
        items = [Item.from_dict(i) for i in data.get("items", [])]
        money = data.get("money", 0)
        return cls(monsters, items, money)
    
    def add_monster(self, monster_data): self._monsters_data.append(monster_data)
    
    def del_item(self, item_name):
        for item in self._items_data:
            if item.name == item_name:
                item.count -= 1
                if item.count <= 0: self._items_data.remove(item)
                return True
        return False