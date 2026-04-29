from model import (
    Location,
    Wizard,
    IceStone,
    FireStone,
    WizardMoves,
    GameAction,
    GameState,
    WizardSpells, NeutralStone,
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
        grid_size = state.grid_size
        wizard_location = state.active_entity_location

        # TODO: YOUR CODE HERE
        grid = [
            [{"up": Bool(f"{r}_{c}_up"),
              "down": Bool(f"{r}_{c}_down"),
              "left": Bool(f"{r}_{c}_left"),
              "right": Bool(f"{r}_{c}_right")} for c in range(grid_size)]
            for r in range(grid_size)
        ]

        s = Solver()
        for r in range(grid_size):
            for c in range(grid_size):
                cell = grid[r][c]

                if r == 0:
                    s.add(cell["up"] == False)
                if r == grid_size - 1:
                    s.add(cell["down"] == False)
                if c == 0:
                    s.add(cell["left"] == False)
                if c == grid_size - 1:
                    s.add(cell["right"] == False)

                if c + 1 < grid_size:
                    s.add(cell["right"] == grid[r][c + 1]["left"])
                if c - 1 >= 0:
                    s.add(cell["left"] == grid[r][c - 1]["right"])
                if r + 1 < grid_size:
                    s.add(cell["down"] == grid[r + 1][c]["up"])
                if r - 1 >= 0:
                    s.add(cell["up"] == grid[r - 1][c]["down"])

                # ensure all cells need to be unvisited or gone through once (deg == 2)
                deg = If(cell["left"], 1, 0) + If(cell["right"], 1, 0) + If(cell["down"], 1, 0) + If(cell["up"], 1, 0)
                s.add(Or(deg == 0, deg == 2))

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

                if fs.col + 1 < grid_size:
                    right = grid[fs.row][fs.col + 1]
                    s.add(Implies(And(cell["up"], cell["right"]),
                                  And(self.straight(up), self.straight(right))))
                if fs.col - 1 >= 0:
                    left = grid[fs.row][fs.col - 1]
                    s.add(Implies(And(cell["up"], cell["left"]),
                                  And(self.straight(up), self.straight(left))))
            if fs.row + 1 < grid_size:
                down = grid[fs.row + 1][fs.col]

                if fs.col + 1 < grid_size:
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

            # Either two neighboring cells must be a turn
            if ice.row - 1 >= 0 and ice.row + 1 < grid_size:
                up = grid[ice.row - 1][ice.col]
                down = grid[ice.row + 1][ice.col]

                s.add(Implies(And(cell["up"], cell["down"], Not(cell["left"]), Not(cell["right"])),
                              Or(self.turn(up), self.turn(down))))

            if ice.col - 1 >= 0 and ice.col + 1 < grid_size:
                right = grid[ice.row][ice.col + 1]
                left = grid[ice.row][ice.col - 1]
                s.add(Implies(And(cell["left"], cell["right"], Not(cell["up"]), Not(cell["down"])),
                              Or(self.turn(left), self.turn(right))))

        return MASYU_1_SOLUTION.pop(0)


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
