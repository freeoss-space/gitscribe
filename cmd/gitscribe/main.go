package main

import (
	"github.com/freeoss-space/gitscribe/internal/app"
	"github.com/freeoss-space/gitscribe/internal/cli"
	"github.com/freeoss-space/gitscribe/internal/config"
)

type gitStub struct{}
func (gitStub) Diff() (string, error) { return "", nil }

type llmStub struct{}
func (llmStub) Generate(_ string) (string, error) { return `{"title":"chore: empty","body":"- empty diff"}`, nil }

func main() {
	cfg := config.Default()
	svc := app.Service{LLM: llmStub{}, Git: gitStub{}, Config: cfg}
	cli.Exit(cli.Execute(&cli.Deps{Service: svc}))
}
