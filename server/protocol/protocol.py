from common.utils import Bet


def read_bet(socket):
    l = __read_from_socket(socket, 2)
    message_size = (l[0] << 8) | l[1]

    data = __read_from_socket(socket, message_size).decode("utf-8")

    fields = data.split("|")
    if len(fields) != 5:
        raise ValueError("Invalid bet received")

    return Bet(
        first_name=fields[0],
        last_name=fields[1],
        document=fields[2],
        birthdate=fields[3],
        number=fields[4],
        agency="1",
    )


def __read_from_socket(skt, size):
    data = b""
    while len(data) < size:
        n = skt.recv(size - len(data))
        if not n:
            raise ConnectionError("Cant read full message")
        data += n

    return data


def send_ack(conn, bet):
    bet_number = bet.number
    ack = bytes([
        (bet_number >> 24) & 0xFF,
        (bet_number >> 16) & 0xFF,
        (bet_number >> 8) & 0xFF,
        bet_number & 0xFF
    ])

    conn.sendall(ack)
