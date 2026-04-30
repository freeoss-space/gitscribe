package config

import (
	"testing"

	"github.com/stretchr/testify/assert"
)

func TestDefaults(t *testing.T) {
	cfg := Defaults()

	assert.Equal(t, "llm", cfg.LLM.Command)
	assert.Equal(t, 30, cfg.LLM.TimeoutSeconds)

	assert.Equal(t, "conventional", cfg.Format.Type)
	assert.Contains(t, cfg.Format.Scopes, "feat")
	assert.Contains(t, cfg.Format.Scopes, "fix")
	assert.False(t, cfg.Format.RequireScope)

	assert.Equal(t, "professional", cfg.Style.Tone)
	assert.Equal(t, "medium", cfg.Style.Verbosity)
	assert.False(t, cfg.Style.Emoji)

	assert.Equal(t, "small", cfg.Body.Mode)
	assert.Equal(t, "dash", cfg.Body.BulletStyle)
	assert.Equal(t, 5, cfg.Body.MaxItems)
	assert.Equal(t, 3, cfg.Body.MinItems)

	assert.Contains(t, cfg.GH.Command, "gh pr create")
	assert.Contains(t, cfg.GH.Command, "{title}")
	assert.Contains(t, cfg.GH.Command, "{body}")
}
