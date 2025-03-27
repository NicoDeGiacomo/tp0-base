import logging
import signal
import socket

from common.utils import store_bets, load_bets, has_won
from protocol.protocol import send_ack, read_bets_batch, read_message_type, is_load_message, is_winners_message, \
    send_winners


class Server:
    def __init__(self, port, listen_backlog, n_clients):
        self._port = port
        self._listen_backlog = listen_backlog
        self._client_socket = None
        self._running = False
        self._n_clients = int(n_clients)
        self._done_clients = set()
        self._agency_per_client = {}

    def __enter__(self):
        signal.signal(signal.SIGTERM, self.__handle_signal_sigterm)
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', self._port))
        self._server_socket.listen(self._listen_backlog)
        self._server_socket.settimeout(0.5)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._server_socket:
            self._server_socket.shutdown(socket.SHUT_RDWR)
            self._server_socket.close()
            logging.info('action: shutdown_server_socket | result: success')
        if self._client_socket:
            self._client_socket.close()
            logging.info('action: shutdown_client_socket | result: success')

    def run(self):
        self._running = True
        while self._running:
            self._client_socket = self.__accept_new_connection()
            if self._client_socket:
                ip = self._client_socket.getpeername()[0]
                self.__handle_client_connection(ip)
        logging.info('action: stop_run | result: success')

    def __handle_client_connection(self, client_ip):
        logging.info('action: handle_connection | result: in_progress')

        try:
            message_type = read_message_type(self._client_socket)

            if is_load_message(message_type):
                bets = read_bets_batch(self._client_socket)
                bets_size = len(bets)
                if bets_size == 0:
                    self._done_clients.add(client_ip)
                    logging.info(f'action: no_more_batches | result: success | ip: {client_ip}')
                    if len(self._done_clients) >= self._n_clients:
                        logging.info('action: all_clients_done | result: success')
                    return

                logging.info(f'action: batch_recibido | result: in_progress | cantidad: {bets_size}')

                self._agency_per_client[client_ip] = bets[0].agency

                store_bets(bets)
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {bets_size}')

                send_ack(self._client_socket, bets[-1])
                logging.info(f'action: send_ack | result: success | numero: {bets[-1].number}')

            elif is_winners_message(message_type):
                all_bets = load_bets()

                winners = []
                for bet in all_bets:
                    if bet.agency != self._agency_per_client[client_ip]:
                        continue
                    if has_won(bet):
                        winners.append(bet.document)

                send_winners(self._client_socket, winners)

        except OSError as e:
            logging.error(f"action: apuesta_recibida | result: fail | error: {e}")

        finally:
            self._client_socket.close()

    def __accept_new_connection(self):
        try:
            logging.info('action: accept_connections | result: in_progress')
            c, addr = self._server_socket.accept()
            logging.info(f'action: accept_connections | result: success | ip: {addr[0]}')
            return c

        except socket.timeout:
            return None

    def __handle_signal_sigterm(self, _, __):
        logging.info('action: signal_received | result: in_progress')
        self._running = False
