import json
import threading
import socket
import random
from game import Game


class Server:
    def __init__(self, host='localhost', port=12345) -> None:
        self.host = host
        self.port = port
        self.clients = []
        self.games = {}
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()
        self.lock = threading.Lock()

    def handle_clients(self, conn: socket.socket, addr: tuple) -> None:
        print(f"Connected by {addr}")
        player_id = f"player{len(self.clients) + 1}"
        self.clients.append((conn, player_id))
        conn.sendall(json.dumps({"type": "CONNECTED", "player_id": player_id}).encode())

        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode())
                if message["type"] == "CREATE":
                    self.create_game(conn, player_id, message["symbol_choice"])
                elif message["type"] == "GET":
                    self.send_games_list(conn)
                elif message["type"] == "JOIN":
                    self.join_game(conn, player_id, message["game_id"])
            except Exception as e:
                print(f"Error: {e}")
                break
        conn.close()

    def create_game(self, conn: socket.socket, player_id: str, symbol_choice: str) -> None:
        with self.lock:
            random_symbol = False
            game_id = len(self.games) + 1
            if symbol_choice == "Random":
                random_symbol = True
                player_symbol = random.choice(["X", "O"])
            else:
                player_symbol = symbol_choice
            game = Game((conn, player_id, player_symbol), random_symbol)
            self.games[game_id] = game
            conn.sendall(json.dumps({"type": "CREATED", "game_id": game_id}).encode())

    def send_games_list(self, conn: socket.socket) -> None:
        with self.lock:
            availible_games = []
            for game_id, game in self.games.items():
                if len(game.players) == 1:
                    availible_games.append({"game_id": game_id, "player_symbol": "Random" if game.random_symbol else game.players["player1"][2]})
            conn.sendall(json.dumps({"type": "LIST", "games": availible_games}).encode())

    def join_game(self, conn: socket.socket, player_id: str, game_id: int) -> None:
        if game_id in self.games and len(self.games[game_id].players) == 1:
            game = self.games[game_id]
            first_player_symbol = game.players["player1"][2]
            player_symbol = "O" if first_player_symbol == "X" else "X"
            game.players["player2"] = (conn, player_id, player_symbol)
            for _, p_id, p_sym in game.players.values():
                if p_sym == "X":
                    game.now_turn = p_id
                    break
            self.start_game(game)

    def start_game(self, game: Game) -> None:
        for _, (conn, player_id, player_symbol) in game.players.items():
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
                        for player in game.players.values():
                            if player[1] == player_id:
                                game.board[row][col] = player[2]
                                break
                        winner = game.check_winners()
                        if winner:
                            for player_conn, _, _ in game.players.values():
                                player_conn.sendall(json.dumps(
                                    {
                                        "type": "END",
                                        "winner": winner,
                                        "board": game.board,
                                        "winner_id": player_id if winner != "draw" else None,
                                    }
                                ).encode())
                            break
                        for _, p_id, _ in game.players.values():
                            if p_id != game.now_turn:
                                game.now_turn = p_id
                                break
                        for player_conn, _, _ in game.players.values():
                            player_conn.sendall(json.dumps(
                                {
                                    "type": "UPDATE",
                                    "board": game.board,
                                    "now_turn": game.now_turn
                                }
                            ).encode())
            except Exception as e:
                print(f"Error: {e}")
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
