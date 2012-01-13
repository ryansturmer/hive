#!/usr/bin/python
import wx
from math import sqrt, pi, exp, cos, sin
import random
THIRTY_DEG = 30*pi/180.0
TILE_SIZE = 64
BORDER_SIZE = 4

PLAYER_1 = 1
PLAYER_2 = 2
PLAYERS = (PLAYER_1, PLAYER_2)
TILE_EMPTY = 0
TILE_QUEEN = 1
TILE_GRASSHOPPER = 2
TILE_ANT = 3
TILE_BEETLE = 4
TILE_LADYBUG = 5
TILE_SPIDER = 6
TILES = (TILE_QUEEN, TILE_GRASSHOPPER, TILE_ANT, TILE_BEETLE, TILE_SPIDER)
TILE_COLORS = { TILE_QUEEN:(0xfc,0xe9,0x4f), 
                TILE_GRASSHOPPER:(0x8a,0xe2,0x34),
                TILE_ANT: (0x72,0x9f,0xcf),
                TILE_BEETLE:(173,127,168),
                TILE_SPIDER:(0xc1,0x7d,0x11)}

HIT_TYPE_MISS = 0
HIT_TYPE_TILE = 1
HIT_TYPE_TILEBOX = 2
HIT_TYPE_EMPTY = 3

MIN_SCALE = 0.2
MAX_SCALE = 10.0
def hex_neighbors(row,col):
    if row % 2:
        return [(row, col-1), (row-1, col), (row-1, col+1), (row, col+1), (row+1, col+1), (row+1, col)]
    else:
        return [(row, col-1), (row-1, col-1), (row-1, col), (row, col+1), (row+1, col), (row+1, col-1)]

class Tile(object):
    def __init__(self, player, type=TILE_EMPTY):
        self.type = type
        self.color = TILE_COLORS.get(type, (186,189,182))
        self.player = player

class HiveGame(object):
    def __init__(self):
        self.tiles = {}
        self.hilighted_tile = None
        self.setup_game()

    def place_new_tile(self, loc, tile_type):
        'Actually make a move.  Places a tile for the current player, if legal.'
        if loc in self.get_legal_place_locs():
            self.add_tile(loc, Tile(self.player, tile_type))
        self.turn += 1
        self.player_tiles[self.player][tile_type] -= 1
        self.player = PLAYER_2 if self.player == PLAYER_1 else PLAYER_1

    def get_legal_place_locs(self, player=None):
        if player == None: player = self.player
        if self.turn == 0:
            return [(0,0)]
        if self.turn == 1:
            return hex_neighbors(0,0)

        boundary_spaces = self.get_legal_locs()
        retval = []
        for space in boundary_spaces:
            neighbors = hex_neighbors(*space)
            ok = True
            for neighbor in neighbors:
                if neighbor in self.tiles and self.tiles[neighbor][-1].player != player:
                    ok = False
                    break
            if ok:
                retval.append(space)
        return retval

    def setup_game(self):    
        self.player = PLAYER_1
        self.player_tiles = {}
        self.turn = 0
        for player in PLAYERS:
            tilebox = {}
            tilebox[TILE_QUEEN] = 1
            tilebox[TILE_GRASSHOPPER] = 3
            tilebox[TILE_ANT] = 3
            tilebox[TILE_BEETLE] = 2
            tilebox[TILE_SPIDER] = 2
            self.player_tiles[player] = tilebox

    
    def add_tile(self, loc, tile):
        if isinstance(tile, int):
            tile = Tile(self.player, tile)
        if loc not in self.tiles:
            self.tiles[loc] = []
        self.tiles[loc].append(tile)

    def hilight_tile(self, loc):
        if loc:
            self.hilighted_tile = loc if loc in self.tiles else None
        else:
            self.hilighted_tile = None

    def can_slide_to(self, loc, dest):
        if loc not in self.tiles:
            raise ValueError("Not a tile, you guys!")
        neighbors = hex_neighbors(*loc)
        if dest not in neighbors:
            return False        
        i = neighbors.index(dest)
        a,b = neighbors[(i+1) % 6], neighbors[i-1]
        return not(a in self.tiles and b in self.tiles)
    
    def get_legal_locs(self):
        # Compute anywhere in the hive that anyone can move
        all_legal_spots = set()
        for (a,b), stack in self.tiles.items():
            neighbors = hex_neighbors(a,b)
            unoccupied_neighbors = filter(lambda n : n not in self.tiles, neighbors)
            for n in unoccupied_neighbors:
                all_legal_spots.add(n)
        return all_legal_spots

    def get_legal_moves(self, loc):
        all_legal_spots = self.get_legal_locs()
        if loc not in self.tiles:
            raise ValueError("Not a tile, you guys!")
        tile = self.tiles[loc][-1]

        if tile.type == TILE_QUEEN:
            # Moves one and only one space, along 
            neighbors = hex_neighbors(*loc)
            valid_neighbors = filter(lambda n : n in all_legal_spots and self.can_slide_to(loc, n), neighbors)
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
        self.scale = 1.0
        self.offset_x = 0
        self.offset_y = 0
        self.last_pos = (0,0)
        self.dragging = False
        self.place_candidates = []
        self.place_type = -1
        self.SetBackgroundStyle(wx.BG_STYLE_CUSTOM)
        self.Bind(wx.EVT_SIZE, self.on_size)
        self.Bind(wx.EVT_PAINT, self.on_paint)
        self.Bind(wx.EVT_MOTION, self.on_motion)
        self.Bind(wx.EVT_LEFT_DOWN, self.on_down)
        self.Bind(wx.EVT_LEFT_UP, self.on_up)
        self.Bind(wx.EVT_MOUSEWHEEL, self.on_wheel)
        #self.Bind(wx.EVT_LEFT_CLICK, self.on_click)
        w,h = self.GetSize()
        self.offset_x = -w/2
        self.offset_y = -h/2
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
        if self.tilebox_centers:
            h,s,r,a,b = hex_dims(self.tilebox_size)
            for cx,cy in self.tilebox_centers:
                dist = sqrt((cx-x)*(cx-x) + (cy-y)*(cy-y))
                if dist < r:
                    return HIT_TYPE_TILEBOX, self.tilebox_centers[(cx,cy)]

        h,s,r,a,b = hex_dims(self.scale*TILE_SIZE)
        for row,col in self.model.tiles:
            cx = self.offset_x + col*a + r*(row%2)
            cy = self.offset_y + row*(s+h)
            dist = sqrt((cx-x)*(cx-x) + (cy-y)*(cy-y))
            if dist < r:
                return HIT_TYPE_TILE, (row, col)

        for row,col in self.place_candidates:
            cx = self.offset_x + col*a + r*(row%2)
            cy = self.offset_y + row*(s+h)
            dist = sqrt((cx-x)*(cx-x) + (cy-y)*(cy-y))
            if dist < r:
                return HIT_TYPE_EMPTY, (row, col)
        return HIT_TYPE_MISS, (-1,-1)

    def on_up(self, evt):
        self.dragging = False
        x,y = evt.GetPosition()
        type, hit = self.hit_test(x,y)
        if(type == HIT_TYPE_TILE):
            self.model.hilight_tile(hit)
            self.place_candidates = []
            self.place_type = -1
            self.Refresh()
        elif(type == HIT_TYPE_TILEBOX):
            self.place_candidates = self.model.get_legal_place_locs()
            self.place_type = hit
        elif(type == HIT_TYPE_EMPTY):
            self.model.place_new_tile(hit, self.place_type)
            self.place_candidates = []
            self.place_type = -1
        else:
            self.model.hilight_tile(None) 
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

    def draw_tilebox(self, dc, hex_size, line_thickness, loc):
        TILEBOX_SPACING = 0.25
        h,s,r,a,b = hex_dims(hex_size)
        x,y = loc
        dc.SetPen(wx.Pen(wx.Colour(128,128,128), line_thickness))
        dc.SetBrush(wx.Brush(wx.Colour(0xff,0xff,0xff,128)))
        dc.DrawRectangle(x-r-(a*TILEBOX_SPACING), (y-(b/2)) - b*TILEBOX_SPACING, a + 2*a*TILEBOX_SPACING, b*len(TILES) + b*(len(TILES)+1)*TILEBOX_SPACING)
        self.tilebox_centers = {}
        self.tilebox_size = hex_size
        for tile_type in TILES:
            self.tilebox_centers[(x,y)] = tile_type
            dc.SetPen(wx.Pen(wx.Colour(128,128,128), line_thickness*2 if tile_type == self.place_type else line_thickness))
            dc.SetBrush(wx.Brush(wx.Colour(*TILE_COLORS[tile_type])))
            self.draw_hex(dc, (h,s,r,a,b), x,y)
            y += b + b*TILEBOX_SPACING

    def draw_text(self, dc):
        pass

    def draw(self, dc):
        w,h = dc.GetSize()
        dc.Clear()
        dc.SetBrush(wx.WHITE_BRUSH)
        h,s,r,a,b = hex_dims(self.scale*TILE_SIZE)
        line_thickness = self.scale*BORDER_SIZE 
        
        # Placement candidates
        dc.SetBrush(wx.Brush(wx.Colour(200,255,200)))
        dc.SetPen(wx.Pen(wx.Colour(128, 255, 128),line_thickness))
        for row, col in self.place_candidates:
            self.draw_hex(dc, (h,s,r,a,b), self.offset_x + col*a + r*(row%2), self.offset_y + row*(s+h))

        dc.SetPen(wx.Pen(wx.Colour(128,128,128), line_thickness))
        for (row,col), tile in self.model.visible_tiles.items():
            if (row,col) == self.model.hilighted_tile:
                dc.SetBrush(wx.GREEN_BRUSH)
            else:
                dc.SetBrush(wx.Brush(wx.Colour(*tile.color)))
                #dc.SetBrush(wx.WHITE_BRUSH)
            self.draw_hex(dc, (h,s,r,a,b), self.offset_x + col*a + r*(row%2), self.offset_y + row*(s+h))
        
        self.draw_tilebox(dc, 20, 1, (w-50, 50))
if __name__ == "__main__":
    app = wx.App(False)
    frame = wx.Frame(None)
    panel = HivePanel(frame)
    frame.SetSize((480,480))
    frame.SetTitle("Hive")
    frame.Show(True)
    app.MainLoop()


