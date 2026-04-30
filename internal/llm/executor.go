package llm

import (
	"bytes"
	"context"
	"fmt"
	"math"
	"os/exec"
	"strings"
	"time"

	"github.com/freeoss-space/gitscribe/internal/config"
)

const (
	maxRetries  = 3
	baseDelayMs = 1000
)

// Executor implements domain.LLMProvider using a CLI command.
// The prompt is written to the command's stdin; the result is read from stdout.
type Executor struct {
	cfg     config.LLMConfig
	cmdFunc func(ctx context.Context, name string, args ...string) Commander
}

// Commander abstracts exec.Cmd for testing.
type Commander interface {
	SetStdin(r *bytes.Reader)
	Output() ([]byte, error)
}

// New returns an Executor configured from cfg.
func New(cfg config.LLMConfig) *Executor {
	return &Executor{
		cfg: cfg,
		cmdFunc: func(ctx context.Context, name string, args ...string) Commander {
			return &realCmd{cmd: exec.CommandContext(ctx, name, args...)}
		},
	}
}

// newWithCmdFunc is used by tests to inject a fake Commander factory.
func newWithCmdFunc(cfg config.LLMConfig, fn func(ctx context.Context, name string, args ...string) Commander) *Executor {
	return &Executor{cfg: cfg, cmdFunc: fn}
}

// Generate calls the configured CLI command with the prompt on stdin.
// It retries up to maxRetries times with exponential backoff.
func (e *Executor) Generate(ctx context.Context, prompt string) (string, error) {
	timeout := time.Duration(e.cfg.TimeoutSeconds) * time.Second
	if timeout == 0 {
		timeout = 30 * time.Second
	}

	parts := strings.Fields(e.cfg.Command)
	if len(parts) == 0 {
		return "", fmt.Errorf("llm.command is not configured")
	}
	name, args := parts[0], parts[1:]

	var lastErr error
	for attempt := 0; attempt < maxRetries; attempt++ {
		if attempt > 0 {
			delay := time.Duration(math.Pow(2, float64(attempt-1))*float64(baseDelayMs)) * time.Millisecond
			select {
			case <-ctx.Done():
				return "", ctx.Err()
			case <-time.After(delay):
			}
		}

		callCtx, cancel := context.WithTimeout(ctx, timeout)
		result, err := e.call(callCtx, name, args, prompt)
		cancel()

		if err == nil {
			return result, nil
		}
		lastErr = err
	}
	return "", fmt.Errorf("llm failed after %d attempts: %w", maxRetries, lastErr)
}

func (e *Executor) call(ctx context.Context, name string, args []string, prompt string) (string, error) {
	cmd := e.cmdFunc(ctx, name, args...)
	cmd.SetStdin(bytes.NewReader([]byte(prompt)))
	out, err := cmd.Output()
	if err != nil {
		return "", err
	}
	return strings.TrimSpace(string(out)), nil
}

// realCmd wraps exec.Cmd.
type realCmd struct {
	cmd *exec.Cmd
}

func (r *realCmd) SetStdin(rb *bytes.Reader) {
	r.cmd.Stdin = rb
}

func (r *realCmd) Output() ([]byte, error) {
	return r.cmd.Output()
}
