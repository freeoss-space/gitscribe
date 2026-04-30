package cli

import (
	"fmt"
	"os"

	"github.com/freeoss-space/gitscribe/internal/config"
	"github.com/freeoss-space/gitscribe/internal/git"
	"github.com/spf13/cobra"
)

func newConfigCmd() *cobra.Command {
	var global, local bool

	cmd := &cobra.Command{
		Use:   "config",
		Short: "Open configuration in $EDITOR",
		Long: `Open the gitscribe configuration file in $EDITOR.

Flags:
  --global  Edit the global config ($XDG_CONFIG_HOME/gitscribe/config.json)
  --local   Edit the local repo config (.gitscribe/config.json)

Without flags, the global config is opened.`,
		RunE: func(cmd *cobra.Command, args []string) error {
			loader := config.NewLoader()

			if local {
				repoRoot, err := getRepoRoot()
				if err != nil {
					return err
				}
				path := loader.LocalConfigPath(repoRoot)
				return openConfig(loader, path)
			}

			// Default to global.
			path := loader.GlobalConfigPath()
			return openConfig(loader, path)
		},
	}

	cmd.Flags().BoolVar(&global, "global", false, "Edit global config")
	cmd.Flags().BoolVar(&local, "local", false, "Edit local repo config")

	return cmd
}

func openConfig(loader *config.Loader, path string) error {
	if _, err := os.Stat(path); os.IsNotExist(err) {
		fmt.Printf("Creating default config at %s\n", path)
		if err := loader.CreateDefault(path); err != nil {
			return fmt.Errorf("create config: %w", err)
		}
	}
	return config.OpenInEditor(path)
}

func getRepoRoot() (string, error) {
	c := git.NewClient()
	root, err := c.GetRepoRoot()
	if err != nil {
		return "", fmt.Errorf("not inside a git repository: %w", err)
	}
	return root, nil
}
