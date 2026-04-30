package prompt

import (
	"strings"

	"github.com/freeoss-space/gitscribe/internal/config"
)

const systemPreamble = `You are an expert software engineer writing high-quality git messages.
Output ONLY the commit message. Do not include explanations, markdown code fences, or commentary.`

// Builder constructs LLM prompts from configuration.
type Builder struct{}

// New returns a Builder.
func New() *Builder { return &Builder{} }

// BuildCommit constructs a prompt for generating a commit message.
// feedback is an optional user instruction to refine the previous attempt.
func (b *Builder) BuildCommit(cfg *config.Config, diff, feedback string) string {
	var sb strings.Builder
	sb.WriteString(systemPreamble)
	sb.WriteString("\n\n")
	sb.WriteString(formatInstructions(cfg))
	sb.WriteString("\n\n")
	sb.WriteString(styleInstructions(cfg))
	sb.WriteString("\n\n")
	sb.WriteString(bodyInstructions(cfg))
	if cfg.Prompts.Base != "" {
		sb.WriteString("\n\n")
		sb.WriteString(cfg.Prompts.Base)
	}
	if cfg.Prompts.Commit != "" {
		sb.WriteString("\n\n")
		sb.WriteString(cfg.Prompts.Commit)
	}
	if feedback != "" {
		sb.WriteString("\n\nAdditional feedback from user:\n")
		sb.WriteString(feedback)
	}
	sb.WriteString("\n\nGit diff:\n")
	sb.WriteString(diff)
	return sb.String()
}

// BuildPR constructs a prompt for generating a PR title and description.
func (b *Builder) BuildPR(cfg *config.Config, diff, prTemplate, feedback string) string {
	var sb strings.Builder
	sb.WriteString(systemPreamble)
	sb.WriteString("\n\n")
	sb.WriteString("Generate a pull request title and description.\n")
	sb.WriteString("Output format:\nTitle: <title>\n\n<description body>")
	sb.WriteString("\n\n")
	sb.WriteString(styleInstructions(cfg))
	if prTemplate != "" {
		sb.WriteString("\n\nUse the following PR template structure:\n")
		sb.WriteString(prTemplate)
	}
	if cfg.Prompts.Base != "" {
		sb.WriteString("\n\n")
		sb.WriteString(cfg.Prompts.Base)
	}
	if cfg.Prompts.PR != "" {
		sb.WriteString("\n\n")
		sb.WriteString(cfg.Prompts.PR)
	}
	if feedback != "" {
		sb.WriteString("\n\nAdditional feedback from user:\n")
		sb.WriteString(feedback)
	}
	sb.WriteString("\n\nGit diff:\n")
	sb.WriteString(diff)
	return sb.String()
}

func formatInstructions(cfg *config.Config) string {
	var sb strings.Builder
	switch cfg.Format.Type {
	case "conventional":
		sb.WriteString("Commit format: Conventional Commits (https://www.conventionalcommits.org)\n")
		sb.WriteString("Title pattern: <type>")
		if !cfg.Format.RequireScope {
			sb.WriteString("[(<scope>)]")
		} else {
			sb.WriteString("(<scope>)")
		}
		sb.WriteString(": <description>\n")
		if len(cfg.Format.Scopes) > 0 {
			sb.WriteString("Valid types: " + strings.Join(cfg.Format.Scopes, ", ") + "\n")
		}
		sb.WriteString("Title rules:\n- Max 72 characters\n- Imperative mood (e.g. \"add feature\", not \"added feature\")\n- No period at end")
	case "simple":
		sb.WriteString("Commit format: Simple plain English title only.\n")
		sb.WriteString("Title rules:\n- Max 72 characters\n- Imperative mood\n- No period at end")
	case "custom":
		if cfg.Format.Template != "" {
			sb.WriteString("Commit format: Use this custom template:\n")
			sb.WriteString(cfg.Format.Template)
		}
	default:
		sb.WriteString("Commit format: Conventional Commits.\n")
		sb.WriteString("Title rules:\n- Max 72 characters\n- Imperative mood")
	}
	return sb.String()
}

func styleInstructions(cfg *config.Config) string {
	var sb strings.Builder
	sb.WriteString("Tone: " + cfg.Style.Tone + "\n")
	switch cfg.Style.Tone {
	case "professional":
		sb.WriteString("- Use formal, concise language. No slang.\n")
	case "casual":
		sb.WriteString("- Use relaxed, everyday language.\n")
	case "fun":
		sb.WriteString("- Use expressive, enthusiastic language.\n")
	case "mixed":
		sb.WriteString("- Balance formal and informal language.\n")
	}
	if cfg.Style.Emoji {
		sb.WriteString("- Emojis are allowed and encouraged.\n")
	} else {
		sb.WriteString("- Do NOT use emojis.\n")
	}
	sb.WriteString("Verbosity: " + cfg.Style.Verbosity)
	return sb.String()
}

func bodyInstructions(cfg *config.Config) string {
	var sb strings.Builder
	switch cfg.Body.Mode {
	case "none":
		sb.WriteString("Body: Do not generate a body. Title only.")
	case "small":
		sb.WriteString("Body: Generate a short body.\n")
		writeBulletRules(&sb, cfg)
	case "large":
		sb.WriteString("Body: Generate a detailed body.\n")
		writeBulletRules(&sb, cfg)
	default:
		sb.WriteString("Body: Generate a short body.\n")
		writeBulletRules(&sb, cfg)
	}
	return sb.String()
}

func writeBulletRules(sb *strings.Builder, cfg *config.Config) {
	sb.WriteString("- ")
	sb.WriteString(bulletPrefix(cfg.Body.BulletStyle))
	sb.WriteString(" bullet style\n")
	sb.WriteString("- ")
	if cfg.Body.MinItems > 0 {
		sb.WriteString(itoa(cfg.Body.MinItems))
		sb.WriteString(" to ")
	}
	sb.WriteString(itoa(cfg.Body.MaxItems))
	sb.WriteString(" bullet points\n- Be concise")
}

func bulletPrefix(style string) string {
	switch style {
	case "star":
		return "Star (*)"
	case "numbered":
		return "Numbered (1.)"
	default:
		return "Dash (-)"
	}
}

func itoa(n int) string {
	if n == 0 {
		return "0"
	}
	digits := []byte{}
	for n > 0 {
		digits = append([]byte{byte('0' + n%10)}, digits...)
		n /= 10
	}
	return string(digits)
}
