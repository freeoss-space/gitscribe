package temp

import (
	"crypto/sha1"
	"encoding/hex"
	"encoding/json"
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
	h := sha1.Sum([]byte(repoPath))
	return filepath.Join(draftsDir(), hex.EncodeToString(h[:])+"_"+kind+".tmp")
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
