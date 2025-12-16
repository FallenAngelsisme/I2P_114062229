import pygame as pg
import random
from src.sprites import BackgroundSprite
from src.scenes.scene import Scene
from src.core import GameManager
from src.utils import Logger, GameSettings
from src.utils.definition import Monster
from src.core.services import scene_manager, sound_manager
from src.interface.components import Button
from typing import override

class CatchPokemonScene(Scene):
    def __init__(self, game_manager: GameManager):
        super().__init__()
        self.game_manager = game_manager
        
        # Pokemon data
        self.wild_pokemon = self._generate_wild_pokemon()
        self.catch_attempts = 0
        self.max_attempts = 3
        self.pokemon_caught = False
        self.catch_failed = False
        
        # Catch success rate (0.0 to 1.0)
        self.base_catch_rate = 0.5
        
        # UI Elements
        self.background = BackgroundSprite("backgrounds/background1.png")
        self.font_small = pg.font.Font("assets/fonts/Minecraft.ttf", 20)
        self.font_medium = pg.font.Font("assets/fonts/Minecraft.ttf", 30)
        self.font_large = pg.font.Font("assets/fonts/Minecraft.ttf", 40)
        
        # Buttons
        self.catch_button = Button(
            "UI/raw/UI_Flat_Button02a_3.png", 
            "UI/raw/UI_Flat_Button02a_3.png",
            450, 500, 150, 50,
            self.attempt_catch
        )
        
        self.run_button = Button(
            "UI/raw/UI_Flat_Button02a_3.png",
            "UI/raw/UI_Flat_Button02a_3.png",
            650, 500, 150, 50,
            self.run_away
        )
        
        # Message display
        self.message = f"A wild {self.wild_pokemon['name']} appeared!"
        self.message_timer = 2.0
        
        # Load pokemon sprite
        try:                                                                        #把圖片轉換成和螢幕相容的格式or透明區
            self.pokemon_sprite = pg.image.load("assets/images/" + self.wild_pokemon["sprite_path"]).convert_alpha()
            self.pokemon_sprite = pg.transform.scale(self.pokemon_sprite, (200, 200))
        except:
            self.pokemon_sprite = None
            Logger.warning(f"Could not load sprite: {self.wild_pokemon['sprite_path']}")
    
    def _generate_wild_pokemon(self):
        """Generate a random wild pokemon我先自己設"""
        pokemon_list = [
            {"name": "Pikachu", "level": random.randint(3, 7), "sprite_path": "menu_sprites/menusprite1.png"},
            {"name": "Charmander", "level": random.randint(3, 7), "sprite_path": "menu_sprites/menusprite2.png"},
            {"name": "Bulbasaur", "level": random.randint(3, 7), "sprite_path": "menu_sprites/menusprite3.png"},
            {"name": "Squirtle", "level": random.randint(3, 7), "sprite_path": "menu_sprites/menusprite4.png"},
        ]
        return random.choice(pokemon_list)
    
    def attempt_catch(self):
        """Attempt to catch the pokemon"""
        if self.pokemon_caught or self.catch_failed:
            return
        
        # Check if player has pokeballs
        has_pokeball = False
        
        for item in self.game_manager.bag._items_data:
            if item.name == "Pokeball" and item.count > 0:
                has_pokeball = True
                break
        
        if not has_pokeball:
            self.message = "No Pokeballs left!"
            self.message_timer = 1.5
            self.catch_failed = True
            return
        
        # Use a pokeball
        self.game_manager.bag.del_item("Pokeball")

        self.catch_attempts += 1
        
        # Calculate catch success
        # Each attempt increases success rate slightly
        catch_rate = self.base_catch_rate + (self.catch_attempts * 0.15)
        success = random.random() < catch_rate
        
        if success:
            self.pokemon_caught = True
            self.message = f"Gotcha! {self.wild_pokemon['name']} was caught!"
            self.message_timer = 2.5
            
            # Create Monster object with proper stats
            level = self.wild_pokemon['level']
            max_hp = 30 + (level * 5)  # Calculate HP based on level
            
            caught_monster = Monster(
                name=self.wild_pokemon['name'],
                hp=max_hp,  # Start with full HP
                max_hp=max_hp,
                level=level,
                sprite_path=self.wild_pokemon['sprite_path']
            )
            
            # Debug: Check bag before adding
            Logger.info(f"Bag before catch: {len(self.game_manager.bag._monsters_data)} monsters")
            
            # Add to game manager's bag
            self.game_manager.bag.add_monster(caught_monster)
            
            # Debug: Check bag after adding
            Logger.info(f"Bag after catch: {len(self.game_manager.bag._monsters_data)} monsters")
            Logger.info(f"Successfully caught {caught_monster.name} Lv.{caught_monster.level}!")
            
        elif self.catch_attempts >= self.max_attempts:
            self.catch_failed = True
            self.message = f"{self.wild_pokemon['name']} broke free and fled!"
            self.message_timer = 2.5
        else:
            self.message = f"Oh no! The Pokemon broke free! ({self.catch_attempts}/{self.max_attempts})"
            self.message_timer = 1.5
    
    def run_away(self):
        """Run away from the encounter"""
        self.message = "Got away safely!"
        self.message_timer = 1.5
        self.catch_failed = True
    
    @override
    def enter(self) -> None:
        sound_manager.play_bgm("RBY 110 Battle! (Wild Pokemon).ogg")
        sound_manager.set_bgm_volume(GameSettings.AUDIO_VOLUME)
        Logger.info("Entered catch scene")
    
    @override
    def exit(self) -> None:
        Logger.info("Exiting catch scene")
    
    @override
    def update(self, dt: float):
        # Update message timer
        if self.message_timer > 0:
            self.message_timer -= dt
        
        # Return to game scene when catch is complete
        if (self.pokemon_caught or self.catch_failed) and self.message_timer <= 0:
            Logger.info("Returning to game scene")
            scene_manager.change_scene("game")
        
        # Update buttons only if catch is still ongoing
        if not self.pokemon_caught and not self.catch_failed:
            self.catch_button.update(dt)
            self.run_button.update(dt)
    
    @override
    def draw(self, screen: pg.Surface) -> None:
        # Draw background
        self.background.draw(screen)
        
        # Draw pokemon sprite
        if self.pokemon_sprite:
            sprite_x = GameSettings.SCREEN_WIDTH // 2 - 100
            sprite_y = 150
            screen.blit(self.pokemon_sprite, (sprite_x, sprite_y))
        
        # Draw pokemon info
        name_text = self.font_large.render(self.wild_pokemon["name"], True, (255, 255, 255))
        name_rect = name_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, 100))
        screen.blit(name_text, name_rect)
        
        level_text = self.font_medium.render(f"Lv. {self.wild_pokemon['level']}", True, (255, 255, 0))
        level_rect = level_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, 380))
        screen.blit(level_text, level_rect)
        
        # Draw message box
        message_bg = pg.Surface((1280, 150))
        message_bg.set_alpha(220)
        message_bg.fill((30, 30, 30))
        screen.blit(message_bg, (0, 450))
        
        # Draw message
        message_text = self.font_medium.render(self.message, True, (255, 255, 255))
        message_rect = message_text.get_rect(center=(GameSettings.SCREEN_WIDTH // 2, 480))
        screen.blit(message_text, message_rect)
        
        # Draw buttons (only if catch is ongoing)
        if not self.pokemon_caught and not self.catch_failed and self.message_timer <= 0:
            self.catch_button.draw(screen)
            catch_text = self.font_small.render("CATCH", True, (0, 0, 0))
            screen.blit(catch_text, (490, 510))
            
            self.run_button.draw(screen)
            run_text = self.font_small.render("RUN", True, (0, 0, 0))
            screen.blit(run_text, (695, 510))
            
            #我要倒數球球數
            pokeball_count = 0
            for item in self.game_manager.bag._items_data:
                if item.name == "Pokeball":
                    pokeball_count = item.count
                    break
            # Draw attempts remaining
            attempts_text = self.font_small.render(
                f"Pokeballs: {pokeball_count}", 
                True, (255, 255, 255)
            )
            screen.blit(attempts_text, (550, 560))

    