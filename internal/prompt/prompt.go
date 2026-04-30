package prompt

import (
	"fmt"
	"strings"

	"gitscribe/internal/config"
)

func BuildCommit(cfg config.Config, diff string) string {
	body := "none"
	if cfg.Body.Mode != "none" {
		body = fmt.Sprintf("%d to %d bullet points", cfg.Body.MinItems, cfg.Body.MaxItems)
	}
	return fmt.Sprintf("Generate a commit message using %s format.\nTone: %s\nEmoji: %v\nBody rules: %s\nAdditional instructions: %s\nGit diff:\n%s",
		cfg.Format.Type, cfg.Style.Tone, yn(cfg.Style.Emoji), body, cfg.Prompts.Commit, diff)
}

func ApplyTemplate(tpl string, vars map[string]string) string {
	out := tpl
	for k, v := range vars {
		out = strings.ReplaceAll(out, "{"+k+"}", v)
	}
	return out
}

func yn(v bool) string {
	if v { return "yes" }
	return "no"
}
