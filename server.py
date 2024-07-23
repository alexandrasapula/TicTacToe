import json
import threading
import socket
from game import Game


class Server:
    def __init__(self, host='localhost', port=12345) -> None:
        self.host = host
        self.port = port
        self.clients = []
        self.games = []
        self.waiting_players = []
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()

    def handle_clients(self, conn: socket.socket, addr: tuple) -> None:
        print(f"Connected by {addr}")
        player_id = f"player{len(self.clients)+1}"
        self.clients.append((conn, player_id))
        self.waiting_players.append((conn, player_id))
        if len(self.waiting_players) >= 2:
            player1, player2 = self.waiting_players[:2]
            self.waiting_players = self.waiting_players[2:]
            game = Game(player1, player2)
            self.games.append(game)
            self.start_game(game)

    def start_game(self, game: Game) -> None:
        for player, (conn, player_id) in game.players.items():
            player_symbol = "X" if player == "player1" else "O"
            conn.sendall(json.dumps(
                {
                    "type": "START",
                    "board": game.board,
                    "now_turn": game.now_turn,
                    "player_id": player_id,
                    "player_symbol": player_symbol
                }
            ).encode())
            threading.Thread(target=self.lopp, args=(game, conn, player_id)).start()

    def lopp(self, game: Game, conn: socket.socket, player_id: str) -> None:
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode())
                if message["type"] == "MOVE" and game.now_turn == player_id:
                    pos = message["position"]
                    row, col = pos
                    if game.board[row][col] == "":
                        game.board[row][col] = "X" if game.now_turn == game.players["player1"][1] else "O"
                        winner = game.check_winners()
                        if winner:
                            for player_conn, _ in game.players.values():
                                player_conn.sendall(json.dumps(
                                    {
                                        "type": "END",
                                        "winner": winner,
                                        "board": game.board,
                                        "winner_id": game.now_turn,
                                    }
                                ).encode())
                            break
                        game.now_turn = game.players["player1"][1] if game.now_turn == game.players["player2"][1] else game.players["player2"][1]
                        for player_conn, _ in game.players.values():
                            player_conn.sendall(json.dumps(
                                {
                                    "type": "UPDATE",
                                    "board": game.board,
                                    "now_turn": game.now_turn
                                }
                            ).encode())
            except Exception:
                break
        conn.close()

    def main(self) -> None:
        print("Server OK")
        while True:
            conn, addr = self.server.accept()
            thread = threading.Thread(target=self.handle_clients, args=(conn, addr))
            thread.start()


if __name__ == "__main__":
    server = Server()
    server.main()
