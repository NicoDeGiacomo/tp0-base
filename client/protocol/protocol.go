package protocol

import (
	"encoding/binary"
	"fmt"
	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/domain"
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
