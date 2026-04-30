package commit

import (
	"context"
	"errors"
	"testing"

	"github.com/freeoss-space/gitscribe/internal/config"
	"github.com/freeoss-space/gitscribe/internal/domain"
	"github.com/freeoss-space/gitscribe/internal/tempfile"
	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// ---- fakes ----

type fakeGit struct {
	hasStaged    bool
	stagedDiff   string
	stagedErr    error
	commitCalled string
	repoRoot     string
}

func (f *fakeGit) HasStagedChanges() (bool, error) { return f.hasStaged, nil }
func (f *fakeGit) GetStagedDiff() (string, error)  { return f.stagedDiff, f.stagedErr }
func (f *fakeGit) GetBranchDiff(string) (string, error) {
	return "", nil
}
func (f *fakeGit) GetCurrentBranch() (string, error)  { return "main", nil }
func (f *fakeGit) GetDefaultBranch() (string, error)   { return "main", nil }
func (f *fakeGit) Commit(msg string) error             { f.commitCalled = msg; return nil }
func (f *fakeGit) GetRepoRoot() (string, error)        { return f.repoRoot, nil }
func (f *fakeGit) FindPRTemplate() (string, error)     { return "", nil }

type fakeLLM struct {
	output string
	err    error
}

func (f *fakeLLM) Generate(_ context.Context, _ string) (string, error) {
	return f.output, f.err
}

func defaultConfig() *config.Config {
	c := config.Defaults()
	return &c
}

// ---- tests ----

func TestGenerate_NoStagedChanges(t *testing.T) {
	git := &fakeGit{hasStaged: false}
	llm := &fakeLLM{}
	uc := New(git, llm, defaultConfig(), tempfile.New())

	_, err := uc.Generate(context.Background(), "")
	assert.ErrorIs(t, err, ErrNoStagedChanges)
}

func TestGenerate_Success(t *testing.T) {
	git := &fakeGit{hasStaged: true, stagedDiff: "diff content", repoRoot: t.TempDir()}
	llm := &fakeLLM{output: "feat: add thing\n\n- does something useful"}
	uc := New(git, llm, defaultConfig(), tempfile.NewWithDir(t.TempDir()))

	msg, err := uc.Generate(context.Background(), "")
	require.NoError(t, err)
	assert.Equal(t, "feat: add thing", msg.Title)
	assert.Equal(t, "- does something useful", msg.Body)
}

func TestGenerate_EmptyDiff_FallbackMessage(t *testing.T) {
	git := &fakeGit{hasStaged: true, stagedDiff: ""}
	uc := New(git, &fakeLLM{}, defaultConfig(), tempfile.New())

	msg, err := uc.Generate(context.Background(), "")
	require.NoError(t, err)
	assert.Equal(t, "chore: empty diff", msg.Title)
}

func TestGenerate_LLMError(t *testing.T) {
	git := &fakeGit{hasStaged: true, stagedDiff: "diff"}
	llm := &fakeLLM{err: errors.New("llm unavailable")}
	uc := New(git, llm, defaultConfig(), tempfile.New())

	_, err := uc.Generate(context.Background(), "")
	assert.ErrorContains(t, err, "llm unavailable")
}

func TestCommit_CallsGit(t *testing.T) {
	git := &fakeGit{repoRoot: t.TempDir()}
	uc := New(git, &fakeLLM{}, defaultConfig(), tempfile.NewWithDir(t.TempDir()))

	msg := domain.Message{Title: "feat: test", Body: "- body line"}
	err := uc.Commit(context.Background(), msg)
	require.NoError(t, err)
	assert.Equal(t, "feat: test\n\n- body line", git.commitCalled)
}

func TestParseMessage_TitleOnly(t *testing.T) {
	msg := parseMessage("feat: add thing")
	assert.Equal(t, "feat: add thing", msg.Title)
	assert.Empty(t, msg.Body)
}

func TestParseMessage_TitleAndBody(t *testing.T) {
	msg := parseMessage("feat: add thing\n\n- does x\n- does y")
	assert.Equal(t, "feat: add thing", msg.Title)
	assert.Equal(t, "- does x\n- does y", msg.Body)
}

func TestParseMessage_Empty(t *testing.T) {
	msg := parseMessage("")
	assert.Empty(t, msg.Title)
}
