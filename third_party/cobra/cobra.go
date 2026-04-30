package cobra

import (
	"fmt"
	"io"
	"os"
)

type Command struct {
	Use string
	RunE func(*Command, []string) error
	cmds []*Command
	out io.Writer
	flags FlagSet
}
func (c *Command) AddCommand(cmds ...*Command){ c.cmds = append(c.cmds, cmds...) }
func (c *Command) Commands() []*Command { return c.cmds }
func (c *Command) Execute() error { if c.RunE != nil { return c.RunE(c, nil) }; return nil }
func (c *Command) OutOrStdout() io.Writer { if c.out!=nil {return c.out}; return os.Stdout }
func (c *Command) Flags() *FlagSet { return &c.flags }

type FlagSet struct{ bools map[string]*bool }
func (f *FlagSet) BoolVar(p *bool, name string, value bool, usage string) { if f.bools==nil {f.bools=map[string]*bool{}}; *p=value; f.bools[name]=p; _=usage }
func (c *Command) SetOut(w io.Writer){ c.out=w }
func (c *Command) Println(a ...any){ fmt.Fprintln(c.OutOrStdout(), a...) }
