package protocol

import (
	"fmt"
	"github.com/7574-sistemas-distribuidos/docker-compose-init/client/domain"
)

func BetToBytes(bet domain.Bet) ([]byte, error) {
	message := fmt.Sprintf("%s|%s|%d|%s|%d", bet.Name, bet.Surname, bet.DocNumber, bet.BirthDate, bet.Number)
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
