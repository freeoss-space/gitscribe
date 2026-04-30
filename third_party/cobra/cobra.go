package cobra

import (
	"fmt"
	"io"
	"os"
)

type Command struct {
	Use  string
	RunE func(*Command, []string) error
	cmds []*Command
	out  io.Writer
	flags FlagSet
}

func (c *Command) AddCommand(cmds ...*Command) { c.cmds = append(c.cmds, cmds...) }
func (c *Command) Commands() []*Command        { return c.cmds }

func (c *Command) Execute() error {
	args := os.Args[1:]
	if len(args) > 0 {
		for _, cmd := range c.cmds {
			if cmd.commandName() == args[0] {
				if cmd.RunE != nil {
					return cmd.RunE(cmd, args[1:])
				}
				return cmd.Execute()
			}
		}
	}
	if c.RunE != nil {
		return c.RunE(c, args)
	}
	return nil
}

func (c *Command) commandName() string {
	for i := 0; i < len(c.Use); i++ {
		switch c.Use[i] {
		case ' ', '\t', '\n':
			return c.Use[:i]
		}
	}
	return c.Use
}

func (c *Command) OutOrStdout() io.Writer {
	if c.out != nil {
		return c.out
	}
	return os.Stdout
}
func (c *Command) Flags() *FlagSet { return &c.flags }

type FlagSet struct{ bools map[string]*bool }

func (f *FlagSet) BoolVar(p *bool, name string, value bool, usage string) {
	if f.bools == nil {
		f.bools = map[string]*bool{}
	}
	*p = value
	f.bools[name] = p
	_ = usage
}
func (c *Command) SetOut(w io.Writer)    { c.out = w }
func (c *Command) Println(a ...any)      { fmt.Fprintln(c.OutOrStdout(), a...) }
