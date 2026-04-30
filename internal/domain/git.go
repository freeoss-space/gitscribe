package domain

// GitClient exposes the git operations gitscribe needs.
type GitClient interface {
	HasStagedChanges() (bool, error)
	GetStagedDiff() (string, error)
	GetBranchDiff(baseBranch string) (string, error)
	GetCurrentBranch() (string, error)
	GetDefaultBranch() (string, error)
	Commit(message string) error
	GetRepoRoot() (string, error)
	FindPRTemplate() (string, error)
}
