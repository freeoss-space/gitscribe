package temp

import (
	"encoding/json"
	"fmt"
	"hash/fnv"
	"os"
	"path/filepath"
)

type Draft struct {
	Title string `json:"title"`
	Body  string `json:"body"`
}

func draftsDir() string {
	return filepath.Join(os.TempDir(), "drafts")
}

func DraftPath(repoPath, kind string) string {
	h := fnv.New64a()
	h.Write([]byte(repoPath))
	return filepath.Join(draftsDir(), fmt.Sprintf("%016x_%s.tmp", h.Sum64(), kind))
}

func Save(repoPath, kind string, d Draft) error {
	if err := os.MkdirAll(draftsDir(), 0o700); err != nil {
		return err
	}
	b, err := json.Marshal(d)
	if err != nil {
		return err
	}
	return os.WriteFile(DraftPath(repoPath, kind), b, 0o600)
}
