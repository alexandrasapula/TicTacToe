class Game:
    def __init__(self, player1: tuple, random_symbol=False) -> None:
        self.players = {
            "player1": player1
        }
        self.board = [["", "", ""], ["", "", ""], ["", "", ""]]
        self.now_turn = None
        self.random_symbol = random_symbol

    def check_winners(self) -> str | None:
        for row in self.board:
            if row[0] == row[1] == row[2] and row[0] != "":
                return row[0]
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] and self.board[0][col] != "":
                return self.board[0][col]
        if self.board[0][0] == self.board[1][1] == self.board[2][2] and self.board[0][0] != "":
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] and self.board[0][2] != "":
            return self.board[0][2]
        for row in self.board:
            for cell in row:
                if cell == "":
                    return None
        return "draw"
