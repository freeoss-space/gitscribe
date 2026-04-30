package tempfile

import (
	"crypto/sha256"
	"encoding/json"
	"fmt"
	"os"
	"path/filepath"
)

// Draft holds an in-progress commit or PR message.
type Draft struct {
	Title string `json:"title"`
	Body  string `json:"body"`
}

// Store persists drafts in the OS temp directory, keyed by a hash of the repo path.
type Store struct {
	dir string // override for tests
}

// New returns a Store that writes to os.TempDir().
func New() *Store { return &Store{} }

// NewWithDir returns a Store that writes to dir. Used by tests.
func NewWithDir(dir string) *Store { return &Store{dir: dir} }

// newWithDir is an internal alias for use within the package tests.
func newWithDir(dir string) *Store { return &Store{dir: dir} }

func (s *Store) baseDir() string {
	if s.dir != "" {
		return s.dir
	}
	return os.TempDir()
}

// SaveCommit persists a commit draft for the given repo path.
func (s *Store) SaveCommit(repoPath string, d Draft) error {
	return s.save(s.commitPath(repoPath), d)
}

// LoadCommit loads a commit draft. Returns nil if none exists.
func (s *Store) LoadCommit(repoPath string) (*Draft, error) {
	return s.load(s.commitPath(repoPath))
}

// DeleteCommit removes the commit draft file.
func (s *Store) DeleteCommit(repoPath string) error {
	return s.delete(s.commitPath(repoPath))
}

// SavePR persists a PR draft.
func (s *Store) SavePR(repoPath string, d Draft) error {
	return s.save(s.prPath(repoPath), d)
}

// LoadPR loads a PR draft. Returns nil if none exists.
func (s *Store) LoadPR(repoPath string) (*Draft, error) {
	return s.load(s.prPath(repoPath))
}

// DeletePR removes the PR draft file.
func (s *Store) DeletePR(repoPath string) error {
	return s.delete(s.prPath(repoPath))
}

func (s *Store) commitPath(repoPath string) string {
	return filepath.Join(s.baseDir(), fmt.Sprintf("%s_commit.tmp", hashPath(repoPath)))
}

func (s *Store) prPath(repoPath string) string {
	return filepath.Join(s.baseDir(), fmt.Sprintf("%s_pr.tmp", hashPath(repoPath)))
}

// hashPath returns the first 16 hex chars of the sha256 of path.
func hashPath(path string) string {
	h := sha256.Sum256([]byte(path))
	return fmt.Sprintf("%x", h[:8])
}

func (s *Store) save(path string, d Draft) error {
	data, err := json.MarshalIndent(d, "", "  ")
	if err != nil {
		return err
	}
	return os.WriteFile(path, data, 0o600)
}

func (s *Store) load(path string) (*Draft, error) {
	data, err := os.ReadFile(path)
	if os.IsNotExist(err) {
		return nil, nil
	}
	if err != nil {
		return nil, err
	}
	var d Draft
	if err := json.Unmarshal(data, &d); err != nil {
		// Corrupt file — ignore silently.
		_ = os.Remove(path)
		return nil, nil
	}
	return &d, nil
}

func (s *Store) delete(path string) error {
	err := os.Remove(path)
	if os.IsNotExist(err) {
		return nil
	}
	return err
}
