import socket
import logging
import signal


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
        """
        Dummy Server loop

        Server that accept a new connections and establishes a
        communication with a client. After client with communucation
        finishes, servers starts to accept new connections again
        """
        self._running = True
        while self._running:
            self._client_socket = self.__accept_new_connection()
            if self._client_socket:
                self.__handle_client_connection()

    def __handle_client_connection(self):
        """
        Read message from a specific client socket and closes the socket

        If a problem arises in the communication with the client, the
        client socket will also be closed
        """
        logging.info('action: handle_connection | result: in_progress')
        try:
            # TODO: Modify the receive to avoid short-reads
            msg = self._client_socket.recv(1024).rstrip().decode('utf-8')
            addr = self._client_socket.getpeername()
            logging.info(f'action: receive_message | result: success | ip: {addr[0]} | msg: {msg}')
            # TODO: Modify the send to avoid short-writes
            self._client_socket.send("{}\n".format(msg).encode('utf-8'))
        except OSError as e:
            logging.error("action: receive_message | result: fail | error: {e}")
        finally:
            self._client_socket.close()

    def __accept_new_connection(self):
        """
        Accept new connections

        Function blocks until a connection to a client is made.
        Then connection created is printed and returned
        """

        # Connection arrived
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
