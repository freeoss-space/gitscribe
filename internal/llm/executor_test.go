package llm

import (
	"bytes"
	"context"
	"errors"
	"testing"

	"github.com/freeoss-space/gitscribe/internal/config"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

type fakeCmd struct {
	output []byte
	err    error
	stdin  string
}

func (f *fakeCmd) SetStdin(r *bytes.Reader) {
	buf := new(bytes.Buffer)
	_, _ = buf.ReadFrom(r)
	f.stdin = buf.String()
}

func (f *fakeCmd) Output() ([]byte, error) {
	return f.output, f.err
}

func makeFakeFactory(output string, err error) func(ctx context.Context, name string, args ...string) Commander {
	return func(_ context.Context, _ string, _ ...string) Commander {
		return &fakeCmd{output: []byte(output), err: err}
	}
}

func TestExecutor_Generate_Success(t *testing.T) {
	cfg := config.LLMConfig{Command: "echo", TimeoutSeconds: 5}
	e := newWithCmdFunc(cfg, makeFakeFactory("feat: add login\n\n- adds session handling", nil))

	result, err := e.Generate(context.Background(), "generate a commit message")
	require.NoError(t, err)
	assert.Equal(t, "feat: add login\n\n- adds session handling", result)
}

func TestExecutor_Generate_ReceivesPromptOnStdin(t *testing.T) {
	var capturedStdin string
	cfg := config.LLMConfig{Command: "myllm", TimeoutSeconds: 5}
	fn := func(_ context.Context, _ string, _ ...string) Commander {
		f := &fakeCmd{output: []byte("result")}
		capturedStdin = "" // will be set via SetStdin
		return &stdinCapture{fakeCmd: f, capture: &capturedStdin}
	}
	e := newWithCmdFunc(cfg, fn)
	_, err := e.Generate(context.Background(), "my prompt text")
	require.NoError(t, err)
	assert.Equal(t, "my prompt text", capturedStdin)
}

type stdinCapture struct {
	*fakeCmd
	capture *string
}

func (s *stdinCapture) SetStdin(r *bytes.Reader) {
	buf := new(bytes.Buffer)
	_, _ = buf.ReadFrom(r)
	*s.capture = buf.String()
}

func TestExecutor_Generate_RetriesOnFailure(t *testing.T) {
	attempts := 0
	cfg := config.LLMConfig{Command: "myllm", TimeoutSeconds: 1}
	fn := func(_ context.Context, _ string, _ ...string) Commander {
		attempts++
		if attempts < maxRetries {
			return &fakeCmd{err: errors.New("transient error")}
		}
		return &fakeCmd{output: []byte("success")}
	}
	e := newWithCmdFunc(cfg, fn)
	// Override delays to speed up the test.
	result, err := e.Generate(context.Background(), "prompt")
	require.NoError(t, err)
	assert.Equal(t, "success", result)
	assert.Equal(t, maxRetries, attempts)
}

func TestExecutor_Generate_FailsAfterMaxRetries(t *testing.T) {
	cfg := config.LLMConfig{Command: "myllm", TimeoutSeconds: 1}
	e := newWithCmdFunc(cfg, makeFakeFactory("", errors.New("permanent error")))

	_, err := e.Generate(context.Background(), "prompt")
	assert.ErrorContains(t, err, "permanent error")
}

func TestExecutor_Generate_EmptyCommand(t *testing.T) {
	cfg := config.LLMConfig{Command: "", TimeoutSeconds: 5}
	e := New(cfg)
	_, err := e.Generate(context.Background(), "prompt")
	assert.ErrorContains(t, err, "not configured")
}

func TestExecutor_Generate_ContextCancellation(t *testing.T) {
	cfg := config.LLMConfig{Command: "myllm", TimeoutSeconds: 5}
	e := newWithCmdFunc(cfg, makeFakeFactory("", errors.New("some error")))
	ctx, cancel := context.WithCancel(context.Background())
	cancel()

	_, err := e.Generate(ctx, "prompt")
	assert.Error(t, err)
}
