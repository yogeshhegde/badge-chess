'''
MicroPython Sunfish Chess Engine for BeagleBadge (LVGL)
- Original Badger 2040 port by: Quan Lin
- Modified by: Jerzy Glowacki
- LVGL port for BeagleBadge by: Yogesh Hegde
- License: GNU GPL v3
'''

import lvgl as lv
import sys
import time
import gc
import re
from collections import namedtuple
from micropython import const

if "core" not in sys.path:
    sys.path.append("core")
from core import app

###############################################################################
# Chess Engine — copied verbatim from main.py (Sunfish)
###############################################################################

@micropython.native
def count(start=0, step=1):
    n = start
    while True:
        yield n
        n += step

@micropython.native
def reverse(s):
    return ''.join(reversed(s))

@micropython.native
def swapcase(s):
    return ''.join(c.lower() if c.isupper() else c.upper() for c in s)

# Piece-Square tables. Tune these to change sunfish's behaviour
piece = {'P': 100, 'N': 280, 'B': 320, 'R': 479, 'Q': 929, 'K': 60000}
pst = {
    'P': (   0,   0,   0,   0,   0,   0,   0,   0,
            78,  83,  86,  73, 102,  82,  85,  90,
             7,  29,  21,  44,  40,  31,  44,   7,
           -17,  16,  -2,  15,  14,   0,  15, -13,
           -26,   3,  10,   9,   6,   1,   0, -23,
           -22,   9,   5, -11, -10,  -2,   3, -19,
           -31,   8,  -7, -37, -36, -14,   3, -31,
             0,   0,   0,   0,   0,   0,   0,   0),
    'N': ( -66, -53, -75, -75, -10, -55, -58, -70,
            -3,  -6, 100, -36,   4,  62,  -4, -14,
            10,  67,   1,  74,  73,  27,  62,  -2,
            24,  24,  45,  37,  33,  41,  25,  17,
            -1,   5,  31,  21,  22,  35,   2,   0,
           -18,  10,  13,  22,  18,  15,  11, -14,
           -23, -15,   2,   0,   2,   0, -23, -20,
           -74, -23, -26, -24, -19, -35, -22, -69),
    'B': ( -59, -78, -82, -76, -23,-107, -37, -50,
           -11,  20,  35, -42, -39,  31,   2, -22,
            -9,  39, -32,  41,  52, -10,  28, -14,
            25,  17,  20,  34,  26,  25,  15,  10,
            13,  10,  17,  23,  17,  16,   0,   7,
            14,  25,  24,  15,   8,  25,  20,  15,
            19,  20,  11,   6,   7,   6,  20,  16,
            -7,   2, -15, -12, -14, -15, -10, -10),
    'R': (  35,  29,  33,   4,  37,  33,  56,  50,
            55,  29,  56,  67,  55,  62,  34,  60,
            19,  35,  28,  33,  45,  27,  25,  15,
             0,   5,  16,  13,  18,  -4,  -9,  -6,
           -28, -35, -16, -21, -13, -29, -46, -30,
           -42, -28, -42, -25, -25, -35, -26, -46,
           -53, -38, -31, -26, -29, -43, -44, -53,
           -30, -24, -18,   5,  -2, -18, -31, -32),
    'Q': (   6,   1,  -8,-104,  69,  24,  88,  26,
            14,  32,  60, -10,  20,  76,  57,  24,
            -2,  43,  32,  60,  72,  63,  43,   2,
             1, -16,  22,  17,  25,  20, -13,  -6,
           -14, -15,  -2,  -5,  -1, -10, -20, -22,
           -30,  -6, -13, -11, -16, -11, -16, -27,
           -36, -18,   0, -19, -15, -15, -21, -38,
           -39, -30, -31, -13, -31, -36, -34, -42),
    'K': (   4,  54,  47, -99, -99,  60,  83, -62,
           -32,  10,  55,  56,  56,  55,  10,   3,
           -62,  12, -57,  44, -67,  28,  37, -31,
           -55,  50,  11,  -4, -19,  13,   0, -49,
           -55, -43, -52, -28, -51, -47,  -8, -50,
           -47, -42, -43, -79, -64, -32, -29, -32,
            -4,   3, -14, -50, -57, -18,  13,   4,
            17,  30,  -3, -14,   6,  -1,  40,  18),
}

@micropython.native
def padrow(row, k):
    return (0,) + tuple(x+piece[k] for x in row) + (0,)

for k, table in pst.items():
    pst[k] = sum((padrow(table[i*8:i*8+8], k) for i in range(8)), ())
    pst[k] = (0,)*20 + pst[k] + (0,)*20

###############################################################################
# Global constants
###############################################################################

A1, H1, A8, H8 = const(91), const(98), const(21), const(28)
initial = (
    '         \n'  #   0 -  9
    '         \n'  #  10 - 19
    ' rnbqkbnr\n'  #  20 - 29
    ' pppppppp\n'  #  30 - 39
    ' ........\n'  #  40 - 49
    ' ........\n'  #  50 - 59
    ' ........\n'  #  60 - 69
    ' ........\n'  #  70 - 79
    ' PPPPPPPP\n'  #  80 - 89
    ' RNBQKBNR\n'  #  90 - 99
    '         \n'  # 100 -109
    '         \n'  # 110 -119
)

N, E, S, W = const(-10), const(1), const(10), const(-1)
directions = {
    'P': (N, N+N, N+W, N+E),
    'N': (N+N+E, E+N+E, E+S+E, S+S+E, S+S+W, W+S+W, W+N+W, N+N+W),
    'B': (N+E, S+E, S+W, N+W),
    'R': (N, E, S, W),
    'Q': (N, E, S, W, N+E, S+E, S+W, N+W),
    'K': (N, E, S, W, N+E, S+E, S+W, N+W)
}

MATE_LOWER = piece['K'] - 10*piece['Q']
MATE_UPPER = piece['K'] + 10*piece['Q']

TABLE_SIZE = const(500)
QS_LIMIT = const(219)
EVAL_ROUGHNESS = const(13)
DRAW_TEST = True
TIME_LIMIT = const(500)

###############################################################################
# Chess logic
###############################################################################

class Position(namedtuple('Position', 'board score wc bc ep kp')):
    ''' A state of a chess game
    board -- a 120 char representation of the board
    score -- the board evaluation
    wc -- the castling rights, [west/queen side, east/king side]
    bc -- the opponent castling rights, [west/king side, east/queen side]
    ep - the en passant square
    kp - the king passant square
    '''

    @micropython.native
    def gen_moves(self):
        for i, p in enumerate(self.board):
            if not p.isupper():
                continue
            for d in directions[p]:
                for j in count(i+d, d):
                    q = self.board[j]
                    if q.isspace() or q.isupper():
                        break
                    if p == 'P' and d in (N, N+N) and q != '.':
                        break
                    if p == 'P' and d == N+N and (i < A1+N or self.board[i+N] != '.'):
                        break
                    if p == 'P' and d in (N+W, N+E) and q == '.' and j not in (self.ep, self.kp, self.kp-1, self.kp+1):
                        break
                    yield (i, j)
                    if p in 'PNK' or q.islower():
                        break
                    if i == A1 and self.board[j+E] == 'K' and self.wc[0]:
                        yield (j+E, j+W)
                    if i == H1 and self.board[j+W] == 'K' and self.wc[1]:
                        yield (j+W, j+E)

    @micropython.native
    def rotate(self):
        return Position(swapcase(reverse(self.board)), -self.score, self.bc, self.wc, 119-self.ep if self.ep else 0, 119-self.kp if self.kp else 0)

    @micropython.native
    def nullmove(self):
        return Position(swapcase(reverse(self.board)), -self.score, self.bc, self.wc, 0, 0)

    @micropython.native
    def put(self, board, i, p):
        return board[:i] + p + board[i+1:]

    @micropython.native
    def move(self, move):
        i, j = move
        p, q = self.board[i], self.board[j]
        board = self.board
        wc, bc, ep, kp = self.wc, self.bc, 0, 0
        score = self.score + self.value(move)
        board = self.put(board, j, board[i])
        board = self.put(board, i, '.')
        if i == A1:
            wc = (False, wc[1])
        if i == H1:
            wc = (wc[0], False)
        if j == A8:
            bc = (bc[0], False)
        if j == H8:
            bc = (False, bc[1])
        if p == 'K':
            wc = (False, False)
            if abs(j-i) == 2:
                kp = (i+j)//2
                board = self.put(board, A1 if j < i else H1, '.')
                board = self.put(board, kp, 'R')
        if p == 'P':
            if A8 <= j <= H8:
                board = self.put(board, j, 'Q')
            if j - i == 2*N:
                ep = i + N
            if j == self.ep:
                board = self.put(board, j+S, '.')
        return Position(board, score, wc, bc, ep, kp).rotate()

    @micropython.native
    def value(self, move):
        i, j = move
        p, q = self.board[i], self.board[j]
        score = pst[p][j] - pst[p][i]
        if q.islower():
            score += pst[q.upper()][119-j]
        if abs(j-self.kp) < 2:
            score += pst['K'][119-j]
        if p == 'K' and abs(i-j) == 2:
            score += pst['R'][(i+j)//2]
            score -= pst['R'][A1 if j < i else H1]
        if p == 'P':
            if A8 <= j <= H8:
                score += pst['Q'][j] - pst['P'][j]
            if j == self.ep:
                score += pst['P'][119-(j+S)]
        return score

###############################################################################
# Search logic
###############################################################################

Entry = namedtuple('Entry', 'lower upper')

class Searcher:
    def __init__(self):
        self.tp_score = {}
        self.tp_move = {}
        self.history = set()
        self.nodes = 0

    @micropython.native
    def bound(self, pos, gamma, depth, root=True):
        self.nodes += 1
        depth = max(depth, 0)

        if pos.score <= -MATE_LOWER:
            return -MATE_UPPER

        if DRAW_TEST:
            if not root and pos in self.history:
                return 0

        entry = self.tp_score.get((pos, depth, root), Entry(-MATE_UPPER, MATE_UPPER))
        if entry.lower >= gamma and (not root or self.tp_move.get(pos) is not None):
            return entry.lower
        if entry.upper < gamma:
            return entry.upper

        @micropython.native
        def is_dead(pos):
            return any(pos.value(m) >= MATE_LOWER for m in pos.gen_moves())

        @micropython.native
        def moves():
            gc.collect()

            if depth > 0 and not root and any(c in pos.board for c in 'RBNQ'):
                yield None, -self.bound(pos.nullmove(), 1-gamma, depth-3, root=False)
            if depth == 0:
                yield None, pos.score
            killer = self.tp_move.get(pos)
            if killer and (depth > 0 or pos.value(killer) >= QS_LIMIT):
                yield killer, -self.bound(pos.move(killer), 1-gamma, depth-1, root=False)
            for move in sorted(pos.gen_moves(), key=pos.value, reverse=True):
                if depth > 0 or pos.value(move) >= QS_LIMIT:
                    yield move, -self.bound(pos.move(move), 1-gamma, depth-1, root=False)

        best = -MATE_UPPER
        for move, score in moves():
            best = max(best, score)
            if best >= gamma:
                if len(self.tp_move) > TABLE_SIZE:
                    self.tp_move.clear()
                self.tp_move[pos] = move
                break

        if best < gamma and best < 0 and depth > 0:
            if all(is_dead(pos.move(m)) for m in pos.gen_moves()):
                in_check = is_dead(pos.nullmove())
                best = -MATE_UPPER if in_check else 0

        if len(self.tp_score) > TABLE_SIZE:
            self.tp_score.clear()
        if best >= gamma:
            self.tp_score[pos, depth, root] = Entry(best, entry.upper)
        if best < gamma:
            self.tp_score[pos, depth, root] = Entry(entry.lower, best)

        return best

    @micropython.native
    def search(self, pos, history=()):
        self.nodes = 0
        if DRAW_TEST:
            self.history = set(history)
            self.tp_score.clear()

        for depth in range(1, 100):
            lower, upper = -MATE_UPPER, MATE_UPPER
            while lower < upper - EVAL_ROUGHNESS:
                gamma = (lower+upper+1)//2
                score = self.bound(pos, gamma, depth)
                if score >= gamma:
                    lower = score
                if score < gamma:
                    upper = score
            self.bound(pos, lower, depth)
            yield depth, self.tp_move.get(pos), self.tp_score.get((pos, depth, True)).lower

###############################################################################
# Coordinate helpers
###############################################################################

def parse(c):
    fil, rank = ord(c[0]) - ord('a'), int(c[1]) - 1
    return A1 + fil - 10*rank

def render(i):
    rank, fil = divmod(i - A1, 10)
    return chr(fil + ord('a')) + str(-rank + 1)

###############################################################################
# LVGL Chess App
###############################################################################

# Game states
STATE_SELECT_FROM = const(0)
STATE_SELECT_TO = const(1)
STATE_ENGINE = const(2)
STATE_GAME_OVER = const(3)

# UI constants — sized for 400x300 display
SQ_SIZE = const(36)
BOARD_PX = const(288)  # 8 * 36

COLOR_LIGHT_SQ = lv.color_white()
COLOR_DARK_SQ = lv.color_make(170, 170, 170)
COLOR_CURSOR = lv.color_make(0, 100, 255)
COLOR_SELECTED = lv.color_make(0, 200, 0)
COLOR_WHITE_PIECE = lv.color_make(255, 255, 255)
COLOR_BLACK_PIECE = lv.color_make(30, 30, 30)


class ChessApp(app.App):
    def __init__(self):
        super().__init__("Chess")
        self.screen = None
        self.bpawn = None
        self.bking = None
        self.bqueen = None
        self.brook = None
        self.bbishop = None
        self.bknight = None
        self.wpawn = None
        self.wking = None
        self.wqueen = None
        self.wrook = None
        self.wbishop = None
        self.wknight = None

    def _load_logo(self, path):
        try:
            with open(path, 'rb') as f:
                png_data = f.read()
            dsc = lv.image_dsc_t()
            dsc.data_size = len(png_data)
            dsc.data = png_data
            return dsc
        except:
            return None

    def enter(self, on_exit=None):
        self.on_exit_cb = on_exit

        # Game state
        self.hist = [Position(initial, 0, (True, True), (True, True), 0, 0)]
        self.searcher = Searcher()
        self.state = STATE_SELECT_FROM
        self.cursor_row = 6
        self.cursor_col = 4
        self.from_row = -1
        self.from_col = -1
        self.my_move_str = ''
        self.your_move_str = '...'

        # Build UI
        self.screen = lv.obj()
        self.screen.set_style_bg_color(lv.color_black(), 0)
        self.screen.set_style_bg_opa(lv.OPA.COVER, 0)
        self.screen.set_style_pad_all(0, 0)
        lv.screen_load(self.screen)

        # Board container — positioned at left
        self.board_cont = lv.obj(self.screen)
        self.board_cont.set_size(BOARD_PX, BOARD_PX)
        self.board_cont.set_style_pad_all(0, 0)
        self.board_cont.set_style_border_width(0, 0)
        self.board_cont.set_style_radius(0, 0)
        self.board_cont.set_style_bg_opa(lv.OPA.TRANSP, 0)
        self.board_cont.align(lv.ALIGN.LEFT_MID, 5, 0)
        self.board_cont.remove_flag(lv.obj.FLAG.SCROLLABLE)

        # Load all logos
        self.bpawn = self._load_logo("assets/chess/black-pawn.png")
        self.bking = self._load_logo("assets/chess/black-king.png")
        self.bknight = self._load_logo("assets/chess/black-knight.png")
        self.bbishop = self._load_logo("assets/chess/black-bishop.png")
        self.brook = self._load_logo("assets/chess/black-rook.png")
        self.bqueen = self._load_logo("assets/chess/black-queen.png")
        self.wpawn = self._load_logo("assets/chess/white-pawn.png")
        self.wking = self._load_logo("assets/chess/white-king.png")
        self.wqueen = self._load_logo("assets/chess/white-queen.png")
        self.wrook = self._load_logo("assets/chess/white-rook.png")
        self.wbishop = self._load_logo("assets/chess/white-bishop.png")
        self.wknight = self._load_logo("assets/chess/white-knight.png")

        # Create 8x8 squares
        self.squares = []
        self.labels = []
        for row in range(8):
            sq_row = []
            #lbl_row = []
            piece_row = []
            for col in range(8):
                sq = lv.obj(self.board_cont)
                sq.set_size(SQ_SIZE, SQ_SIZE)
                sq.set_pos(col * SQ_SIZE, row * SQ_SIZE)
                sq.set_style_radius(0, 0)
                sq.set_style_border_width(0, 0)
                sq.set_style_pad_all(0, 0)
                sq.remove_flag(lv.obj.FLAG.SCROLLABLE)

                if (row + col) % 2 == 0:
                    sq.set_style_bg_color(COLOR_LIGHT_SQ, 0)
                else:
                    sq.set_style_bg_color(COLOR_DARK_SQ, 0)
                sq.set_style_bg_opa(lv.OPA.COVER, 0)

                # lbl = lv.label(sq)
                # lbl.set_text("")
                # lbl.set_style_text_font(lv.font_montserrat_24, 0)
                # lbl.center()

                img = lv.image(sq)
                img.set_size(30,30)
                img.center()

                sq_row.append(sq)
                piece_row.append(img)
            self.squares.append(sq_row)
            self.labels.append(piece_row)

        # Info panel — right side
        self.info_panel = lv.obj(self.screen)
        self.info_panel.set_size(100, BOARD_PX)
        self.info_panel.align(lv.ALIGN.RIGHT_MID, -2, 0)
        self.info_panel.set_style_bg_color(lv.color_black(), 0)
        self.info_panel.set_style_bg_opa(lv.OPA.COVER, 0)
        self.info_panel.set_style_border_width(0, 0)
        self.info_panel.set_style_radius(4, 0)
        self.info_panel.set_style_pad_all(6, 0)
        self.info_panel.remove_flag(lv.obj.FLAG.SCROLLABLE)
        self.info_panel.set_flex_flow(lv.FLEX_FLOW.COLUMN)
        self.info_panel.set_style_flex_main_place(lv.FLEX_ALIGN.START, 0)
        self.info_panel.set_style_pad_row(4, 0)

        self.title_lbl = self._make_info_label("Chess", lv.color_white())
        self._make_info_label("--------", lv.color_make(100, 100, 100))

        self.status_lbl = self._make_info_label("Your turn", lv.color_make(100, 200, 100))

        self._make_info_label("You:", lv.color_make(180, 180, 180))
        self.your_move_lbl = self._make_info_label("...", lv.color_white())

        self._make_info_label("Engine:", lv.color_make(180, 180, 180))
        self.my_move_lbl = self._make_info_label("", lv.color_white())

        self._make_info_label("--------", lv.color_make(100, 100, 100))
        self._make_info_label("Arrows", lv.color_make(140, 140, 140))
        self._make_info_label("OK:Sel", lv.color_make(140, 140, 140))
        self._make_info_label("Esc:Back", lv.color_make(140, 140, 140))

        # Register input
        import input
        if input.driver and input.driver.group:
            input.driver.group.remove_all_objs()
            input.driver.group.add_obj(self.screen)
            lv.group_focus_obj(self.screen)
        self.screen.add_event_cb(self.on_key, lv.EVENT.KEY, None)

        # Draw initial board and cursor
        self.refresh_board()
        self._draw_cursor()

    def _make_info_label(self, text, color):
        lbl = lv.label(self.info_panel)
        lbl.set_text(text)
        lbl.set_style_text_font(lv.font_montserrat_14, 0)
        lbl.set_style_text_color(color, 0)
        return lbl

    def _create_piece_images(self):
        '''Create LVGL image descriptors for each piece type and color.'''
        self.piece_imgs = []
        logo_img.set_src(self.profile_images[self.profile_index])

    def refresh_board(self):
        pos = self.hist[-1]
        rows = pos.board.split()
        for row in range(8):
            for col in range(8):
                p = rows[row][col]
                lbl = self.labels[row][col]
                if p == '.':
                    #lbl.set_text("")
                    lbl.set_src(None)
                elif p.isupper():
                    #lbl.set_text(p)
                    #lbl.set_style_text_color(COLOR_WHITE_PIECE, 0)
                    if p == 'P':
                        lbl.set_src(self.wpawn)
                    elif p == 'R':
                        lbl.set_src(self.wrook)
                    elif p == 'B':
                        lbl.set_src(self.wbishop)
                    elif p == 'N':
                        lbl.set_src(self.wknight)
                    elif p == 'K':
                        lbl.set_src(self.wking)
                    elif p == 'Q':
                        lbl.set_src(self.wqueen)
                    else:
                        lbl.set_src(None)
                else:
                    #lbl.set_text(p.upper())
                    #lbl.set_style_text_color(COLOR_BLACK_PIECE, 0)
                    if p == 'p':
                        lbl.set_src(self.bpawn)
                    elif p == 'r':
                        lbl.set_src(self.brook)
                    elif p == 'b':
                        lbl.set_src(self.bbishop)
                    elif p == 'n':
                        lbl.set_src(self.bknight)
                    elif p == 'k':
                        lbl.set_src(self.bking)
                    elif p == 'q':
                        lbl.set_src(self.bqueen)
                    else:
                        lbl.set_src(None)
                lbl.set_scale(64)

    def _clear_all_borders(self):
        for row in range(8):
            for col in range(8):
                self.squares[row][col].set_style_border_width(0, 0)

    def _draw_cursor(self):
        self._clear_all_borders()
        # Re-draw source selection if active
        if self.state == STATE_SELECT_TO and self.from_row >= 0:
            sq = self.squares[self.from_row][self.from_col]
            sq.set_style_border_width(3, 0)
            sq.set_style_border_color(COLOR_SELECTED, 0)
        # Draw cursor
        sq = self.squares[self.cursor_row][self.cursor_col]
        sq.set_style_border_width(3, 0)
        sq.set_style_border_color(COLOR_CURSOR, 0)

    def _move_cursor(self, dr, dc):
        new_r = self.cursor_row + dr
        new_c = self.cursor_col + dc
        if 0 <= new_r <= 7 and 0 <= new_c <= 7:
            self.cursor_row = new_r
            self.cursor_col = new_c
            self._draw_cursor()

    def _board_index(self, row, col):
        '''Convert grid (row, col) to the 120-square board index.'''
        return 21 + row * 10 + col

    def on_key(self, e):
        key = e.get_key()

        if self.state == STATE_GAME_OVER:
            if key in (lv.KEY.ESC, lv.KEY.BACKSPACE, 14, lv.KEY.LEFT):
                self.exit()
                if self.on_exit_cb:
                    self.on_exit_cb()
            return

        if self.state == STATE_ENGINE:
            return

        # Navigation
        if key == lv.KEY.UP:
            self._move_cursor(-1, 0)
        elif key == lv.KEY.DOWN:
            self._move_cursor(1, 0)
        elif key == lv.KEY.LEFT:
            self._move_cursor(0, -1)
        elif key == lv.KEY.RIGHT:
            self._move_cursor(0, 1)

        # Select / Confirm
        elif key == lv.KEY.ENTER:
            if self.state == STATE_SELECT_FROM:
                self.from_row = self.cursor_row
                self.from_col = self.cursor_col
                self.state = STATE_SELECT_TO
                self._draw_cursor()
            elif self.state == STATE_SELECT_TO:
                self._try_player_move()

        # Cancel / Exit
        elif key == lv.KEY.ESC or key == lv.KEY.BACKSPACE or key == 14:
            if self.state == STATE_SELECT_TO:
                self.state = STATE_SELECT_FROM
                self.from_row = -1
                self.from_col = -1
                self._draw_cursor()
            else:
                self.exit()
                if self.on_exit_cb:
                    self.on_exit_cb()

    def _try_player_move(self):
        from_idx = self._board_index(self.from_row, self.from_col)
        to_idx = self._board_index(self.cursor_row, self.cursor_col)
        move = (from_idx, to_idx)

        # Check if move is legal
        legal_moves = list(self.hist[-1].gen_moves())
        if move not in legal_moves:
            # Invalid move — flash back to select-from state
            self.state = STATE_SELECT_FROM
            self.from_row = -1
            self.from_col = -1
            self.status_lbl.set_text("Invalid!")
            self.status_lbl.set_style_text_color(lv.color_make(255, 100, 100), 0)
            self._draw_cursor()
            return

        # Apply player move
        self.your_move_str = render(from_idx) + render(to_idx)
        self.your_move_lbl.set_text(self.your_move_str)
        self.my_move_lbl.set_text("...")
        self.hist.append(self.hist[-1].move(move))

        # Trim history for memory
        if len(self.hist) > 8:
            trimmed = self.hist[-8:]
            self.hist.clear()
            self.hist.extend(trimmed)

        # Show board after player move (rotated back for white's view)
        self.refresh_board_rotated()

        # Check if player delivered checkmate
        if self.hist[-1].score <= -MATE_LOWER:
            self.status_lbl.set_text("You won!")
            self.status_lbl.set_style_text_color(lv.color_make(100, 255, 100), 0)
            self.state = STATE_GAME_OVER
            self._clear_all_borders()
            return

        # Engine's turn
        self.state = STATE_ENGINE
        self.status_lbl.set_text("Thinking..")
        self.status_lbl.set_style_text_color(lv.color_make(255, 200, 100), 0)
        self.from_row = -1
        self.from_col = -1
        self._clear_all_borders()

        # Force LVGL to redraw before blocking search
        lv.refr_now(None)

        self._do_engine_move()

    def refresh_board_rotated(self):
        '''Show the board from white's perspective after applying a move.
        hist[-1] is always rotated (ready for next player = black/engine),
        so we rotate() it back to show white's view.'''
        pos = self.hist[-1].rotate()
        rows = pos.board.split()
        for row in range(8):
            for col in range(8):
                p = rows[row][col]
                lbl = self.labels[row][col]
                if p == '.':
                    #lbl.set_text("")
                    lbl.set_src(None)
                elif p.isupper():
                    #lbl.set_text(p)
                    #lbl.set_style_text_color(COLOR_WHITE_PIECE, 0)
                    if p == 'P':
                        lbl.set_src(self.wpawn)
                    elif p == 'R':
                        lbl.set_src(self.wrook)
                    elif p == 'B':
                        lbl.set_src(self.wbishop)
                    elif p == 'N':
                        lbl.set_src(self.wknight)
                    elif p == 'K':
                        lbl.set_src(self.wking)
                    elif p == 'Q':
                        lbl.set_src(self.wqueen)
                    else:
                        lbl.set_src(None)
                else:
                    #lbl.set_text(p.upper())
                    #lbl.set_style_text_color(COLOR_BLACK_PIECE, 0)
                    if p == 'p':
                        lbl.set_src(self.bpawn)
                    elif p == 'r':
                        lbl.set_src(self.brook)
                    elif p == 'b':
                        lbl.set_src(self.bbishop)
                    elif p == 'n':
                        lbl.set_src(self.bknight)
                    elif p == 'k':
                        lbl.set_src(self.bking)
                    elif p == 'q':
                        lbl.set_src(self.bqueen)
                    else:
                        lbl.set_src(None)
                lbl.set_scale(64)

    @micropython.native
    def _do_engine_move(self):
        start = time.ticks_ms()
        _depth = 0
        move = None
        score = 0
        for _d, _m, _s in self.searcher.search(self.hist[-1], self.hist):
            _depth = _d
            move = _m
            score = _s
            diff = time.ticks_diff(time.ticks_ms(), start)
            if diff > TIME_LIMIT:
                break

        if move is None:
            # Engine has no move — stalemate or error
            self.status_lbl.set_text("Stalemate")
            self.status_lbl.set_style_text_color(lv.color_make(200, 200, 100), 0)
            self.state = STATE_GAME_OVER
            return

        if score == MATE_UPPER:
            self.status_lbl.set_text("Checkmate!")
            self.status_lbl.set_style_text_color(lv.color_make(255, 100, 100), 0)

        # The engine moves from a rotated position, so back-rotate for display
        self.my_move_str = render(119-move[0]) + render(119-move[1])
        self.my_move_lbl.set_text(self.my_move_str)
        self.your_move_lbl.set_text(self.your_move_str)

        self.hist.append(self.hist[-1].move(move))
        gc.collect()

        # Trim history
        if len(self.hist) > 8:
            trimmed = self.hist[-8:]
            self.hist.clear()
            self.hist.extend(trimmed)

        # hist[-1] is now white's turn position (already rotated by move())
        # so we can display it directly
        self.refresh_board()

        # Check if engine won
        if self.hist[-1].score <= -MATE_LOWER:
            self.status_lbl.set_text("You lost!")
            self.status_lbl.set_style_text_color(lv.color_make(255, 100, 100), 0)
            self.state = STATE_GAME_OVER
            self._clear_all_borders()
            return

        # Back to player
        self.state = STATE_SELECT_FROM
        self.cursor_row = 6
        self.cursor_col = 4
        self.status_lbl.set_text("Your turn")
        self.status_lbl.set_style_text_color(lv.color_make(100, 200, 100), 0)
        self._draw_cursor()

    def exit(self):
        if self.screen:
            self.screen.delete()
            self.screen = None
