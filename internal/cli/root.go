package cli

import (
	"os"

	"github.com/rs/zerolog"
	"github.com/rs/zerolog/log"
	"github.com/spf13/cobra"
	"gopkg.in/natefinch/lumberjack.v2"
)

var rootCmd = &cobra.Command{
	Use:   "gitscribe",
	Short: "AI-powered git commit and PR message generator",
	Long: `gitscribe generates commit messages and PR descriptions using LLMs.

Configuration: $XDG_CONFIG_HOME/gitscribe/config.json (global)
               .gitscribe/config.json (local, overrides global)`,
	SilenceUsage:  true,
	SilenceErrors: true,
}

// Execute runs the root command.
func Execute() {
	if err := rootCmd.Execute(); err != nil {
		log.Error().Err(err).Msg("command failed")
		os.Exit(1)
	}
}

func init() {
	initLogger()
	rootCmd.AddCommand(newConfigCmd())
	rootCmd.AddCommand(newCommitCmd())
	rootCmd.AddCommand(newPRCmd())
}

func initLogger() {
	logFile := &lumberjack.Logger{
		Filename:   logFilePath(),
		MaxSize:    10, // MB
		MaxBackups: 3,
		Compress:   true,
	}
	log.Logger = zerolog.New(logFile).With().Timestamp().Logger()
}

func logFilePath() string {
	dir := os.Getenv("XDG_STATE_HOME")
	if dir == "" {
		home, _ := os.UserHomeDir()
		dir = home + "/.local/state"
	}
	return dir + "/gitscribe/gitscribe.log"
}
