package temp

import (
	"crypto/sha1"
	"encoding/hex"
	"encoding/json"
	"os"
	"path/filepath"
)

type Draft struct { Title string `json:"title"`; Body string `json:"body"` }

func DraftPath(repoPath, kind string) string {
	h := sha1.Sum([]byte(repoPath))
	return filepath.Join(os.TempDir(), hex.EncodeToString(h[:])+"_"+kind+".tmp")
}

func Save(repoPath, kind string, d Draft) error {
	b, _ := json.Marshal(d)
	return os.WriteFile(DraftPath(repoPath, kind), b, 0o600)
}
