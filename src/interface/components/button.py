from __future__ import annotations
import pygame as pg

from src.sprites import Sprite
from src.core.services import input_manager
from src.utils import Logger
from typing import Callable, override
from .component import UIComponent

class Button(UIComponent): #def模板
    img_button: Sprite #Sprite圖上的物件
    img_button_default: Sprite
    img_button_hover: Sprite
    hitbox: pg.Rect
    on_click: Callable[[], None] | None

    img_button_on: Sprite| None
    img_button_off: Sprite| None
    is_toggled: bool

    def __init__(
        self,
        img_path: str, img_hovered_path:str,
        x: int, y: int, width: int, height: int,
        on_click: Callable[[], None] | None = None,#不回傳直
        img_on: str | None = None,
        img_off: str | None = None
    ):
        self.img_button_default = Sprite(img_path, (width, height))
        #沒滑鼠在按鈕上
        self.hitbox = pg.Rect(x, y, width, height)
        self.rect = self.hitbox #3
        #表示按鈕的「區域」
        '''
        [TODO HACKATHON 1]
        Initialize the properties
        
        self.img_button_hover = ...
        self.img_button = ...       --> This is a reference for which image to render
        self.on_click = ...
        '''
        self.img_button_hover = Sprite(img_hovered_path, (width, height))
        self.img_button = self.img_button_default
        self.on_click = on_click


        # toggle切換 images（可選）
        self.img_button_on = Sprite(img_on, (width, height)) if img_on else None
        self.img_button_off = Sprite(img_off, (width, height)) if img_off else None
        self.is_toggled = False

    def set_state(self, is_on: bool):
        if self.img_button_on and self.img_button_off:
            self.is_toggled = is_on

            # 靜音 = True → 用 OFF 圖片
            # 非靜音 = False → 用 ON 圖片
            self.img_button = self.img_button_off if is_on else self.img_button_on
    
    # ⭐⭐⭐ 新增這個方法 ⭐⭐⭐
    def handle_event(self, event: pg.event.Event) -> bool:
        """
        處理事件（用於 GameScene.handle_event）
        返回 True 表示事件被處理，False 表示未處理
        """
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.hitbox.collidepoint(event.pos):
                # Toggle 按鈕邏輯
                if self.img_button_on is not None and self.img_button_off is not None:
                    self.is_toggled = not self.is_toggled
                    self.img_button = self.img_button_on if self.is_toggled else self.img_button_off
                
                # 執行回調
                if self.on_click is not None:
                    self.on_click()
                
                Logger.info(f"Button clicked at {self.hitbox}")
                return True  # ⭐ 事件被處理
        
        return False  # ⭐ 事件未被處理

    # ⭐ 同時添加 handle_input 方法（用於對話框按鈕）
    def handle_input(self, event: pg.event.Event) -> bool:
        """別名方法，與 handle_event 功能相同"""
        return self.handle_event(event)

    
    @override
    def update(self, dt: float) -> None:
        '''
        [TODO HACKATHON 1]
        Check if the mouse cursor is colliding with the button, 
        1. If collide, draw the hover image
        2. If collide & clicked, call the on_click function
        
        if self.hitbox.collidepoint(input_manager.mouse_pos):
            ...
            if input_manager.mouse_pressed(1) and self.on_click is not None:
                ...
        else:
            ...
        '''
        #????
        mouse_pos = input_manager.mouse_pos
        is_hover = self.hitbox.collidepoint(mouse_pos)
        clicked = input_manager.mouse_pressed(1)

        is_toggle_button = self.img_button_on is not None and self.img_button_off is not None

        if is_toggle_button:

            if is_hover and clicked:
                self.is_toggled = not self.is_toggled
                if self.on_click:
                    self.on_click()

            # toggle 按鈕不使用）
            self.img_button = (
                self.img_button_on if self.is_toggled else self.img_button_off
            )
            return

   
        if is_hover:
            self.img_button = self.img_button_hover
            if clicked and self.on_click:
                self.on_click()
        else:
            self.img_button = self.img_button_default
        pass
    
    @override
    def draw(self, screen: pg.Surface) -> None:
        '''
        [TODO HACKATHON 1]
        You might want to change this too
        '''
        screen.blit(self.img_button.image, self.hitbox)

    
def main():
    import sys
    import os
    
    pg.init()

    WIDTH, HEIGHT = 800, 800
    screen = pg.display.set_mode((WIDTH, HEIGHT))
    pg.display.set_caption("Button Test")
    clock = pg.time.Clock()
    
    bg_color = (0, 0, 0)
    def on_button_click():
        nonlocal bg_color
        if bg_color == (0, 0, 0):
            bg_color = (255, 255, 255)
        else:
            bg_color = (0, 0, 0)
    
    button = Button(
        img_path="UI/button_play.png",
        img_hovered_path="UI/button_play_hover.png",
        x=WIDTH // 2 - 50,
        y=HEIGHT // 2 - 50,
        width=100,
        height=100,
        on_click=on_button_click
    )
    button2 = Button(
        img_path="UI/button_play.png",
        img_hovered_path="UI/button_play_hover.png",
        x=WIDTH // 2 - 100,
        y=HEIGHT // 2 - 50,
        width=100,
        height=100,
        on_click=on_button_click
    )

    mute_button = Button(
        img_path="UI/mute_off.png",     #?????    # fallback 圖（不常用）
        img_hovered_path=None, # fallback hover 圖
        x=300,
        y=100,
        width=100,
        height=100,
        on_click=on_button_click,
        img_on="UI/button_mute_on.png",
        img_off="UI/button_mute_off.png"
    )
    running = True
    dt = 0
    
    while running:
        for event in pg.event.get():
            if event.type == pg.QUIT:
                running = False
            input_manager.handle_events(event)
        
        dt = clock.tick(60) / 1000.0
        button.update(dt)
        button2.update(dt)
        mute_button.update(dt)

        input_manager.reset()
        
        _ = screen.fill(bg_color)
        
        button.draw(screen)
        button2.draw(screen)
        mute_button.draw(screen)

        pg.display.flip()
    
    pg.quit()


if __name__ == "__main__":
    main()
