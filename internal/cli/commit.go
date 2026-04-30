package cli

import (
	"context"
	"fmt"

	tea "charm.land/bubbletea/v2"
	"github.com/freeoss-space/gitscribe/internal/config"
	"github.com/freeoss-space/gitscribe/internal/git"
	"github.com/freeoss-space/gitscribe/internal/llm"
	"github.com/freeoss-space/gitscribe/internal/tempfile"
	tuicommit "github.com/freeoss-space/gitscribe/internal/tui/commit"
	commitUC "github.com/freeoss-space/gitscribe/internal/usecase/commit"
	"github.com/spf13/cobra"
)

func newCommitCmd() *cobra.Command {
	var noInterface bool

	cmd := &cobra.Command{
		Use:     "commit",
		Aliases: []string{"c"},
		Short:   "Generate a commit message from staged changes",
		Long: `Generate a commit message from the current staged diff using an LLM.

Key bindings (TUI):
  enter       Commit (from title field)
  ctrl+s      Commit (from body field)
  tab         Switch between title and body fields
  ctrl+r      Regenerate message
  ctrl+f      Regenerate with feedback
  ctrl+c      Copy to clipboard
  esc         Exit`,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runCommit(cmd.Context(), noInterface)
		},
	}

	cmd.Flags().BoolVar(&noInterface, "no-interface", false, "Print generated message only, do not commit")

	return cmd
}

func runCommit(ctx context.Context, noInterface bool) error {
	gitClient := git.NewClient()

	repoRoot, err := gitClient.GetRepoRoot()
	if err != nil {
		return fmt.Errorf("not inside a git repository: %w", err)
	}

	loader := config.NewLoader()
	cfg, err := loader.Load(repoRoot)
	if err != nil {
		return fmt.Errorf("load config: %w", err)
	}

	executor := llm.New(cfg.LLM)
	store := tempfile.New()
	uc := commitUC.New(gitClient, executor, cfg, store)

	if noInterface {
		msg, err := uc.Generate(ctx, "")
		if err != nil {
			return err
		}
		fmt.Println(msg.String())
		return nil
	}

	model := tuicommit.New(ctx, uc)
	p := tea.NewProgram(model)
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("TUI error: %w", err)
	}
	return nil
}
