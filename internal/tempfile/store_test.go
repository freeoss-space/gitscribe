package tempfile

import (
	"os"
	"testing"

	"github.com/stretchr/testify/assert"
	"github.com/stretchr/testify/require"
)

func TestSaveAndLoadCommit(t *testing.T) {
	s := newWithDir(t.TempDir())
	d := Draft{Title: "feat: add thing", Body: "- does stuff"}

	require.NoError(t, s.SaveCommit("/repo/myproject", d))

	loaded, err := s.LoadCommit("/repo/myproject")
	require.NoError(t, err)
	require.NotNil(t, loaded)
	assert.Equal(t, d.Title, loaded.Title)
	assert.Equal(t, d.Body, loaded.Body)
}

func TestLoadCommit_NoneExists(t *testing.T) {
	s := newWithDir(t.TempDir())
	loaded, err := s.LoadCommit("/some/repo")
	require.NoError(t, err)
	assert.Nil(t, loaded)
}

func TestDeleteCommit(t *testing.T) {
	s := newWithDir(t.TempDir())
	require.NoError(t, s.SaveCommit("/repo", Draft{Title: "feat: x"}))
	require.NoError(t, s.DeleteCommit("/repo"))

	loaded, err := s.LoadCommit("/repo")
	require.NoError(t, err)
	assert.Nil(t, loaded)
}

func TestDeleteCommit_NotExist_NoError(t *testing.T) {
	s := newWithDir(t.TempDir())
	assert.NoError(t, s.DeleteCommit("/nonexistent/repo"))
}

func TestSaveAndLoadPR(t *testing.T) {
	s := newWithDir(t.TempDir())
	d := Draft{Title: "Add feature X", Body: "## Summary\n- does X"}

	require.NoError(t, s.SavePR("/repo", d))

	loaded, err := s.LoadPR("/repo")
	require.NoError(t, err)
	require.NotNil(t, loaded)
	assert.Equal(t, d.Title, loaded.Title)
}

func TestLoadCommit_CorruptFile(t *testing.T) {
	s := newWithDir(t.TempDir())
	path := s.commitPath("/repo")
	require.NoError(t, os.WriteFile(path, []byte("{corrupt"), 0o600))

	loaded, err := s.LoadCommit("/repo")
	require.NoError(t, err)
	assert.Nil(t, loaded, "corrupt file should be silently ignored")
}

func TestHashPath_Deterministic(t *testing.T) {
	h1 := hashPath("/home/user/project")
	h2 := hashPath("/home/user/project")
	assert.Equal(t, h1, h2)
}

func TestHashPath_DifferentPaths(t *testing.T) {
	h1 := hashPath("/path/a")
	h2 := hashPath("/path/b")
	assert.NotEqual(t, h1, h2)
}

func TestHashPath_Length(t *testing.T) {
	h := hashPath("/any/path")
	assert.Len(t, h, 16, "should be 16 hex chars (8 bytes)")
}
