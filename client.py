import pygame
import socket
import json
import threading


class Client():
    def __init__(self, host='localhost', port=12345) -> None:
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        self.board = [["", "", ""], ["", "", ""], ["", "", ""]]
        self.now_turn = None
        self.player = None
        self.run = True
        self.game_over = False
        self.player_symbol = None
        self.winner_id = None
        self.lock = threading.Lock()
        self.winner = None
        self.timer = 0
        self.current_menu = "main"
        self.available_games = []

        pygame.init()
        self.width, self.height = 300, 400
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Крестики-нолики")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 72)
        self.font_small = pygame.font.Font(None, 32)

        self.thread = threading.Thread(target=self.handle_messages)
        self.thread.start()

    def draw_board(self) -> None:
        self.screen.fill((0, 0, 0))
        self.draw_text(f"You: {self.player_symbol}", self.font_small, (255, 255, 0), self.screen, 100, 330)
        for row in range(3):
            for col in range(3):
                pygame.draw.rect(self.screen, (255, 255, 255), (col*100, row*100, 100, 100), 3)
                if self.board[row][col] == "X":
                    pygame.draw.line(self.screen, (124, 252, 0), (col*100, row*100), (col*100+100, row*100+100), 5)
                    pygame.draw.line(self.screen, (124, 252, 0), (col*100+100, row*100), (col*100, row*100+100), 5)
                elif self.board[row][col] == "O":
                    pygame.draw.circle(self.screen, (0, 255, 255), (col*100+50, row*100+50), 50, 5)
        pygame.display.flip()

    def draw_text(self, text: str, font: pygame.font.Font, color: tuple, surface: pygame.Surface, x: int, y: int) -> None:
        text_obj = font.render(text, True, color)
        text_rect = text_obj.get_rect()
        text_rect.topleft = (x, y)
        surface.blit(text_obj, text_rect)

    def handle_messages(self) -> None:
        while self.run:
            try:
                data = self.client.recv(1024)
                if data:
                    message = json.loads(data.decode())
                    if message["type"] == "START":
                        self.board = message["board"]
                        self.now_turn = message["now_turn"]
                        self.player = message["player_id"]
                        self.player_symbol = message["player_symbol"]
                        self.current_menu = "game"
                    elif message["type"] == "UPDATE":
                        self.board = message["board"]
                        self.now_turn = message["now_turn"]
                    elif message["type"] == "END":
                        with self.lock:
                            self.board = message["board"]
                            self.winner = message["winner"]
                            self.winner_id = message["winner_id"]
                            self.game_over = True
                            self.run = False
                    elif message["type"] == "CONNECTED":
                        self.player = message["player_id"]
                    elif message["type"] == "CREATED":
                        self.current_menu = "waiting"
                    elif message["type"] == "LIST":
                        self.available_games = message["games"]
            except Exception as e:
                print(f"Error: {e}")
                self.run = False
                break

    def main_menu(self) -> None:
        self.screen.fill((0, 0, 0))
        self.draw_text("Create Game", self.font_small, (255, 255, 255), self.screen, 70, 150)
        if self.available_games:
            self.draw_text("Join Game", self.font_small, (255, 255, 255), self.screen, 70, 200)
        pygame.display.flip()

    def create_game_menu(self) -> None:
        self.screen.fill((0, 0, 0))
        self.draw_text("Choose Symbol", self.font_small, (255, 255, 255), self.screen, 50, 50)
        self.draw_text("X", self.font_small, (255, 255, 255), self.screen, 70, 150)
        self.draw_text("O", self.font_small, (255, 255, 255), self.screen, 70, 200)
        self.draw_text("Random", self.font_small, (255, 255, 255), self.screen, 70, 250)
        pygame.display.flip()

    def waiting_menu(self) -> None:
        self.screen.fill((0, 0, 0))
        self.draw_text("Waiting for player...", self.font_small, (255, 255, 255), self.screen, 50, 150)
        pygame.display.flip()

    def join_game_menu(self) -> None:
        self.screen.fill((0, 0, 0))
        self.draw_text("Join Game:", self.font_small, (255, 255, 255), self.screen, 50, 50)
        for i, game in enumerate(self.available_games):
            self.draw_text(f"{i+1}. Game: {game['player_symbol']}", self.font_small, (255, 255, 255), self.screen, 70, 150 + i*30)
        pygame.display.flip()

    def create_game(self, symbol_choice: str) -> None:
        self.client.sendall(json.dumps({
            "type": "CREATE",
            "symbol_choice": symbol_choice
        }).encode())

    def get_games_list(self) -> None:
        self.client.sendall(json.dumps({"type": "GET"}).encode())

    def join_game(self, game_id: int) -> None:
        self.client.sendall(json.dumps({"type": "JOIN", "game_id": game_id}).encode())

    def select_game(self, pos: int) -> None:
        if 0 <= pos < len(self.available_games):
            game_id = self.available_games[pos]['game_id']
            self.join_game(game_id)
            self.current_menu = "waiting"

    def loop(self) -> None:
        self.get_games_list()
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    if self.current_menu == "main":
                        x, y = pygame.mouse.get_pos()
                        if 70 <= x <= 230:
                            if 150 <= y <= 180:
                                self.current_menu = "create"
                            elif 200 <= y <= 230:
                                self.get_games_list()
                                self.current_menu = "join"
                    elif self.current_menu == "create":
                        x, y = pygame.mouse.get_pos()
                        if 70 <= x <= 230:
                            if 150 <= y <= 180:
                                self.create_game("X")
                            elif 200 <= y <= 230:
                                self.create_game("O")
                            elif 250 <= y <= 280:
                                self.create_game("Random")
                    elif self.current_menu == "join":
                        x, y = pygame.mouse.get_pos()
                        if 70 <= x <= 230:
                            pos = (y - 150) // 30
                            self.select_game(pos)
                    elif self.current_menu == "game" and not self.game_over:
                        with self.lock:
                            if self.now_turn == self.player:
                                x, y = pygame.mouse.get_pos()
                                row, col = y // 100, x // 100
                                if self.board[row][col] == "":
                                    self.client.sendall(json.dumps(
                                        {
                                            "type": "MOVE",
                                            "player": self.player,
                                            "position": [row, col]
                                        }
                                    ).encode())
            if self.current_menu == "game":
                self.draw_board()
            elif self.current_menu == "main":
                self.main_menu()
            elif self.current_menu == "create":
                self.create_game_menu()
            elif self.current_menu == "waiting":
                self.waiting_menu()
            elif self.current_menu == "join":
                self.join_game_menu()
            self.clock.tick(60)
        while self.game_over:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.game_over = False
                with self.lock:
                    if self.timer == 0:
                        self.draw_board()
                        pygame.time.delay(2000)
                    self.screen.fill((0, 0, 0))
                    if self.winner == "draw":
                        self.draw_text("It's a draw", self.font, (255, 255, 255), self.screen, 50, 100)
                    else:
                        if self.winner_id == self.player:
                            self.draw_text("You won", self.font, (255, 255, 255), self.screen, 70, 100)
                        else:
                            self.draw_text("You lose", self.font, (255, 255, 255), self.screen, 70, 100)
                    pygame.display.flip()
                    self.timer += 1
        pygame.quit()
        self.client.close()


if __name__ == "__main__":
    client = Client()
    client.loop()
