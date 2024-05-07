import pygame
import os


tile_img_path = os.path.join("resources", "img", "tiles")
tile_imgs = {}


def get_tile_image(tile_name):
    if tile_name not in tile_imgs:
        load_tile_image(tile_name)
    return tile_imgs[tile_name]

def load_tile_image(tile_name):
    tile_img = pygame.image.load(os.path.join(tile_img_path, "Front.png")).convert_alpha()
    tile_img.blit(
        pygame.image.load(os.path.join(tile_img_path, tile_name + ".png")).convert_alpha(), (0, 0)
    )
    tile_imgs[tile_name] = tile_img


pygame.mixer.init()
sounds_path = os.path.join("resources", "sounds")
sounds = {}


def get_sound(sound_name):
    if sound_name not in sounds:
        load_sound(sound_name)
    return sounds[sound_name]

def load_sound(sound_name):
    sound = pygame.mixer.Sound(os.path.join(sounds_path, sound_name + ".wav"))
    sounds[sound_name] = sound