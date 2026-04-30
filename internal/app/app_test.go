package app

import (
	"testing"

	"gitscribe/internal/config"
)

type fakeRunner struct{ out string }
func (f fakeRunner) Generate(_ string) (string, error) { return f.out, nil }

type fakeGit struct{ diff string }
func (f fakeGit) Diff() (string, error) { return f.diff, nil }

func TestGenerateCommit(t *testing.T) {
	cfg := config.Default()
	s := Service{LLM: fakeRunner{out:`{"title":"feat: x","body":"- a"}`}, Git: fakeGit{diff:"d"}, Config: cfg}
	msg, err := s.GenerateCommit()
	if err != nil { t.Fatal(err) }
	if msg.Title != "feat: x" { t.Fatalf("got %+v", msg) }
}
