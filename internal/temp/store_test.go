package temp

import (
	"strings"
	"testing"
)

func TestPathUsesHash(t *testing.T) {
	p := DraftPath("/tmp/repo", "commit")
	if !strings.Contains(p, "_commit.tmp") { t.Fatal(p) }
}
