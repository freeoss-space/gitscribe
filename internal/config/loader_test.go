package config

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestLoader_GlobalConfigPath(t *testing.T) {
	l := NewLoader()

	t.Run("uses XDG_CONFIG_HOME when set", func(t *testing.T) {
		t.Setenv("XDG_CONFIG_HOME", "/tmp/xdg")
		assert.Equal(t, "/tmp/xdg/gitscribe/config.json", l.GlobalConfigPath())
	})

	t.Run("falls back to ~/.config when XDG not set", func(t *testing.T) {
		t.Setenv("XDG_CONFIG_HOME", "")
		home, _ := os.UserHomeDir()
		assert.Equal(t, filepath.Join(home, ".config", "gitscribe", "config.json"), l.GlobalConfigPath())
	})
}

func TestLoader_LocalConfigPath(t *testing.T) {
	l := NewLoader()
	assert.Equal(t, "/repo/.gitscribe/config.json", l.LocalConfigPath("/repo"))
}

func TestLoader_Load_NoFiles(t *testing.T) {
	t.Setenv("XDG_CONFIG_HOME", t.TempDir()) // point to empty dir
	l := NewLoader()
	cfg, err := l.Load(t.TempDir())
	require.NoError(t, err)
	assert.Equal(t, Defaults(), *cfg)
}

func TestLoader_Load_GlobalOverrides(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", dir)

	// Write a partial global config.
	globalPath := filepath.Join(dir, "gitscribe", "config.json")
	require.NoError(t, os.MkdirAll(filepath.Dir(globalPath), 0o755))
	data := `{"llm":{"command":"my-llm","timeout_seconds":60},"style":{"emoji":true}}`
	require.NoError(t, os.WriteFile(globalPath, []byte(data), 0o644))

	l := NewLoader()
	cfg, err := l.Load(t.TempDir())
	require.NoError(t, err)

	assert.Equal(t, "my-llm", cfg.LLM.Command)
	assert.Equal(t, 60, cfg.LLM.TimeoutSeconds)
	assert.True(t, cfg.Style.Emoji)
	// Defaults should still apply to untouched fields.
	assert.Equal(t, "professional", cfg.Style.Tone)
	assert.Equal(t, "conventional", cfg.Format.Type)
}

func TestLoader_Load_LocalOverridesGlobal(t *testing.T) {
	xdgDir := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", xdgDir)

	globalPath := filepath.Join(xdgDir, "gitscribe", "config.json")
	require.NoError(t, os.MkdirAll(filepath.Dir(globalPath), 0o755))
	require.NoError(t, os.WriteFile(globalPath, []byte(`{"llm":{"command":"global-llm"}}`), 0o644))

	repoDir := t.TempDir()
	localDir := filepath.Join(repoDir, ".gitscribe")
	require.NoError(t, os.MkdirAll(localDir, 0o755))
	require.NoError(t, os.WriteFile(filepath.Join(localDir, "config.json"), []byte(`{"llm":{"command":"local-llm"}}`), 0o644))

	l := NewLoader()
	cfg, err := l.Load(repoDir)
	require.NoError(t, err)

	assert.Equal(t, "local-llm", cfg.LLM.Command)
}

func TestLoader_Load_CorruptFileUsesDefaults(t *testing.T) {
	dir := t.TempDir()
	t.Setenv("XDG_CONFIG_HOME", dir)

	globalPath := filepath.Join(dir, "gitscribe", "config.json")
	require.NoError(t, os.MkdirAll(filepath.Dir(globalPath), 0o755))
	require.NoError(t, os.WriteFile(globalPath, []byte(`{invalid json`), 0o644))

	l := NewLoader()
	cfg, err := l.Load(t.TempDir())
	require.NoError(t, err)
	assert.Equal(t, Defaults(), *cfg)
}

func TestLoader_Save(t *testing.T) {
	dir := t.TempDir()
	path := filepath.Join(dir, "sub", "config.json")
	l := NewLoader()
	cfg := Defaults()
	cfg.LLM.Command = "saved-llm"

	require.NoError(t, l.Save(path, &cfg))

	data, err := os.ReadFile(path)
	require.NoError(t, err)

	var loaded Config
	require.NoError(t, json.Unmarshal(data, &loaded))
	assert.Equal(t, "saved-llm", loaded.LLM.Command)
}

func TestDeepMerge(t *testing.T) {
	dst := map[string]any{
		"a": "original",
		"nested": map[string]any{
			"x": 1,
			"y": 2,
		},
	}
	src := map[string]any{
		"a": "overridden",
		"nested": map[string]any{
			"y": 99,
		},
		"b": "new",
	}
	result := deepMerge(dst, src)

	assert.Equal(t, "overridden", result["a"])
	assert.Equal(t, "new", result["b"])
	nested := result["nested"].(map[string]any)
	assert.Equal(t, 1, nested["x"])
	assert.Equal(t, 99, nested["y"])
}
