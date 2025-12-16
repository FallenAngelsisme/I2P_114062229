from __future__ import annotations
import pygame as pg

from src.sprites import Sprite
from src.core.services import input_manager
from src.utils import Logger
from typing import Callable, override
from .component import UIComponent

class Slider(UIComponent):
    def __init__(
        self,
        x: int, y: int,
        width: int, height: int,
        min_value: float, max_value: float,
        initial_value: float,
        knob_img: str | None = None ,
        knob_width: int = 20,     # 新增
        knob_height: int = 40 
    ):
        self.rect = pg.Rect(x, y, width, height)
        self.knob_img = knob_img
        
        self.knob_width = knob_width
        self.knob_height = knob_height

        self.min_value = min_value
        self.max_value = max_value
        self.value = initial_value
        self.dragging = False

        ratio = (initial_value - min_value) / (max_value - min_value)#比例
        knob_x = x + ratio * width#比例位置
        knob_y = y + height // 2

        
        if knob_img is None:
            # 長方形 knob
            self.knob_rect = pg.Rect(
                knob_x - self.knob_width // 2,
                knob_y - self.knob_height // 2,
                self.knob_width,
                self.knob_height
            )
            self.knob_sprite = None  # 沒圖片
        else:
            # 圖片 knob
            self.knob_sprite = Sprite(knob_img)
            self.knob_sprite.image = pg.transform.scale(
                self.knob_sprite.image,
                (self.knob_width, self.knob_height)
            )
            self.knob_rect = self.knob_sprite.image.get_rect()
            self.knob_rect.center = (knob_x, knob_y)

    def set_knob_image(self, sprite: Sprite) -> None:
        
        # 保留原本中心位置
        old_center = self.knob_rect.center

        self.knob_sprite = sprite
        # rect 跟圖片大小同步
        self.knob_rect = sprite.image.get_rect()

        # 移回原本位置
        self.knob_rect.center = old_center

    def update_knob_position(self):
        ratio = (self.value - self.min_value) / (self.max_value - self.min_value)
        knob_center_x = self.rect.x + ratio * self.rect.width
        self.knob_rect.centerx = knob_center_x
    @override
    def update(self, dt: float) -> None:
        mouse = input_manager.mouse_pos
        pressed = input_manager.mouse_pressed(1)

        if pressed:       #knob                        #bar底條                        #拖移中
            if self.knob_rect.collidepoint(mouse) or self.rect.collidepoint(mouse) or self.dragging:
                self.dragging = True

                        #x座標
                rel_x = mouse[0] - self.rect.x
                # 0 < rel_x < self.rect.width
                rel_x = max(0, min(self.rect.width, rel_x))

                ratio = rel_x / self.rect.width
                self.value = self.min_value + ratio * (self.max_value - self.min_value)
                                #底標x座標
                knob_center_x = self.rect.x + ratio * self.rect.width
                self.knob_rect.centerx = knob_center_x
        else:
            self.dragging = False

    @override
    def draw(self, screen: pg.Surface) -> None:
        # bar
        pg.draw.rect(screen, (180, 180, 180), self.rect)

        # knob（長方形）
        if  self.knob_sprite:
            self.knob_sprite.rect = self.knob_rect
            screen.blit(self.knob_sprite.image, self.knob_sprite.rect)
        else:
            # 沒給圖片時用 fallback
            pg.draw.rect(screen, (255, 255, 255), self.knob_rect)

    