package prompt

import (
	"strings"
	"testing"

	"github.com/freeoss-space/gitscribe/internal/config"
	"github.com/stretchr/testify/assert"
)

func defaultCfg() *config.Config {
	cfg := config.Defaults()
	return &cfg
}

func TestBuildCommit_ContainsDiff(t *testing.T) {
	b := New()
	diff := "diff --git a/foo.go\n+added line"
	result := b.BuildCommit(defaultCfg(), diff, "")
	assert.Contains(t, result, diff)
}

func TestBuildCommit_ContainsPreamble(t *testing.T) {
	b := New()
	result := b.BuildCommit(defaultCfg(), "diff", "")
	assert.Contains(t, result, "expert software engineer")
}

func TestBuildCommit_ConventionalFormat(t *testing.T) {
	b := New()
	cfg := defaultCfg()
	cfg.Format.Type = "conventional"
	result := b.BuildCommit(cfg, "diff", "")
	assert.Contains(t, result, "Conventional Commits")
	assert.Contains(t, result, "feat")
	assert.Contains(t, result, "72 characters")
}

func TestBuildCommit_SimpleFormat(t *testing.T) {
	b := New()
	cfg := defaultCfg()
	cfg.Format.Type = "simple"
	result := b.BuildCommit(cfg, "diff", "")
	assert.Contains(t, result, "Simple plain English")
}

func TestBuildCommit_CustomFormat(t *testing.T) {
	b := New()
	cfg := defaultCfg()
	cfg.Format.Type = "custom"
	cfg.Format.Template = "[{type}] {description}"
	result := b.BuildCommit(cfg, "diff", "")
	assert.Contains(t, result, "[{type}] {description}")
}

func TestBuildCommit_ProfessionalTone(t *testing.T) {
	b := New()
	cfg := defaultCfg()
	cfg.Style.Tone = "professional"
	result := b.BuildCommit(cfg, "diff", "")
	assert.Contains(t, result, "formal")
	assert.Contains(t, result, "NOT use emojis")
}

func TestBuildCommit_FunToneWithEmoji(t *testing.T) {
	b := New()
	cfg := defaultCfg()
	cfg.Style.Tone = "fun"
	cfg.Style.Emoji = true
	result := b.BuildCommit(cfg, "diff", "")
	assert.Contains(t, result, "enthusiastic")
	assert.Contains(t, result, "Emojis are allowed")
}

func TestBuildCommit_BodyModeNone(t *testing.T) {
	b := New()
	cfg := defaultCfg()
	cfg.Body.Mode = "none"
	result := b.BuildCommit(cfg, "diff", "")
	assert.Contains(t, result, "Title only")
}

func TestBuildCommit_BodyModeSmall(t *testing.T) {
	b := New()
	cfg := defaultCfg()
	cfg.Body.Mode = "small"
	cfg.Body.MinItems = 3
	cfg.Body.MaxItems = 5
	result := b.BuildCommit(cfg, "diff", "")
	assert.Contains(t, result, "3 to 5")
}

func TestBuildCommit_BulletStyleStar(t *testing.T) {
	b := New()
	cfg := defaultCfg()
	cfg.Body.BulletStyle = "star"
	result := b.BuildCommit(cfg, "diff", "")
	assert.Contains(t, result, "Star (*)")
}

func TestBuildCommit_WithFeedback(t *testing.T) {
	b := New()
	result := b.BuildCommit(defaultCfg(), "diff", "make it shorter")
	assert.Contains(t, result, "make it shorter")
}

func TestBuildCommit_WithCustomPrompts(t *testing.T) {
	b := New()
	cfg := defaultCfg()
	cfg.Prompts.Base = "base instruction"
	cfg.Prompts.Commit = "commit instruction"
	result := b.BuildCommit(cfg, "diff", "")
	assert.Contains(t, result, "base instruction")
	assert.Contains(t, result, "commit instruction")
}

func TestBuildPR_ContainsTitle(t *testing.T) {
	b := New()
	result := b.BuildPR(defaultCfg(), "diff", "", "")
	assert.Contains(t, result, "pull request title")
}

func TestBuildPR_WithTemplate(t *testing.T) {
	b := New()
	result := b.BuildPR(defaultCfg(), "diff", "## Summary\n## Test plan", "")
	assert.Contains(t, result, "## Summary")
}

func TestBuildPR_WithFeedback(t *testing.T) {
	b := New()
	result := b.BuildPR(defaultCfg(), "diff", "", "expand the description")
	assert.Contains(t, result, "expand the description")
}

func TestBuildPR_PRPrompt(t *testing.T) {
	b := New()
	cfg := defaultCfg()
	cfg.Prompts.PR = "focus on the API changes"
	result := b.BuildPR(cfg, "diff", "", "")
	assert.Contains(t, result, "focus on the API changes")
}

func TestBuildCommit_DiffAtEnd(t *testing.T) {
	b := New()
	diff := "unique-diff-content"
	result := b.BuildCommit(defaultCfg(), diff, "")
	idx := strings.LastIndex(result, diff)
	assert.True(t, idx > 0, "diff should appear in the prompt")
	assert.True(t, idx > strings.Index(result, "expert"), "diff should come after instructions")
}
