#!/usr/bin/env python
# coding: utf8
import mapnik 
import math
import getopt, sys, os, re
import cairo
from math import tan, radians, hypot, cos, sin, atan2, sqrt

centrex=10.5
centrey=51.3
zoom=7
scale=2
attribution="population per square kilometre in Germany - Andreas Binder ©OpenStreetMap contributors ODbL (State 14.05.2019)"

merc = mapnik.Projection('+proj=merc +a=6378137 +b=6378137 +lat_ts=0.0 +lon_0=0.0 +x_0=0.0 +y_0=0 +k=1.0 +units=m +nadgrids=@null +no_defs +over')

longlat = mapnik.Projection('+proj=longlat +ellps=WGS84 +datum=WGS84 +no_defs')

width=450 * scale
height=600 * scale

m = mapnik.Map(width, height)

mapnik.load_map(m, 'population-density.xml')
m.srs = merc.params()

centre = mapnik.Coord(centrex, centrey)  
transform = mapnik.ProjTransform(longlat, merc)
merc_centre = transform.forward(centre)

dx = ((20037508.34*2*(width/2)))/(256*(2 ** (zoom)))
minx = merc_centre.x - dx
maxx = merc_centre.x + dx

m.aspect_fix_mode = mapnik.aspect_fix_mode.ADJUST_BBOX_HEIGHT

bounds = mapnik.Box2d(minx, merc_centre.y-10, maxx, merc_centre.y+10)
m.zoom_to_box(bounds)
bbox_latlon = merc.inverse(m.envelope())

R = 6373.0

surface = cairo.ImageSurface(cairo.FORMAT_ARGB32,m.width,m.height)

ctx = cairo.Context(surface)
mapnik.render(m,ctx,scale,0,0)

# attribution
ctx.set_source_rgba(1,1,1,0.5)
ctx.select_font_face("DejaVu Sans Condensed")
ctx.set_font_size(8*scale)
(x,y,width,height,dx,dy) = ctx.text_extents(attribution)
ctx.rectangle(0,m.height - height - 3*scale,m.width,m.height)
ctx.fill()
ctx.move_to(3 * scale,m.height -2*scale)
ctx.set_source_rgb(0,0,0)
ctx.show_text(attribution)

# make legend
ctx.set_source_rgb(0,int("ff",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*15,height,height)
ctx.fill()
ctx.set_source_rgb(0,int("dd",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*14,height,height)
ctx.fill()
ctx.set_source_rgb(0,int("cc",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*13,height,height)
ctx.fill()
ctx.set_source_rgb(0,int("bb",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*12,height,height)
ctx.fill()
ctx.set_source_rgb(0,int("aa",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*11,height,height)
ctx.fill()
ctx.set_source_rgb(0,int("99",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*10,height,height)
ctx.fill()
ctx.set_source_rgb(0,int("66",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*9,height,height)
ctx.fill()
ctx.set_source_rgb(0,int("55",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*8,height,height)
ctx.fill()
ctx.set_source_rgb(0,int("44",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*7,height,height)
ctx.fill()
ctx.set_source_rgb(0,int("33",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*6,height,height)
ctx.fill()
ctx.set_source_rgb(0,int("22",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*5,height,height)
ctx.fill()
ctx.set_source_rgb(0,int("11",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*4,height,height)
ctx.fill()

ctx.set_font_size(6*scale)
ctx.set_source_rgb(0,0,0)

ctx.move_to(3 * scale,m.height - height*15 - 3)
ctx.show_text("Persons per km²")
ctx.move_to(6 * scale + height,m.height - height*14 - 3)
ctx.show_text("<10")
ctx.move_to(6 * scale + height,m.height - height*13 - 3)
ctx.show_text("[10-20[")
ctx.move_to(6 * scale + height,m.height - height*12 - 3)
ctx.show_text("[20-40[")
ctx.move_to(6 * scale + height,m.height - height*11 - 3)
ctx.show_text("[40-80[")
ctx.move_to(6 * scale + height,m.height - height*10 - 3)
ctx.show_text("[80-160[")
ctx.move_to(6 * scale + height,m.height - height*9 - 3)
ctx.show_text("[160-320[")
ctx.move_to(6 * scale + height,m.height - height*8 - 3)
ctx.show_text("[320-640[")
ctx.move_to(6 * scale + height,m.height - height*7 - 3)
ctx.show_text("[640-1200[")
ctx.move_to(6 * scale + height,m.height - height*6 - 3)
ctx.show_text("[1200-2400[")
ctx.move_to(6 * scale + height,m.height - height*5 - 3)
ctx.show_text("[2400-4800[")
ctx.move_to(6 * scale + height,m.height - height*4 - 3)
ctx.show_text(u"\u2265 4800")
ctx.move_to(6 * scale + height,m.height - height*3 - 3)
ctx.show_text("No population tag in OpenStreetMap found")

ctx.set_source_rgb(int("ff",16)/255.0,int("8c",16)/255.0,0)
ctx.rectangle(3 * scale,m.height - height*4,height,height)
ctx.fill()

# finish
surface.write_to_png("population-density.png")
surface.finish()

