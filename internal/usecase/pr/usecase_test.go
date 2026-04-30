package pr

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
	branchDiff     string
	branchDiffErr  error
	defaultBranch  string
	prTemplate     string
	repoRoot       string
}

func (f *fakeGit) HasStagedChanges() (bool, error)       { return false, nil }
func (f *fakeGit) GetStagedDiff() (string, error)        { return "", nil }
func (f *fakeGit) GetBranchDiff(_ string) (string, error) { return f.branchDiff, f.branchDiffErr }
func (f *fakeGit) GetCurrentBranch() (string, error)     { return "feature/x", nil }
func (f *fakeGit) GetDefaultBranch() (string, error)     { return f.defaultBranch, nil }
func (f *fakeGit) Commit(_ string) error                 { return nil }
func (f *fakeGit) GetRepoRoot() (string, error)          { return f.repoRoot, nil }
func (f *fakeGit) FindPRTemplate() (string, error)       { return f.prTemplate, nil }

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

func TestGenerate_AutoDetectsBaseBranch(t *testing.T) {
	git := &fakeGit{branchDiff: "diff content", defaultBranch: "main", repoRoot: t.TempDir()}
	llm := &fakeLLM{output: "Title: Add feature\n\nAdds the feature."}
	uc := New(git, llm, defaultConfig(), tempfile.NewWithDir(t.TempDir()))

	msg, err := uc.Generate(context.Background(), "", "")
	require.NoError(t, err)
	assert.Equal(t, "Add feature", msg.Title)
}

func TestGenerate_UsesProvidedBase(t *testing.T) {
	git := &fakeGit{branchDiff: "diff content", repoRoot: t.TempDir()}
	llm := &fakeLLM{output: "Title: Fix bug\n\nFixes it."}
	uc := New(git, llm, defaultConfig(), tempfile.NewWithDir(t.TempDir()))

	msg, err := uc.Generate(context.Background(), "develop", "")
	require.NoError(t, err)
	assert.Equal(t, "Fix bug", msg.Title)
}

func TestGenerate_EmptyDiff(t *testing.T) {
	git := &fakeGit{branchDiff: ""}
	uc := New(git, &fakeLLM{}, defaultConfig(), tempfile.New())

	_, err := uc.Generate(context.Background(), "main", "")
	assert.ErrorIs(t, err, ErrEmptyDiff)
}

func TestGenerate_LLMError(t *testing.T) {
	git := &fakeGit{branchDiff: "diff"}
	llm := &fakeLLM{err: errors.New("llm down")}
	uc := New(git, llm, defaultConfig(), tempfile.New())

	_, err := uc.Generate(context.Background(), "main", "")
	assert.ErrorContains(t, err, "llm down")
}

func TestParsePRMessage_WithTitlePrefix(t *testing.T) {
	msg := parsePRMessage("Title: Add login\n\nAdds login feature.")
	assert.Equal(t, "Add login", msg.Title)
	assert.Equal(t, "Adds login feature.", msg.Body)
}

func TestParsePRMessage_WithoutTitlePrefix(t *testing.T) {
	msg := parsePRMessage("Add login\n\nAdds login feature.")
	assert.Equal(t, "Add login", msg.Title)
	assert.Equal(t, "Adds login feature.", msg.Body)
}

func TestParsePRMessage_TitleOnly(t *testing.T) {
	msg := parsePRMessage("Add feature")
	assert.Equal(t, "Add feature", msg.Title)
	assert.Empty(t, msg.Body)
}

func TestParsePRMessage_Empty(t *testing.T) {
	msg := parsePRMessage("")
	assert.Empty(t, msg.Title)
}

func TestShellQuote(t *testing.T) {
	assert.Equal(t, "'hello world'", shellQuote("hello world"))
	assert.Equal(t, `'it'"'"'s fine'`, shellQuote("it's fine"))
}

func TestGenerate_SavesDraft(t *testing.T) {
	repoRoot := t.TempDir()
	storeDir := t.TempDir()
	git := &fakeGit{branchDiff: "diff", defaultBranch: "main", repoRoot: repoRoot}
	llm := &fakeLLM{output: "Title: Draft PR\n\nbody here"}
	store := tempfile.NewWithDir(storeDir)
	uc := New(git, llm, defaultConfig(), store)

	_, err := uc.Generate(context.Background(), "", "")
	require.NoError(t, err)

	draft, err := store.LoadPR(repoRoot)
	require.NoError(t, err)
	require.NotNil(t, draft)
	assert.Equal(t, "Draft PR", draft.Title)
}

func TestGenerate_WithFeedback(t *testing.T) {
	var capturedPrompt string
	git := &fakeGit{branchDiff: "diff", defaultBranch: "main", repoRoot: t.TempDir()}
	llm := &captureLLM{output: "Title: PR\n\nbody"}
	uc := New(git, llm, defaultConfig(), tempfile.NewWithDir(t.TempDir()))

	_, err := uc.Generate(context.Background(), "", "make it concise")
	require.NoError(t, err)
	_ = capturedPrompt
	assert.Contains(t, llm.lastPrompt, "make it concise")
}

type captureLLM struct {
	output     string
	lastPrompt string
}

func (f *captureLLM) Generate(_ context.Context, p string) (string, error) {
	f.lastPrompt = p
	return f.output, nil
}

func TestGenerate_WithTemplate(t *testing.T) {
	git := &fakeGit{branchDiff: "diff", defaultBranch: "main", prTemplate: "## Summary", repoRoot: t.TempDir()}
	llm := &captureLLM{output: "Title: PR\n\nbody"}
	uc := New(git, llm, defaultConfig(), tempfile.NewWithDir(t.TempDir()))

	_, err := uc.Generate(context.Background(), "", "")
	require.NoError(t, err)
	assert.Contains(t, llm.lastPrompt, "## Summary")
}

func TestMsgString(t *testing.T) {
	msg := domain.Message{Title: "feat: x", Body: "- body"}
	assert.Equal(t, "feat: x\n\n- body", msg.String())
}
