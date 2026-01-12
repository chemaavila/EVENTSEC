//go:build windows

package config

import (
	"os"
	"path/filepath"
)

func DefaultConfigPath() string {
	return filepath.Join(os.Getenv("ProgramData"), "Eventsec", "agent.yml")
}

func DefaultStateDir() string {
	return filepath.Join(os.Getenv("ProgramData"), "Eventsec", "state")
}
