package tui

import "testing"

func TestModelInit(t *testing.T) {
	m := NewModel("title", "body")
	if m.Title != "title" || m.Body != "body" { t.Fatal("bad model") }
}
