#!/usr/bin/python
import wx
from math import sqrt, pi, exp, cos, sin
import random
THIRTY_DEG = 30*pi/180.0
TILE_SIZE = 64
BORDER_SIZE = 4

TILE_EMPTY = 0
TILE_QUEEN = 1
TILE_GRASSHOPPER = 2
TILE_ANT = 3
TILE_BEETLE = 4
TILE_LADYBUG = 5

def hex_neighbors(x,y):
    return [(x-1,y), (x,y-1), (x+1,y-1), (x+1,y), (x,y+1), (x, y-1)]

class Tile(object): pass

class HiveGame(object):
    def __init__(self):
        self.tiles = {}

    def add_tile(self, x,y, tile):
        if (x,y) not in self.tiles:
            self.tiles[(x,y)] = []
        self.tiles[(x,y)].append(tile)

    def get_legal_moves(self, x,y):
        if (x,y) not in self.tiles:
            raise ValueError("Not a tile, you guys!")
        return [(x-1,y-1), (x-1,y), (x-1, y+1)]

    @property
    def visible_tiles(self):
        keys = self.tiles.keys()
        values = [self.tiles[key][-1] for key in keys]
        return dict(zip(keys,values))

def hex_dims(s):
    h = sin(THIRTY_DEG)*s
    r = cos(THIRTY_DEG)*s
    b = s + 2*h
    a = 2*r
    return (h,s,r,a,b)


class HivePanel(wx.Panel):
    def __init__(self, parent):
        wx.Panel.__init__(self, parent, -1)
        self.model = HiveGame()
        self.model.add_tile(0,0, Tile())
        self.model.add_tile(1,0, Tile())
        self.model.add_tile(1,1, Tile())
        self.model.add_tile(3,3, Tile())


        self.hilighted_tile = (1,1)
        self.offset_x = 0
        self.offset_y = 0
        self.last_pos = (0,0)
        self.dragging = False
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_up)
        #self.Bind(wx.EVT_LEFT_CLICK, self.on_click)
        
    def on_motion(self, evt):
        if self.dragging:
            x,y = evt.GetPosition()
            dx,dy = self.last_pos[0]-x, self.last_pos[1]-y
            self.offset_x -= dx
            self.offset_y -= dy
            self.last_pos = (x,y)
            self.Refresh()

    def on_down(self, evt):
        self.dragging = True
        x,y = evt.GetPosition()
        self.last_pos = (x,y)

    def on_up(self, evt):
        self.dragging = False
        x,y = evt.GetPosition()

    def draw_hex(self, dc, dims, x, y):
        h,s,r,a,b = dims
        points = [(0,h),(r,0),(a,h),(a,h+s),(r,b),(0,s+h)]
        dc.DrawPolygon(points, x, y)

    def load_images(self):
        self.TILE = wx.Bitmap('images/tile_64.png')

    def on_size(self, evt):
        self.Refresh()
        evt.Skip()

    def on_paint(self, evt):
        dc = wx.AutoBufferedPaintDC(self)
        self.draw(dc)

    def draw(self, dc):
        w,h = dc.GetSize()
        dc.SetBrush(wx.WHITE_BRUSH)
        dc.SetPen(wx.Pen(wx.Colour(128,128,128), BORDER_SIZE))
        h,s,r,a,b = hex_dims(TILE_SIZE)
                
        for row,col in self.model.visible_tiles:
            if (row,col) == self.hilighted_tile:
                dc.SetBrush(wx.GREEN_BRUSH)
            else:
                dc.SetBrush(wx.WHITE_BRUSH)
            self.draw_hex(dc, (h,s,r,a,b), self.offset_x + col*a + r*(row%2), self.offset_y + row*(s+h))
        

if __name__ == "__main__":
    app = wx.App(False)
    frame = wx.Frame(None)
    panel = HivePanel(frame)
    frame.SetSize((480,480))
    frame.SetTitle("Hive")
    frame.Show(True)
    app.MainLoop()


