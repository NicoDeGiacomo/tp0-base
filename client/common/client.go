package common

import (
	"encoding/binary"
	"fmt"
	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/protocol"
	"github.com/op/go-logging"
	"io"
	"net"
	"os"
	"os/signal"
	"syscall"
)

var log = logging.MustGetLogger("log")

type ClientConfig struct {
	ID            string
	ServerAddress string
}

type Client struct {
	config  ClientConfig
	conn    net.Conn
	running bool
}

func NewClient(config ClientConfig) *Client {
	c := &Client{
		config:  config,
		running: true,
	}

	s := make(chan os.Signal, 1)
	signal.Notify(s, syscall.SIGTERM)
	go func() {
		<-s
		log.Info("action: signal_received | result: in_progress")
		if c.conn != nil {
			_ = c.conn.Close()
		}
		c.running = false
	}()

	return c
}

func (c *Client) createClientSocket() error {
	conn, err := net.Dial("tcp", c.config.ServerAddress)
	if err != nil {
		return fmt.Errorf("failed to connect to server %s | %v", c.config.ServerAddress, err)
	}
	c.conn = conn
	return nil
}

func (c *Client) StartClient() {
	if !c.running {
		return
	}

	betsLoader, err := NewBetsLoader(c.config.ID)
	if err != nil {
		log.Errorf("action: create_bets_loader | result: fail | error: %v", err)
		return
	}
	defer betsLoader.Close()

	bets, err := betsLoader.NextChunk(1)
	if err != nil {
		log.Errorf("action: load_bets | result: fail | error: %v", err)
		return
	}

	bet := bets[0]

	err = c.createClientSocket()
	if err != nil {
		log.Errorf("action: create_socket | result: fail | error: %v", err)
		return
	}

	message, err := protocol.BetToBytes(bet)
	if err != nil {
		log.Errorf("action: create_message | result: fail | error: %v", err)
		return
	}

	err = sendMessage(c.conn, message)
	if err != nil {
		log.Errorf("action: send_message | result: fail | error: %v", err)
		return
	}

	err = readAck(c.conn, bet.Number)
	if err != nil {
		log.Errorf("action: read_ack | result: fail | error: %v", err)
		return
	}

	err = c.conn.Close()
	if err != nil {
		log.Errorf("action: close_socket | result: fail | error: %v", err)
		return
	}

	log.Infof("action: apuesta_enviada | result: success | dni: %d | numero: %d", bet.DocNumber, bet.Number)

	log.Infof("action: loop_finished | result: success")
}

func sendMessage(conn net.Conn, message []byte) error {
	sent := 0

	for sent < len(message) {
		n, err := conn.Write(message[sent:])
		if err != nil {
			return fmt.Errorf("failed to send message")
		}
		sent += n
	}

	return nil
}

func readAck(conn net.Conn, expectedNumber int) error {
	ackBytes := make([]byte, 4)

	_, err := io.ReadFull(conn, ackBytes)
	if err != nil {
		return fmt.Errorf("failed to read full ack: %v", err)
	}

	ack := binary.BigEndian.Uint32(ackBytes)
	if int(ack) != expectedNumber {
		return fmt.Errorf("ack number does not match")
	}

	return nil
}
