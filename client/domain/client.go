package domain

import (
	"fmt"
	"strconv"
)

type Bet struct {
	Agency    int
	Name      string
	Surname   string
	DocNumber int
	BirthDate string
	Number    int
}

func NewBet(agency string, name string, surname string, docNumber string, birthDate string, betNumber string) (Bet, error) {
	agencyNumber, err := strconv.Atoi(agency)
	if err != nil {
		return Bet{}, fmt.Errorf("error parsing agency | %v", err)
	}

	document, err := strconv.Atoi(docNumber)
	if err != nil {
		return Bet{}, fmt.Errorf("error parsing document | %v", err)
	}

	number, err := strconv.Atoi(betNumber)
	if err != nil {
		return Bet{}, fmt.Errorf("error parsing number | %v", err)
	}

	return Bet{
		Agency:    agencyNumber,
		Name:      name,
		Surname:   surname,
		DocNumber: document,
		BirthDate: birthDate,
		Number:    number,
	}, nil
}
