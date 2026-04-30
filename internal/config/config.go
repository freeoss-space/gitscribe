package config

import (
	"encoding/json"
	"os"
	"path/filepath"
)

type Config struct {
	LLM struct {
		Command        string `json:"command"`
		TimeoutSeconds int    `json:"timeout_seconds"`
	} `json:"llm"`
	Format struct {
		Type         string   `json:"type"`
		Types        []string `json:"types"`
		RequireScope bool     `json:"require_scope"`
		Template     string   `json:"template"`
	} `json:"format"`
	Style struct {
		Tone      string `json:"tone"`
		Verbosity string `json:"verbosity"`
		Emoji     bool   `json:"emoji"`
	} `json:"style"`
	Body struct {
		Mode        string `json:"mode"`
		BulletStyle string `json:"bullet_style"`
		MaxItems    int    `json:"max_items"`
		MinItems    int    `json:"min_items"`
	} `json:"body"`
	Prompts struct {
		Base   string `json:"base"`
		Commit string `json:"commit"`
		PR     string `json:"pr"`
	} `json:"prompts"`
}

func Default() Config {
	c := Config{}
	c.LLM.Command = ""
	c.LLM.TimeoutSeconds = 30
	c.Format.Type = "conventional"
	c.Format.Types = []string{"feat", "fix", "chore", "docs", "refactor", "test"}
	c.Style.Tone = "professional"
	c.Style.Verbosity = "medium"
	c.Body.Mode = "small"
	c.Body.BulletStyle = "dash"
	c.Body.MinItems = 3
	c.Body.MaxItems = 5
	c.Prompts.Base = "Summarize the git diff into a clear and useful message."
	c.Prompts.Commit = "Generate a commit message following the configured format."
	c.Prompts.PR = "Generate a pull request title and description."
	return c
}

func Load(globalPath, repoRoot string) (Config, error) {
	cfg := Default()

	globalCfg, err := read(globalPath)
	if err != nil {
		return cfg, err
	}
	cfg, err = merge(cfg, globalCfg)
	if err != nil {
		return cfg, err
	}

	repoCfg, err := read(filepath.Join(repoRoot, ".gitscribe", "config.json"))
	if err != nil {
		return cfg, err
	}
	cfg, err = merge(cfg, repoCfg)
	if err != nil {
		return cfg, err
	}

	return cfg, nil
}

func read(path string) (map[string]any, error) {
	b, err := os.ReadFile(path)
	if err != nil {
		if os.IsNotExist(err) {
			return map[string]any{}, nil
		}
		return nil, err
	}
	m := map[string]any{}
	if err := json.Unmarshal(b, &m); err != nil {
		return nil, err
	}
	return m, nil
}

func merge(base Config, overlay map[string]any) (Config, error) {
	b, err := json.Marshal(base)
	if err != nil {
		return base, err
	}
	m := map[string]any{}
	if err := json.Unmarshal(b, &m); err != nil {
		return base, err
	}
	deepMerge(m, overlay)
	out, err := json.Marshal(m)
	if err != nil {
		return base, err
	}
	if err := json.Unmarshal(out, &base); err != nil {
		return base, err
	}
	return base, nil
}

func deepMerge(dst, src map[string]any) {
	for k, v := range src {
		if sv, ok := v.(map[string]any); ok {
			if dv, ok := dst[k].(map[string]any); ok {
				deepMerge(dv, sv)
				dst[k] = dv
				continue
			}
		}
		dst[k] = v
	}
}
