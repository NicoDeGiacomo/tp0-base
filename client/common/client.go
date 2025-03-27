package common

import (
	"fmt"
	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/protocol"
	"github.com/op/go-logging"
	"net"
	"os"
	"os/signal"
	"syscall"
	"time"
)

var log = logging.MustGetLogger("log")

type ClientConfig struct {
	ID            string
	ServerAddress string
	BatchSize     int
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
	retries := 5
	for retries > 0 {
		conn, err := net.Dial("tcp", c.config.ServerAddress)
		if err != nil {
			retries--
			time.Sleep(2 * time.Second)
			continue
		}
		c.conn = conn
		return nil
	}

	return fmt.Errorf("failed to connect to server %s", c.config.ServerAddress)
}

func (c *Client) StartClient() {
	if !c.running {
		return
	}

	size := protocol.CalculateMaxBatchSize(c.config.BatchSize)
	betsLoader, err := NewBetsLoader(c.config.ID)
	if err != nil {
		log.Errorf("action: create_bets_loader | result: fail | error: %v", err)
		return
	}
	defer betsLoader.Close()

	for c.running {
		bets, err := betsLoader.NextChunk(size)
		if err != nil {
			log.Errorf("action: load_bets | result: fail | error: %v", err)
			return
		}
		betsLen := len(bets)

		err = c.createClientSocket()
		if err != nil {
			log.Errorf("action: create_socket | result: fail | error: %v", err)
			return
		}

		if betsLen == 0 {
			err = protocol.SendFinalMessage(c.conn)
			log.Infof("action: done_sending_bets | result: success")
			break
		}

		message, err := protocol.BetsToBytes(bets)
		if err != nil {
			log.Errorf("action: create_message | result: fail | error: %v", err)
			return
		}

		err = protocol.SendLoadMessage(c.conn, message)
		if err != nil {
			log.Errorf("action: send_message | result: fail | error: %v", err)
			return
		}

		err = protocol.ReadAck(c.conn, bets[betsLen-1].Number)
		if err != nil {
			log.Errorf("action: read_ack | result: fail | error: %v", err)
			return
		}

		err = c.conn.Close()
		if err != nil {
			log.Errorf("action: close_socket | result: fail | error: %v", err)
			return
		}

		log.Infof("action: apuesta_enviada | result: success | cantidad: %d | ultima: %d", betsLen, bets[betsLen-1].Number)
	}

	c.CheckForWinners()

	logging.Reset()
	time.Sleep(10 * time.Second)

	log.Infof("action: exit | result: success")
}

func (c *Client) CheckForWinners() {
	retries := 5
	for retries > 0 {
		err := c.createClientSocket()
		if err != nil {
			log.Errorf("action: winners_create_socket | result: fail | error: %v", err)
			return
		}

		err = protocol.SendWinnersMessage(c.conn)
		if err != nil {
			retries -= 1
			time.Sleep(2 * time.Second)
			continue
		}

		winners, err := protocol.ReadWinners(c.conn)
		if err != nil {
			retries -= 1
			time.Sleep(2 * time.Second)
			continue
		}

		err = c.conn.Close()
		if err != nil {
			log.Errorf("action: winners_close_socket | result: fail | error: %v", err)
			return
		}

		log.Infof("action: consulta_ganadores | result: success | cant_ganadores: %d | ganadores: %v", len(winners), winners)
		return
	}

	log.Errorf("action: read_winners | result: fail")
}
