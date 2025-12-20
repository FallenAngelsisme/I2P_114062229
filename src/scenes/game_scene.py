import pygame as pg
import threading
import time
import json
import pygame



from src.scenes.scene import Scene
from src.core import GameManager, OnlineManager
from src.utils import Logger, PositionCamera, GameSettings, Position
from src.core.services import sound_manager,input_manager,scene_manager
from src.sprites import Sprite, Animation
from typing import override
from src.interface.components import Button#my2
from src.interface.components.slider import Slider#my2
from src.core.managers.minimap_manager import MinimapManager
from src.core.managers.navigation_manager  import NavigationManager
from src.interface.components.navigation_ui  import NavigationUI

from typing import override, Dict, Tuple
from src.interface.components.chat_overlay import ChatOverlay


class GameScene(Scene):
    game_manager: GameManager
    online_manager: OnlineManager | None
    sprite_online: Sprite
   
    def __init__(self):
        self.chat_overlay = None
        self.online_sprites: Dict[int, Sprite] = {} #online
        super().__init__()
        #minimap
        self.game_manager = None
        self.minimap = None
        #navigation
        self.nav_manager = None
        self.nav_ui = None
        
        #
        self.warning_sign = Sprite(
            "exclamation.png",
            (GameSettings.TILE_SIZE // 2, GameSettings.TILE_SIZE // 2)
        )
        


        # Overlay 狀態
        self.is_overlay_open = False
        self.is_bag_overlay_open = False

        # ★ NEW: 金錢 UI 
        self.coin_icon = pg.image.load("assets/images/ingame_ui/coin.png").convert_alpha()
        self.coin_icon = pg.transform.scale(self.coin_icon, (30, 30))

        #buttom
        px, py = GameSettings.SCREEN_WIDTH // 2, GameSettings.SCREEN_HEIGHT // 2
        self.bag = Button(
            "UI/button_backpack.png", "UI/button_backpack_hover.png",
            GameSettings.SCREEN_WIDTH-170, 20, 60, 60,# x, y 座標
            self.open_bag
            #lambda: scene_manager.change_scene("game")
        )#my2
        self.setting_button = Button(
            "UI/button_setting.png", "UI/button_setting_hover.png",
            GameSettings.SCREEN_WIDTH-100, 20, 60, 60,# x, y 座標
            self.open_overlay
            #lambda: scene_manager.change_scene("game")
        )#my2
        self.btn_back = Button(
            "UI/button_back.png", "UI/button_back_hover.png",
            300, 440,
            60, 60,
            self.close_overlay
        )
        
        self.save_button = Button(
            "UI/button_save.png","UI/button_save_hover.png",
            x=300, y=360, width=60, height=60,
            on_click=self.save_game
        )

        self.load_button = Button(
            "UI/button_load.png","UI/button_load_hover.png",
            x=370, y=360, width=60, height=60,
            on_click=self.load_game
        )

        
        

        self.back_image = pg.image.load("assets/images/UI/raw/UI_Flat_Frame03a.png").convert_alpha()
        self.back_image = pg.transform.scale(self.back_image, (800, 520))  # 寬高
       
        self.vol_max_width = 700
        self.vol_height = 20
       
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

        # MUTE BUTTON
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
        self.texts = [
        ("Setting ", self.font_large, (600, 150)),
        ("Volume",  self.font_medium,(300, 220)),
        ("Mute",self.font_medium, (300, 300))
        ]

        # 儲存/讀取訊息顯示
        self.message_text = ""
        self.message_timer = 0
        self.message_duration = 2.0  # 訊息顯示2秒

        # Game Manager
        manager = GameManager.load("saves/game0.json")
        if manager is None:
            Logger.error("Failed to load game manager")
            exit(1)
        self.game_manager = manager
       
        # Online Manager
        if GameSettings.IS_ONLINE:
            self.online_manager = OnlineManager()
            self.chat_overlay = ChatOverlay(
                send_callback= self.online_manager.send_chat, #<- send chat method
                get_messages= self.online_manager.get_recent_chat, #<- get chat messages method
            )
        else:
            self.online_manager = None
        self.sprite_online = Sprite("ingame_ui/options1.png", (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE))
        self._chat_bubbles: Dict[int, Tuple[str, str]] = {}
        self._last_chat_id_seen = 0
        #button 生效時!我需要
    def open_overlay(self):
        self.is_overlay_open = True
        self.volume_slider.value = GameSettings.AUDIO_VOLUME  # ← 新增
        self.volume_slider.update_knob_position()  


    def close_overlay(self):
        self.is_overlay_open = False

    def open_bag(self):
        self.game_manager.bag.toggle()



    def toggle_mute(self):
        self.is_muted = not self.is_muted
        if self.is_muted:
            sound_manager.set_bgm_volume(0)
        else:
            sound_manager.set_bgm_volume(self.volume_slider.value)


    def save_game(self):
        """儲存遊戲狀態"""
        try:
            if self.game_manager and self.game_manager.player:
                # 更新當前地圖的玩家位置
                current_map = self.game_manager.current_map
                
                
                # 儲存到檔案
                self.game_manager.save("saves/game0.json")
                self.show_message("Game Saved!")
                Logger.info(f"Game saved at position: ({self.game_manager.player.position.x}, {self.game_manager.player.position.y})")
            else:
                self.show_message("Save Failed!")
                Logger.warning("Cannot save: player is None")
        except Exception as e:
            self.show_message("Save Failed!")
            Logger.error(f"Failed to save game: {e}")

    def load_game(self):
        """讀取遊戲狀態"""
        try:
            # 重新載入遊戲資料
            manager = GameManager.load("saves/game0.json")
            if manager is None:
                self.show_message("Load Failed!")
                Logger.error("Failed to load game manager")
                return
            
            # 保存舊的 online_manager
            old_online = self.online_manager
            
            # 更新 game_manager
            self.game_manager = manager
            self.online_manager = old_online
            
             #重建 minimap
            self.minimap = MinimapManager(self.game_manager)
            # 確保玩家位置正確設置
            if self.game_manager.player:
                # 從存檔讀取的位置已經是像素座標
                spawn_pos = self.game_manager.current_map.spawn
                self.game_manager.player.position = Position(spawn_pos.x, spawn_pos.y)
                
                # 強制更新相機位置，避免畫面跳動
                self.game_manager.player.animation.update_pos(self.game_manager.player.position)
                
                self.show_message("Game Loaded!")
                Logger.info(f"Game loaded at position: ({spawn_pos.x}, {spawn_pos.y})")
            else:
                self.show_message("Load Failed!")
                Logger.warning("Loaded game has no player")
                
        except Exception as e:
            self.show_message("Load Failed!")
            Logger.error(f"Failed to load game: {e}")

    def show_message(self, text: str):
        """顯示訊息"""
        self.message_text = text
        self.message_timer = self.message_duration

    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 103 Pallet Town.ogg")
        #sound_manager.set_bgm_volume(self.volume_slider.value)
        if not self.is_muted:
            sound_manager.set_bgm_volume(GameSettings.AUDIO_VOLUME)
        else:
            sound_manager.set_bgm_volume(0)
        if self.online_manager:
            self.online_manager.enter()
        
        #minimap
        
        self.minimap = MinimapManager(self.game_manager)

        #navigation
        self.nav_manager = NavigationManager(
            self.game_manager.player,
            self.game_manager
        )
        self.nav_ui = NavigationUI(self.nav_manager, self.font_large, self.font_medium)
    @override
    def exit(self) -> None:
        # Keep online connection alive when switching scenes (e.g. to battle)
        # to preserve the same player id and chat state. Do not call
        # `self.online_manager.exit()` here to avoid reconnects on return.
        pass
       
    @override
    def update(self, dt: float):
        if self.message_timer > 0:
            self.message_timer -= dt
            if self.message_timer <= 0:
                self.message_text = ""

        if self.game_manager.bag.visible:
            self.game_manager.bag.update(dt)
            return
    
        if self.is_overlay_open:

            # 阻擋 navigation 的事件，但不隱藏按鈕
            if self.nav_ui:
                self.nav_ui.block_input = True


            self.btn_back.update(dt)
            self.load_button.update(dt)
            self.save_button.update(dt)
            #vol
            self.mute_button.update(dt)
            old_value = self.volume_slider.value
            self.volume_slider.update(dt)
            if not self.is_muted:
                if abs(self.volume_slider.value - old_value) > 0.001:
                    GameSettings.AUDIO_VOLUME = self.volume_slider.value
                    self.saved_volume = self.volume_slider.value
                    sound_manager.set_bgm_volume(self.volume_slider.value)
            
            else:
                # 靜音時，滑桿移動會更新 saved_volume，但不影響實際播放音量
                if abs(self.volume_slider.value - old_value) > 0.001:
                    self.saved_volume = self.volume_slider.value
                    GameSettings.AUDIO_VOLUME = self.volume_slider.value

            
        
        if self.nav_ui:
            self.nav_ui.block_input = False 
        # Check if there is assigned next scene
        self.game_manager.try_switch_map()
       
        # Update player and other data
        if self.game_manager.player:
            self.game_manager.player.update(dt)
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.update(dt)
            if enemy.detected and input_manager.key_pressed(pygame.K_SPACE):
                
                scene_manager.change_scene("battle") 

        for npc in self.game_manager.current_npcs:
            npc.update(dt)
            if npc.detected and input_manager.key_pressed(pygame.K_SPACE):
                if npc.type == "shop":
                    from src.scenes.shop_scene import ShopScene
                    scene_manager.register_scene("shop", ShopScene(self.game_manager))
                    scene_manager.change_scene("shop")
                elif npc.type == "talk":
                    from src.scenes.talk_scene import TalkScene
                    scene_manager.register_scene("talk", TalkScene(npc.dialogues))
                    scene_manager.change_scene("talk")
                
        if self.game_manager.player:
            player_rect = pg.Rect(
                self.game_manager.player.position.x,
                self.game_manager.player.position.y,
                GameSettings.TILE_SIZE,
                GameSettings.TILE_SIZE
            )
            for bush_rect in self.game_manager.current_map._bush_map:
                if player_rect.colliderect(bush_rect) and pg.key.get_pressed()[pg.K_SPACE]:
                    # 進入抓寶可夢場景
                    from src.scenes.catch_scene import CatchPokemonScene
                    scene_manager.register_scene("catch", CatchPokemonScene(self.game_manager))
                    scene_manager.change_scene("catch")
                    break  # 避免一次碰撞多次觸發


        # navigation 更新（正常狀態）
        self.nav_manager.update(dt)
        if self.nav_ui:
            self.nav_ui.update(dt) 
        # Update others
        #TODO: UPDATE CHAT OVERLAY:

        if self.chat_overlay:
            if input_manager.key_pressed(pg.K_t):
                self.chat_overlay.open()
            self.chat_overlay.update(dt)
        # Update chat bubbles from recent messages

        # This part's for the chatting feature, we've made it for you.
        if self.online_manager:
            try:
                msgs = self.online_manager.get_recent_chat(50)
                max_id = self._last_chat_id_seen
                now = time.monotonic()
                for m in msgs:
                    mid = int(m.get("id", 0))
                    if mid <= self._last_chat_id_seen:
                        continue
                    sender = int(m.get("from", -1))
                    text = str(m.get("text", ""))
                    if sender >= 0 and text:
                        self._chat_bubbles[sender] = (text, now + 5.0)
                    if mid > max_id:
                        max_id = mid
                self._last_chat_id_seen = max_id
            except Exception:
                pass
        if self.game_manager.player is not None and self.online_manager is not None:
            p = self.game_manager.player
            self.online_manager.update(
                p.position.x,
                p.position.y,
                self.game_manager.current_map.path_name,
                p.direction,
                p.is_moving
            )
            # Advance online sprites' animations each frame so they animate
            try:
                for sp in self.online_sprites.values():
                    sp.update(dt)
            except Exception:
                pass
        self.setting_button.update(dt)#my2
        self.bag.update(dt)#my2
        
        

        

        
            

    @override
    def draw(self, screen: pg.Surface):  
        player = self.game_manager.player      
        if self.game_manager.player:
            '''
            [TODO HACKATHON 3]
            Implement the camera algorithm logic here
            Right now it's hard coded, you need to follow the player's positions
            you may use the below example, but the function still incorrect, you may trace the entity.py
           
            camera = self.game_manager.player.camera
            '''
            ####
            if GameSettings.DEBUG:  # 如果有 debug 模式
                Logger.info(f"Player position: {self.game_manager.player.position.x}, {self.game_manager.player.position.y}")
            #camera = PositionCamera(16 * GameSettings.TILE_SIZE, 30 * GameSettings.TILE_SIZE) 固定鏡頭
            camera = self.game_manager.player.camera #在entity.py裡面有 camera(self) 裡面用player的position算鏡頭位置
            #所以這裡用play.camera
            self.game_manager.current_map.draw(screen, camera)
            self.game_manager.player.draw(screen, camera)
        else:
            Logger.warning("Player is None!")
            camera = PositionCamera(0, 0)
            self.game_manager.current_map.draw(screen, camera)
       
        for enemy in self.game_manager.current_enemy_trainers:
            enemy.draw(screen, camera)

        for npc in self.game_manager.current_npcs:
            npc.draw(screen, camera)
        
       
        
        self.minimap.draw(screen)

        # Draw online players on minimap via MinimapManager
        if self.online_manager:
            try:
                players = self.online_manager.get_list_players()
                current_map_key = self.game_manager.current_map.path_name
                self.minimap.draw_online_players(screen, players, current_map_key)
            except Exception:
                pass

        
        if self.chat_overlay:
            self.chat_overlay.draw(screen)
        # --- Debug: online manager status (temporary) ---
        if self.online_manager:
            try:
                dbg_x, dbg_y = 10, 10
                info_font = self.font_small
                pid = self.online_manager.player_id
                players = self.online_manager.get_list_players()
                info_lines = [f"online_id={pid}", f"others={len(players)}"]
                for i, line in enumerate(info_lines):
                    surf = info_font.render(line, True, (255, 255, 0))
                    screen.blit(surf, (dbg_x, dbg_y + i * (info_font.get_height() + 2)))
            except Exception:
                pass
        if self.online_manager and self.game_manager.player:
            list_online = self.online_manager.get_list_players()
            for p in self.online_manager.get_list_players():
                pid = p["id"]

                if pid not in self.online_sprites:
                    # Use same animation as Entity so we can switch rows/directions
                    self.online_sprites[pid] = Animation(
                        "character/ow6.png",
                        ["down", "left", "right", "up"],
                        4,
                        (GameSettings.TILE_SIZE, GameSettings.TILE_SIZE)
                    )

                sprite = self.online_sprites[pid]

                sprite.set_direction(p["dir"])
                if p["moving"]:
                    sprite.play()
                else:
                    sprite.stop()

                cam = self.game_manager.player.camera
                # Use world position and let sprite.draw handle camera transform
                world_pos = Position(p["x"], p["y"])
                sprite.update_pos(world_pos)
                sprite.draw(screen, cam)
            try:
                self._draw_chat_bubbles(screen, camera)
            except Exception:
                pass
       

        self.game_manager.bag.draw(screen)
        self.bag.draw(screen) #my2
        self.setting_button.draw(screen)
        
        # ★ NEW: 繪製金錢 (Requirement 2)
        if self.game_manager and self.game_manager.bag:
            money = self.game_manager.bag._money
            
            coin_x = GameSettings.SCREEN_WIDTH - 350 
            coin_y = 20
            
            screen.blit(self.coin_icon, (coin_x, coin_y))

            money_text = self.font_medium.render(f"{money}", True, (255, 255, 255)) 
            screen.blit(money_text, (coin_x + 35, coin_y + 4))
        
        if self.nav_ui:
            self.nav_ui.draw(screen, camera)

        # Overlay
        if self.is_overlay_open:
            # 暗背景
                #建立一個新的層
            overlay = pg.Surface((GameSettings.SCREEN_WIDTH, GameSettings.SCREEN_HEIGHT))
                #alpha是指 整體透明度
            overlay.set_alpha(180)
                #填上顏色
            overlay.fill((0, 0, 0))
                #貼到主畫上
            screen.blit(overlay, (0, 0))

            # Overlay 內容
            screen.blit(self.back_image, (250, 100)) #位置

            self.volume_slider.draw(screen)
            self.mute_button.draw(screen)
            self.load_button.draw(screen)
            self.save_button.draw(screen)
        
            for text, font, pos in self.texts:
                text_surface = font.render(text, True, (0,0,0))
                screen.blit(text_surface, pos)
           
            volume_percent = int(self.volume_slider.value * 100)
            volume_value = self.font_medium.render(f"{volume_percent}%", True, (255, 255, 255))
            screen.blit(volume_value, (500, 220))
            # 返回
            self.btn_back.draw(screen)

            #self.game_manager.bag.draw(screen)
        
            # 儲存/讀取訊息
            if self.message_timer > 0:
                surf = self.font_medium.render(self.message_text, True, (255, 255, 255))
                rect = surf.get_rect(center=(GameSettings.SCREEN_WIDTH//2, 50))

                bg = pg.Surface((rect.width + 20, rect.height + 10))
                bg.set_alpha(200)
                bg.fill((0, 0, 0))
                screen.blit(bg, (rect.x - 10, rect.y - 5))
                screen.blit(surf, rect)

            return    
        
    
         #navigate
        if self.nav_ui:
            self.nav_ui.draw(screen, camera)
        

            

        # 顯示儲存/讀取訊息
        if self.message_timer > 0:
            message_surface = self.font_medium.render(self.message_text, True, (255, 255, 255))
            message_rect = message_surface.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, 50))
            
            # 半透明背景
            bg_rect = pg.Rect(message_rect.x - 10, message_rect.y - 5, 
                            message_rect.width + 20, message_rect.height + 10)
            bg_surface = pg.Surface((bg_rect.width, bg_rect.height))
            bg_surface.set_alpha(200)
            bg_surface.fill((0, 0, 0))
            screen.blit(bg_surface, bg_rect)
            
            # 訊息文字
            screen.blit(message_surface, message_rect)

    def _draw_chat_bubbles(self, screen: pg.Surface, camera: PositionCamera) -> None:
        
        if not self.online_manager:
            return
        # REMOVE EXPIRED BUBBLES
        now = time.monotonic()
        expired = [pid for pid, (_, ts) in self._chat_bubbles.items() if ts <= now]
        for pid in expired:
            self._chat_bubbles.pop(pid, None)        
        
        if not self._chat_bubbles:
            return

        # DRAW LOCAL PLAYER'S BUBBLE
        local_pid = self.online_manager.player_id
        if self.game_manager.player and local_pid in self._chat_bubbles:
            text, _ = self._chat_bubbles[local_pid]
            self._draw_chat_bubble_for_pos(
                screen,
                camera,
                self.game_manager.player.position,
                text,
                self.font_small
            )

        # DRAW OTHER PLAYERS' BUBBLES
        for p in self.online_manager.get_list_players():
            pid = p["id"]
            if pid == local_pid:
                continue
            if pid not in self._chat_bubbles:
                continue

            world_pos = Position(p["x"], p["y"])
            text, _ = self._chat_bubbles[pid]
            self._draw_chat_bubble_for_pos(
                screen,
                camera,
                world_pos,
                text,
                self.font_small
            )
        """
        DRAWING CHAT BUBBLES:
        - When a player sends a chat message, the message should briefly appear above
        that player's character in the world, similar to speech bubbles in RPGs.
        - Each bubble should last only a few seconds before fading or disappearing.
        - Only players currently visible on the map should show bubbles.

         What you need to think about:
            ------------------------------
            1. **Which players currently have messages?**
            You will have a small structure mapping player IDs to the text they sent
            and the time the bubble should disappear.

            2. **How do you know where to place the bubble?**
            The bubble belongs above the player's *current position in the world*.
            The game already tracks each player’s world-space location.
            Convert that into screen-space and draw the bubble there.

            3. **How should bubbles look?**
            You decide. The visual style is up to you:
            - A rounded rectangle, or a simple box.
            - Optional border.
            - A small triangle pointing toward the character's head.
            - Enough padding around the text so it looks readable.

            4. **How do bubbles disappear?**
            Compare the current time to the stored expiration timestamp.
            Remove any bubbles that have expired.

            5. **In what order should bubbles be drawn?**
            Draw them *after* world objects but *before* UI overlays.

        Reminder:
        - For the local player, you can use the self.game_manager.player.position to get the player's position
        - For other players, maybe you can find some way to store other player's last position?
        - For each player with a message, maybe you can call a helper to actually draw a single bubble?
        """
    def _draw_chat_bubble_for_pos(self, screen: pg.Surface, camera: PositionCamera, world_pos: Position, text: str, font: pg.font.Font):
        # 1. 世界座標 → 螢幕座標
        screen_pos = camera.transform_position_as_position(world_pos)

        # 2. 設定泡泡顯示在角色「頭上」
        sprite_center_x = int(screen_pos.x + (GameSettings.TILE_SIZE / 2))
        sprite_top_y = int(screen_pos.y)

        # 3. 渲染文字並計算尺寸
        text_surf = font.render(text, True, (0, 0, 0))
        text_rect = text_surf.get_rect()

        padding_x = 12  # 增加水平內邊距
        padding_y = 10  # 增加垂直內邊距
        border_radius = 8  # 圓角半徑
        vertical_gap = 15 # 泡泡與角色頭部之間的距離

        bubble_width = text_rect.width + padding_x * 2
        bubble_height = text_rect.height + padding_y * 2

        # 泡泡頂部位置 (考慮 vertical_gap)
        bubble_left = sprite_center_x - (bubble_width // 2)
        bubble_top = sprite_top_y - bubble_height - vertical_gap
        bubble_rect = pg.Rect(bubble_left, bubble_top, bubble_width, bubble_height)

        # 限制泡泡不超出螢幕邊界 (保持您的原版邏輯)
        sw, sh = screen.get_size()
        if bubble_rect.left < 6:
            bubble_rect.left = 6
        if bubble_rect.right > sw - 6:
            bubble_rect.left = sw - 6 - bubble_rect.width
        if bubble_rect.top < 6:
            bubble_rect.top = 6
        
        # 重新計算置中的 X 座標 (如果因為邊界修正了 left)
        # 這樣文字才能正確置中於修正後的矩形內
        text_x = bubble_rect.x + padding_x
        text_y = bubble_rect.y + padding_y

        # --- 精美繪圖開始 ---

        # 顏色定義
        COLOR_BG = (255, 255, 255) # 白色背景
        COLOR_BORDER = (0, 0, 0)   # 黑色邊框
        COLOR_SHADOW = (150, 150, 150, 100) # 淺灰陰影 (半透明)
        
        # 陰影偏移
        shadow_offset = 3

        # 1. 繪製陰影 (圓角矩形)
        shadow_rect = bubble_rect.move(shadow_offset, shadow_offset)
        
        # 注意：pg.draw.rect 繪製圓角在老版本 Pygame 上可能不支援透明度，但我們在這裡使用一個技巧：
        # 建立一個 Surface 讓它透明，然後在這個 Surface 上繪製。
        shadow_surf = pg.Surface((shadow_rect.width, shadow_rect.height), pg.SRCALPHA)
        pg.draw.rect(shadow_surf, COLOR_SHADOW, shadow_surf.get_rect(), border_radius=border_radius)
        screen.blit(shadow_surf, shadow_rect.topleft)

        # 2. 繪製泡泡主體 (圓角矩形)
        pg.draw.rect(
            screen,
            COLOR_BG,
            bubble_rect,
            border_radius=border_radius
        )

        # 3. 繪製邊框
        pg.draw.rect(
            screen,
            COLOR_BORDER,
            bubble_rect,
            width=2, # 邊框厚度
            border_radius=border_radius
        )

        # 4. 繪製指向角色的箭頭 (指標)
        arrow_size = 10
        # 箭頭頂點
        p_tip = (sprite_center_x, sprite_top_y - 2) # 靠近角色頭部的點
        
        # 箭頭底邊（位於泡泡底部中間）
        p_base_center_x = sprite_center_x
        p_base_y = bubble_rect.bottom 
        
        # 三個頂點：
        # V1: 左邊底部點
        # V2: 頂部點 (指向角色)
        # V3: 右邊底部點
        arrow_points = [
            (p_base_center_x - arrow_size // 2, p_base_y), 
            p_tip,
            (p_base_center_x + arrow_size // 2, p_base_y)
        ]
        
        # 繪製箭頭主體 (白色)
        pg.draw.polygon(screen, COLOR_BG, arrow_points)
        
        # 繪製箭頭邊框 (黑色)
        # 這裡只需要畫兩條線，連接 p_tip 到左右底點
        pg.draw.line(screen, COLOR_BORDER, p_tip, arrow_points[0], 2)
        pg.draw.line(screen, COLOR_BORDER, p_tip, arrow_points[2], 2)
        
        # 由於箭頭與矩形相交處可能會露黑線，需要額外在矩形上補一小塊邊框 (這是一個 Pygame 圓角矩形和多邊形重疊的常見問題)
        # 在箭頭底部繪製一條短黑線，覆蓋矩形底部的白色 (可選，但能讓邊界更清晰)
        pg.draw.line(
            screen, 
            COLOR_BORDER, 
            (arrow_points[0][0], p_base_y), 
            (arrow_points[2][0], p_base_y), 
            2
        )

        # 5. 畫文字
        text_pos = (text_x, text_y)
        screen.blit(text_surf, text_pos)