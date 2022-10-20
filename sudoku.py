#!/usr/bin/env python
#coding:utf-8

"""
Each sudoku board is represented as a dictionary with string keys and
int values.
e.g. my_board['A1'] = 8
"""
from asyncio.windows_events import NULL
import sys
from collections import deque
import copy
import time
import statistics

ROW = "ABCDEFGHI"
COL = "123456789"


def print_board(board):
    """Helper function to print board in a square."""
    print("-----------------")
    for i in ROW:
        row = ''
        for j in COL:
            row += (str(board[i + j]) + " ")
        print(row)


def board_to_string(board):
    """Helper function to convert board dictionary to string for writing."""
    ordered_vals = []
    for r in ROW:
        for c in COL:
            ordered_vals.append(str(board[r + c]))
    return ''.join(ordered_vals)

"""
Class of AC-3 that makes the Sudoku arc-consistent
"""
class AC3:
    def __init__(self, csp):
        # store the csp
        self.csp = csp

    def revise(self, Xi, Xj):
        """function to see if we need to revise the domain of position Xi (possible values)"""
        revised = False
        index = 0
        Di = self.csp.values[Xi]
        for x in Di:
            invalid = True
            for y in self.csp.values[Xj]:
                if (x != y):
                    invalid = False
            if (invalid):
                Di.pop(index) # delete x from Di
                revised = True
            else:
                index += 1
        return revised

    def solve(self):
        """function to make the csp arc-consistent, returns false if an inconsistency is found, otherwise true"""
        q = deque()
        for arc in self.csp.getArcs():
            q.append(arc)
        while not q:
            (Xi, Xj) = q.pop()
            if (self.revise(Xi, Xj)):
                if (len(self.csp.values[Xi]) == 0):
                    return False
                for Xk in self.csp.getNeighbors(Xi):
                    if (Xk != Xj): #change2
                        q.append((Xk, Xi))
        return True

"""
Class of sudoku that stores possible values for each position and possible arc pairs
"""
class Sudoku:
    def __init__(self, board):
        # store possible values for each position
        self.values = {}
        for row in ROW:
            for col in COL:
                num = board[row + col]
                if (num == 0):
                    val = [1, 2, 3, 4, 5, 6, 7, 8, 9]
                else:
                    val = [num]
                self.values[row + col] = val
        

        #store possible arc pairs
        self.arcs = {}
        for row in ROW:
            for col in COL:
                self.arcs[row + col] = self.getNeighborArcs(row, col)

    def getNeighborArcs(self, r, c):
        """function to get all possible arc pairs for one position"""
        arcs = {}
        pos = r + c
        
        # get all positions in the same row
        for col in COL:
            if (col != c):
                arcs[(pos, r + col)] = 1
        # get all positions in the same column
        for row in ROW:
            if (row != r):
                arcs[(pos, row + c)] = 1
        # get all positions in the same box
        for row in ROW:
            for col in COL:
                if (getBoxNum(row, col) == getBoxNum(r, c)):
                    if (row != r or col != c):
                        arcs[(pos, row + col)] = 1
        
        return arcs.keys()

    def getArcs(self):
        """function to get all arc pairs of the whole Sudoku"""
        res = []
        for row in ROW:
            for col in COL:
                res += self.getNeighborArcs(row, col)
        return res

    def getNeighbors(self, pos):
        """function to get all neighbors of one position (in the same row, same column, or same box)"""
        res = []
        for (x, y) in self.arcs[pos]:
            res.append(y)
        return res

    def isSolved(self):
        """function to check whether the current Sudoku is solved"""
        res = True
        for d in self.values.values():
            if (len(d) > 1):
                res = False
                break
        return res

    def board(self):
        """function that create a board of the current Sudoku"""
        res = {}
        for row in ROW:
            for col in COL:
                res[row + col] = self.values[row + col][0]
        return res

    def cloneValues(self):
        """function that clones the current status of the Sudoku"""
        values = {}
        for pos in self.values.keys():
            newValues = []
            for nextVal in self.values[pos]:
                newValues.append(nextVal)
            values[pos] = newValues
        return values

"""
Class of Backtrack that solves the Sudoku by backtracking
"""
class Backtrack:
    def __init__(self, csp, use):
        self.csp = csp
        self.unassigned = {}
        self.useAC3 = use

        for key in self.csp.values.keys():
            value = self.csp.values[key]
            self.unassigned[key] = (len(value) != 1)

    def selectUnassignedVar(self):
        """function that gets the next unassigned position 
        and its possible values using minimum remaining value heuristic"""
        minKey = None
        minValues = None
        for key in self.unassigned.keys():
            if (self.unassigned[key]):
                value = self.csp.values[key]
                if (minValues == None or len(minValues) > len(value)):
                    minKey = key
                    minValues = value
        return (minKey, minValues)

    def isConsistent(self, key, value):
        """function to check if the value is consistent with the assignment (current csp)"""
        res = True
        for Xk in self.csp.getNeighbors(key):
            values = self.csp.values[Xk]
            if (len(values) == 1 and  values[0] == value):
                res = False
        return res

    def forwardCheck(self, key, value):
        """function that forward-check the Sudoku to reduce variables domains"""
        savedData = {}
        savedData[key] = copy.copy(self.csp.values[key])
        self.unassigned[key] = False

        self.csp.values[key] = [value]
        for Xk in self.csp.getNeighbors(key):
            index = 0
            domain = self.csp.values[Xk]
            copied = False
            for val in domain:
                if (val == value):
                    if not copied:
                        savedData[Xk] = copy.copy(domain)
                        copied = True
                    domain.pop(index)  # delete val from the domain
                else:
                    index += 1
        return savedData

    def search(self, depth):
        """functio that use backtrack to solve the Sudoku"""
        if (self.csp.isSolved()):
            return True
        
        (pos, values) = self.selectUnassignedVar()

        for val in values:
            if (self.isConsistent(pos, val)):
                if self.useAC3:
                    savedValues = self.csp.cloneValues()
                    self.csp.values[pos] = [val]
                    self.unassigned[pos] = False
                    ac3 = AC3(self.csp)
                    ac3.solve()
                else:
                    savedData = self.forwardCheck(pos, val)

                if (self.search(depth + 1)):
                    return True
                
                if self.useAC3:
                    self.unassigned[pos] = True
                    self.csp.values = savedValues
                else:
                    self.unassigned[pos] = True
                    for nextPos in savedData.keys():
                        self.csp.values[nextPos] = savedData[nextPos]
        
        return False

    def solve(self):
        """function that invokes the search by backtracking, starting at depth 1"""
        return self.search(1)

def getBoxNum(r, c):
    """Helper function to get the box number of a position"""
    x = ROW.find(r) - ROW.find("A")
    y = COL.find(c) - COL.find("1")
    return x // 3 * 3 + y // 3

def backtracking(board):
    """Takes a board and returns solved board."""
    # TODO: implement this
    s = Sudoku(board)
    game = Backtrack(s, False)
    game.solve()
    return s.board()


    
    


if __name__ == '__main__':
    if len(sys.argv) > 1:
        
        # Running sudoku solver with one board $python3 sudoku.py <input_string>.
        print(sys.argv[1])
        # Parse boards to dict representation, scanning board L to R, Up to Down
        board = { ROW[r] + COL[c]: int(sys.argv[1][9*r+c])
                  for r in range(9) for c in range(9)}       
        
        solved_board = backtracking(board)
        
        # Write board to file
        out_filename = 'output.txt'
        outfile = open(out_filename, "w")
        outfile.write(board_to_string(solved_board))
        outfile.write('\n')

    else:
        # Running sudoku solver for boards in sudokus_start.txt $python3 sudoku.py
        number_of_boards=0
        mintime=float("inf")
        maxtime=0
        total=0
        lst_time=[]
        #  Read boards from source.
        src_filename = 'sudokus_start.txt'
        try:
            srcfile = open(src_filename, "r")
            sudoku_list = srcfile.read()
        except:
            print("Error reading the sudoku file %s" % src_filename)
            exit()

        # Setup output file
        out_filename = 'output.txt'
        outfile = open(out_filename, "w")

        # Solve each board using backtracking
        for line in sudoku_list.split("\n"):
            start=time.process_time()
            if len(line) < 9:
                continue

            # Parse boards to dict representation, scanning board L to R, Up to Down
            board = { ROW[r] + COL[c]: int(line[9*r+c])
                      for r in range(9) for c in range(9)}

            # Print starting board. TODO: Comment this out when timing runs.
            # print_board(board)

            # Solve with backtracking
            solved_board = backtracking(board)

            # Print solved board. TODO: Comment this out when timing runs.
            # print_board(solved_board)

            number_of_boards+=1
            total_time=time.process_time() - start
            if total_time < mintime: mintime=total_time
            if total_time > maxtime: maxtime=total_time
            lst_time.append(total_time)
            total+=total_time

            # Write board to file
            outfile.write(board_to_string(solved_board))
            outfile.write('\n')

        print("Finishing all boards in file.")
        mean=float(total/number_of_boards)
        std=statistics.stdev(lst_time)
        print(number_of_boards)
        print(mean)
        print(std)
        print(maxtime)
        print(mintime)