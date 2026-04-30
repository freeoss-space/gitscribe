package pr

import (
	"context"
	"fmt"
	"os/exec"
	"strings"

	"github.com/freeoss-space/gitscribe/internal/config"
	"github.com/freeoss-space/gitscribe/internal/domain"
	"github.com/freeoss-space/gitscribe/internal/prompt"
	"github.com/freeoss-space/gitscribe/internal/tempfile"
)

// UseCase orchestrates PR description generation.
type UseCase struct {
	git     domain.GitClient
	llm     domain.LLMProvider
	builder *prompt.Builder
	store   *tempfile.Store
	cfg     *config.Config
}

// New returns a configured UseCase.
func New(git domain.GitClient, llm domain.LLMProvider, cfg *config.Config, store *tempfile.Store) *UseCase {
	return &UseCase{
		git:     git,
		llm:     llm,
		builder: prompt.New(),
		store:   store,
		cfg:     cfg,
	}
}

// Generate produces a PR message comparing HEAD against baseBranch.
// If baseBranch is empty, it is auto-detected from origin/HEAD.
// feedback is an optional user correction for the previous attempt.
func (uc *UseCase) Generate(ctx context.Context, baseBranch, feedback string) (domain.Message, error) {
	if baseBranch == "" {
		detected, err := uc.git.GetDefaultBranch()
		if err != nil {
			detected = "main"
		}
		baseBranch = detected
	}

	diff, err := uc.git.GetBranchDiff(baseBranch)
	if err != nil {
		return domain.Message{}, fmt.Errorf("get branch diff: %w", err)
	}
	if diff == "" {
		return domain.Message{}, ErrEmptyDiff
	}

	prTemplate, _ := uc.git.FindPRTemplate()

	p := uc.builder.BuildPR(uc.cfg, diff, prTemplate, feedback)
	raw, err := uc.llm.Generate(ctx, p)
	if err != nil {
		return domain.Message{}, fmt.Errorf("generate: %w", err)
	}

	msg := parsePRMessage(raw)

	repoRoot, _ := uc.git.GetRepoRoot()
	_ = uc.store.SavePR(repoRoot, tempfile.Draft{Title: msg.Title, Body: msg.Body})

	return msg, nil
}

// CreateGitHubPR opens a GitHub pull request using the gh CLI.
func (uc *UseCase) CreateGitHubPR(msg domain.Message) error {
	cmdStr := uc.cfg.GH.Command
	cmdStr = strings.ReplaceAll(cmdStr, "{title}", shellQuote(msg.Title))
	cmdStr = strings.ReplaceAll(cmdStr, "{body}", shellQuote(msg.Body))

	cmd := exec.Command("sh", "-c", cmdStr)
	cmd.Stdout = nil
	cmd.Stderr = nil
	if out, err := cmd.CombinedOutput(); err != nil {
		return fmt.Errorf("gh pr create: %s: %w", strings.TrimSpace(string(out)), err)
	}

	repoRoot, _ := uc.git.GetRepoRoot()
	_ = uc.store.DeletePR(repoRoot)
	return nil
}

// ErrEmptyDiff is returned when there are no changes between branches.
var ErrEmptyDiff = fmt.Errorf("no diff found between branches")

// parsePRMessage parses the LLM output.
// Expected format:
//
//	Title: <title>
//
//	<body>
func parsePRMessage(raw string) domain.Message {
	if raw == "" {
		return domain.Message{}
	}
	lines := strings.SplitN(raw, "\n", 2)
	title := strings.TrimPrefix(strings.TrimSpace(lines[0]), "Title: ")
	if len(lines) == 1 {
		return domain.Message{Title: title}
	}
	body := strings.TrimSpace(lines[1])
	body = strings.TrimPrefix(body, "\n")
	return domain.Message{Title: title, Body: body}
}

func shellQuote(s string) string {
	return "'" + strings.ReplaceAll(s, "'", "'\"'\"'") + "'"
}
