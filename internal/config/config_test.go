package config

import (
	"os"
	"path/filepath"
	"testing"
)

func TestLoadDeepMerge(t *testing.T) {
	dir := t.TempDir()
	global := filepath.Join(dir, "global.json")
	localDir := filepath.Join(dir, "repo", ".gitscribe")
	if err := os.MkdirAll(localDir, 0o755); err != nil { t.Fatal(err) }
	local := filepath.Join(localDir, "config.json")
	if err := os.WriteFile(global, []byte(`{"style":{"tone":"professional","emoji":false},"body":{"mode":"small","max_items":5}}`), 0o644); err != nil { t.Fatal(err) }
	if err := os.WriteFile(local, []byte(`{"style":{"emoji":true},"body":{"min_items":3}}`), 0o644); err != nil { t.Fatal(err) }

	cfg, err := Load(global, filepath.Join(dir, "repo"))
	if err != nil { t.Fatal(err) }
	if cfg.Style.Tone != "professional" || !cfg.Style.Emoji || cfg.Body.MaxItems != 5 || cfg.Body.MinItems != 3 {
		t.Fatalf("unexpected cfg: %+v", cfg)
	}
}
