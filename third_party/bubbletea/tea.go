package bubbletea

type Msg interface{}
type Cmd func() Msg

type Model interface { Init() Cmd; Update(Msg)(Model, Cmd); View() string }

type Program struct { m Model }
func NewProgram(m Model) *Program { return &Program{m:m} }
func (p *Program) Run() (Model, error) { return p.m, nil }
func Quit() Msg { return nil }

type KeyMsg struct { K string }
func (k KeyMsg) String() string { return k.K }
