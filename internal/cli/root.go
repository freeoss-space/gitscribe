package cli

import (
	"fmt"
	"os"

	tea "github.com/charmbracelet/bubbletea"
	"github.com/spf13/cobra"
	"gitscribe/internal/app"
	"gitscribe/internal/tui"
)

type Deps struct{ Service app.Service }

func NewRoot(d *Deps) *cobra.Command {
	root := &cobra.Command{Use: "gitscribe"}
	root.AddCommand(newCommitCmd(d), newPRCmd(d), newConfigCmd())
	return root
}

func newConfigCmd() *cobra.Command {
	return &cobra.Command{Use: "config", RunE: func(cmd *cobra.Command, args []string) error { return nil }}
}

func validateDeps(d *Deps) error {
	if d == nil {
		return fmt.Errorf("missing dependencies")
	}
	if d.Service.Git == nil {
		return fmt.Errorf("missing Git provider")
	}
	if d.Service.LLM == nil {
		return fmt.Errorf("missing LLM runner")
	}
	return nil
}

func newCommitCmd(d *Deps) *cobra.Command {
	var noInterface bool
	cmd := &cobra.Command{Use: "commit", RunE: func(cmd *cobra.Command, args []string) error {
		if err := validateDeps(d); err != nil {
			return err
		}
		msg, err := d.Service.GenerateCommit()
		if err != nil {
			return err
		}
		if noInterface {
			fmt.Fprintln(cmd.OutOrStdout(), msg.Title)
			fmt.Fprintln(cmd.OutOrStdout(), msg.Body)
			return nil
		}
		p := tea.NewProgram(tui.NewModel(msg.Title, msg.Body))
		_, err = p.Run()
		return err
	}}
	cmd.Flags().BoolVar(&noInterface, "no-interface", false, "print only")
	return cmd
}

func newPRCmd(d *Deps) *cobra.Command {
	var noInterface bool
	cmd := &cobra.Command{Use: "pr", RunE: func(cmd *cobra.Command, args []string) error {
		if err := validateDeps(d); err != nil {
			return err
		}
		if noInterface {
			fmt.Fprintln(cmd.OutOrStdout(), "pr generation pending")
			return nil
		}
		return nil
	}}
	cmd.Flags().BoolVar(&noInterface, "no-interface", false, "print only")
	return cmd
}

func Execute(d *Deps) error { return NewRoot(d).Execute() }
func Exit(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
