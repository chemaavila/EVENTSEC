//go:build darwin

package config

import "path/filepath"

func DefaultConfigPath() string {
	return filepath.Join("/Library/Application Support/Eventsec", "agent.yml")
}

func DefaultStateDir() string {
	return filepath.Join("/Library/Application Support/Eventsec", "state")
}
