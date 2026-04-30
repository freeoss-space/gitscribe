package commit

import (
	"context"
	"fmt"
	"strings"

	"charm.land/bubbles/v2/spinner"
	"charm.land/bubbles/v2/textarea"
	"charm.land/bubbles/v2/textinput"
	tea "charm.land/bubbletea/v2"

	"github.com/atotto/clipboard"
	"github.com/freeoss-space/gitscribe/internal/domain"
	"github.com/freeoss-space/gitscribe/internal/tui/styles"
	commitUC "github.com/freeoss-space/gitscribe/internal/usecase/commit"
)

type state int

const (
	stateGenerating state = iota
	stateEditing
	stateFeedback
	stateError
	stateDone
)

// Model is the Bubble Tea model for the commit TUI.
type Model struct {
	uc      *commitUC.UseCase
	ctx     context.Context
	cancel  context.CancelFunc
	state   state
	spinner spinner.Model
	title   textinput.Model
	body    textarea.Model
	errMsg  string
	focused int // 0 = title, 1 = body
}

// Msg types for async commands.
type generatedMsg struct{ msg domain.Message }
type generateErrMsg struct{ err error }
type committedMsg struct{}
type commitErrMsg struct{ err error }

// New creates the model and begins generation immediately.
func New(ctx context.Context, uc *commitUC.UseCase) Model {
	ctx, cancel := context.WithCancel(ctx)

	sp := spinner.New(spinner.WithSpinner(spinner.Dot))

	ti := textinput.New()
	ti.Placeholder = "Commit title…"
	ti.CharLimit = 72

	ta := textarea.New()
	ta.Placeholder = "Commit body…"
	ta.SetHeight(6)
	ta.SetWidth(70)

	return Model{
		uc:      uc,
		ctx:     ctx,
		cancel:  cancel,
		state:   stateGenerating,
		spinner: sp,
		title:   ti,
		body:    ta,
	}
}

func (m Model) Init() tea.Cmd {
	return tea.Batch(m.spinner.Tick, generateCmd(m.ctx, m.uc, ""))
}

func (m Model) Update(msg tea.Msg) (tea.Model, tea.Cmd) {
	switch msg := msg.(type) {

	case generatedMsg:
		m.state = stateEditing
		m.title.SetValue(msg.msg.Title)
		m.body.SetValue(msg.msg.Body)
		return m, m.title.Focus()

	case generateErrMsg:
		m.state = stateError
		m.errMsg = msg.err.Error()
		return m, nil

	case committedMsg:
		m.state = stateDone
		m.cancel()
		return m, tea.Quit

	case commitErrMsg:
		m.state = stateError
		m.errMsg = msg.err.Error()
		return m, nil

	case tea.KeyPressMsg:
		return m.handleKey(msg)

	case spinner.TickMsg:
		if m.state == stateGenerating {
			var cmd tea.Cmd
			m.spinner, cmd = m.spinner.Update(msg)
			return m, cmd
		}
	}

	return m.updateFields(msg)
}

func (m Model) handleKey(msg tea.KeyPressMsg) (tea.Model, tea.Cmd) {
	switch msg.String() {
	case "esc":
		m.cancel()
		return m, tea.Quit

	case "ctrl+c":
		if m.state == stateEditing {
			text := m.currentMessage().String()
			go func() { _ = clipboard.WriteAll(text) }()
		}

	case "ctrl+r":
		if m.state == stateEditing || m.state == stateError {
			m.state = stateGenerating
			return m, tea.Batch(m.spinner.Tick, generateCmd(m.ctx, m.uc, ""))
		}

	case "ctrl+f":
		if m.state == stateEditing {
			m.state = stateFeedback
			m.body.Blur()
			m.title.Blur()
			m.title.Placeholder = "Describe what to change…"
			m.title.SetValue("")
			return m, m.title.Focus()
		}
		if m.state == stateFeedback {
			return m.submitFeedback()
		}

	case "enter":
		if m.state == stateEditing && m.focused == 0 {
			return m.doCommit()
		}
		if m.state == stateFeedback {
			return m.submitFeedback()
		}

	case "ctrl+s":
		if m.state == stateEditing {
			return m.doCommit()
		}

	case "tab":
		if m.state == stateEditing {
			if m.focused == 0 {
				m.focused = 1
				m.title.Blur()
				return m, m.body.Focus()
			}
			m.focused = 0
			m.body.Blur()
			return m, m.title.Focus()
		}
	}

	return m.updateFields(msg)
}

func (m Model) submitFeedback() (tea.Model, tea.Cmd) {
	feedback := m.title.Value()
	m.title.SetValue("")
	m.title.Placeholder = "Commit title…"
	m.state = stateGenerating
	return m, tea.Batch(m.spinner.Tick, generateCmd(m.ctx, m.uc, feedback))
}

func (m Model) doCommit() (tea.Model, tea.Cmd) {
	return m, commitCmd(m.ctx, m.uc, m.currentMessage())
}

func (m Model) currentMessage() domain.Message {
	return domain.Message{
		Title: strings.TrimSpace(m.title.Value()),
		Body:  strings.TrimSpace(m.body.Value()),
	}
}

func (m Model) updateFields(msg tea.Msg) (tea.Model, tea.Cmd) {
	var cmds []tea.Cmd
	if m.focused == 0 || m.state == stateFeedback {
		var cmd tea.Cmd
		m.title, cmd = m.title.Update(msg)
		cmds = append(cmds, cmd)
	} else {
		var cmd tea.Cmd
		m.body, cmd = m.body.Update(msg)
		cmds = append(cmds, cmd)
	}
	return m, tea.Batch(cmds...)
}

func (m Model) View() tea.View {
	var sb strings.Builder

	sb.WriteString(styles.Title.Render("gitscribe commit") + "\n\n")

	switch m.state {
	case stateGenerating:
		sb.WriteString(styles.Muted.Render(m.spinner.View() + " Generating commit message…"))

	case stateEditing:
		sb.WriteString(styles.Muted.Render("Title (max 72 chars)") + "\n")
		sb.WriteString(m.title.View() + "\n\n")
		sb.WriteString(styles.Muted.Render("Body") + "\n")
		sb.WriteString(m.body.View() + "\n\n")
		sb.WriteString(helpText())

	case stateFeedback:
		sb.WriteString(styles.Secondary.Render("Feedback") + "\n")
		sb.WriteString(m.title.View() + "\n")
		sb.WriteString(styles.Help.Render("Enter to regenerate • Esc to cancel"))

	case stateError:
		sb.WriteString(styles.Error.Render("Error: "+m.errMsg) + "\n\n")
		sb.WriteString(styles.Help.Render("ctrl+r to retry • esc to exit"))

	case stateDone:
		sb.WriteString(styles.Success.Render("✓ Committed!"))
	}

	v := tea.NewView(sb.String())
	v.AltScreen = true
	return v
}

func helpText() string {
	return styles.Help.Render(
		"enter/ctrl+s: commit • tab: switch field • ctrl+r: regenerate • ctrl+f: feedback • ctrl+c: copy • esc: exit",
	)
}

func generateCmd(ctx context.Context, uc *commitUC.UseCase, feedback string) tea.Cmd {
	return func() tea.Msg {
		msg, err := uc.Generate(ctx, feedback)
		if err != nil {
			return generateErrMsg{err: err}
		}
		return generatedMsg{msg: msg}
	}
}

func commitCmd(ctx context.Context, uc *commitUC.UseCase, msg domain.Message) tea.Cmd {
	return func() tea.Msg {
		if err := uc.Commit(ctx, msg); err != nil {
			return commitErrMsg{err: fmt.Errorf("commit failed: %w", err)}
		}
		return committedMsg{}
	}
}
