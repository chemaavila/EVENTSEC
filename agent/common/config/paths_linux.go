//go:build linux

package config

import "path/filepath"

func DefaultConfigPath() string {
	return filepath.Join("/etc/eventsec", "agent.yml")
}

func DefaultStateDir() string {
	return filepath.Join("/var/lib/eventsec", "state")
}
