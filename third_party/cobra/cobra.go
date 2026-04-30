package cobra

import (
	"fmt"
	"io"
	"os"
	"strconv"
	"strings"
)

type Command struct {
	Use   string
	RunE  func(*Command, []string) error
	cmds  []*Command
	out   io.Writer
	flags FlagSet
}

func (c *Command) AddCommand(cmds ...*Command) { c.cmds = append(c.cmds, cmds...) }
func (c *Command) Commands() []*Command        { return c.cmds }

func (c *Command) Execute() error {
	return c.executeWith(os.Args[1:])
}

func (c *Command) executeWith(args []string) error {
	if len(args) > 0 {
		for _, cmd := range c.cmds {
			if cmd.commandName() == args[0] {
				remaining, err := cmd.flags.Parse(args[1:])
				if err != nil {
					return err
				}
				if cmd.RunE != nil {
					return cmd.RunE(cmd, remaining)
				}
				return cmd.executeWith(remaining)
			}
		}
		if len(c.cmds) > 0 {
			return fmt.Errorf("unknown command %q", args[0])
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

func (f *FlagSet) Parse(args []string) ([]string, error) {
	var remaining []string
	for _, arg := range args {
		if !strings.HasPrefix(arg, "--") {
			remaining = append(remaining, arg)
			continue
		}
		name := arg[2:]
		val := "true"
		if idx := strings.IndexByte(name, '='); idx >= 0 {
			val = name[idx+1:]
			name = name[:idx]
		}
		if p, ok := f.bools[name]; ok {
			b, err := strconv.ParseBool(val)
			if err != nil {
				return nil, fmt.Errorf("invalid bool value %q for --%s", val, name)
			}
			*p = b
		} else {
			remaining = append(remaining, arg)
		}
	}
	return remaining, nil
}

func (c *Command) SetOut(w io.Writer) { c.out = w }
func (c *Command) Println(a ...any)   { fmt.Fprintln(c.OutOrStdout(), a...) }
