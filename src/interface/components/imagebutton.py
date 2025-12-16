from src.sprites import Sprite
from src.core.services import input_manager
from src.utils import Logger
from typing import Callable, override
from .component import UIComponent

import pygame as pg

class ImageButton:
    def __init__(self, img, x, y, width, height, on_click=None):
        self.image = pg.transform.scale(img, (width, height))
        self.rect = pg.Rect(x, y, width, height)
        self.on_click = on_click

        self.hover = False

    def draw(self, screen):
        screen.blit(self.image, self.rect)

        # 可選：加 hover 邊框（若不想要可以刪掉）
        if self.hover:
            pg.draw.rect(screen, (255, 255, 0), self.rect, 2)

    '''def handle_event(self, event):
        print("[ImageButton] Checking click:", self.rect)
        if event.type == pg.MOUSEMOTION:
            self.hover = self.rect.collidepoint(event.pos)
        if event.type == pg.MOUSEBUTTONDOWN and event.button == 1:
            if self.rect.collidepoint(event.pos):
                if self.on_click:
                    self.on_click()
                return True
        return False'''
    
    def update(self, dt: float):
        """處理按鈕的懸停和點擊邏輯 (輪詢模式)。"""
        
        mouse_pos = input_manager.mouse_pos
        is_pressed = input_manager.mouse_pressed(1) # 檢查滑鼠左鍵是否被按下
        is_released = input_manager.mouse_released(1) # 檢查滑鼠左鍵是否被釋放 (通常用於精準點擊)
        
        # 1. 懸停狀態 (Hover)
        self.hover = self.rect.collidepoint(mouse_pos)
        
        # 2. 點擊邏輯
        
        if self.hover and is_pressed:
            if self.on_click:
                self.on_click()
                Logger.info(f"ImageButton clicked at {self.rect}")
        
        