#!/usr/bin/python
import wx
from math import sqrt, pi, exp, cos, sin
import random
THIRTY_DEG = 30*pi/180.0
TILE_SIZE = 64
BORDER_SIZE = 4

PLAYER_1 = 1
PLAYER_2 = 2

TILE_EMPTY = 0
TILE_QUEEN = 1
TILE_GRASSHOPPER = 2
TILE_ANT = 3
TILE_BEETLE = 4
TILE_LADYBUG = 5
TILE_COLORS = {TILE_QUEEN:(252,233,79), TILE_BEETLE:(173,127,168)}

MIN_SCALE = 0.2
MAX_SCALE = 10.0
def hex_neighbors(row,col):
    if row % 2:
        return [(row, col-1), (row-1, col), (row-1, col+1), (row, col+1), (row+1, col+1), (row+1, col)]
    else:
        return [(row, col-1), (row-1, col-1), (row-1, col), (row, col+1), (row+1, col), (row+1, col-1)]

class Tile(object):
    def __init__(self, type=TILE_EMPTY):
        self.type = type
        self.color = TILE_COLORS.get(type, (186,189,182))

class HiveGame(object):
    def __init__(self):
        self.tiles = {}
        self.player = PLAYER_1
        self.hilighted_tile = None

    def add_tile(self, x,y, tile):
        if isinstance(tile, int):
            tile = Tile(tile)
        if (x,y) not in self.tiles:
            self.tiles[(x,y)] = []
        self.tiles[(x,y)].append(tile)

    def hilight_tile(self, loc):
        if loc:
            self.hilighted_tile = loc if loc in self.tiles else None
        else:
            self.hilighted_tile = None

    def get_legal_moves(self, x,y):
        if (x,y) not in self.tiles:
            raise ValueError("Not a tile, you guys!")
        tile = self.tiles[(x,y)][-1]

        # Compute anywhere in the hive that anyone can move
        all_legal_spots = set()
        for (a,b), stack in self.tiles.items():
            neighbors = hex_neighbors(a,b)
            unoccupied_neighbors = filter(lambda n : n not in self.tiles, neighbors)
            for n in unoccupied_neighbors:
                all_legal_spots.add(n)

        if tile.type == TILE_QUEEN:
            # Moves one and only one space, along 
            neighbors = hex_neighbors(x,y)
            valid_neighbors = filter(lambda n : n in all_legal_spots, neighbors)
            return valid_neighbors
        elif tile.type == TILE_BEETLE:
            neighbors = hex_neighbors(x,y)
            return neighbors
        else:
            return []
        
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
        self.model.add_tile(1,0, Tile(TILE_QUEEN))
        self.model.add_tile(1,1, Tile())
        self.model.add_tile(3,3, Tile())
        self.scale = 1.0
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
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_wheel)
        #self.Bind(wx.EVT_LEFT_CLICK, self.on_click)
        
    def on_wheel(self, evt):
        rot = evt.GetWheelRotation()
        if rot > 0:
            self.scale += 0.1
        else:
            self.scale -= 0.1
        if self.scale < MIN_SCALE:
            self.scale = MIN_SCALE
        if self.scale > MAX_SCALE:
            self.scale = MAX_SCALE
        self.Refresh()
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

    def hit_test(self, x,y):
        'Now checks for a hit in an inscribed circle!  Close enough!'
        h,s,r,a,b = hex_dims(self.scale*TILE_SIZE)
        for row,col in self.model.tiles:
            cx = self.offset_x + col*a + r*(row%2)
            cy = self.offset_y + row*(s+h)
            dist = sqrt((cx-x)*(cx-x) + (cy-y)*(cy-y))
            if dist < r:
                return (row, col)

    def on_up(self, evt):
        self.dragging = False
        x,y = evt.GetPosition()
        coords = self.hit_test(x,y)
        self.model.hilight_tile(coords)
        self.Refresh()

    def draw_hex(self, dc, dims, x, y):
        h,s,r,a,b = dims
        x = x-r
        y = y-h-(s/2)
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
        h,s,r,a,b = hex_dims(self.scale*TILE_SIZE)
        line_thickness = self.scale*BORDER_SIZE 
        if self.model.hilighted_tile:
            dc.SetBrush(wx.Brush(wx.Colour(200,255,200)))
            dc.SetPen(wx.Pen(wx.Colour(128, 255, 128),line_thickness))
            for row, col in self.model.get_legal_moves(*self.model.hilighted_tile):
                self.draw_hex(dc, (h,s,r,a,b), self.offset_x + col*a + r*(row%2), self.offset_y + row*(s+h))

        dc.SetPen(wx.Pen(wx.Colour(128,128,128), line_thickness))
        for (row,col), tile in self.model.visible_tiles.items():
            if (row,col) == self.model.hilighted_tile:
                dc.SetBrush(wx.GREEN_BRUSH)
            else:
                dc.SetBrush(wx.Brush(wx.Colour(*tile.color)))
                #dc.SetBrush(wx.WHITE_BRUSH)
            self.draw_hex(dc, (h,s,r,a,b), self.offset_x + col*a + r*(row%2), self.offset_y + row*(s+h))
        

if __name__ == "__main__":
    app = wx.App(False)
    frame = wx.Frame(None)
    panel = HivePanel(frame)
    frame.SetSize((480,480))
    frame.SetTitle("Hive")
    frame.Show(True)
    app.MainLoop()


