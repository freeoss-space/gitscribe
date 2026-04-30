package domain

import "context"

// LLMProvider generates text from a prompt.
type LLMProvider interface {
	Generate(ctx context.Context, prompt string) (string, error)
}
