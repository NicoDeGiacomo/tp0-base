from common.utils import Bet


def read_bet(socket):
    l = __read_from_socket(socket, 2)
    message_size = (l[0] << 8) | l[1]

    data = __read_from_socket(socket, message_size).decode("utf-8")

    return __read_bet_from_string(data)


def read_bets_batch(socket):
    l = __read_from_socket(socket, 2)
    batch_size = (l[0] << 8) | l[1]
    if batch_size == 0:
        return []

    batch_data = __read_from_socket(socket, batch_size)

    bets = []
    index = 0
    while index < batch_size:
        bet_size = (batch_data[index] << 8) | batch_data[index + 1]
        index += 2

        bet_message = batch_data[index: index + bet_size].decode("utf-8")
        index += bet_size

        bets.append(__read_bet_from_string(bet_message))

    return bets


def __read_from_socket(skt, size):
    data = b""
    while len(data) < size:
        n = skt.recv(size - len(data))
        if not n:
            raise ConnectionError("Cant read full message")
        data += n

    return data


def __read_bet_from_string(data):
    fields = data.split("|")
    if len(fields) != 6:
        raise ValueError("Invalid bet received")

    return Bet(
        agency=fields[0],
        first_name=fields[1],
        last_name=fields[2],
        document=fields[3],
        birthdate=fields[4],
        number=fields[5],
    )


def send_ack(conn, bet):
    bet_number = bet.number
    ack = bytes([
        (bet_number >> 24) & 0xFF,
        (bet_number >> 16) & 0xFF,
        (bet_number >> 8) & 0xFF,
        bet_number & 0xFF
    ])

    conn.sendall(ack)
