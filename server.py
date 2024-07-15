import json
import threading
import socket
import pdb


class Server:
    def __init__(self, host='localhost', port=12345):
        self.host = host
        self.port = port
        self.clients = []
        self.board = [["", "", ""], ["", "", ""], ["", "", ""]]
        self.now_turn = "player1"
        self.players = []
        self.server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.server.bind((self.host, self.port))
        self.server.listen()

    def check_winners(self):
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

    def hadle_clients(self, conn, addr):
        print(f"Connected by {addr}")
        if len(self.players) < 2:
            player_id = f"player{len(self.players)+1}"
            self.players.append(player_id)
        else:
            conn.close()
            return
        conn.sendall(json.dumps(
            {
                "type": "START",
                "board": self.board,
                "now_turn": self.now_turn,
                "player_id": player_id
            }
        ).encode())
        while True:
            try:
                data = conn.recv(1024)
                if not data:
                    break
                message = json.loads(data.decode())
                if message["type"] == "MOVE" and self.now_turn == message["player"]:
                    pos = message["position"]
                    row, col = pos
                    if self.board[row][col] == "":
                        self.board[row][col] = "X" if self.now_turn == "player1" else "O"
                        winner = self.check_winners()
                        if winner:
                            for client in self.clients:
                                client.sendall(json.dumps(
                                    {
                                        "type": "END",
                                        "winner": winner,
                                        "board": self.board
                                    }
                                ).encode())
                                break
                        self.now_turn = "player1" if self.now_turn == "player2" else "player2"
                        for client in self.clients:
                            client.sendall(json.dumps(
                                {
                                    "type": "UPDATE",
                                    "board": self.board,
                                    "now_turn": self.now_turn
                                }
                            ).encode())
            except Exception:
                break
        conn.close()

    def main(self):
        print("Server OK")

        while True:
            conn, addr = self.server.accept()
            self.clients.append(conn)
            thread = threading.Thread(target=self.hadle_clients, args=(conn, addr))
            thread.start()


if __name__ == "__main__":
    server = Server()
    server.main()
