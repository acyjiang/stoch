import numpy as np


def create_sudoku(n):
    if int(np.sqrt(n)) ** 2 != n:
        raise ValueError("n must be a perfect square")

    def pattern(r, c):
        return (
            n // int(np.sqrt(n)) * (r % int(np.sqrt(n))) + r // int(np.sqrt(n)) + c
        ) % n

    def shuffle(s):
        return np.random.permutation(s)

    r_base = range(int(np.sqrt(n)))
    rows = [g * int(np.sqrt(n)) + r for g in shuffle(r_base) for r in shuffle(r_base)]
    cols = [g * int(np.sqrt(n)) + c for g in shuffle(r_base) for c in shuffle(r_base)]
    nums = shuffle(range(1, n + 1))

    board = np.array([[nums[pattern(r, c)] for c in cols] for r in rows])

    return board


n = 9  # Example size
sudoku_board = create_sudoku(n)
print(sudoku_board)
