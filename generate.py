import sys

from crossword import *


class CrosswordCreator():

    def __init__(self, crossword):
        """
        Create new CSP crossword generate.
        """
        self.crossword = crossword
        self.domains = {
            var: self.crossword.words.copy()
            for var in self.crossword.variables
        }

    def letter_grid(self, assignment):
        """
        Return 2D array representing a given assignment.
        """
        letters = [
            [None for _ in range(self.crossword.width)]
            for _ in range(self.crossword.height)
        ]
        for variable, word in assignment.items():
            direction = variable.direction
            for k in range(len(word)):
                i = variable.i + (k if direction == Variable.DOWN else 0)
                j = variable.j + (k if direction == Variable.ACROSS else 0)
                letters[i][j] = word[k]
        return letters

    def print(self, assignment):
        """
        Print crossword assignment to the terminal.
        """
        letters = self.letter_grid(assignment)
        for i in range(self.crossword.height):
            for j in range(self.crossword.width):
                if self.crossword.structure[i][j]:
                    print(letters[i][j] or " ", end="")
                else:
                    print("█", end="")
            print()

    def save(self, assignment, filename):
        """
        Save crossword assignment to an image file.
        """
        from PIL import Image, ImageDraw, ImageFont
        cell_size = 100
        cell_border = 2
        interior_size = cell_size - 2 * cell_border
        letters = self.letter_grid(assignment)

        # Create a blank canvas
        img = Image.new(
            "RGBA",
            (self.crossword.width * cell_size,
             self.crossword.height * cell_size),
            "black"
        )
        font = ImageFont.truetype("assets/fonts/OpenSans-Regular.ttf", 80)
        draw = ImageDraw.Draw(img)

        for i in range(self.crossword.height):
            for j in range(self.crossword.width):

                rect = [
                    (j * cell_size + cell_border,
                     i * cell_size + cell_border),
                    ((j + 1) * cell_size - cell_border,
                     (i + 1) * cell_size - cell_border)
                ]
                if self.crossword.structure[i][j]:
                    draw.rectangle(rect, fill="white")
                    if letters[i][j]:
                        _, _, w, h = draw.textbbox((0, 0), letters[i][j], font=font)
                        draw.text(
                            (rect[0][0] + ((interior_size - w) / 2),
                             rect[0][1] + ((interior_size - h) / 2) - 10),
                            letters[i][j], fill="black", font=font
                        )

        img.save(filename)

    def solve(self):
        """
        Enforce node and arc consistency, and then solve the CSP.
        """
        self.enforce_node_consistency()
        self.ac3()
        return self.backtrack(dict())

    def enforce_node_consistency(self):
        """
        Update `self.domains` such that each variable is node-consistent.
        (Remove any values that are inconsistent with a variable's unary
        constraints; in this case, the length of the word.)
        """
        # For loop over the variables
        for variable in self.domains:
            values_copy = set(self.domains[variable])

            # Check the values and see if theyre node consistent(length of value = length of variable)
            for value in values_copy:       
                if len(value) != variable.length:

                    # If a value is not node consistent. remove it
                    self.domains[variable].remove(value)

    def revise(self, x, y):
        """
        Make variable `x` arc consistent with variable `y`.
        To do so, remove values from `self.domains[x]` for which there is no
        possible corresponding value for `y` in `self.domains[y]`.

        Return True if a revision was made to the domain of `x`; return
        False if no revision was made.
        """
        # Get the overlap position
        overlap = self.crossword.overlaps[x , y]

        # Create a new copy of X variable
        X_copy = set(self.domains[x])

        # Inital revised is false
        revised = False

        # If there is an overlap, compare the characters in X and Y values to see if theres a match
        if overlap is not None and len(overlap) == 2:
            overlap_X_value, overlap_Y_value = overlap

            for valueX in X_copy:
                # Flag indicating if there is a satisfying value in Y's domain
                has_satisfying_value = any(valueY[overlap_Y_value] == valueX[overlap_X_value] for valueY in self.domains[y])

                # If there is no match, remove the X value
                if not has_satisfying_value:
                    self.domains[x].remove(valueX)
                    revised = True
        
        # Return True or False
        return revised
        

    def ac3(self, arcs=None):
        """
        Update `self.domains` such that each variable is arc consistent.
        If `arcs` is None, begin with initial list of all arcs in the problem.
        Otherwise, use `arcs` as the initial list of arcs to make consistent.

        Return True if arc consistency is enforced and no domains are empty;
        return False if one or more domains end up empty.
        """

        # If arcs is none, begin with initial list of all arcs
        if arcs is None:
            arcs = []

            # get all the arcs in the crossword (all overlaps)
            for value in self.crossword.overlaps:
                if self.crossword.overlaps[value] is not None:
                    arcs.append(value)

        # While the queue is not None:
        while arcs:

            # Take a single arc from the queue (2 variables X, Y)
            x, y = arcs.pop()

            # Call the revise function that makes X, Y arc consistent and return False if there are no values in X
            if self.revise(x, y):
                if  len(self.domains[x]) == 0:
                    return False
                
                # If change was made, then gather all other arcs, Z, connected to X (except Y) and enqueue them in the queue
                for z in self.crossword.neighbors(x):
                    if z != y:
                        arcs.append((z, x))

        return True



    def assignment_complete(self, assignment):
        """
        Return True if `assignment` is complete (i.e., assigns a value to each
        crossword variable); return False otherwise.
        """

        return all(variable in assignment for variable in self.domains)

    def consistent(self, assignment):
        """
        Return True if `assignment` is consistent (i.e., words fit in crossword
        puzzle without conflicting characters); return False otherwise.
        """
        # Initialize is_consistent
        is_consistent = True

        # Check values are distinct
        for variable1 in assignment:
            for variable2 in assignment:
                if variable2 != variable1 and assignment[variable1] == assignment[variable2]:
                    is_consistent = False
                    break
            if not is_consistent:
                break

        for variable in assignment:

            # Value is the correct length
            if variable.length != len(assignment[variable]):
                is_consistent = False
                break

            # No conflict with neighbours
            for neighbor in self.crossword.neighbors(variable):
                if neighbor in assignment:
                    overlap = self.crossword.overlaps[variable, neighbor]
                    if (overlap and assignment[variable][overlap[0]] != assignment[neighbor][overlap[1]]):
                        is_consistent = False
                        break

        # Return is_consistent
        return is_consistent
    
    def order_domain_values(self, var, assignment):
        """
        Return a list of values in the domain of `var`, in order by
        the number of values they rule out for neighboring variables.
        The first value in the list, for example, should be the one
        that rules out the fewest values among the neighbors of `var`.
        """

        value_ruleout = {val: 0 for val in self.domains[var]}

        # Iterate over domains and neighbors and increase value_ruleout for every value ruled out by a variable
        for variable in self.domains[var]:
            if variable not in assignment:
                for neighbor in self.crossword.neighbors(var):
                    if neighbor not in assignment:
                        overlap = self.crossword.overlaps[var, neighbor]
                        x, y = overlap
                        for neighbor_value in self.domains[neighbor]:
                            if overlap and variable[x] != neighbor_value[y]:
                                value_ruleout[variable] += 1

        # Return list of vals sorted from fewest to most other_vals ruled out:
        return sorted(value_ruleout.keys(), key = lambda x: value_ruleout[x])


    def select_unassigned_variable(self, assignment):
        """
        Return an unassigned variable not already part of `assignment`.
        Choose the variable with the minimum number of remaining values
        in its domain. If there is a tie, choose the variable with the highest
        degree. If there is a tie, any of the tied variables are acceptable
        return values.
        """

        variable_value_length = {}

        # Iterate through the variables not present in assignment
        for variable in self.domains:
            if variable not in assignment:

                # Create tuple with domain lengths and degrees. Add to dictionary.
                variable_value_length[variable] = (len(self.domains[variable]), -len(self.crossword.neighbors(variable)))
        
        # Return the minimum value, checking domain lengths first, then degrees second, if necessary.
        return min(variable_value_length , key= lambda var: variable_value_length[var])
            

    def backtrack(self, assignment):
        """
        Using Backtracking Search, take as input a partial assignment for the
        crossword and return a complete assignment if possible to do so.

        `assignment` is a mapping from variables (keys) to words (values).

        If no assignment is possible, return None.
        """
        # If assignment is complete, return assignment
        if self.assignment_complete(assignment):
            return assignment

        # Backtrack through each assignment
        var = self.select_unassigned_variable(assignment)
        for value in self.order_domain_values(var, assignment):
            assignment[var] = value
            if self.consistent(assignment):
                result = self.backtrack(assignment)
                if result:
                    return result
            del assignment[var]
        return None

def main():

    # Check usage
    if len(sys.argv) not in [3, 4]:
        sys.exit("Usage: python generate.py structure words [output]")

    # Parse command-line arguments
    structure = sys.argv[1]
    words = sys.argv[2]
    output = sys.argv[3] if len(sys.argv) == 4 else None

    # Generate crossword
    crossword = Crossword(structure, words)
    creator = CrosswordCreator(crossword)
    assignment = creator.solve()

    # Print result
    if assignment is None:
        print("No solution.")
    else:
        creator.print(assignment)
        if output:
            creator.save(assignment, output)


if __name__ == "__main__":
    main()
