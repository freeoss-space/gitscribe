package git

import (
	"errors"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

// fakeRunner implements Runner for testing.
type fakeRunner struct {
	outputs map[string]string
	codes   map[string]int
	errs    map[string]error
}

func newFake() *fakeRunner {
	return &fakeRunner{
		outputs: make(map[string]string),
		codes:   make(map[string]int),
		errs:    make(map[string]error),
	}
}

func (f *fakeRunner) key(name string, args []string) string {
	k := name
	for _, a := range args {
		k += " " + a
	}
	return k
}

func (f *fakeRunner) set(output string, code int, err error, name string, args ...string) {
	k := f.key(name, args)
	f.outputs[k] = output
	f.codes[k] = code
	f.errs[k] = err
}

func (f *fakeRunner) Run(name string, args ...string) (string, error) {
	k := f.key(name, args)
	return f.outputs[k], f.errs[k]
}

func (f *fakeRunner) RunWithCode(name string, args ...string) (string, int, error) {
	k := f.key(name, args)
	return f.outputs[k], f.codes[k], f.errs[k]
}

func TestGetRepoRoot(t *testing.T) {
	f := newFake()
	f.set("/home/user/myrepo\n", 0, nil, "git", "rev-parse", "--show-toplevel")
	c := newClientWithRunner(f)

	root, err := c.GetRepoRoot()
	require.NoError(t, err)
	assert.Equal(t, "/home/user/myrepo", root)
}

func TestGetRepoRoot_NotARepo(t *testing.T) {
	f := newFake()
	f.set("", 128, errors.New("not a git repo"), "git", "rev-parse", "--show-toplevel")
	c := newClientWithRunner(f)

	_, err := c.GetRepoRoot()
	assert.ErrorContains(t, err, "git repository")
}

func TestHasStagedChanges_True(t *testing.T) {
	f := newFake()
	f.set("", 1, nil, "git", "diff", "--cached", "--quiet")
	c := newClientWithRunner(f)

	has, err := c.HasStagedChanges()
	require.NoError(t, err)
	assert.True(t, has)
}

func TestHasStagedChanges_False(t *testing.T) {
	f := newFake()
	f.set("", 0, nil, "git", "diff", "--cached", "--quiet")
	c := newClientWithRunner(f)

	has, err := c.HasStagedChanges()
	require.NoError(t, err)
	assert.False(t, has)
}

func TestGetStagedDiff(t *testing.T) {
	f := newFake()
	f.set("diff --git a/foo.go b/foo.go\n+line", 0, nil, "git", "diff", "--cached")
	c := newClientWithRunner(f)

	diff, err := c.GetStagedDiff()
	require.NoError(t, err)
	assert.Contains(t, diff, "foo.go")
}

func TestGetBranchDiff(t *testing.T) {
	f := newFake()
	f.set("diff output", 0, nil, "git", "diff", "main...HEAD")
	c := newClientWithRunner(f)

	diff, err := c.GetBranchDiff("main")
	require.NoError(t, err)
	assert.Equal(t, "diff output", diff)
}

func TestGetCurrentBranch(t *testing.T) {
	f := newFake()
	f.set("feature/my-branch\n", 0, nil, "git", "rev-parse", "--abbrev-ref", "HEAD")
	c := newClientWithRunner(f)

	branch, err := c.GetCurrentBranch()
	require.NoError(t, err)
	assert.Equal(t, "feature/my-branch", branch)
}

func TestGetDefaultBranch_FromOrigin(t *testing.T) {
	f := newFake()
	f.set("origin/main\n", 0, nil, "git", "rev-parse", "--abbrev-ref", "origin/HEAD")
	c := newClientWithRunner(f)

	branch, err := c.GetDefaultBranch()
	require.NoError(t, err)
	assert.Equal(t, "main", branch)
}

func TestGetDefaultBranch_FallsBackToMain(t *testing.T) {
	f := newFake()
	f.set("", 128, errors.New("no origin"), "git", "rev-parse", "--abbrev-ref", "origin/HEAD")
	c := newClientWithRunner(f)

	branch, err := c.GetDefaultBranch()
	require.NoError(t, err)
	assert.Equal(t, "main", branch)
}

func TestCommit(t *testing.T) {
	f := newFake()
	f.set("[main abc1234] feat: add thing\n", 0, nil, "git", "commit", "-m", "feat: add thing")
	c := newClientWithRunner(f)

	err := c.Commit("feat: add thing")
	require.NoError(t, err)
}
