import tcod as libtcod
import pygame
from typing import List, Tuple, Callable, Union, Dict

# Game Files
from constants import *

PYGAME_DISPLAY: pygame.Surface = None
SURFACE_MAIN: pygame.Surface = None
FOV_CALCULATE: bool = None
CLOCK: pygame.time.Clock = None
ASSETS: 'struc_Assets' = None

# Typing
T_MAP = List[List['struc_Tile']]
T_SURFACE = pygame.Surface
T_RECT = Union[pygame.Rect, Tuple[int, int, int, int]]
T_CREATURE = 'com_Creature'
T_AI = 'ai_Test'
T_ITEM = 'com_Item'
T_CONTAINER = 'com_Container'
T_COLOR = Tuple[int, int, int]
T_COORDINATE = Tuple[int, int]
T_MESSAGE = Tuple[str, T_COLOR, T_COLOR]
T_ACTOR = 'obj_Actor'
T_FONT = pygame.font.Font


#  ____  _                   _
# / ___|| |_ _ __ _   _  ___| |_
# \___ \| __| '__| | | |/ __| __|
#  ___) | |_| |  | |_| | (__| |_
# |____/ \__|_|   \__,_|\___|\__|


class struc_Tile:
    """This class functions as a struct that tracks the data for each
    tile within a map.

    # Properties
    struc_Tile.block_path : TRUE if tile prevents actors from moving
    through it under normal circumstances.

    struc_Tile.explored : Initializes to FALSE, set to true if player
    has seen it before."""

    def __init__(self, block_path: bool):
        self.block_path = block_path
        self.explored = False


class struc_Assets:
    """This class is a struct that holds all the assets used in the
    game. This includes sprites, sound effects, and music."""

    def __init__(self):
        # Spritesheets
        # self.spritesheet_player = obj_Spritesheet("data/reptiles.png", 16, 16)
        # self.spritesheet_aquatic = obj_Spritesheet("data/aquatic.png", 16, 16)

        self.spritesheet_player = obj_Spritesheet_Set(
            access_dawnlike_list(["Player0", "Player1"], "Characters/"), 16, 16)
        self.spritesheet_aquatic = obj_Spritesheet_Set(
            access_dawnlike_list(["Aquatic0", "Aquatic1"], "Characters/"), 16, 16)

        self.spritesheet_wall = obj_Spritesheet(access_dawnlike("Objects/Wall"), 16, 16)
        self.spritesheet_floor = obj_Spritesheet(access_dawnlike("Objects/Floor"), 16, 16)

        # Animations
        self.A_PLAYER = self.spritesheet_player.get_animation([(0, 0, 3), (1, 0, 3)], CELL_SIZE)
        self.A_ENEMY = self.spritesheet_aquatic.get_animation([(0, 5, 0), (1, 5, 0)], CELL_SIZE)

        # Sprites
        self.S_WALL = self.spritesheet_wall.get_sprite(3, 3, CELL_SIZE)
        self.S_WALL_EXPLORED: T_SURFACE = self.S_WALL.copy()
        self.S_WALL_EXPLORED.fill((100, 100, 100), special_flags=pygame.BLEND_MULT)

        self.S_FLOOR = self.spritesheet_floor.get_sprite(1, 4, CELL_SIZE)
        self.S_FLOOR_EXPLORED = self.S_FLOOR.copy()
        self.S_FLOOR_EXPLORED.fill((100, 100, 100), special_flags=pygame.BLEND_MULT)

        self.S_CROSSHAIR = self.spritesheet_wall.get_sprite(1, 1, CELL_SIZE)
        self.S_CROSSHAIR.set_alpha(150)

        # Fonts
        self.F_STANDARD: T_FONT = pygame.font.Font(None, 30)
        self.F_MESSAGE: T_FONT = pygame.font.Font(access_dawnlike("GUI/SDS_8x8.ttf"), 16)
        self.F_SMALL_MESSAGE: T_FONT = pygame.font.Font(access_dawnlike("GUI/SDS_6x6.ttf"), 16)

        if USE_CURSOR:
            self.S_CURSOR_STANDARD: T_SURFACE = pygame.image.load("data/cursor_standard.png").convert()
            self.S_CURSOR_STANDARD.set_colorkey(COLOR_WHITE)
            self.S_CURSOR_STANDARD = pygame.transform.scale(self.S_CURSOR_STANDARD, CURSOR_SIZE).convert()

            self.S_CURSOR_INVENTORY: T_SURFACE = pygame.image.load("data/cursor_bag.png").convert()
            self.S_CURSOR_INVENTORY.set_colorkey(COLOR_BLACK)
            self.S_CURSOR_INVENTORY = pygame.transform.scale(self.S_CURSOR_INVENTORY, CURSOR_SIZE).convert()

            self.S_CURSOR_UNUSED: T_SURFACE = pygame.image.load("data/cursor.png").convert()
            self.S_CURSOR_UNUSED.set_colorkey(COLOR_WHITE)
            self.S_CURSOR_UNUSED = pygame.transform.scale(self.S_CURSOR_UNUSED, CURSOR_SIZE).convert()

            # TODO: Add inpect cursor
            self.S_CURSOR_INSPECT: T_SURFACE = None
        else:
            self.S_CURSOR_STANDARD: T_SURFACE = None
            self.S_CURSOR_INVENTORY: T_SURFACE = None
            self.S_CURSOR_INSPECT: T_SURFACE = None
            self.S_CURSOR_UNUSED: T_SURFACE = None


#   ___  _     _           _
#  / _ \| |__ (_) ___  ___| |_ ___
# | | | | '_ \| |/ _ \/ __| __/ __|
# | |_| | |_) | |  __/ (__| |_\__ \
#  \___/|_.__// |\___|\___|\__|___/
#           |__/


class obj_Actor:
    """The actor object represents every entity in the game that
    'interacts' with the player or the environment in some way.  It
    is made up of components which alter an actors behavior.

    # Arguments
    x : starting x position on the current map

    y : starting y position on the current map

    name_object : string containing the name of the object, "chair" or
    "goblin" for example.

    animation : a list of images that make up the object's
   spritesheet. Created within the struc_Assets class.

    obj_Actor.animation_speed : time in seconds it takes to loop through
    the object animation.

    # Properties
    obj_Actor.flicker_speed : derived property, represents the
    conversion of animation length in seconds to number of frames

    obj_Actor.flicker_timer : the current counter until the next frame
    of the animation should be displayed.

    obj_Actor.sprite_image : the current image of the animation that
    is being displayed.  0 is first image, 1 is second, etc.

    # Components
    obj_Actor.creature : any object that has health, and generally can fight.

    obj_Actor.ai : ai is a component that is basically a function that is
    executed every time the object is able to act.  Usually only on creatures.

    obj_Actor.container : containers are objects that can hold an inventory.
    obj_Actor.item : items are items that are able to be picked up and used.

    # Methods
    obj_Actor.draw() : this method draws the object to the screen."""

    def __init__(self, x: int, y: int, name_object: str, animation: List[T_SURFACE], animation_speed: float = 1.0,
                 creature: T_CREATURE = None, ai: T_AI = None, item: T_ITEM = None, container: T_CONTAINER = None):
        self.x: int = x
        self.y: int = y

        self.animation: List[T_SURFACE] = animation
        self.sprite_image: int = 0
        self.animation_speed: float = animation_speed  # in seconds (for the entire animation)

        # animation flicker speed
        self.flicker_timer: float = 0.0

        self.name_object: str = name_object

        self._creature: T_CREATURE = None
        self._item: T_ITEM = None
        self._container: T_CONTAINER = None
        self._ai: T_AI = None

        self.creature = creature
        self.ai = ai
        self.item = item
        self.container = container

    def draw(self):
        """Draws the actor on the screen. If it is an animation, it loops through the entire animation over
        self.animation_speed seconds"""
        is_visible = libtcod.map_is_in_fov(FOV_MAP, self.x, self.y)

        if is_visible:
            if len(self.animation) == 1:
                # SURFACE_MAIN.blit(self.animation[0], (self.x * CELL_WIDTH, self.y * CELL_HEIGHT))
                draw_surface(self.animation[0], SURFACE_MAIN, (self.x * CELL_WIDTH, self.y * CELL_HEIGHT))
            else:
                if CLOCK.get_fps() > 0.0:
                    self.flicker_timer += 1 / CLOCK.get_fps()

                    if self.flicker_timer >= self.animation_speed / len(self.animation):
                        self.sprite_image = (self.sprite_image + 1) % len(self.animation)
                        self.flicker_timer = 0.0

                current_frame = self.animation[self.sprite_image]
                # SURFACE_MAIN.blit(current_frame, (self.x * CELL_WIDTH, self.y * CELL_HEIGHT))
                draw_surface(current_frame, SURFACE_MAIN, (self.x * CELL_WIDTH, self.y * CELL_HEIGHT))

    @property
    def pos(self) -> T_COORDINATE:
        return self.x, self.y

    @pos.setter
    def pos(self, value: T_COORDINATE):
        self.x = value[0]
        self.y = value[1]

    @property
    def creature(self) -> T_CREATURE:
        return self._creature

    @creature.setter
    def creature(self, value: T_CREATURE):
        if value is None:
            if self._creature is not None:
                self._creature.owner = None
                self._creature = None
        else:
            if self._creature is None:
                self._creature = value
                self._creature.owner = self
            else:
                self._creature.owner = None
                self._creature = value
                self._creature.owner = self

    @property
    def item(self) -> T_ITEM:
        return self._item

    @item.setter
    def item(self, value: T_ITEM):
        if value is None:
            if self._item is not None:
                self._item.owner = None
                self._item = None
        else:
            if self._item is None:
                self._item = value
                self._item.owner = self
            else:
                self._item.owner = None
                self._item = value
                self._item.owner = self

    @property
    def container(self) -> T_CONTAINER:
        return self._container

    @container.setter
    def container(self, value: T_CONTAINER):
        if value is None:
            if self._container is not None:
                self._container.owner = None
                self._container = None
        else:
            if self._container is None:
                self._container = value
                self._container.owner = self
            else:
                self._container.owner = None
                self._container = value
                self._container.owner = self

    @property
    def ai(self) -> T_AI:
        return self._ai

    @ai.setter
    def ai(self, value: T_AI):
        if value is None:
            if self._ai is not None:
                self._ai.owner = None
                self._ai = None
        else:
            if self._ai is None:
                self._ai = value
                self._ai.owner = self
            else:
                self._ai.owner = None
                self._ai = value
                self._ai.owner = self

    def distance_to(self, other: T_ACTOR) -> float:
        dx = other.x - self.x
        dy = other.y - self.y
        return ((dx ** 2) + (dy ** 2)) ** 0.5

    def __del__(self):
        self.creature = None
        self.item = None
        self.container = None
        self.ai = None


class obj_Game:
    """The obj_Game is an object that stores all the information used by
    the game to 'keep track' of progress.  It will track maps, object lists,
    and game history or record of messages.

    # Properties
    obj_Game.current_map : whatever map is currently loaded.

    obj_Game.current_objects : list of objects for the current map.

    obj_Game.message_history : list of messages that have been pushed
    to the player over the course of a game."""

    def __init__(self):
        self.current_map = map_create()
        self.current_objects: List[obj_Actor] = []

        self.message_history: List[T_MESSAGE] = []


class obj_Spritesheet:
    """Class used to grab images out of a sprite sheet.  As a class,
    it allows you to access and subdivide portions of the
    sprite_sheet.

    # Arguments
    file_name : String which contains the directory/filename of the
    image for use as a spritesheet.

    width : Integer that specifies how wide each sprite in the
    spritesheet is in pixels.

    height : Integer that specifies how high each sprite in the
    spritesheet is in pixels.

    # Properties
    obj_Spritesheet.sprite_sheet : The loaded spritesheet accessed
    through the file_name argument.

    # Methods
    obj_Spritesheet.get_image : returns a list containing a single
    image from a spritesheet given a grid location.

    obj_Spritesheet.get_animation : returns a list containing a
    sequence of images starting from a grid location."""

    def __init__(self, file_name: str, width: int, height: int):
        # Load the spritesheet
        self.sprite_sheet = pygame.image.load(file_name).convert()

        self.width = width
        self.height = height

    def get_sprite(self, column: int, row: int, scale: Tuple[int, int] = None, width: int = None,
                   height: int = None) -> T_SURFACE:
        """This method returns a single image obtained from the spritesheet.

        # Arguments
        column : Column of the image.

        row : Row of the image.

        scale = None : Tuple (width, height).  If included, scales the
        images to a new size in pixels

        width : Integer that specifies how wide each sprite in the
        spritesheet is in pixels. Defaults to the width given in the constructor.

        height : Integer that specifies how high each sprite in the
        spritesheet is in pixels. Defaults to the height given in the constructor."""
        if width is None:
            width = self.width

        if height is None:
            height = self.height

        # Create a blank image
        image: T_SURFACE = pygame.Surface((width, height)).convert(PYGAME_DISPLAY)

        # Copy from spritesheet onto the spritesheet
        image_area = (column * width, row * height, width, height)
        draw_surface(self.sprite_sheet, image, (0, 0), area=image_area)

        # Set transparency to black
        image.set_colorkey(COLOR_BLACK)

        # Scale the image to the desired size
        if scale:
            new_w, new_h = scale
            image = pygame.transform.scale(image, (new_w, new_h)).convert()

        return image

    def get_image(self, column: int, row: int, scale: Tuple[int, int] = None, width: int = None,
                  height: int = None) -> List[T_SURFACE]:
        """This method returns a single image within a list
        created from the spritesheet.

        # Arguments
        column : Column of the image.

        row : Row of the image.

        scale = None : Tuple (width, height).  If included, scales the
        images to a new size in pixels

        width : Integer that specifies how wide each sprite in the
        spritesheet is in pixels. Defaults to the width given in the constructor.

        height : Integer that specifies how high each sprite in the
        spritesheet is in pixels. Defaults to the height given in the constructor."""
        return [self.get_sprite(column, row, scale, width, height)]

    def get_animation(self, coords: List[T_COORDINATE], scale: Tuple[int, int] = None,
                      width: int = None, height: int = None) -> List[T_SURFACE]:
        """This method returns a sequence of images within a list
        created from the spritesheet.

        # Arguments
        coords : List [Tuple (column, row)]. A list of tuples that specify the coordinates
        of the images to be taken

        scale = None : Tuple (width, height).  If included, scales the
        images to a new size in pixels

        width : Integer that specifies how wide each sprite in the
        spritesheet is in pixels. Defaults to the width given in the constructor.

        height : Integer that specifies how high each sprite in the
        spritesheet is in pixels. Defaults to the height given in the constructor."""
        image_list = []

        if width is None:
            width = self.width

        if height is None:
            height = self.height

        for column, row in coords:
            # Create a blank image
            image: T_SURFACE = pygame.Surface((width, height)).convert(PYGAME_DISPLAY)

            # Copy from the spritesheet onto the image
            image_area = (column * width, row * height, width, height)
            draw_surface(self.sprite_sheet, image, (0, 0), area=image_area)

            # Set transparency to blank
            image.set_colorkey(COLOR_BLACK)

            # Scale the image to the desired size
            if scale:
                new_w, new_h = scale
                image = pygame.transform.scale(image, (new_w, new_h)).convert()

            image_list.append(image)

        return image_list


class obj_Spritesheet_Set:
    """Class used to grab images out of multiple spritesheets.  As a class,
    it allows you to access and subdivide portions of the
    sprite_sheet.

    # Arguments
    file_names : List of strings which contains the directory/filename of the
    images for use as the spritesheets.

    width : Integer that specifies how wide each sprite in the
    spritesheets are in pixels.

    height : Integer that specifies how high each sprite in the
    spritesheets are in pixels.

    # Properties
    obj_Spritesheet.sprite_sheets : The list of loaded spritesheet accessed
    through the file_names argument.

    # Methods
    obj_Spritesheet.get_image : returns a list containing a single
    image from a spritesheet given a grid location.

    obj_Spritesheet.get_animation : returns a list containing a
    sequence of images starting from a grid location."""

    def __init__(self, file_names: List[str], width: int, height: int):
        self.sprite_sheets: List[obj_Spritesheet] = [obj_Spritesheet(file_name, width, height) for file_name in
                                                     file_names]

        self.width = width
        self.height = height

    def get_sprite(self, sprite_sheet: int, column: int, row: int, scale: Tuple[int, int] = None,
                   width: int = None, height: int = None) -> T_SURFACE:
        """This method returns a single image obtained from the spritesheet.

        # Arguments
        column : Column of the image.

        row : Row of the image.

        scale = None : Tuple (width, height).  If included, scales the
        images to a new size in pixels

        width : Integer that specifies how wide each sprite in the
        spritesheet is in pixels. Defaults to the width given in the constructor.

        height : Integer that specifies how high each sprite in the
        spritesheet is in pixels. Defaults to the height given in the constructor."""
        return self.sprite_sheets[sprite_sheet].get_sprite(column, row, scale, width, height)

    def get_image(self, sprite_sheet: int, column: int, row: int, scale: Tuple[int, int] = None,
                  width: int = None, height: int = None) -> List[T_SURFACE]:
        """This method returns a single image within a list
        created from the spritesheet.

        # Arguments
        sprite_sheet : Which spritesheet to use.

        column : Column of the image.

        row : Row of the image.

        scale = None : Tuple (width, height).  If included, scales the
        images to a new size in pixels

        width : Integer that specifies how wide each sprite in the
        spritesheet is in pixels. Defaults to the width given in the constructor.

        height : Integer that specifies how high each sprite in the
        spritesheet is in pixels. Defaults to the height given in the constructor."""
        return self.sprite_sheets[sprite_sheet].get_image(column, row, scale, width, height)

    def get_animation(self, coords: List[Tuple[int, int, int]], scale: Tuple[int, int] = None,
                      width: int = None, height: int = None) -> List[T_SURFACE]:
        """This method returns a sequence of images within a list
        created from the spritesheet.

        # Arguments
        coords : List [Tuple (spritesheet, column, row)]. A list of tuples that specify the coordinates
        of the images to be taken.

        scale = None : Tuple (width, height).  If included, scales the
        images to a new size in pixels

        width : Integer that specifies how wide each sprite in the
        spritesheet is in pixels. Defaults to the width given in the constructor.

        height : Integer that specifies how high each sprite in the
        spritesheet is in pixels. Defaults to the height given in the constructor."""
        image_list = []

        for sprite_sheet, column, row in coords:
            image_list.append(self.sprite_sheets[sprite_sheet].get_sprite(column, row, scale, width, height))

        return image_list


#   ____                                             _
#  / ___|___  _ __ ___  _ __   ___  _ __   ___ _ __ | |_ ___
# | |   / _ \| '_ ` _ \| '_ \ / _ \| '_ \ / _ \ '_ \| __/ __|
# | |__| (_) | | | | | | |_) | (_) | | | |  __/ | | | |_\__ \
#  \____\___/|_| |_| |_| .__/ \___/|_| |_|\___|_| |_|\__|___/
#                      |_|

class com_Creature:
    """Creatures have health, and can damage other objects by attacking
    them.  Can also die.

    # Arguments
    name_instance : String, name of specific object. "Bob" for
    example.

    hp : Integer, health of the creature.  Is converted into both the
    maximum health and the current health of the creature.

    death_function : function, this function is executed whenever the
    creature's health dips below 0.  Normally just converts the
    creature into a dead object.

    # Properties
    com_Creature.MAX_HP : The maximum hp of the creature.

    com_Creature.owner : The actor that has this creature component attached to it

    # Methods
    com_Creature.move : function takes in two arguments, the
    difference of x and the difference of y, attempts to move the
    object in that direction.

    com_Creature.attack : allows the creature to attack a target.

    com_Creature.take_damage : Creature takes damage, and if the
    creature's health falls below 0, executes the death function."""

    def __init__(self, name_instance: str, hp: int = 10, death_function: Callable = None):
        self.name_instance = name_instance
        self.MAX_HP = hp
        self.hp = hp

        self.owner: obj_Actor = None
        self.death_function = death_function

    def move(self, dx: int, dy: int):
        """Moves the creature with relative coordinates. If the creature stumbles upon an enemy it will attack it.

        # Arguments
        dx : The relative x value to move the creature

        dy : The relative y value to move the creature"""
        did_something = False

        tile_is_blocked = GAME.current_map[self.owner.x + dx][self.owner.y + dy].block_path

        target = map_get_creature(self.owner.x + dx, self.owner.y + dy, excluded_objects=[self.owner])

        if target:
            self.attack(target, 3)
            did_something = True

        if not tile_is_blocked and target is None:
            self.owner.x += dx
            self.owner.y += dy
            did_something = True

        return did_something

    def move_towards(self, target: T_ACTOR):
        line = map_find_line(self.owner.pos, target.pos)
        target_point = line[1]
        change_position = (target_point[0] - self.owner.x, target_point[1] - self.owner.y)
        self.move(*change_position)

    def attack(self, target: T_ACTOR, damage: int):
        """Attacks the target creature. Automatically called if the creature moves on the target

        # Arguments
        target : The actor to attack

        damage : How much damage to be dealt to the creature"""
        target_name = target.creature.name_instance
        game_message(f"{self.name_instance} attacks {target_name} for {damage} damage!",
                     COLOR_D_GREEN)
        target.creature.take_damage(damage)

    def take_damage(self, damage: int):
        """ Makes the creature take damage.

        # Arguments
        damage : How much damage the creature takes"""
        self.hp -= damage
        # game_message(f"{self.name_instance}'s health is {self.hp}/{self.MAX_HP}", COLOR_RED)

        if self.hp <= 0:
            if self.death_function is not None:
                self.death_function(self.owner)

    def heal(self, value: int):
        self.hp += value
        if self.hp > self.MAX_HP:
            self.hp = self.MAX_HP

    @property
    def full_name(self):
        return f"{self.name_instance} the {self.owner.name_object}"


class com_Item:
    """Items can be picked up, dropped and used

    # Arguments
    weight : How heavy this item is. TODO: Will slow down how the holder will move.

    volume : How large this item is. TODO: Will limit how much the holder can carry

    # Properties
    com_Item.owner : The actor that has this item component attached to it

    com_Item.current_container : The current_container component that has this item in its inventory"""

    def __init__(self, weight: float = 0.0, volume: float = 0.0, use_function: Callable = None, value=None):
        self.weight = weight
        self.volume = volume

        self.value = value

        self.owner: obj_Actor = None
        self.current_container: T_CONTAINER = None

        self.use_function = use_function

    # Pick up the item
    def pick_up(self, actor: obj_Actor):
        """Picks up the item and adds it to the actors conatiner

        # Arguments
        actor : The actor that will pick up the item"""
        if actor.container:
            if actor.container.current_volume + self.volume > actor.container.max_volume:
                game_message("Not enough room to pick up", COLOR_L_RED)
            else:
                actor.container.add(self.owner)
                GAME.current_objects.remove(self.owner)
                game_message("You pick it up", COLOR_L_GREEN)

    # Drop the item
    def drop(self, new_coords: T_COORDINATE = None):
        """Drops the item.

        # Arguments
        new_coords : A tuple of the coordinates of where the item will be dropped.
        Defaults to where the current_container is."""
        if new_coords is None:
            new_x = self.current_container.owner.x
            new_y = self.current_container.owner.y
        else:
            new_x, new_y = new_coords

        GAME.current_objects.append(self.owner)
        self.current_container.remove(self.owner)
        self.owner.x = new_x
        self.owner.y = new_y
        game_message("You drop the item", COLOR_L_GREEN)

    # TODO: Use the item
    def use(self):
        """Uses the item.

        This function calls com_Item.use_function and passes any arguments
        taken from use and inserts it into use_function

        # Arguments
        TODO: All Arguments are passed onto use_function"""
        if self.use_function is not None:
            result = self.use_function(self.current_container.owner, self.value)
            if result == 'destroy':
                self.current_container.remove(self.owner)
            elif result == 'cancelled':
                pass
        else:
            game_message("You can't use that", COLOR_L_RED)


class com_Container:
    """Containers can hold items, TODO: and have a maximum volume they can hold

    # Arguments
    max_volume : The maximum volume this current_container can hold. Defaults to 10.0

    inventory : A list containing all the items it is carrying. Defaults to an empty list

    # Properties
    com_Container.owner : The actor that has this current_container component attached to it

    com_Container.current_volume : The total volume occupied by all the items in its inventory"""

    def __init__(self, max_volume: float = 10.0, inventory: List[obj_Actor] = None):
        if inventory is None:
            self.inventory: List[obj_Actor] = []
        else:
            self.inventory: List[obj_Actor] = inventory

        self.max_volume = max_volume
        self.owner: obj_Actor = None

    def add(self, item_actor: T_ACTOR):
        self.inventory.append(item_actor)
        item_actor.item.current_container = self

    def remove(self, item_actor: T_ACTOR):
        self.inventory.remove(item_actor)
        item_actor.item.current_container = None

    # TODO: Get Names of everything in inventory

    # Get volume within current_container
    @property
    def current_volume(self):
        total_volume = 0.0
        for obj in self.inventory:
            total_volume += obj.item.volume

        return total_volume

    # TODO: Get Weight

    def __del__(self):
        for item_actor in self.inventory:
            item_actor.item.current_container = None

        self.inventory = []


#      ___       __
#     /   \     |  |
#    /  ^  \    |  |
#   /  /_\  \   |  |
#  /  _____  \  |  |
# /__/     \__\ |__|


class ai_Confuse:
    """Once per turn, execute"""

    def __init__(self):
        self.owner: obj_Actor = None

    def take_turn(self):
        self.owner.creature.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))


class ai_Chase:
    """A basic monster the ai that chases and tries to harm the player."""
    def __init__(self):
        self.owner: T_ACTOR = None

    def take_turn(self):
        if libtcod.map_is_in_fov(FOV_MAP, self.owner.x, self.owner.y):
            # Move towards the player if you can see him
            self.owner.creature.move_towards(PLAYER)
        else:
            # Move randomly
            self.owner.creature.move(libtcod.random_get_int(0, -1, 1), libtcod.random_get_int(0, -1, 1))


#  ____             _   _
# |  _ \  ___  __ _| |_| |__
# | | | |/ _ \/ _` | __| '_ \
# | |_| |  __/ (_| | |_| | | |
# |____/ \___|\__,_|\__|_| |_|


def death_monster(monster: T_ACTOR):
    """On death, most monsters stop moving."""
    game_message(monster.creature.name_instance + " is dead!", COLOR_GREEN)

    monster.name_object = f"Corpse of {monster.creature.name_instance}"

    monster.creature = None
    monster.ai = None
    monster.item = com_Item(use_function=cast_heal, value=4)
    monster.item.owner = monster

    monster.animation = [monster.animation[0]]


#  __  __             _
# |  \/  | __ _  __ _(_) ___
# | |\/| |/ _` |/ _` | |/ __|
# | |  | | (_| | (_| | | (__
# |_|  |_|\__,_|\__, |_|\___|
#               |___/


def cast_heal(target: T_ACTOR, value: int = 1):
    if target.creature.hp < target.creature.MAX_HP:
        game_message(f"{target.creature.full_name} healed for {value}")
        target.creature.heal(value)
        return 'destroy'
    else:
        game_message(f"{target.creature.full_name} is already at full health")
        return 'cancelled'


def cast_lightning():
    damage = 5

    # Prompt the player for a tile
    target_point = menu_tile_select({"coords_origin": PLAYER.pos,
                                     "max_range": 5,
                                     "penetrate_walls": False})

    if target_point is None:
        return "Cancelled"

    # Convert that tile into a list of tiles from A to B
    # Ignore starting tile to avoid damaging the caster
    list_of_tiles = map_find_line((PLAYER.x, PLAYER.y), target_point, include_start_point=False)
    if len(list_of_tiles) == 0:
        return "Cancelled"

    # Cycle through the list, damaging everything in it
    for x, y in list_of_tiles:
        target = map_get_creature(x, y)
        if target is not None:
            target.creature.take_damage(damage)

    return "Success"


def cast_fireball():
    damage = 5
    radius = 1
    max_range = 4

    # Get target tile
    target_point = menu_tile_select(
        line_config={"coords_origin": PLAYER.pos,
                     "max_range": max_range,
                     "penetrate_walls": False,
                     "penetrate_creatures": False},
        circle_config={"radius": radius})

    if target_point is None:
        return "Cancelled"

    # Get sequence of tiles
    tiles_to_damage = map_find_radius(target_point, radius)

    # Damage all creatures
    for tile_x, tile_y in tiles_to_damage:
        target_to_damage = map_get_creature(tile_x, tile_y)
        if target_to_damage is not None:
            target_to_damage.creature.take_damage(damage)
            if target_to_damage is not PLAYER and target_to_damage.creature is not None:
                game_message(f"{target_to_damage.creature.full_name} howls in pain.", COLOR_RED)

    return "Success"


# .___  ___.      ___      .______
# |   \/   |     /   \     |   _  \
# |  \  /  |    /  ^  \    |  |_)  |
# |  |\/|  |   /  /_\  \   |   ___/
# |  |  |  |  /  _____  \  |  |
# |__|  |__| /__/     \__\ | _|


def map_create() -> T_MAP:
    """Creates a map which is a 2D array containing 'struc_Tile's"""
    new_map = [[struc_Tile(False) for y in range(MAP_HEIGHT)] for x in range(MAP_WIDTH)]

    new_map[10][10].block_path = True
    new_map[10][15].block_path = True

    for x in range(MAP_WIDTH):
        new_map[x][0].block_path = True
        new_map[x][MAP_HEIGHT - 1].block_path = True

    for y in range(MAP_HEIGHT):
        new_map[0][y].block_path = True
        new_map[MAP_WIDTH - 1][y].block_path = True

    map_make_fov(new_map)

    return new_map


def map_objects_at_coords(coords_x: int, coords_y: int):
    """Returns a list of all the actors that are at the specified coordinates

    # Arguments
    coords_x = The x coordinate to check.

    coords_y : The y coordinate to check."""
    objects = [obj for obj in GAME.current_objects if obj.x == coords_x and obj.y == coords_y]

    return objects


def map_get_objects(x: int = None, y: int = None,
                    creature: bool = False, item: bool = False, container: bool = False,
                    excluded_objects: List[obj_Actor] = None,
                    search_objects: List[obj_Actor] = None) -> List[obj_Actor]:
    """Returns all of the current actors. If any parameter is given, the objects are filtered accordingly.

    # Arguments
    x : If given, only returns actors at the specified x coordinates.

    y : If given, only returns actors at the specified x coordinates.

    creature : If True, only returns actors that have the creature component.

    item : If True, only returns actors that have the item component.

    current_container : If True, only returns actors that have the current_container component.

    excluded_objects : If given a list of actors, these actors are filtered from the search.

    search_objects : If given a list of actors, Only these actors will be filtered instead of all actors."""
    valid_objects = []
    if excluded_objects is None:
        excluded_objects = []

    if search_objects is None:
        objs_to_search = GAME.current_objects
    else:
        objs_to_search = search_objects

    for obj in objs_to_search:
        if obj in excluded_objects:
            continue
        if x is not None:
            if obj.x != x:
                continue
        if y is not None:
            if obj.y != y:
                continue
        if creature:
            if obj.creature is None:
                continue
        if item:
            if obj.item is None:
                continue
        if container:
            if obj.container is None:
                continue
        valid_objects.append(obj)

    return valid_objects


def map_get_creature(x: int = None, y: int = None,
                     item: bool = False, container: bool = False,
                     excluded_objects: List[obj_Actor] = None,
                     search_objects: List[obj_Actor] = None) -> obj_Actor:
    """Returns the first creature in the list that matches any parameters given.

    # Arguments
    x : If given, only returns the creature at the specified x coordinates. (Should be given)

    y : If given, only returns the creature at the specified x coordinates. (Should be given)

    item : If True, only return the creature that have the item component.

    container : If True, only returns the creature that have the container component

    excluded_objects : If given a list of actors, these actors are filtered from the search.

    search_objects : If given a list of actors, Only these actors will be filtered instead of all actors."""

    if excluded_objects is None:
        excluded_objects = []

    if search_objects is None:
        objs_to_search = [obj for obj in GAME.current_objects if obj.creature is not None]
    else:
        objs_to_search = [obj for obj in search_objects if obj.creature is not None]

    for obj in objs_to_search:
        if obj in excluded_objects:
            continue
        if x is not None:
            if obj.x != x:
                continue
        if y is not None:
            if obj.y != y:
                continue
        if item:
            if obj.item is None:
                continue
        if container:
            if obj.container is None:
                continue

        return obj


def map_make_fov(incoming_map: T_MAP):
    """Creates an FOV map using libtcod in order to calculate the field of vision"""
    global FOV_MAP
    FOV_MAP = libtcod.map_new(MAP_WIDTH, MAP_HEIGHT)

    for y in range(MAP_HEIGHT):
        for x in range(MAP_WIDTH):
            libtcod.map_set_properties(FOV_MAP, x, y,
                                       not incoming_map[x][y].block_path,
                                       not incoming_map[x][y].block_path)


def map_calculate_fov():
    """Calculates the FOV. Should be called every time the player moves
    (or any change that should result in an FOV change)."""
    global FOV_CALCULATE

    if FOV_CALCULATE:
        FOV_CALCULATE = False
        libtcod.map_compute_fov(FOV_MAP, PLAYER.x, PLAYER.y, TORCH_RADIUS,
                                FOV_LIGHT_WALLS, FOV_ALGO)


def map_check_wall(x, y):
    return GAME.current_map[x][y].block_path


def map_find_line(coords1: T_COORDINATE, coords2: T_COORDINATE,
                  include_start_point: bool = True) -> List[T_COORDINATE]:
    """Converts to x, y coordinates into a list of tiles.

    # Arguments
    coords1 : (x1, y1) The starting point of the line

    coords2 : (x2, y2) The ending point of the line"""
    x1, y1 = coords1
    x2, y2 = coords2

    if x1 == x2 and y1 == y2:
        if include_start_point:
            return [(x1, x2)]
        else:
            return []

    libtcod.line_init(x1, y1, x2, y2)
    calc_x, calc_y = libtcod.line_step()
    if include_start_point:
        coord_list: List[T_COORDINATE] = [coords1]
    else:
        coord_list: List[T_COORDINATE] = []

    while calc_x is not None:
        coord_list.append((calc_x, calc_y))
        if calc_x == x2 and calc_y == y2:
            return coord_list

        calc_x, calc_y = libtcod.line_step()


def map_find_radius(coords: T_COORDINATE, radius: int, include_center: bool = True) -> List[T_COORDINATE]:
    center_x, center_y = coords
    tile_list: List[T_COORDINATE] = []

    start_x = center_x - radius
    end_x = center_x + radius + 1

    start_y = center_y - radius
    end_y = center_y + radius + 1

    # +1 because range(start, stop) does not include the stop value
    for tile_x in range(start_x, end_x):
        for tile_y in range(start_y, end_y):
            tile_list.append((tile_x, tile_y))

    if not include_center:
        tile_list.remove(coords)

    return tile_list


#  ____                     _
# |  _ \ _ __ __ ___      _(_)_ __   __ _
# | | | | '__/ _` \ \ /\ / / | '_ \ / _` |
# | |_| | | | (_| |\ V  V /| | | | | (_| |
# |____/|_|  \__,_| \_/\_/ |_|_| |_|\__, |
#                                   |___/


def draw_game(cursor: T_SURFACE = None, update_display: bool = True):
    """Draws the map, objects, console messages, and debug information and updates the screen"""
    global SURFACE_MAIN

    # Clear the Surface
    SURFACE_MAIN.fill(COLOR_DEFAULT_BG)

    # Draw the Map
    draw_map(GAME.current_map)

    # Draw the Objects
    draw_objects()

    draw_debug()
    draw_messages()

    # Update the Display
    if update_display:
        draw_update_display(cursor)


def draw_debug():
    """Draws debug information (currently on FPS) on the top left of the screen."""
    global SURFACE_MAIN

    draw_text(SURFACE_MAIN, f"FPS: {int(CLOCK.get_fps())}", (0, 0), COLOR_WHITE, COLOR_BLACK)


def draw_objects():
    """Draws all the actors (by calling obj_Actor.draw())."""
    for obj in GAME.current_objects:
        obj.draw()


def draw_messages():
    """Draws the last [NUM_MESSAGES] messages on the bottom left of the screen."""
    global SURFACE_MAIN

    if len(GAME.message_history) <= NUM_MESSAGES:
        to_draw = GAME.message_history
    else:
        to_draw = GAME.message_history[-NUM_MESSAGES:]

    text_height = helper_text_height(ASSETS.F_MESSAGE)
    start_y = ((MAP_HEIGHT * CELL_HEIGHT)
               - (len(to_draw) * text_height)) - PIXELS_UNDER_MESSAGES

    i = 0
    for msg, msg_color, bg_color in to_draw:
        draw_text(SURFACE_MAIN, msg, (0, start_y + (i * text_height)),
                  msg_color, bg_color, ASSETS.F_MESSAGE)

        i += 1


def draw_map(map_to_draw: T_MAP):
    """Draws the specified map on the screen.

    # Arguments
    map_to_draw : The map to draw"""
    global SURFACE_MAIN

    for x in range(MAP_WIDTH):
        for y in range(MAP_HEIGHT):
            is_visible = libtcod.map_is_in_fov(FOV_MAP, x, y)

            if is_visible:
                map_to_draw[x][y].explored = True

                if map_to_draw[x][y].block_path:
                    # Draw Wall
                    SURFACE_MAIN.blit(ASSETS.S_WALL, (x * CELL_WIDTH, y * CELL_WIDTH))
                else:
                    # Draw Floor
                    SURFACE_MAIN.blit(ASSETS.S_FLOOR, (x * CELL_WIDTH, y * CELL_WIDTH))
            elif map_to_draw[x][y].explored:
                if map_to_draw[x][y].block_path:
                    # Draw Wall
                    SURFACE_MAIN.blit(ASSETS.S_WALL_EXPLORED, (x * CELL_WIDTH, y * CELL_WIDTH))
                else:
                    # Draw Floor
                    SURFACE_MAIN.blit(ASSETS.S_FLOOR_EXPLORED, (x * CELL_WIDTH, y * CELL_WIDTH))


def draw_text(display_surface: T_SURFACE, text: str, coords: T_COORDINATE,
              text_color: T_COLOR, back_color: T_COLOR = None, font: T_FONT = None, mode: str = "corner"):
    """This function takes in text, and displays it on the referenced surface

    # Arguments
    display_surface : The surface to draw the text on.

    text : The text to display.

    coords : A tuple containing the coordinates of where to draw the text.

    text_color : The color of the text.

    back_color : The color of the background. If None, leaves it transparent.

    font : The font of the text

    mode : How to position the given coordinates.
    Available modes [corner (Default), center]
    """
    if font is None:
        font = ASSETS.F_STANDARD

    text_surf, text_rect = helper_text_objects(text, text_color, back_color, font)

    if mode == "center":
        text_rect.center = coords
    else:
        text_rect.topleft = coords

    display_surface.blit(text_surf, text_rect)


def draw_surface(src: T_SURFACE, dest: T_SURFACE, coords: T_COORDINATE = (0, 0),
                 rect: T_RECT = None, area: T_RECT = None, mode: str = "corner"):
    """Draws a surface onto another surface.

    src : The surface to draw.

    dest : The surface to draw on.

    coords : A tuple containing the coordinates of where to draw the surface.

    rect : Can be given instead of coords. Is a rectangle of where the surface will be drawn.

    area : If given, Is a rectangle of where of the source surface will be drawn onto the destination

    mode : How to position the given coordinates. It is not used if the 'rect' parameter is given.
    Available modes [corner (Default), center]
    """
    if rect is None:
        src_rect: T_RECT = src.get_rect()
        if mode == "center":
            src_rect.center = coords
        else:
            src_rect.topleft = coords

        dest.blit(src, src_rect, area=area)
    else:
        dest.blit(src, rect, area=area)


def draw_cursor(cursor: T_SURFACE):
    if USE_CURSOR:
        mpos = pygame.mouse.get_pos()
        c_rect: T_RECT = cursor.get_rect()
        c_rect.topleft = mpos
        draw_surface(cursor, PYGAME_DISPLAY, rect=c_rect)


def draw_crosshair(coords: T_COORDINATE):
    coords = coords[0] * CELL_WIDTH, coords[1] * CELL_HEIGHT
    draw_surface(ASSETS.S_CROSSHAIR, SURFACE_MAIN, coords)


def draw_tile_rect(coords: T_COORDINATE, color: T_COLOR = None, alpha: int = 150):
    coords = coords[0] * CELL_WIDTH, coords[1] * CELL_HEIGHT
    new_surface = pygame.Surface([CELL_WIDTH, CELL_HEIGHT])

    if color is None:
        new_surface.fill(COLOR_WHITE)
    else:
        new_surface.fill(color)

    new_surface.set_alpha(alpha)
    draw_surface(new_surface, SURFACE_MAIN, coords)


def draw_update_display(cursor: T_SURFACE = None):
    PYGAME_DISPLAY.blit(SURFACE_MAIN, (0, 0))
    if USE_CURSOR and cursor is not None:
        pygame.mouse.set_visible(False)
        draw_cursor(cursor)
    elif USE_CURSOR:
        pygame.mouse.set_visible(True)
    pygame.display.flip()


#  _   _      _
# | | | | ___| |_ __   ___ _ __ ___
# | |_| |/ _ \ | '_ \ / _ \ '__/ __|
# |  _  |  __/ | |_) |  __/ |  \__ \
# |_| |_|\___|_| .__/ \___|_|  |___/
#              |_|


def helper_text_objects(text: str, text_color: T_COLOR, back_color: T_COLOR = None,
                        font: T_FONT = None) -> Tuple[T_SURFACE, T_RECT]:
    """Returns the surface and rectangle of the text rendered by the font

    # Arguments
    text : The text to render

    text_color : The color to draw the text

    back_color : The color of the background behind the text. Defaults to colorless.

    font : The font to use to render the text."""
    text_surface: T_SURFACE = font.render(text, False, text_color, back_color)

    return text_surface, text_surface.get_rect()


def helper_text_height(font: T_FONT, text: str = 'a') -> int:
    """Returns the height in pixels of the font given.

    # Arguments
    font : The font to measure its height.

    text : If given, the sample text to measure the height. Defaults to 'a'."""
    font_object = font.render(text, False, (0, 0, 0))
    font_rect = font_object.get_rect()

    return font_rect.height


def helper_text_width(font: T_FONT, text: str) -> int:
    """Returns the width in pixels of the text render in the given font.

    # Arguments
    font : The font to render the text.

    text : The text to render and then measure its width."""
    font_object: T_SURFACE = font.render(text, False, (0, 0, 0))
    font_rect: T_RECT = font_object.get_rect()
    return font_rect.width


def access_dawnlike(further_path: str, prefix: str = '') -> str:
    path = "data/DawnLike/" + prefix + further_path
    if '.' not in path:
        path += '.png'
    return path


def access_dawnlike_list(further_paths: List[str], prefix: str = '') -> List[str]:
    return [access_dawnlike(further_path, prefix) for further_path in further_paths]


#  __  __
# |  \/  | ___ _ __  _   _ ___
# | |\/| |/ _ \ '_ \| | | / __|
# | |  | |  __/ | | | |_| \__ \
# |_|  |_|\___|_| |_|\__,_|___/


def menu_pause():
    """This menu pauses the game and displays a simple message"""
    global SURFACE_MAIN

    menu_text = "PAUSED"
    menu_font = ASSETS.F_STANDARD

    menu_close = False
    while not menu_close:
        events_list = pygame.event.get()
        for event in events_list:
            if event.type == pygame.QUIT:
                game_exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_p, pygame.K_ESCAPE]:
                    menu_close = True

        # Draw the text at the center of the game window
        draw_text(SURFACE_MAIN, menu_text, (GAME_WIDTH / 2, GAME_HEIGHT / 2),
                  COLOR_WHITE, COLOR_BLACK, menu_font, "center")
        draw_debug()
        CLOCK.tick(GAME_FPS)
        draw_update_display()


def menu_inventory():
    """Opens up the inventory menu.

    The inventory menu allows the player to examine whatever items they are currently holding.
    Right clicking an item will drop it."""

    # Menu Characteristics
    menu_width = 300
    menu_height = 200

    menu_text_font = ASSETS.F_MESSAGE
    menu_text_height = helper_text_height(menu_text_font)
    menu_text_color = COLOR_WHITE
    menu_text_bg = COLOR_BLACK

    local_inventory_surface = pygame.Surface((menu_width, menu_height))
    local_inventory_rect: T_RECT = local_inventory_surface.get_rect()
    local_inventory_rect.center = (GAME_WIDTH / 2, GAME_HEIGHT / 2)

    menu_close = False
    while not menu_close:
        # Clear the menu
        local_inventory_surface.fill(COLOR_BLACK)

        # TODO: Register Changes
        print_list = [obj.name_object for obj in PLAYER.container.inventory]

        events_list = pygame.event.get()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_rel_x = mouse_x - local_inventory_rect.topleft[0]
        mouse_rel_y = mouse_y - local_inventory_rect.topleft[1]

        mouse_in_window = bool(local_inventory_rect.collidepoint(mouse_x, mouse_y))
        mouse_line_selection = mouse_rel_y // menu_text_height

        for event in events_list:
            if event.type == pygame.QUIT:
                game_exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_i, pygame.K_ESCAPE]:
                    menu_close = True

            elif event.type == pygame.MOUSEBUTTONUP:
                if event.button == 1:
                    # Left Click TODO: Allow examining the items
                    if mouse_in_window and 0 < mouse_line_selection <= len(print_list):
                        PLAYER.container.inventory[mouse_line_selection - 1].item.use()
                        menu_close = True
                elif event.button == 3:
                    # Right Click: Drop the item
                    if mouse_in_window and 0 < mouse_line_selection <= len(print_list):
                        PLAYER.container.inventory[mouse_line_selection - 1].item.drop()

        # Draw Menu
        draw_text(local_inventory_surface, "Inventory:", (0, 0), COLOR_WHITE, font=menu_text_font)
        # line starts at 1 to account for the "Inventory:" text that appears at the top
        for line, name in enumerate(print_list, start=1):
            if mouse_in_window and line == mouse_line_selection:
                # Reverse text and background color to show that it is being selected
                draw_text(local_inventory_surface, name, (0, line * menu_text_height),
                          text_color=menu_text_bg, back_color=menu_text_color, font=menu_text_font)
            else:
                draw_text(local_inventory_surface, name, (0, line * menu_text_height),
                          text_color=menu_text_color, back_color=menu_text_bg, font=menu_text_font)
        # Display Menu

        draw_game(update_display=False)

        draw_surface(local_inventory_surface, SURFACE_MAIN, rect=local_inventory_rect)
        draw_debug()

        CLOCK.tick(GAME_FPS)
        draw_update_display(ASSETS.S_CURSOR_INVENTORY)


def menu_drop():
    """Opens up the drop menu. The player can click on an item to drop it."""

    # Menu Characteristics
    menu_width = 300
    menu_height = 200

    menu_text_font = ASSETS.F_MESSAGE
    menu_text_height = helper_text_height(menu_text_font)
    menu_text_color = COLOR_WHITE
    menu_text_bg = COLOR_BLACK

    local_inventory_surface = pygame.Surface((menu_width, menu_height))
    local_inventory_rect: T_RECT = local_inventory_surface.get_rect()
    local_inventory_rect.center = (GAME_WIDTH / 2, GAME_HEIGHT / 2)

    menu_close = False
    while not menu_close:
        # Clear the menu
        local_inventory_surface.fill(COLOR_BLACK)

        # TODO: Register Changes
        print_list = [obj.name_object for obj in PLAYER.container.inventory]

        events_list = pygame.event.get()
        mouse_x, mouse_y = pygame.mouse.get_pos()
        mouse_rel_x = mouse_x - local_inventory_rect.topleft[0]
        mouse_rel_y = mouse_y - local_inventory_rect.topleft[1]

        mouse_in_window = bool(local_inventory_rect.collidepoint(mouse_x, mouse_y))
        mouse_line_selection = mouse_rel_y // menu_text_height

        for event in events_list:
            if event.type == pygame.QUIT:
                game_exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_d, pygame.K_ESCAPE]:
                    menu_close = True

            elif event.type == pygame.MOUSEBUTTONUP:
                # Left Click
                if event.button == 1:
                    if mouse_in_window and 0 < mouse_line_selection <= len(print_list):
                        PLAYER.container.inventory[mouse_line_selection - 1].item.drop()

        # Draw Menu
        draw_text(local_inventory_surface, "Inventory:", (0, 0), COLOR_WHITE, font=menu_text_font)
        # line starts at 1 to account for the "Inventory:" text that appears at the top
        for line, name in enumerate(print_list, start=1):
            if mouse_in_window and line == mouse_line_selection:
                # Reverse text and background color to show that it is being selected
                draw_text(local_inventory_surface, name, (0, line * menu_text_height),
                          text_color=menu_text_bg, back_color=menu_text_color, font=menu_text_font)
            else:
                draw_text(local_inventory_surface, name, (0, line * menu_text_height),
                          text_color=menu_text_color, back_color=menu_text_bg, font=menu_text_font)
        # Display Menu
        draw_surface(local_inventory_surface, SURFACE_MAIN, rect=local_inventory_rect)
        draw_debug()
        CLOCK.tick(GAME_FPS)
        draw_update_display()


# Depreciated
def old_menu_tile_select(coords_origin: T_COORDINATE = None, display_start_coordinate: bool = False,
                         max_range: int = None, penetrate_walls: bool = True, penetrate_creatures: bool = True,
                         ignore_click: bool = False) -> T_COORDINATE:
    """This menu lets the player select a tile.

    This function pauses the game, produces a crosshair and when
    the player presses the mb, will return the coordinates clicked."""
    menu_close = False

    while not menu_close:
        # Get mouse position

        # Get button clicks
        events_list = pygame.event.get()
        mouse_x, mouse_y = pygame.mouse.get_pos()

        map_coord_x = mouse_x // CELL_WIDTH
        map_coord_y = mouse_y // CELL_HEIGHT

        valid_tiles = []

        if coords_origin is not None:
            full_list_tiles = map_find_line(coords_origin, (map_coord_x, map_coord_y))

            for i, (x, y) in enumerate(full_list_tiles):
                valid_tiles.append((x, y))

                if max_range is not None and i == max_range:
                    # Stop at max range
                    break
                elif not penetrate_walls and map_check_wall(x, y):
                    # Stop at wall
                    break
                elif not penetrate_creatures and map_get_creature(x, y) is not None and i != 0:
                    # Stop at creature
                    break
        else:
            valid_tiles = [(map_coord_x, map_coord_y)]

        for event in events_list:
            if event.type == pygame.QUIT:
                game_exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE]:
                    menu_close = True
                elif event.key in [pygame.K_l]:
                    if ignore_click:
                        menu_close = True

            elif event.type == pygame.MOUSEBUTTONUP:
                # Left Click
                if event.button == 1:
                    # Return selected coordinate
                    if not ignore_click:
                        return valid_tiles[-1]

        # Draw Game First
        draw_game(cursor=ASSETS.S_CURSOR_INSPECT, update_display=False)

        # Draw crosshair at mouse position on top of the game
        for tile_x, tile_y in valid_tiles:
            if not display_start_coordinate and (tile_x, tile_y) == coords_origin:
                continue
            draw_tile_rect((tile_x, tile_y))
        # draw_crosshair((mouse_x_rel, mouse_y_rel))

        # Draw debug information
        draw_debug()
        CLOCK.tick(GAME_FPS)

        # Update the display
        draw_update_display()


def menu_tile_select(line_config: Dict = None, circle_config: Dict = None, ignore_click: bool = False) -> T_COORDINATE:
    """This menu lets the player select a tile.

    This function pauses the game, produces a crosshair and when
    the player presses the mb, will return the coordinates clicked.

    # Arguments
    line_config: Dictionary containing all variables needed to define the drawing of the line.
        - "coords_origin": Tuple[int, int]. Coordinates to draw the line. If undefined no line will be drawn.
        - "max_range": The maximum range that can be reached. Defaults to infinity.
        - "penetrate_walls": Defines if the line can go through walls. Defaults to True.
        - "penetrate_creatures": Defines if the line can go through creatures. Defaults to True.
        - "line_color": The color of the line. Automatically becomes transparent. Defaults to White.
        - "display_start_coordinates": Defines if the line will draw over the start coordinates. Defaults to False.

    circle_config: Dictionary containing all variables needed to define the drawing of the circle around the line.
        - "radius": The radius of the circle. If undefined the circle will not be drawn.
        - "circle_color": The color of the circle. Automatically becomes transparent. Defaults to Red."""

    # Initialize variables
    coords_origin: T_COORDINATE = None
    max_range: int = None
    penetrate_walls: bool = True
    penetrate_creatures: bool = True
    line_color: T_COLOR = COLOR_WHITE
    display_start_coordinates: bool = False

    radius: int = None
    circle_color: T_COLOR = COLOR_RED

    if line_config is not None:
        coords_origin = coords_origin if "coords_origin" not in line_config else line_config["coords_origin"]
        max_range = max_range if "max_range" not in line_config else line_config["max_range"]
        penetrate_walls = penetrate_walls if "penetrate_walls" not in line_config else line_config["penetrate_walls"]
        penetrate_creatures = penetrate_creatures if "penetrate_creatures" not in line_config else line_config[
            "penetrate_creatures"]
        line_color = line_color if "line_color" not in line_config else line_config["line_color"]
        display_start_coordinates = display_start_coordinates if "display_start_coordinates" not in line_config else line_config["display_start_coordinates"]

    if circle_config is not None:
        radius = radius if "radius" not in circle_config else circle_config["radius"]
        circle_color = circle_color if "circle_color" not in circle_config else circle_config["circle_color"]

    menu_close = False

    while not menu_close:
        # Get button clicks
        events_list = pygame.event.get()
        mouse_x, mouse_y = pygame.mouse.get_pos()

        map_coord_x = mouse_x // CELL_WIDTH
        map_coord_y = mouse_y // CELL_HEIGHT

        valid_tiles = []

        if coords_origin is not None:
            full_list_tiles = map_find_line(coords_origin, (map_coord_x, map_coord_y))

            for i, (x, y) in enumerate(full_list_tiles):
                valid_tiles.append((x, y))

                if max_range is not None and i == max_range:
                    # Stop at max range
                    break
                elif not penetrate_walls and map_check_wall(x, y):
                    # Stop at wall
                    break
                elif not penetrate_creatures and map_get_creature(x, y) is not None and i != 0:
                    # Stop at creature
                    break
        else:
            valid_tiles = [(map_coord_x, map_coord_y)]

        for event in events_list:
            if event.type == pygame.QUIT:
                game_exit()

            elif event.type == pygame.KEYDOWN:
                if event.key in [pygame.K_ESCAPE]:
                    menu_close = True
                elif event.key in [pygame.K_l]:
                    if ignore_click:
                        menu_close = True

            elif event.type == pygame.MOUSEBUTTONUP:
                # Left Click
                if event.button == 1:
                    # Return selected coordinate
                    if not ignore_click:
                        return valid_tiles[-1]

        # Draw Game First
        draw_game(cursor=ASSETS.S_CURSOR_INSPECT, update_display=False)

        # Draw crosshair at mouse position on top of the game
        for tile_x, tile_y in valid_tiles:
            if not display_start_coordinates and (tile_x, tile_y) == coords_origin:
                continue
            draw_tile_rect((tile_x, tile_y), line_color)

        if radius is not None:
            circle_tiles = map_find_radius(valid_tiles[-1], radius)
            for tile_x, tile_y in circle_tiles:
                draw_tile_rect((tile_x, tile_y), circle_color)

        # draw_crosshair((mouse_x_rel, mouse_y_rel))

        # Draw debug information
        draw_debug()
        CLOCK.tick(GAME_FPS)

        # Update the display
        draw_update_display()


#   _______      ___      .___  ___.  _______
#  /  _____|    /   \     |   \/   | |   ____|
# |  |  __     /  ^  \    |  \  /  | |  |__
# |  | |_ |   /  /_\  \   |  |\/|  | |   __|
# |  |__| |  /  _____  \  |  |  |  | |  |____
#  \______| /__/     \__\ |__|  |__| |_______|


def game_main_loop():
    """In this function, we loop the main game"""
    game_quit = False

    while not game_quit:

        # Handle player input
        player_action = game_handle_keys()

        map_calculate_fov()

        if player_action == "QUIT":
            game_quit = True

        if player_action != "no-action" and player_action != "QUIT":
            for obj in GAME.current_objects:
                if obj.ai:
                    obj.ai.take_turn()

        # Draw the Game
        draw_game(cursor=ASSETS.S_CURSOR_STANDARD)

        CLOCK.tick(GAME_FPS)

    # Quit the Game
    game_exit()


def game_initialize():
    """This function initializes the main window and pygame and other global variables"""

    global PYGAME_DISPLAY, SURFACE_MAIN, GAME, CLOCK, FOV_CALCULATE, PLAYER, ASSETS

    # initialize pygame
    pygame.init()

    pygame.key.set_repeat(200, 70)

    PYGAME_DISPLAY = pygame.display.set_mode(WINDOW_SIZE)

    SURFACE_MAIN = pygame.Surface(WINDOW_SIZE)

    GAME = obj_Game()

    CLOCK = pygame.time.Clock()

    FOV_CALCULATE = True

    if USE_CURSOR:
        pygame.mouse.set_visible(False)

    ASSETS = struc_Assets()
    PLAYER = obj_Actor(13, 13, "human", ASSETS.A_PLAYER, creature=com_Creature("Greg"), container=com_Container())
    ENEMY = obj_Actor(15, 15, "Smart Crab", ASSETS.A_ENEMY,
                      creature=com_Creature("Jackie", death_function=death_monster), ai=ai_Chase())
    ENEMY2 = obj_Actor(14, 15, "Dumb Crab", ASSETS.A_ENEMY,
                       creature=com_Creature("Bob", death_function=death_monster), ai=ai_Confuse())

    GAME.current_objects.extend([PLAYER, ENEMY, ENEMY2])


def game_handle_keys() -> str:
    """Handles the key inputs given by the player during the main game loop
    and returns the action taken by the player."""
    global FOV_CALCULATE

    # Get Player Input
    events_list = pygame.event.get()

    response = "no-action"

    # TODO: Process Input
    for event in events_list:
        if event.type == pygame.QUIT:
            return "QUIT"

        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_UP, pygame.K_KP8]:
                if PLAYER.creature.move(0, -1):
                    response = "player-moved"
                    FOV_CALCULATE = True
            elif event.key in [pygame.K_DOWN, pygame.K_KP2]:
                if PLAYER.creature.move(0, 1):
                    response = "player-moved"
                    FOV_CALCULATE = True
            elif event.key in [pygame.K_LEFT, pygame.K_KP4]:
                if PLAYER.creature.move(-1, 0):
                    response = "player-moved"
                    FOV_CALCULATE = True
            elif event.key in [pygame.K_RIGHT, pygame.K_KP6]:
                if PLAYER.creature.move(1, 0):
                    response = "player-moved"
                    FOV_CALCULATE = True
            elif event.key in [pygame.K_KP7]:
                if PLAYER.creature.move(-1, -1):
                    response = "player-moved"
                    FOV_CALCULATE = True
            elif event.key in [pygame.K_KP9]:
                if PLAYER.creature.move(1, -1):
                    response = "player-moved"
                    FOV_CALCULATE = True
            elif event.key in [pygame.K_KP3]:
                if PLAYER.creature.move(1, 1):
                    response = "player-moved"
                    FOV_CALCULATE = True
            elif event.key in [pygame.K_KP1]:
                if PLAYER.creature.move(-1, 1):
                    response = "player-moved"
                    FOV_CALCULATE = True
            elif event.key in [pygame.K_KP5, pygame.K_SPACE]:
                response = "player-pass"
            elif event.key in [pygame.K_g]:
                items_at_player = map_get_objects(PLAYER.x, PLAYER.y, item=True)

                for obj in items_at_player:
                    obj.item.pick_up(PLAYER)
                    response = "player-pickup"
            elif event.key in [pygame.K_i]:
                menu_inventory()
            elif event.key in [pygame.K_p]:
                menu_pause()
            elif event.key in [pygame.K_d]:
                menu_drop()
            elif event.key in [pygame.K_l]:
                cast_lightning()
                response = "player-attacked"
            elif event.key in [pygame.K_f]:
                cast_fireball()
                response = "player-attacked"
            elif event.key in [pygame.K_h]:
                game_message(f"You are at {PLAYER.creature.hp}/{PLAYER.creature.MAX_HP} health!")
            elif event.key in [pygame.K_c]:
                exec(input("Code to execute: "))
            elif event.key in [pygame.K_x]:
                print(menu_tile_select({"coords_origin": PLAYER.pos}))

    return response


def game_message(game_msg: str, msg_color: T_COLOR = COLOR_GREY, bg_color: T_COLOR = COLOR_BLACK):
    """Adds the given message to the console messages to be displayed.

    # Arguments
    game_msg : The message to add.

    msg_color : The color of the message (Defaults to grey).

    bg_color : The color of the background behind the message (Defaults to black)."""
    GAME.message_history.append((game_msg, msg_color, bg_color))


def game_exit():
    """Disengage pygame and exit the program."""
    pygame.quit()
    exit()


if __name__ == "__main__":
    game_initialize()
    game_main_loop()
