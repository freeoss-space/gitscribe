package git

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
)

// Client implements domain.GitClient using the git CLI.
type Client struct {
	runner Runner
}

// Runner abstracts exec.Command so tests can inject a fake.
type Runner interface {
	Run(name string, args ...string) (string, error)
	RunWithCode(name string, args ...string) (string, int, error)
}

// NewClient returns a Client that executes real git commands.
func NewClient() *Client {
	return &Client{runner: &execRunner{}}
}

// newClientWithRunner is used by tests.
func newClientWithRunner(r Runner) *Client {
	return &Client{runner: r}
}

func (c *Client) GetRepoRoot() (string, error) {
	out, err := c.runner.Run("git", "rev-parse", "--show-toplevel")
	if err != nil {
		return "", fmt.Errorf("not inside a git repository")
	}
	return strings.TrimSpace(out), nil
}

func (c *Client) HasStagedChanges() (bool, error) {
	_, code, err := c.runner.RunWithCode("git", "diff", "--cached", "--quiet")
	if err != nil && code == 0 {
		return false, err
	}
	return code != 0, nil
}

func (c *Client) GetStagedDiff() (string, error) {
	out, err := c.runner.Run("git", "diff", "--cached")
	if err != nil {
		return "", fmt.Errorf("git diff --cached: %w", err)
	}
	return out, nil
}

func (c *Client) GetBranchDiff(baseBranch string) (string, error) {
	out, err := c.runner.Run("git", "diff", baseBranch+"...HEAD")
	if err != nil {
		return "", fmt.Errorf("git diff %s...HEAD: %w", baseBranch, err)
	}
	return out, nil
}

func (c *Client) GetCurrentBranch() (string, error) {
	out, err := c.runner.Run("git", "rev-parse", "--abbrev-ref", "HEAD")
	if err != nil {
		return "", fmt.Errorf("git rev-parse HEAD: %w", err)
	}
	return strings.TrimSpace(out), nil
}

func (c *Client) GetDefaultBranch() (string, error) {
	out, err := c.runner.Run("git", "rev-parse", "--abbrev-ref", "origin/HEAD")
	if err != nil {
		return "main", nil
	}
	branch := strings.TrimSpace(out)
	if after, ok := strings.CutPrefix(branch, "origin/"); ok {
		return after, nil
	}
	return branch, nil
}

func (c *Client) Commit(message string) error {
	_, err := c.runner.Run("git", "commit", "-m", message)
	if err != nil {
		return fmt.Errorf("git commit: %w", err)
	}
	return nil
}

func (c *Client) FindPRTemplate() (string, error) {
	root, err := c.GetRepoRoot()
	if err != nil {
		return "", err
	}
	candidates := []string{
		".github/pull_request_template.md",
		".github/PULL_REQUEST_TEMPLATE.md",
		"pull_request_template.md",
		"PULL_REQUEST_TEMPLATE.md",
		"docs/pull_request_template.md",
	}
	for _, rel := range candidates {
		path := filepath.Join(root, rel)
		data, err := os.ReadFile(path)
		if err == nil {
			return string(data), nil
		}
	}
	return "", nil
}

// execRunner delegates to real os/exec.
type execRunner struct{}

func (r *execRunner) Run(name string, args ...string) (string, error) {
	out, err := exec.Command(name, args...).Output()
	return string(out), err
}

func (r *execRunner) RunWithCode(name string, args ...string) (string, int, error) {
	cmd := exec.Command(name, args...)
	out, err := cmd.Output()
	if exitErr, ok := err.(*exec.ExitError); ok {
		return string(out), exitErr.ExitCode(), nil
	}
	return string(out), 0, err
}
