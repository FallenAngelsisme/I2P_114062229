'''
[TODO HACKATHON 5]
Try to mimic the menu_scene.py or game_scene.py to create this new scene
'''
import pygame as pg
import threading
import time




from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import scene_manager, sound_manager, input_manager
from src.sprites import Sprite
from typing import override
from src.interface.components import Button
from src.interface.components.slider import Slider








class SettingScene(Scene):




    back_button: Button




    def __init__(self):
        super().__init__()




       
        self.background = BackgroundSprite("backgrounds/background1.png")
         # 回主選單but
        #self.back_button = Sprite("UI/button_back.png", (100, 50))
       
        self.back_button = Button(
        "UI/button_back.png",
        "UI/button_back_hover.png",
        GameSettings.SCREEN_WIDTH//2 - 300,
        GameSettings.SCREEN_HEIGHT//2 + 100,
        100, 100, #按鈕寬高
        lambda: scene_manager.change_scene("menu")
         )
       
        #底圖
        self.bg_image = pg.image.load("assets/images/UI/raw/UI_Flat_Frame01a.png").convert_alpha()
        self.bg_image = pg.transform.scale(self.bg_image, (800, 520))  # 寬高
           
        self.vol_max_width = 700
        self.vol_height = 20
        #self.volume = 0.5
        #knob_image = pg.image.load("assets/images/UI/raw/UI_Flat_Handle03a.png").convert_alpha()
        self.volume_slider = Slider(
            x=300,
            y=260,   # 這裡是滑桿 Y 座標
            width=self.vol_max_width,
            height=self.vol_height,
            min_value=0,
            max_value=1,
            initial_value=GameSettings.AUDIO_VOLUME,
            knob_img="UI/raw/UI_Flat_Handle03a.png",
            knob_width=30,    
            knob_height=30
        )




        # --- MUTE BUTTON ---
        self.is_muted = False
        #####
        self.saved_volume = GameSettings.AUDIO_VOLUME
        self.mute_button = Button(
            img_path="UI/raw/UI_Flat_ToggleOff03a.png",
            img_hovered_path="UI/raw/UI_Flat_ToggleOff03a.png",      # toggle 不用 hover
            x=400, y=300, width=40, height=40,
            on_click=self.toggle_mute,
            img_on="UI/raw/UI_Flat_ToggleOn03a.png",
            img_off="UI/raw/UI_Flat_ToggleOff03a.png"
        )
        
        #字
                                 #None表預設字型 or  我這裡有設                                     #60是字大小
        self.font_small  = pg.font.Font("assets/fonts/Minecraft.ttf", 20)
        self.font_medium = pg.font.Font("assets/fonts/Minecraft.ttf", 30)
        self.font_large  = pg.font.Font("assets/fonts/Minecraft.ttf", 60)
        #self.text_surface = self.font.render("Setting", True, (0,0,0)) #白
        self.texts = [
        ("Setting ", self.font_large, (600, 150)),
        ("Volume",  self.font_medium,(300, 220)),
        ("Mute",self.font_medium, (300, 300))
        ]




    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            sound_manager.set_bgm_volume(0)
        else:
            sound_manager.set_bgm_volume(self.volume_slider.value)


    


    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 101 Opening (Part 1).ogg")
        self.volume_slider.value = GameSettings.AUDIO_VOLUME


        #####
        self.volume_slider.update_knob_position()
        # 根據當前音量設定實際播放音量
        if self.is_muted:
            sound_manager.set_bgm_volume(0)
        else:
            sound_manager.set_bgm_volume(GameSettings.AUDIO_VOLUME)

       
        pass
       
    @override
    def exit(self) -> None:
        #####
        GameSettings.AUDIO_VOLUME = self.volume_slider.value
        pass
       
    @override
    def update(self, dt: float):
        #vol
        old_value = self.volume_slider.value
        self.volume_slider.update(dt)
        
        if abs(self.volume_slider.value - old_value) > 0.001:  # 有變化
            GameSettings.AUDIO_VOLUME = self.volume_slider.value
            
            if not self.is_muted:
                sound_manager.set_bgm_volume(GameSettings.AUDIO_VOLUME)
        
        self.mute_button.update(dt)

        #goback
        self.back_button.update(dt)
       
       
    @override
    def draw(self, screen: pg.Surface) -> None:
        self.background.draw(screen)
        screen.blit(self.bg_image, (250, 100)) #位置
        self.volume_slider.draw(screen)
        self.back_button.draw(screen)
       




        for text, font, pos in self.texts:
            text_surface = font.render(text, True, (0,0,0))
            screen.blit(text_surface, pos)




        volume_percent = int(self.volume_slider.value * 100)
        volume_value = self.font_medium.render(f"{volume_percent}%", True, (255, 255, 255))
        screen.blit(volume_value, (500, 220))




        self.mute_button.draw(screen)
       


    @override
    def handle_event(self, event: pg.event.Event) -> None:
        """處理場景專屬的事件，例如按鈕點擊和滑塊操作。"""
        # 可選的除錯輸出，用於確認事件被接收
        print("[SettingScene] Event:", event) 
        
        # 將事件傳遞給場景中的所有可互動 UI 元件
        # 這些元件需要處理滑鼠點擊、拖曳等事件
        self.back_button.handle_event(event)
        self.volume_slider.handle_event(event)
        # 由於您在 update 中使用了 mute_button，這裡也應將事件傳遞給它
        self.mute_button.handle_event(event)


