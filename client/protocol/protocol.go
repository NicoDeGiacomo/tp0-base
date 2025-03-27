package protocol

import (
	"encoding/binary"
	"fmt"
	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/domain"
	"io"
	"net"
	"strings"
	"time"
)

const defaultMaxBatchSize = 63

func BetToBytes(bet domain.Bet) ([]byte, error) {
	message := fmt.Sprintf("%d|%s|%s|%d|%s|%d", bet.Agency, bet.Name, bet.Surname, bet.DocNumber, bet.BirthDate, bet.Number)
	if len(message) > 65535 {
		return nil, fmt.Errorf("message too long")
	}
	messageSize := uint16(len(message))

	return append(
		[]byte{
			byte(messageSize >> 8),
			byte(messageSize),
		},
		[]byte(message)...,
	), nil
}

func BetsToBytes(bets []domain.Bet) ([]byte, error) {
	var bytes []byte

	for _, bet := range bets {
		betBytes, err := BetToBytes(bet)
		if err != nil {
			return nil, err
		}

		bytes = append(bytes, betBytes...)
	}

	totalBytes := len(bytes)
	sizePrefix := make([]byte, 2)
	binary.BigEndian.PutUint16(sizePrefix, uint16(totalBytes))

	return append(sizePrefix, bytes...), nil
}

func CalculateMaxBatchSize(configMaxBatchSize int) int {
	if configMaxBatchSize <= 0 {
		return defaultMaxBatchSize
	}
	return configMaxBatchSize
}

func SendFinalMessage(conn net.Conn) error {
	return SendLoadMessage(conn, []byte{0, 0})
}

func SendLoadMessage(conn net.Conn, message []byte) error {
	fullMessage := append([]byte{'L'}, message...)
	return sendMessage(conn, fullMessage)
}

func SendWinnersMessage(conn net.Conn) error {
	return sendMessage(conn, []byte{'W'})
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

func ReadAck(conn net.Conn, expectedNumber int) error {
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

func ReadWinners(conn net.Conn) ([]string, error) {
	err := conn.SetReadDeadline(time.Now().Add(20 * time.Second))
	if err != nil {
		return nil, fmt.Errorf("failed to set timeout to read winners: %v", err)
	}

	size := make([]byte, 2)
	_, err = io.ReadFull(conn, size)
	if err != nil {
		return nil, fmt.Errorf("failed to read winners size: %v", err)
	}

	winnersSize := int(binary.BigEndian.Uint16(size))
	winnersData := make([]byte, winnersSize)
	_, err = io.ReadFull(conn, winnersData)
	if err != nil {
		return nil, fmt.Errorf("failed to read winners data: %v", err)
	}

	if len(winnersData) == 0 {
		return []string{}, nil
	}

	return strings.Split(string(winnersData), "|"), nil
}
