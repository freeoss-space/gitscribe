package config

import "os/exec"

// newExecCommand is a var so tests can replace it.
var newExecCommand = func(name string, args ...string) *exec.Cmd {
	return exec.Command(name, args...)
}
