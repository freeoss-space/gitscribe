package temp

import (
	"path/filepath"
	"strings"
	"testing"
)

func TestPathUsesCommitSuffix(t *testing.T) {
	p := DraftPath("/tmp/repo", "commit")
	if !strings.Contains(p, "_commit.tmp") {
		t.Fatalf("unexpected path: %s", p)
	}
	base := filepath.Base(p)
	prefix := strings.TrimSuffix(base, "_commit.tmp")
	if len(prefix) != 16 {
		t.Fatalf("expected 16-char hex hash prefix, got %q", prefix)
	}
}
