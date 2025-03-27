import logging
import multiprocessing
import signal
import socket

from common.utils import store_bets, load_bets, has_won
from protocol.protocol import send_ack, read_bets_batch, read_message_type, is_load_message, is_winners_message, \
    send_winners


class Server:
    def __init__(self, port, listen_backlog, n_clients):
        self._port = port
        self._listen_backlog = listen_backlog
        self._server_socket = None
        self._running = False
        self._n_clients = int(n_clients)

        self._lock = multiprocessing.Lock()
        self._manager = multiprocessing.Manager()
        self._done_clients = self._manager.dict()
        self._agency_per_client = self._manager.dict()

        self._winners_cache = self._manager.dict()
        self._winners_ready = multiprocessing.Event()

        self._processes = []

    def __enter__(self):
        signal.signal(signal.SIGTERM, self.__handle_signal_sigterm)
        self._server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self._server_socket.bind(('', self._port))
        self._server_socket.listen(self._listen_backlog)
        self._server_socket.settimeout(1)
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        if self._server_socket:
            self._server_socket.shutdown(socket.SHUT_RDWR)
            self._server_socket.close()
            logging.info('action: shutdown_server_socket | result: success')
        for process in self._processes:
            if process.is_alive():
                process.terminate()
                process.join()

    def run(self):
        self._running = True
        while self._running:
            client_socket = self.__accept_new_connection()
            if client_socket:
                process = multiprocessing.Process(
                    target=self.__handle_client_connection, args=(client_socket,)
                )
                process.start()
                self._processes.append(process)
        logging.info('action: stop_run | result: success')

    def __handle_client_connection(self, client_socket):
        logging.info('action: handle_connection | result: in_progress')
        client_ip = client_socket.getpeername()[0]

        try:
            message_type = read_message_type(client_socket)

            if is_load_message(message_type):
                bets = read_bets_batch(client_socket)
                bets_size = len(bets)
                if bets_size == 0:
                    self._done_clients[client_ip] = True
                    logging.info(f'action: no_more_batches | result: success | ip: {client_ip}')
                    if len(self._done_clients) >= self._n_clients:
                        logging.info('action: all_clients_done | result: success')
                        self.__precompute_winners()
                    return

                logging.info(f'action: batch_recibido | result: in_progress | cantidad: {bets_size}')

                self._agency_per_client[client_ip] = bets[0].agency

                with self._lock:
                    store_bets(bets)
                logging.info(f'action: apuesta_recibida | result: success | cantidad: {bets_size}')

                send_ack(client_socket, bets[-1])
                logging.info(f'action: send_ack | result: success | numero: {bets[-1].number}')

            elif is_winners_message(message_type):
                if self._winners_ready.is_set():
                    agency = self._agency_per_client.get(client_ip, None)
                    winners = self._winners_cache.get(agency, [])

                    send_winners(client_socket, winners)
                    logging.info(f'action: send_winners | result: success | agency: {agency} | winners: {winners} | ip: {client_ip}')

        except OSError as e:
            logging.error(f"action: apuesta_recibida | result: fail | error: {e}")

        finally:
            client_socket.close()

    def __precompute_winners(self):
        logging.info("action: precompute_winners | result: in_progress")
        with self._lock:
            all_bets = load_bets()
            winners_by_agency = {}
            for bet in all_bets:
                if has_won(bet):
                    if bet.agency not in winners_by_agency:
                        winners_by_agency[bet.agency] = []
                    winners_by_agency[bet.agency].append(bet.document)
            self._winners_cache.update(winners_by_agency)
            self._winners_ready.set()
        logging.info(f"action: precompute_winners | result: success | winners_count: {len(self._winners_cache)}")

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
