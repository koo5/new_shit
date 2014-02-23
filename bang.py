#!/usr/bin/python
#-*- coding: utf-8 -*-

import pygame
from pygame import gfxdraw, font

pygame.init()

screen_surface = pygame.display.set_mode((800,300))
screen_surface.fill((0,0,0))
pygame.display.flip()

font = font.SysFont('monospace', 16)
fontw, fonth = font.size("X")

for line in self.lines:
	for ch in line:
s = font.render(ch[0],True,ch[1]['color'],bg)
screen_surface.blit(s,(x,y))
        mods = pygame.key.get_mods()
        if mods & pygame.KMOD_LSHIFT:
            print "left shift pressed"
    pygame.display.flip()



