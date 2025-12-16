import pygame as pg

from src.utils import GameSettings, Logger
from .services import scene_manager, input_manager

from src.scenes.menu_scene import MenuScene
from src.scenes.game_scene import GameScene
from src.scenes.setting_scene import SettingScene
from src.scenes.battle_scene import BattleScene
#from src.scenes.catch_scene import CatchPokemonScene
#from src.scenes.gym_scene import GymScene
#from src.scenes.shop_scene import ShopScene
class Engine:

    screen: pg.Surface              # Screen Display of the Game
    clock: pg.time.Clock            # Clock for FPS control
    running: bool                   # Running state of the game

    def __init__(self):
        Logger.info("Initializing Engine")

        pg.init()

        self.screen = pg.display.set_mode((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
        self.clock = pg.time.Clock() #Clock 控制 FPS：例如 60 FPS → 每秒畫面更新 60 次。
        self.running = True

        pg.display.set_caption(GameSettings.TITLE)

        scene_manager.register_scene("menu", MenuScene())#一開始就固定存在
        scene_manager.register_scene("game", GameScene())#一開始就固定存在
        scene_manager.register_scene("setting", SettingScene())#一開始就固定存在
        scene_manager.register_scene("battle", BattleScene()) #我之後可以改成動態註冊，跟catch一樣
        
        
        '''{
            "menu" : MenuScene(),
            "game" : GameScene(),
            "setting" : SettingScene(),
            "battle" : BattleScene(),
            }'''
        #scene_manager.register_scene("catch", CatchPokemonScene())
        '''
        [TODO HACKATHON 5]
        Register the setting scene here
        '''
        scene_manager.change_scene("menu")
        
        
    def run(self):
        Logger.info("Running the Game Loop ...")

        while self.running:
            dt = self.clock.tick(GameSettings.FPS) / 1000.0
            self.handle_events()
            self.update(dt)
            self.render()

    def handle_events(self): #我之後應該要在gamescene那裏用到
        input_manager.reset()
        for event in pg.event.get():
            if event.type == pg.QUIT:
                self.running = False
            input_manager.handle_events(event)

        

    def update(self, dt: float):
        scene_manager.update(dt)

    def render(self):
        self.screen.fill((0, 0, 0))     # Make sure the display is cleared
        scene_manager.draw(self.screen) # Draw the current scene
        pg.display.flip()               # Render the display
        '''Engine.render()
            │
            ├─ clear screen
            │
            ├─ scene_manager.draw(screen)
            │    └─ current_scene.draw(screen)
            │         ├─ font.render(text)  ← 產生文字圖片
            │         ├─ screen.blit(...)   ← 把文字/角色/背景畫上去
            │         └─ 其他圖片繪製
            │
            └─ pg.display.flip()  ← 顯示到螢幕
            '''