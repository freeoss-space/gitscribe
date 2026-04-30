package cli

import (
	"context"
	"fmt"

	tea "charm.land/bubbletea/v2"
	"github.com/freeoss-space/gitscribe/internal/config"
	"github.com/freeoss-space/gitscribe/internal/git"
	"github.com/freeoss-space/gitscribe/internal/llm"
	"github.com/freeoss-space/gitscribe/internal/tempfile"
	tuipr "github.com/freeoss-space/gitscribe/internal/tui/pr"
	prUC "github.com/freeoss-space/gitscribe/internal/usecase/pr"
	"github.com/spf13/cobra"
)

func newPRCmd() *cobra.Command {
	var noInterface bool
	var base string

	cmd := &cobra.Command{
		Use:   "pr",
		Short: "Generate a pull request description",
		Long: `Generate a PR title and description from the branch diff using an LLM.
Then optionally create the PR via the GitHub CLI.

Key bindings (TUI):
  enter       Create PR (from title field)
  ctrl+s      Create PR (from body field)
  tab         Switch between title and body fields
  ctrl+r      Regenerate
  ctrl+f      Regenerate with feedback
  ctrl+c      Copy to clipboard
  esc         Exit`,
		RunE: func(cmd *cobra.Command, args []string) error {
			return runPR(cmd.Context(), noInterface, base)
		},
	}

	cmd.Flags().BoolVar(&noInterface, "no-interface", false, "Print generated message only, do not create PR")
	cmd.Flags().StringVar(&base, "base", "", "Base branch to diff against (default: auto-detect)")

	return cmd
}

func runPR(ctx context.Context, noInterface bool, base string) error {
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
	uc := prUC.New(gitClient, executor, cfg, store)

	if noInterface {
		msg, err := uc.Generate(ctx, base, "")
		if err != nil {
			return err
		}
		fmt.Println(msg.String())
		return nil
	}

	model := tuipr.New(ctx, uc, base)
	p := tea.NewProgram(model)
	if _, err := p.Run(); err != nil {
		return fmt.Errorf("TUI error: %w", err)
	}
	return nil
}
