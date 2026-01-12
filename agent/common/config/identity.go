package config

import (
	"crypto/rand"
	"errors"
	"fmt"
	"os"
	"path/filepath"
)

func EnsureAgentID(stateDir string) (string, error) {
	if stateDir == "" {
		stateDir = DefaultStateDir()
	}
	if err := os.MkdirAll(stateDir, 0o750); err != nil {
		return "", err
	}
	path := filepath.Join(stateDir, "agent_id")
	if data, err := os.ReadFile(path); err == nil {
		id := string(data)
		if id != "" {
			return id, nil
		}
	}
	id := newUUID()
	if err := os.WriteFile(path, []byte(id), 0o600); err != nil {
		return "", err
	}
	return id, nil
}

func EnsureDir(path string) error {
	if path == "" {
		return errors.New("path required")
	}
	return os.MkdirAll(path, 0o750)
}

func newUUID() string {
	var b [16]byte
	_, _ = rand.Read(b[:])
	b[6] = (b[6] & 0x0f) | 0x40
	b[8] = (b[8] & 0x3f) | 0x80
	return fmt.Sprintf("%08x-%04x-%04x-%04x-%012x", b[0:4], b[4:6], b[6:8], b[8:10], b[10:16])
}
