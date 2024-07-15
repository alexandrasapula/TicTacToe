import pygame
import socket
import json
import threading


class Client():
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.client = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.client.connect((self.host, self.port))
        self.board = [["", "", ""], ["", "", ""], ["", "", ""]]
        self.now_turn = "player1"
        self.player = None
        self.run = True
        self.game_over = False
        self.lock = threading.Lock()

        pygame.init()
        self.width, self.heigth = 300, 300
        self.screen = pygame.display.set_mode((self.width, self.heigth))
        pygame.display.set_caption("Крестики-нолики")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.Font(None, 36)

        self.thread = threading.Thread(target=self.handle_messages)
        self.thread.start()

    def draw_board(self):
        self.screen.fill((0, 0, 0))
        for row in range(3):
            for col in range(3):
                pygame.draw.rect(self.screen, (255, 255, 255), (col*100, row*100, 100, 100), 3)
                if self.board[row][col] == "X":
                    pygame.draw.line(self.screen, (124, 252, 0), (col*100, row*100), (col*100+100, row*100+100), 5)
                    pygame.draw.line(self.screen, (124, 252, 0), (col*100+100, row*100), (col*100, row*100+100), 5)
                elif self.board[row][col] == "O":
                    pygame.draw.circle(self.screen, (0, 255, 255), (col*100+50, row*100+50), 50, 5)
        pygame.display.flip()

    def draw_text(self, text, font, color, surface, x, y):
        text_obj = font.render(text, True, color)
        text_rect = text_obj.get_rect()
        text_rect.topleft = (x, y)
        surface.blit(text_obj, text_rect)

    def handle_messages(self):
        while self.run:
            try:
                data = self.client.recv(1024)
                if data:
                    message = json.loads(data.decode())
                    if message["type"] == "START":
                        self.board = message["board"]
                        self.now_turn = message["now_turn"]
                        self.player = message["player_id"]
                    elif message["type"] == "UPDATE":
                        self.board = message["board"]
                        self.now_turn = message["now_turn"]
                    elif message["type"] == "END":
                        with self.lock:
                            self.board = message["board"]
                            winner = message["winner"]
                            self.game_over = True
                            self.screen.fill((0, 0, 0))
                            if winner == "draw":
                                self.draw_text("It's a draw", self.font, (255, 255, 255), self.screen, 50, 50)
                            else:
                                self.draw_text(f"{winner} wins", self.font, (255, 255, 255), self.screen, 50, 50)
                            pygame.display.flip()
            except Exception as e:
                print(f"Error: {e}")
                self.run = False
                break

    def loop(self):
        while self.run:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.run = False
                elif event.type == pygame.MOUSEBUTTONDOWN:
                    with self.lock:
                        if self.now_turn == self.player and not self.game_over:
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
            self.draw_board()
            self.clock.tick(60)

        pygame.quit()
        self.client.close()


if __name__ == "__main__":
    client = Client()
    client.loop()
