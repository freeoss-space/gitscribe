package tui

import tea "github.com/charmbracelet/bubbletea"

type Model struct {
	Title string
	Body  string
	Done  bool
}

func NewModel(title, body string) Model { return Model{Title: title, Body: body} }
func (m Model) Init() tea.Cmd { return nil }
func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	if k, ok := msg.(tea.KeyMsg); ok {
		switch k.String() {
		case "esc", "ctrl+c":
			m.Done = true
			return m, tea.Quit
		}
	}
	return m, nil
}
func (m Model) View() string { return "Editing commit message\nTitle: " + m.Title + "\n\n" + m.Body }
