package bubbletea

type Msg interface{}
type Cmd func() Msg

type Model interface {
	Init() Cmd
	Update(Msg) (Model, Cmd)
	View() string
}

type Program struct{ m Model }

func NewProgram(m Model) *Program { return &Program{m: m} }

func (p *Program) Run() (Model, error) {
	if p.m == nil {
		return nil, nil
	}
	if cmd := p.m.Init(); cmd != nil {
		if msg := cmd(); msg != nil {
			if m, _ := p.m.Update(msg); m != nil {
				p.m = m
			}
		}
	}
	return p.m, nil
}

func Quit() Msg { return nil }

type KeyMsg struct{ K string }

func (k KeyMsg) String() string { return k.K }
