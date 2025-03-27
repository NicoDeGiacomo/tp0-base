import socket
import logging
import signal

from common.utils import store_bets
from protocol.protocol import read_bet, send_ack


class Server:
    def __init__(self, port, listen_backlog):
        self._port = port
        self._listen_backlog = listen_backlog
        self._client_socket = None
        self._running = False

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
                self.__handle_client_connection()
        logging.info('action: stop_run | result: success')

    def __handle_client_connection(self):
        logging.info('action: handle_connection | result: in_progress')

        try:
            bet = read_bet(self._client_socket)
            logging.info(f'action: received_bet | result: success | bet: {bet}')

            store_bets([bet])
            logging.info(f'action: apuesta_almacenada | result: success | dni: {bet.document} | numero: {bet.number}')

            send_ack(self._client_socket, bet)
            logging.info(f'action: send_ack | result: success | numero: {bet.number}')

        except OSError as e:
            logging.error(f"action: receive_message | result: fail | error: {e}")

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
