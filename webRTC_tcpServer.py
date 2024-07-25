import socket

server = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
server.bind(("192.168.11.199", 1234))
server.listen(1)
print("Server listening on 192.168.11.199:1234")

conn, addr = server.accept()
print(f"Connection from {addr}")
while True:
    data = conn.recv(1024)
    if not data:
        break
    print(f"Received: {data.decode()}")
    conn.sendall(data)
conn.close()
