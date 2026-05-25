import socket


def is_online(host: str = "gmail.googleapis.com") -> bool:
    try:
        socket.create_connection((host, 443), timeout=2)
        return True
    except OSError:
        return False
