package domain

// Message holds the generated title and optional body.
type Message struct {
	Title string
	Body  string
}

// String returns a commit-ready representation: title, blank line, body.
func (m Message) String() string {
	if m.Body == "" {
		return m.Title
	}
	return m.Title + "\n\n" + m.Body
}
