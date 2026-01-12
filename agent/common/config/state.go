package config

import (
	"os"
	"path/filepath"
)

func LoadAPIKey(stateDir string) (string, error) {
	if stateDir == "" {
		stateDir = DefaultStateDir()
	}
	path := filepath.Join(stateDir, "api_key")
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

func SaveAPIKey(stateDir, apiKey string) error {
	if stateDir == "" {
		stateDir = DefaultStateDir()
	}
	if err := os.MkdirAll(stateDir, 0o750); err != nil {
		return err
	}
	path := filepath.Join(stateDir, "api_key")
	return os.WriteFile(path, []byte(apiKey), 0o600)
}

func LoadServerAgentID(stateDir string) (string, error) {
	if stateDir == "" {
		stateDir = DefaultStateDir()
	}
	path := filepath.Join(stateDir, "server_agent_id")
	data, err := os.ReadFile(path)
	if err != nil {
		return "", err
	}
	return string(data), nil
}

func SaveServerAgentID(stateDir, agentID string) error {
	if stateDir == "" {
		stateDir = DefaultStateDir()
	}
	if err := os.MkdirAll(stateDir, 0o750); err != nil {
		return err
	}
	path := filepath.Join(stateDir, "server_agent_id")
	return os.WriteFile(path, []byte(agentID), 0o600)
}
