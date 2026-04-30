package commit

import (
	"context"
	"fmt"

	"github.com/freeoss-space/gitscribe/internal/config"
	"github.com/freeoss-space/gitscribe/internal/domain"
	"github.com/freeoss-space/gitscribe/internal/prompt"
	"github.com/freeoss-space/gitscribe/internal/tempfile"
)

// UseCase orchestrates commit message generation.
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

// Generate produces a commit message for the current staged diff.
// feedback is an optional user correction applied on top of the base prompt.
func (uc *UseCase) Generate(ctx context.Context, feedback string) (domain.Message, error) {
	has, err := uc.git.HasStagedChanges()
	if err != nil {
		return domain.Message{}, fmt.Errorf("check staged changes: %w", err)
	}
	if !has {
		return domain.Message{}, ErrNoStagedChanges
	}

	diff, err := uc.git.GetStagedDiff()
	if err != nil {
		return domain.Message{}, fmt.Errorf("get diff: %w", err)
	}
	if diff == "" {
		return domain.Message{Title: "chore: empty diff"}, nil
	}

	p := uc.builder.BuildCommit(uc.cfg, diff, feedback)
	raw, err := uc.llm.Generate(ctx, p)
	if err != nil {
		return domain.Message{}, fmt.Errorf("generate: %w", err)
	}

	msg := parseMessage(raw)

	repoRoot, _ := uc.git.GetRepoRoot()
	_ = uc.store.SaveCommit(repoRoot, tempfile.Draft{Title: msg.Title, Body: msg.Body})

	return msg, nil
}

// Commit creates a git commit with the given message.
func (uc *UseCase) Commit(ctx context.Context, msg domain.Message) error {
	if err := uc.git.Commit(msg.String()); err != nil {
		return err
	}
	repoRoot, _ := uc.git.GetRepoRoot()
	_ = uc.store.DeleteCommit(repoRoot)
	return nil
}

// ErrNoStagedChanges is returned when there is nothing staged.
var ErrNoStagedChanges = fmt.Errorf("no staged changes found — run `git add` first")

// parseMessage splits an LLM response into title + body.
// The first line is the title; remaining non-empty content is the body.
func parseMessage(raw string) domain.Message {
	if raw == "" {
		return domain.Message{}
	}
	// Find first newline.
	for i, c := range raw {
		if c == '\n' {
			title := raw[:i]
			body := trimLeadingBlankLines(raw[i+1:])
			return domain.Message{Title: title, Body: body}
		}
	}
	return domain.Message{Title: raw}
}

func trimLeadingBlankLines(s string) string {
	for len(s) > 0 && (s[0] == '\n' || s[0] == '\r') {
		s = s[1:]
	}
	return s
}
