package styles

import (
	"charm.land/lipgloss/v2"
)

var (
	Primary   = lipgloss.NewStyle().Foreground(lipgloss.Color("#7B61FF")).Bold(true)
	Secondary = lipgloss.NewStyle().Foreground(lipgloss.Color("#FF61DC"))
	Accent    = lipgloss.NewStyle().Foreground(lipgloss.Color("#61FFB3"))
	Muted     = lipgloss.NewStyle().Foreground(lipgloss.Color("#6C7086"))
	Error     = lipgloss.NewStyle().Foreground(lipgloss.Color("#FF5555")).Bold(true)
	Success   = lipgloss.NewStyle().Foreground(lipgloss.Color("#50FA7B"))
	Warning   = lipgloss.NewStyle().Foreground(lipgloss.Color("#F1FA8C"))

	Title = lipgloss.NewStyle().
		Foreground(lipgloss.Color("#7B61FF")).
		Bold(true).
		Padding(0, 1)

	Box = lipgloss.NewStyle().
		Border(lipgloss.RoundedBorder()).
		BorderForeground(lipgloss.Color("#7B61FF")).
		Padding(0, 1)

	Help = lipgloss.NewStyle().Foreground(lipgloss.Color("#6C7086"))
)
