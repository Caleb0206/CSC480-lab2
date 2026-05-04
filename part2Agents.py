from model import (
    Location,
    Wizard,
    IceStone,
    FireStone,
    WizardMoves,
    GameAction,
    GameState,
    WizardSpells, NeutralStone, Wall,
)
from agents import WizardAgent

import z3
from z3 import (Solver, Bool, Bools, Int, Ints, Or, Not, And, Implies, Distinct, If)


class PuzzleWizard(WizardAgent):
    def straight(self, cell):
        return Or(And(cell["up"], cell["down"], Not(cell["left"]), Not(cell["right"])),
                  And(cell["left"], cell["right"], Not(cell["up"]), Not(cell["down"])))

    def turn(self, cell):
        return Or(And(cell["up"], cell["right"], Not(cell["down"]), Not(cell["left"])),
                  And(cell["up"], cell["left"], Not(cell["down"]), Not(cell["right"])),
                  And(cell["down"], cell["right"], Not(cell["up"]), Not(cell["left"])),
                  And(cell["down"], cell["left"], Not(cell["up"]), Not(cell["right"])))

    def react(self, state: GameState) -> WizardMoves:
        fire_stones = state.get_all_tile_locations(FireStone)
        ice_stones = state.get_all_tile_locations(IceStone)
        row_size, col_size = state.grid_size
        wizard_location = state.active_entity_location

        # TODO: YOUR CODE HERE
        # add wall_locations -> unusable
        wall_locations = state.get_all_tile_locations(Wall)

        # Add a planned moves storage to solve once instead of every time
        if hasattr(self, "planned") and self.planned:
            return self.planned.pop(0)

        # grid - up/down/left/right = Boolean values, rank = order for only 1 cycle/loop
        grid = [
            [{"up": Bool(f"{r}_{c}_up"),
              "down": Bool(f"{r}_{c}_down"),
              "left": Bool(f"{r}_{c}_left"),
              "right": Bool(f"{r}_{c}_right"),
              "rank": Int(f"{r}_{c}_rank")} for c in range(col_size)]
            for r in range(row_size)
        ]
        # initialize Solver
        s = Solver()
        for r in range(row_size):
            for c in range(col_size):
                cell = grid[r][c]
                # if cell is on the border of the grid, make edge booleans False
                if r == 0:
                    s.add(cell["up"] == False)
                if r == row_size - 1:
                    s.add(cell["down"] == False)
                if c == 0:
                    s.add(cell["left"] == False)
                if c == col_size - 1:
                    s.add(cell["right"] == False)

                # cell's direction boolean should equal neighbor's opposite corresponding direction boolean
                if c + 1 < col_size:
                    s.add(cell["right"] == grid[r][c + 1]["left"])
                if c - 1 >= 0:
                    s.add(cell["left"] == grid[r][c - 1]["right"])
                if r + 1 < row_size:
                    s.add(cell["down"] == grid[r + 1][c]["up"])
                if r - 1 >= 0:
                    s.add(cell["up"] == grid[r - 1][c]["down"])

                # Calculate degree: all cells need to be unvisited or gone through once (deg == 2)
                deg = (If(cell["left"], 1, 0) +
                       If(cell["right"], 1, 0) +
                       If(cell["down"], 1, 0) +
                       If(cell["up"], 1, 0))

                # Ensure the cell is not a Wall tile
                if Location(r, c) in wall_locations:
                    s.add(deg == 0)
                else:
                    # Otherwise, degree is 0 (unused), or 2 (passes through)
                    s.add(Or(deg == 0, deg == 2))

                # ensure all cells ranks
                if r == wizard_location.row and c == wizard_location.col:
                    # Starting Cell = Wizard Location, must connect back
                    s.add(deg == 2)
                    s.add(cell["rank"] == 0)  # rank = 0 because needs to end at Wizard
                else:
                    # Non-Wizard, unused rank == -1, used rank > 0
                    s.add(Implies(deg == 0, cell["rank"] == -1))
                    s.add(Implies(deg == 2, cell["rank"] > 0))

                    # if non-wizard is used, at least one neighbor has smaller rank
                    small_neighbors = []

                    # check for in-bound smaller neighbors
                    if c + 1 < col_size:
                        small_neighbors.append(And(cell["right"], grid[r][c + 1]["rank"] < cell["rank"]))
                    if c - 1 >= 0:
                        small_neighbors.append(And(cell["left"], grid[r][c - 1]["rank"] < cell["rank"]))
                    if r - 1 >= 0:
                        small_neighbors.append(And(cell["up"], grid[r - 1][c]["rank"] < cell["rank"]))
                    if r + 1 < row_size:
                        small_neighbors.append(And(cell["down"], grid[r + 1][c]["rank"] < cell["rank"]))

                    # add rule that if cell was passed through, its neighbors should be smaller ranked
                    s.add(Implies(deg == 2, Or(small_neighbors)))

        # Stones
        for fs in fire_stones:
            cell = grid[fs.row][fs.col]
            deg = If(cell["left"], 1, 0) + If(cell["right"], 1, 0) + If(cell["down"], 1, 0) + If(cell["up"], 1, 0)
            s.add(deg == 2)
            # needs to be a turn
            s.add(self.turn(cell))

            # two neighboring cells must be straight
            if fs.row - 1 >= 0:
                up = grid[fs.row - 1][fs.col]

                if fs.col + 1 < col_size:
                    right = grid[fs.row][fs.col + 1]
                    s.add(Implies(And(cell["up"], cell["right"]),
                                  And(self.straight(up), self.straight(right))))
                if fs.col - 1 >= 0:
                    left = grid[fs.row][fs.col - 1]
                    s.add(Implies(And(cell["up"], cell["left"]),
                                  And(self.straight(up), self.straight(left))))
            if fs.row + 1 < row_size:
                down = grid[fs.row + 1][fs.col]

                if fs.col + 1 < col_size:
                    right = grid[fs.row][fs.col + 1]
                    s.add(Implies(And(cell["down"], cell["right"]),
                                  And(self.straight(down), self.straight(right))))
                if fs.col - 1 >= 0:
                    left = grid[fs.row][fs.col - 1]
                    s.add(Implies(And(cell["down"], cell["left"]),
                                  And(self.straight(down), self.straight(left))))

        for ice in ice_stones:
            cell = grid[ice.row][ice.col]
            deg = If(cell["left"], 1, 0) + If(cell["right"], 1, 0) + If(cell["down"], 1, 0) + If(cell["up"], 1, 0)
            s.add(deg == 2)
            # needs to be a straight
            s.add(self.straight(cell))

            # At least 1 neighboring cell must be a turn
            if ice.row - 1 >= 0 and ice.row + 1 < row_size:
                up = grid[ice.row - 1][ice.col]
                down = grid[ice.row + 1][ice.col]

                s.add(Implies(And(cell["up"], cell["down"], Not(cell["left"]), Not(cell["right"])),
                              Or(self.turn(up), self.turn(down))))

            if ice.col - 1 >= 0 and ice.col + 1 < col_size:
                right = grid[ice.row][ice.col + 1]
                left = grid[ice.row][ice.col - 1]
                s.add(Implies(And(cell["left"], cell["right"], Not(cell["up"]), Not(cell["down"])),
                              Or(self.turn(left), self.turn(right))))

        match s.check():
            case z3.sat:
                m = s.model()

                start = wizard_location
                current_loc = start
                previous = None
                moves = []

                while True:
                    cell = grid[current_loc.row][current_loc.col]

                    # check the valid moves
                    valid = []
                    if z3.is_true(m[cell["up"]]):
                        valid.append((WizardMoves.UP, Location(current_loc.row - 1, current_loc.col)))
                    if z3.is_true(m[cell["down"]]):
                        valid.append((WizardMoves.DOWN, Location(current_loc.row + 1, current_loc.col)))
                    if z3.is_true(m[cell["left"]]):
                        valid.append((WizardMoves.LEFT, Location(current_loc.row, current_loc.col - 1)))
                    if z3.is_true(m[cell["right"]]):
                        valid.append((WizardMoves.RIGHT, Location(current_loc.row, current_loc.col + 1)))

                    chosen_move = None
                    chosen_next = None
                    for dir, next_loc in valid:
                        # do not return an already visited location
                        if next_loc != previous:
                            chosen_move = dir
                            chosen_next = next_loc
                            break
                    moves.append(chosen_move)

                    previous = current_loc
                    current_loc = chosen_next

                    if current_loc == start:
                        break;
                self.planned = moves
                return self.planned.pop(0)

            case z3.unsat:
                raise RuntimeError("Could not find a path for the Masyu map.")

        # return MASYU_1_SOLUTION.pop(0)


class SpellCastingPuzzleWizard(WizardAgent):

    def react(self, state: GameState) -> GameAction:
        fire_stones = state.get_all_tile_locations(FireStone)
        ice_stones = state.get_all_tile_locations(IceStone)
        neutral_stones = state.get_all_tile_locations(NeutralStone)

        grid_size = state.grid_size
        wizard_location = state.active_entity_location

        # TODO: YOUR CODE HERE
        return MASYU_2_SOLUTION.pop(0)


"""
Here are some reference solutions for some of the included puzzle maps you can use to help you test things
"""

MASYU_1_SOLUTION = [WizardMoves.RIGHT, WizardMoves.UP, WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.RIGHT,
                    WizardMoves.RIGHT, WizardMoves.DOWN, WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.DOWN,
                    WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.RIGHT, WizardMoves.UP, WizardMoves.UP,
                    WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.DOWN, WizardMoves.LEFT,
                    WizardMoves.LEFT, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.RIGHT,
                    WizardMoves.RIGHT, WizardMoves.UP, WizardMoves.UP, WizardMoves.RIGHT, WizardMoves.UP,
                    WizardMoves.UP, WizardMoves.UP, WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.UP,
                    WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.DOWN, WizardMoves.DOWN,
                    WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.LEFT, WizardMoves.DOWN,
                    WizardMoves.RIGHT, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.LEFT,
                    WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.UP, WizardMoves.RIGHT,
                    WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.UP, WizardMoves.LEFT, WizardMoves.LEFT,
                    WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.LEFT,
                    WizardMoves.LEFT, WizardMoves.UP, WizardMoves.UP, WizardMoves.UP, WizardMoves.RIGHT,
                    WizardMoves.RIGHT, WizardMoves.UP, WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.LEFT,
                    WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.LEFT, WizardMoves.UP,
                    WizardMoves.UP, WizardMoves.UP, WizardMoves.UP, WizardMoves.RIGHT, WizardMoves.RIGHT,
                    WizardMoves.UP, WizardMoves.UP, WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.UP]

MASYU_2_SOLUTION = [WizardMoves.RIGHT, WizardSpells.FIREBALL, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.RIGHT,
                    WizardMoves.UP, WizardMoves.UP, WizardMoves.RIGHT, WizardMoves.DOWN, WizardMoves.DOWN,
                    WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.UP,
                    WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.UP, WizardMoves.RIGHT,
                    WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.DOWN, WizardMoves.DOWN,
                    WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.DOWN,
                    WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.LEFT, WizardMoves.UP, WizardMoves.UP,
                    WizardMoves.UP, WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.DOWN, WizardMoves.RIGHT,
                    WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.UP,
                    WizardMoves.UP, WizardMoves.UP, WizardMoves.UP, WizardMoves.RIGHT, WizardMoves.UP,
                    WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.UP, WizardMoves.LEFT, WizardMoves.LEFT,
                    WizardMoves.LEFT, WizardMoves.DOWN, WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.UP,
                    WizardMoves.LEFT, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.RIGHT, WizardMoves.RIGHT,
                    WizardMoves.DOWN, WizardSpells.FREEZE, WizardMoves.DOWN, WizardMoves.DOWN, WizardMoves.DOWN,
                    WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.UP,
                    WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.RIGHT, WizardMoves.UP, WizardMoves.UP,
                    WizardMoves.LEFT, WizardMoves.LEFT, WizardMoves.DOWN, WizardMoves.LEFT, WizardMoves.UP,
                    WizardMoves.UP, WizardMoves.RIGHT, WizardMoves.UP, WizardMoves.UP, WizardMoves.UP, WizardMoves.LEFT,
                    WizardMoves.UP, WizardMoves.UP, WizardSpells.FIREBALL, WizardMoves.RIGHT]
