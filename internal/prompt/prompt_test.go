package prompt

import (
	"strings"
	"testing"
	"github.com/freeoss-space/gitscribe/internal/config"
)

func TestBuildCommitPrompt(t *testing.T) {
	cfg := config.Default()
	cfg.Style.Tone = "professional"
	cfg.Prompts.Commit = "Custom"
	out := BuildCommit(cfg, "diff --git")
	if !strings.Contains(out, "Tone: professional") || !strings.Contains(out, "Additional instructions: Custom") || !strings.Contains(out, "Git diff:\ndiff --git") {
		t.Fatal(out)
	}
}
