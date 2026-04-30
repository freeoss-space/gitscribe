package app

import (
	"encoding/json"
	"fmt"

	"gitscribe/internal/config"
	"gitscribe/internal/prompt"
)

type Message struct {
	Title    string `json:"title"`
	Body     string `json:"body"`
	Breaking bool   `json:"breaking"`
}

type LLMRunner interface{ Generate(prompt string) (string, error) }
type GitProvider interface{ Diff() (string, error) }

type Service struct {
	LLM    LLMRunner
	Git    GitProvider
	Config config.Config
}

func (s Service) GenerateCommit() (Message, error) {
	if s.Git == nil {
		return Message{}, fmt.Errorf("git provider not configured")
	}
	if s.LLM == nil {
		return Message{}, fmt.Errorf("LLM runner not configured")
	}
	diff, err := s.Git.Diff()
	if err != nil {
		return Message{}, err
	}
	if diff == "" {
		diff = "EMPTY_DIFF"
	}
	p := prompt.BuildCommit(s.Config, diff)
	out, err := s.LLM.Generate(p)
	if err != nil {
		return Message{}, err
	}
	msg := Message{}
	if err := json.Unmarshal([]byte(out), &msg); err != nil {
		return Message{}, fmt.Errorf("invalid llm json: %w", err)
	}
	return msg, nil
}
