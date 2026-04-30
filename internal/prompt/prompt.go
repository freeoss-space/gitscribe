package prompt

import (
	"fmt"
	"strings"

	"github.com/freeoss-space/gitscribe/internal/config"
)

func BuildCommit(cfg config.Config, diff string) string {
	body := "none"
	if cfg.Body.Mode != "none" {
		body = fmt.Sprintf("%d to %d bullet points", cfg.Body.MinItems, cfg.Body.MaxItems)
	}
	return fmt.Sprintf(`Generate a commit message from the git diff and return ONLY valid JSON.
The response must be exactly one JSON object with this schema:
{"title": string, "body": string, "breaking": boolean}
Do not include markdown fences, explanations, or any text before or after the JSON.
Use %s format.
Tone: %s
Emoji: %s
Body rules: %s
Additional instructions: %s
Git diff:
%s`,
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
