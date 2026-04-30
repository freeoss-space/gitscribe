package cli

import "testing"

func TestRootHasCommands(t *testing.T) {
	root := NewRoot(nil)
	if root == nil || root.Use != "gitscribe" { t.Fatal("missing root") }
	if len(root.Commands()) < 3 { t.Fatal("expected commands") }
}
