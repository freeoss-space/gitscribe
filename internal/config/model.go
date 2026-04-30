package config

// Config is the root configuration structure. Fields map 1:1 with config.json keys.
type Config struct {
	LLM     LLMConfig     `json:"llm"     mapstructure:"llm"`
	Format  FormatConfig  `json:"format"  mapstructure:"format"`
	Style   StyleConfig   `json:"style"   mapstructure:"style"`
	Body    BodyConfig    `json:"body"    mapstructure:"body"`
	Prompts PromptsConfig `json:"prompts" mapstructure:"prompts"`
	GH      GHConfig      `json:"gh"      mapstructure:"gh"`
}

// LLMConfig configures CLI-based LLM execution.
type LLMConfig struct {
	// Command is the full command string. The prompt is piped to its stdin.
	Command        string `json:"command"         mapstructure:"command"`
	TimeoutSeconds int    `json:"timeout_seconds" mapstructure:"timeout_seconds"`
}

// FormatConfig controls the structure of generated commit messages.
type FormatConfig struct {
	// Type is one of: conventional, simple, custom.
	Type         string   `json:"type"          mapstructure:"type"`
	// Scopes lists the allowed conventional commit types (e.g. feat, fix).
	Scopes       []string `json:"scopes"        mapstructure:"scopes"`
	RequireScope bool     `json:"require_scope" mapstructure:"require_scope"`
	// Template is used when Type == "custom". Supports {title} and {body} placeholders.
	Template     string   `json:"template"      mapstructure:"template"`
}

// StyleConfig controls tone and emoji usage.
type StyleConfig struct {
	// Tone is one of: professional, casual, fun, mixed.
	Tone      string `json:"tone"      mapstructure:"tone"`
	Verbosity string `json:"verbosity" mapstructure:"verbosity"`
	Emoji     bool   `json:"emoji"     mapstructure:"emoji"`
}

// BodyConfig controls how the commit body is generated.
type BodyConfig struct {
	// Mode is one of: none, small, large.
	Mode        string `json:"mode"         mapstructure:"mode"`
	// BulletStyle is one of: dash, star, numbered.
	BulletStyle string `json:"bullet_style" mapstructure:"bullet_style"`
	MaxItems    int    `json:"max_items"    mapstructure:"max_items"`
	MinItems    int    `json:"min_items"    mapstructure:"min_items"`
}

// PromptsConfig holds user-supplied prompt fragments appended to the base prompt.
type PromptsConfig struct {
	Base   string `json:"base"   mapstructure:"base"`
	Commit string `json:"commit" mapstructure:"commit"`
	PR     string `json:"pr"     mapstructure:"pr"`
}

// GHConfig configures the GitHub CLI command template.
type GHConfig struct {
	// Command supports {title} and {body} placeholders.
	Command string `json:"command" mapstructure:"command"`
}

// Defaults returns a Config populated with sensible defaults.
func Defaults() Config {
	return Config{
		LLM: LLMConfig{
			Command:        "llm",
			TimeoutSeconds: 30,
		},
		Format: FormatConfig{
			Type:         "conventional",
			Scopes:       []string{"feat", "fix", "chore", "docs", "refactor", "test"},
			RequireScope: false,
		},
		Style: StyleConfig{
			Tone:      "professional",
			Verbosity: "medium",
			Emoji:     false,
		},
		Body: BodyConfig{
			Mode:        "small",
			BulletStyle: "dash",
			MaxItems:    5,
			MinItems:    3,
		},
		Prompts: PromptsConfig{},
		GH: GHConfig{
			Command: "gh pr create --title {title} --body {body}",
		},
	}
}
