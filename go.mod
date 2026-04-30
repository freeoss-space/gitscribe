module gitscribe

go 1.25

require (
	github.com/charmbracelet/bubbletea v0.0.0
	github.com/spf13/cobra v0.0.0
)

replace github.com/charmbracelet/bubbletea => ./third_party/bubbletea
replace github.com/spf13/cobra => ./third_party/cobra
