package config

import (
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
)

// Loader handles reading and writing gitscribe configuration.
type Loader struct{}

// NewLoader returns a configured Loader.
func NewLoader() *Loader { return &Loader{} }

// GlobalConfigPath returns $XDG_CONFIG_HOME/gitscribe/config.json.
func (l *Loader) GlobalConfigPath() string {
	base := os.Getenv("XDG_CONFIG_HOME")
	if base == "" {
		home, _ := os.UserHomeDir()
		base = filepath.Join(home, ".config")
	}
	return filepath.Join(base, "gitscribe", "config.json")
}

// LocalConfigPath returns {repoRoot}/.gitscribe/config.json.
func (l *Loader) LocalConfigPath(repoRoot string) string {
	return filepath.Join(repoRoot, ".gitscribe", "config.json")
}

// Load merges global and local configs on top of defaults. Errors in individual
// files are tolerated (logged via stderr); missing files are silently ignored.
func (l *Loader) Load(repoRoot string) (*Config, error) {
	cfg := Defaults()

	globalPath := l.GlobalConfigPath()
	if err := l.mergeFile(&cfg, globalPath); err != nil {
		_, _ = fmt.Fprintf(os.Stderr, "gitscribe: warning: could not read global config: %v\n", err)
	}

	if repoRoot != "" {
		localPath := l.LocalConfigPath(repoRoot)
		if err := l.mergeFile(&cfg, localPath); err != nil {
			_, _ = fmt.Fprintf(os.Stderr, "gitscribe: warning: could not read local config: %v\n", err)
		}
	}

	return &cfg, nil
}

// Save writes cfg as indented JSON to path, creating parent directories as needed.
func (l *Loader) Save(path string, cfg *Config) error {
	if err := os.MkdirAll(filepath.Dir(path), 0o755); err != nil {
		return fmt.Errorf("create config dir: %w", err)
	}
	data, err := json.MarshalIndent(cfg, "", "  ")
	if err != nil {
		return fmt.Errorf("marshal config: %w", err)
	}
	if err := os.WriteFile(path, data, 0o644); err != nil {
		return fmt.Errorf("write config: %w", err)
	}
	return nil
}

// mergeFile reads a JSON config file and deep-merges it into dst.
// Returns nil (no error) when the file does not exist.
func (l *Loader) mergeFile(dst *Config, path string) error {
	data, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return nil
	}
	if err != nil {
		return err
	}

	// Parse into a raw map for deep merge.
	var override map[string]any
	if err := json.Unmarshal(data, &override); err != nil {
		return fmt.Errorf("parse %s: %w", path, err)
	}

	// Re-serialize defaults + override through JSON round-trip.
	base, err := json.Marshal(dst)
	if err != nil {
		return err
	}
	var baseMap map[string]any
	if err := json.Unmarshal(base, &baseMap); err != nil {
		return err
	}

	merged := deepMerge(baseMap, override)

	mergedData, err := json.Marshal(merged)
	if err != nil {
		return err
	}
	return json.Unmarshal(mergedData, dst)
}

// deepMerge recursively merges src into dst. src takes precedence for scalar values.
func deepMerge(dst, src map[string]any) map[string]any {
	result := make(map[string]any, len(dst))
	for k, v := range dst {
		result[k] = v
	}
	for k, sv := range src {
		if sm, ok := sv.(map[string]any); ok {
			if dm, ok := result[k].(map[string]any); ok {
				result[k] = deepMerge(dm, sm)
				continue
			}
		}
		result[k] = sv
	}
	return result
}

// currentPlatform returns macos, linux, or windows.
func currentPlatform() string {
	switch runtime.GOOS {
	case "darwin":
		return "macos"
	case "windows":
		return "windows"
	default:
		return "linux"
	}
}

// CreateDefault writes a default config.json to path and returns the path.
// Used by `gitscribe config` when the file does not yet exist.
func (l *Loader) CreateDefault(path string) error {
	cfg := Defaults()
	return l.Save(path, &cfg)
}

// OpenInEditor opens filePath in $EDITOR (falling back to vi).
func OpenInEditor(filePath string) error {
	editor := os.Getenv("EDITOR")
	if editor == "" {
		editor = "vi"
	}
	// Split editor in case it has flags, e.g. "code --wait"
	parts := strings.Fields(editor)
	args := append(parts[1:], filePath)
	cmd := newExecCommand(parts[0], args...)
	cmd.Stdin = os.Stdin
	cmd.Stdout = os.Stdout
	cmd.Stderr = os.Stderr
	return cmd.Run()
}
