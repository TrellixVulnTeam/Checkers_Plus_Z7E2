import sys
from alphabeta import AlphaBeta
from gametree import GameTree
from gametree import Coord
from gametree import Move


'''
    Title: getsizeof_recursive.py
    Author: durden
    Source: https://gist.github.com/durden/0b93cfe4027761e17e69c48f9d5c4118
    Licence: MIT
        The following method 'get_size' is attributed to github user "durden"
        
    desc: Get size of Python object recursively to handle size of containers within containers

'''


# Start attribution
def get_size(obj, seen=None):
    """Recursively finds size of objects"""
    size = sys.getsizeof(obj)
    if seen is None:
        seen = set()
    obj_id = id(obj)
    if obj_id in seen:
        return 0
    # Important mark as seen *before* entering recursion to gracefully handle
    # self-referential objects
    seen.add(obj_id)
    if isinstance(obj, dict):
        size += sum([get_size(v, seen) for v in obj.values()])
        size += sum([get_size(k, seen) for k in obj.keys()])
    elif hasattr(obj, '__dict__'):
        size += get_size(obj.__dict__, seen)
    elif hasattr(obj, '__iter__') and not isinstance(obj, (str, bytes, bytearray)):
        size += sum([get_size(i, seen) for i in obj])
    return size

# End attribution


# simple obj that holds piece data
class Piece:
    def __init__(self, team):
        self.team = team
        self.king = False

    def add_widget(self, widget):
        self.widget = widget

    def king_me(self):
        self.king = True


# compound obj of pieces
class VirtualBoard:
    def __init__(self):
        self.vBoard = [[], [], [], [], [], [], [], []]
        for i in range(8):
            row = self.vBoard[i]
            for j in range(8):
                row.append(None)
            self.vBoard[i] = row
        self.a_bDiff = 0
        self.learning = None

    '''
        pre: Matrix of pieces, state
        post: Initialized virtual board
        desc: constructs a virtual board from a matrix of pieces
    '''
    def initFromState(self, state):
        self.__init__()
        for c in range(8):
            for r in range(8):
                self.vBoard[c][r] = state[c][r]

    '''
        pre: None
        post: None
        desc: adds piece at x, y,
    '''
    def add_piece_to_board(self, x, y, piece):
        self.vBoard[x][y] = piece

    '''
        pre: all param are indices
        post: Piece moved in virtual board
        desc: Move from x,y to x,y
    '''
    def move_piece(self, fromX, fromY, toX, toY):
        if abs(fromX-toX) == 2 or abs(fromY-toY) == 2:
            self.execute_jump(fromX, fromY, toX, toY)
            return
        piece = None
        piece = self.vBoard[fromY][fromX]
        self.vBoard[fromY][fromX] = None
        self.vBoard[toY][toX] = piece
        #print(str(self.vBoard.__str__()))

    '''
        pre: all param are indices
        post: None
        desc: returns true if move is valid
    '''
    def check_move(self, fromX, fromY, toX, toY, team):
        # is piece at starting coords
        isAtStart = self.vBoard[fromY][fromX] is not None
        if isAtStart:
            #print("is at start", end='|')
            pass
        else:
            return False

        # is there a piece aat ending coords
        endOpen = self.vBoard[toY][toX] is None
        #print(self.vBoard[toY][toX])
        if endOpen:
            #print("end is open", end='|')
            pass

        # is the piece yours
        correctTeam = self.vBoard[fromY][fromX].team == team
        if correctTeam:
            #print("piece is yours", end='|')
            pass

        # is valid direction to move (x +/- 1, y + 1)
        if self.vBoard[fromY][fromX].team == "red":
            validPawnMove = (fromY == toY - 1 and toX + 1 == fromX) or \
                            (fromY == toY - 1 and toX - 1 == fromX)
        else:
            validPawnMove = (fromY == toY + 1 and toX + 1 == fromX) or \
                            (fromY == toY + 1 and toX - 1 == fromX)

        if validPawnMove:
            #print("valid pawn move", end='|')
            pass

        # if king and valid king move (x +/- 1, y - 1)
        if self.vBoard[fromY][fromX].team == "red":
            validKingMove = self.vBoard[fromY][fromX].king and \
                            ((fromY - 1  == toY and fromX + 1 == toX) or
                             (fromY - 1  == toY and fromX - 1 == toX))

        else:
            #print(self.vBoard[fromY][fromX].king)
            #print((fromY + 1 == toY and (fromX + 1 == toX or fromX - 1 == toX)))
            validKingMove = self.vBoard[fromY][fromX].king and \
                            (fromY + 1 == toY and (fromX + 1 == toX or fromX - 1 == toX))

        if validKingMove:
            #print("valid king move", end='|')
            pass
        #print()
        return isAtStart and endOpen and correctTeam and (validPawnMove or validKingMove)

    '''
        pre: all param are indices
        post: None
        desc: kings piece at x,y
    '''
    def king_piece(self, x, y):
        self.vBoard[y][x].king_me()

    '''
        pre: all param are indices
        post: None
        desc: Gets king at x,y
    '''
    def get_king(self, x, y):
        if self.vBoard[y][x] is not None:
            return self.vBoard[y][x].king
        return False

    '''
        pre: all param are indices
        post: None
        desc: gets team of piece at x,y
    '''
    def get_team(self, x, y):
        if self.vBoard[y][x] is not None:
            return self.vBoard[y][x].team
        return None

    '''
        pre: valid team (one playing)
        post: None
        desc: returns possible jumps
    '''
    def check_jumps(self, team):
        possibleList = []
        for y in range(8):
            for x in range(8):
                returns = self.check_jump(x, y, team)
                if returns.pop(0):
                    #print(returns)
                    for jump in returns:
                        possibleList.append(Move(Coord(x, y), Coord(jump[0], jump[1])))
                        #print("found a jump from %d, %d to %d, %d" % (x, y, jump[0], jump[1]))

        #if len(possibleList) == 0:
            #print("no jumps found")
        #print(possibleList)
        return possibleList

    '''
        pre: indices x,y and valid team
        post: returns a list of [bool, (x,y), (x,y)]
        desc: checks if jump is valid, hard coded iteratively for speed of execution
    '''
    def check_jump(self, x, y, team):
        toReturn = [False]
        #checking jump
        if self.vBoard[y][x] is not None:
            piece = self.vBoard[y][x]

            #if correct team (player ready to move)
            if piece.team == team:

                #check for jumps from target piece
                #check to see if adj to enemy piece
                if team == "red":
                    withinRangeDown = 0 <= y - 1 < 8
                    withinRangeUp = 0 <= y + 1 < 8
                    withinRangeLeft = 0 <= x + 1 < 8
                    withinRangeRight = 0 <= x - 1 < 8
                    enemyDownLeft = enemyDownRight = enemyUpLeft = enemyUpRight = False
                    # target is up-left
                    if withinRangeUp and withinRangeLeft:
                        enemyUpLeft = self.vBoard[y + 1][x + 1] is not None and self.vBoard[y + 1][x + 1].team != team

                    # target is up-right
                    if withinRangeUp and withinRangeRight:
                        enemyUpRight = self.vBoard[y + 1][x - 1] is not None and self.vBoard[y + 1][x - 1].team != team

                    if withinRangeDown and (withinRangeLeft or withinRangeRight):
                        if piece.king and not (enemyUpLeft or enemyUpRight):
                            # target is down-left
                            if withinRangeLeft:
                                enemyDownLeft = self.vBoard[y - 1][x + 1] is not None and self.vBoard[y - 1][
                                    x + 1].team != team
                            # target is down-right
                            if withinRangeRight:
                                enemyDownRight = self.vBoard[y - 1][x - 1] is not None and self.vBoard[y - 1][
                                    x - 1].team != team

                #black
                else:
                    withinRangeUp = 0 <= y - 1 < 8
                    withinRangeDown = 0 <= y + 1 < 8
                    withinRangeLeft = 0 <= x - 1 < 8
                    withinRangeRight = 0 <= x + 1 < 8
                    enemyDownLeft = enemyDownRight = enemyUpLeft = enemyUpRight = False
                    # target is up-left
                    if withinRangeUp and withinRangeLeft:
                        enemyUpLeft = self.vBoard[y - 1][x - 1] is not None and self.vBoard[y - 1][x - 1].team != team

                    # target is up-right
                    if withinRangeUp and withinRangeRight:
                        enemyUpRight = self.vBoard[y - 1][x + 1] is not None and self.vBoard[y - 1][x + 1].team != team

                    if withinRangeDown and (withinRangeLeft or withinRangeRight):
                        if piece.king:
                            # target is down-left
                            if withinRangeLeft:
                                enemyDownLeft = self.vBoard[y + 1][x - 1] is not None and self.vBoard[y + 1][
                                    x - 1].team != team
                            # target is down-right
                            if withinRangeRight:
                                enemyDownRight = self.vBoard[y + 1][x + 1] is not None and self.vBoard[y + 1][
                                    x + 1].team != team

                # if enemy exists
                if enemyUpLeft or enemyUpRight or enemyDownLeft or enemyDownRight:
                    #print("\nJump function:\nUpLeft: ", enemyUpLeft, "\nUpRight: ", enemyUpRight, "\nDownLeft: ",enemyDownLeft, "\nDownRight: ", enemyDownRight)
                    # check if the following tile is empty

                    if team == "red":
                        #print("red piece at %d,%d has enemies" % (x,y))
                        withinRangeDown = 0 <= y - 2 < 8
                        withinRangeUp = 0 <= y + 2 < 8
                        withinRangeLeft = 0 <= x + 2 < 8
                        withinRangeRight = 0 <= x - 2 < 8
                        if enemyUpLeft:
                            if withinRangeUp and withinRangeLeft:
                                if self.vBoard[y+2][x+2] is None:
                                    toReturn[0] = True
                                    toReturn.append((x + 2, y + 2))
                                else:
                                    #print(y + 2, x + 2, " is occupied")
                                    pass

                        if enemyUpRight:
                            if withinRangeUp and withinRangeRight:
                                if self.vBoard[y+2][x-2] is None:
                                    toReturn[0] = True
                                    toReturn.append((x - 2, y + 2))
                                else:
                                    #print(y + 2, x - 2, " is occupied")
                                    pass

                        if enemyDownLeft:
                            if withinRangeDown and withinRangeLeft:
                                if self.vBoard[y-2][x+2] is None:
                                    toReturn[0] = True
                                    toReturn.append((x + 2, y - 2))
                                else:
                                    #print(y - 2, x + 2, " is occupied")
                                    pass

                        if enemyDownRight:
                            if withinRangeDown and withinRangeRight:
                                if self.vBoard[y-2][x-2] is None:
                                    toReturn[0] = True
                                    toReturn.append((x - 2, y - 2))
                                else:
                                    #print(y - 2, x - 2, " is occupied")
                                    pass

                    #black
                    else:
                        #print("black piece at %d,%d has enemies" % (x,y))
                        withinRangeUp = 0 <= y - 2 < 8
                        withinRangeDown = 0 <= y + 2 < 8
                        withinRangeLeft = 0 <= x - 2 < 8
                        withinRangeRight = 0 <= x + 2 < 8
                        if enemyUpLeft:
                            if withinRangeUp and withinRangeLeft:
                                if self.vBoard[y-2][x-2] is None:
                                    toReturn[0] = True
                                    toReturn.append((x - 2, y - 2))
                                else:
                                    #print(y-2, x-2, " is occupied")
                                    pass

                        if enemyUpRight:
                            if withinRangeUp and withinRangeRight:
                                if self.vBoard[y-2][x+2] is None:
                                    toReturn[0] = True
                                    toReturn.append((x + 2, y - 2))
                                else:
                                    #print(y-2, x+2, " is occupied")
                                    pass

                        if enemyDownLeft:
                            if withinRangeDown and withinRangeLeft:
                                if self.vBoard[y+2][x-2] is None:
                                    toReturn[0] = True
                                    toReturn.append((x - 2, y + 2))
                                else:
                                    #print(y+2, x+2, " is occupied")
                                    pass

                        if enemyDownRight:
                            if withinRangeDown and withinRangeRight:
                                if self.vBoard[y+2][x+2] is None:
                                    toReturn[0] = True
                                    toReturn.append((x + 2, y + 2))
                                else:
                                    #print(y+2, x-2, " is occupied")
                                    pass
        return toReturn

    '''
        pre: all param are indices
        post: piece is jumped from x,y to x,y
        desc: jumps piece
    '''
    def execute_jump(self, fromX, fromY, toX, toY):
        piece = self.vBoard[fromY][fromX]

        if toX > fromX:
            middleX = toX-1
        else:
            middleX = toX+1

        if toY > fromY:
            middleY = toY-1
        else:
            middleY = toY+1

        self.vBoard[middleY][middleX] = None

        self.vBoard[toY][toX] = piece
        self.vBoard[fromY][fromX] = None
        pass

    '''
        pre: all param are indices
        post: None
        desc: returns piece at x, y
    '''
    def announce_piece(self, x, y):
        if x < 8 and y < 8:
            piece = self.vBoard[int(x)][int(y)]
            if piece is not None:
                print(piece.team, " piece at %d, %d" % (x, y), "\n")
            else:
                print("No piece at %d, %d" % (x, y), "\n")

    '''
        pre: Valid team and difficulty
        post: None
        desc: returns a gamestate tree based on difficulty of ai
    '''
    def generate_game_tree(self, team, diff):
        '''
        each state should be named according to the format fromX,fromY-toX,toY
        '''
        states =[]
        moves = self.check_jumps(team)
        if len(moves) == 0:
            moves = self.generate_possible_team_moves(team)
        #print(moves)
        for move in moves:
            states.append(self.generate_game_tree_helper(move, diff, diff))

        print('size of states', get_size(states))
        print(states)
        print()
        tree = GameTree(states)
        print('size of tree', get_size(tree))
        return tree

    # TODO Mutli thread it?
    '''
        pre: called by generate_game_tree
        post: None
        desc: returns a list of possible game states assuming the move sent is made looking depth moves deep
    '''
    def generate_game_tree_helper(self, move, depth, diff, team='red'):
        newBoard = VirtualBoard()
        newBoard.initFromState(self.vBoard)
        newBoard.move_piece(move.frm.x, move.frm.y, move.to.x, move.to.y)
        #print(str(newBoard.__str__()))

        #base
        if depth == 0:
            child = (move, newBoard.eval_state(diff))
            return child

        else:
            if team == 'red':
                team = 'black'
            else:
                team = 'red'

            nextMoves = newBoard.generate_possible_team_moves(team)
            children = []
            #for every move possible for the other team
            nextJumps = newBoard.check_jumps(team)
            #print('next jumps', nextJumps)
            for jump in nextJumps:
                children.append(newBoard.generate_game_tree_helper(jump, depth - 1, diff, team))
            if len(nextJumps) == 0:
                for nextMove in nextMoves:
                    #print("next Moves", nextMoves)
                    children.append(newBoard.generate_game_tree_helper(nextMove, depth-1, diff, team))

            child = [move, children]

            return child

    '''
        pre: Valid team and difficulty
        post: format: [((fromx,fromy) , (tox,toy)) , ...]
        desc: returns a list of possible moves given a starting coord
    '''
    def generate_possible_moves(self, x, y, team):
        moves = []
        fromX = x
        fromY = y
        for toY in range(y-1, y+2):
            for toX in range(x-1, x+2):
                if 0 <= toX < 8 and 0 <= toY < 8 and self.check_move(fromX, fromY, toX, toY, team):
                    moves += [Move(Coord(fromX, fromY), Coord(toX, toY))]
        return moves

    '''
        pre: Valid team and difficulty
        post: format: [((fromx,fromy) , (tox,toy)) , ...]
        desc: returns a list of possible moves given a team
    '''
    def generate_possible_team_moves(self, team):
        moves = []
        for y in range(8):
            for x in range(8):
                piece = self.vBoard[y][x]
                if piece is not None:
                    moves += self.generate_possible_moves(x, y, team)
        return moves

    '''
        pre: int difficulty 
        post: None
        desc: Evals state
    '''
    def eval_state(self, diff):
        value = 0

        for c in self.vBoard:
            for piece in c:
                if piece is not None:
                    # 1: only piece count, favor keeping team pieces
                    # 2: count kings as more valuable
                    # 3: count the edges as stronger, 3 for edges
                    if diff > 0:
                        if piece.team == 'black':
                            value -= 6
                            if diff > 1 and piece.king:
                                value -= 4
                            if diff > 2:
                                if c == 0 or c == 7:
                                    value -= 3

                        elif piece.team == 'red':
                            value += 8
                            if diff > 1 and piece.king:
                                value += 6
                            if diff > 2:
                                if c == 0 or c == 7:
                                    value += 3

        return value

    '''
        pre: None
        post: None
        desc: returns (true, x) f game over, x is team that won
    '''
    def check_for_game_end(self):
        redLose = True
        blackLose = True
        for col in self.vBoard:
            for piece in col:
                if piece is not None:
                    if piece.team == 'red':
                        redLose = False
                    elif piece.team == 'black':
                        blackLose = False
        redCanMove = len(self.generate_possible_team_moves('red')) > 0
        blackCanMove = len(self.generate_possible_team_moves('black')) > 0

        if not redCanMove:
            redLose = True
        if not blackCanMove:
            blackLose = True

        if redLose:
            print("red no more pieces")
            if self.learning is not None:
                self.learning.reinforce_game(False)
                self.learning.save()
            return (True, 'black')

        if blackLose:
            print("black no more pieces")
            if self.learning is not None:
                self.learning.reinforce_game(True)
                self.learning.save()
            return (True, 'red')


        return (False, 'none')

    '''
        pre: None
        post: None
        desc: returns string representation
    '''
    def __str__(self):
        toReturn = ''
        for c in range(8):
            for r in range(8):
                if self.vBoard[c][r] is not None:
                    if self.vBoard[c][r].team == "red":
                        toReturn += 'r'
                    else:
                        toReturn += 'b'
                else:
                    toReturn += '+'
            toReturn += '\n'
        return toReturn

    '''
        pre: string board stored in fine named fname
        post: None
        desc: parse string version of board
    '''
    def parse_data_as_text(self, fname):
        with open(fname) as f:
            for r in range(8):
                line = f.readline().rstrip('\n')
                for c in range(len(line)):
                    char = line[c]
                    if char == 'r':
                        self.add_piece_to_board(r, c, Piece('red'))
                    elif char == 'b':
                        self.add_piece_to_board(r, c, Piece('black'))

    '''
        pre: aiDiff int
        post: None
        desc: sets diff
    '''
    def set_ai_difficulty(self, aiDiff):
        self.a_bDiff = aiDiff

    '''
        pre: None
        post: ai move made
        desc: does ai move
    '''
    def do_ai_move(self):
        if self.a_bDiff != -2:
            tree = self.generate_game_tree('red', self.a_bDiff)
            a_b = AlphaBeta(tree)
            move = a_b.alpha_beta_search(a_b.root)
            self.move_piece(move.frm.x, move.frm.y, move.to.x, move.to.y)
        else:
            move = self.learning.choose_move(self)
        return move

    '''
        pre: Learning AI model, ai
        post: None
        desc: add learning ai model
    '''
    def addLearningAi(self, ai):
        self.learning = ai

def main():
    filename = '.\\assets\\test_files\\testBoardStates.txt'
    print("hello world! " + filename)
    testBoard = VirtualBoard()
    testBoard.parse_data_as_text(filename)
    print(testBoard)
    tree = testBoard.generate_game_tree('red', 3)
    a_b = AlphaBeta(tree)
    a_b.alpha_beta_search(a_b.root)
if __name__ == "__main__":
    main()
