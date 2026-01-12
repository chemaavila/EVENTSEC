package config

import (
	"bufio"
	"encoding/json"
	"errors"
	"os"
	"path/filepath"
	"strings"
	"time"
)

type Config struct {
	ServerURL         string        `json:"server_url" yaml:"server_url"`
	APIKey            string        `json:"api_key" yaml:"api_key"`
	EnrollmentKey     string        `json:"enrollment_key" yaml:"enrollment_key"`
	ServerAgentID     string        `json:"server_agent_id" yaml:"server_agent_id"`
	HeartbeatInterval time.Duration `json:"heartbeat_interval" yaml:"heartbeat_interval"`
	InventoryInterval time.Duration `json:"inventory_interval" yaml:"inventory_interval"`
	WatchedPaths      []string      `json:"watched_paths" yaml:"watched_paths"`
	MaxSpoolMB        int           `json:"max_spool_mb" yaml:"max_spool_mb"`
	LogLevel          string        `json:"log_level" yaml:"log_level"`
	EnableFileHashing bool          `json:"enable_file_hashing" yaml:"enable_file_hashing"`
	IOCFeedInterval   time.Duration `json:"ioc_feed_interval" yaml:"ioc_feed_interval"`
}

func Default() Config {
	return Config{
		ServerURL:         "https://localhost:8443",
		HeartbeatInterval: 30 * time.Second,
		InventoryInterval: 10 * time.Minute,
		MaxSpoolMB:        256,
		LogLevel:          "info",
		IOCFeedInterval:   30 * time.Minute,
	}
}

func Load(path string) (Config, error) {
	cfg := Default()
	if path == "" {
		return cfg, errors.New("config path is required")
	}

	data, err := os.ReadFile(path)
	if err != nil {
		return cfg, err
	}

	ext := strings.ToLower(filepath.Ext(path))
	switch ext {
	case ".json":
		if err := json.Unmarshal(data, &cfg); err != nil {
			return cfg, err
		}
	case ".yaml", ".yml":
		if err := parseYAML(data, &cfg); err != nil {
			return cfg, err
		}
	default:
		if err := json.Unmarshal(data, &cfg); err != nil {
			if err := parseYAML(data, &cfg); err != nil {
				return cfg, errors.New("unsupported config format")
			}
		}
	}

	if cfg.HeartbeatInterval == 0 {
		cfg.HeartbeatInterval = Default().HeartbeatInterval
	}
	if cfg.InventoryInterval == 0 {
		cfg.InventoryInterval = Default().InventoryInterval
	}
	if cfg.MaxSpoolMB == 0 {
		cfg.MaxSpoolMB = Default().MaxSpoolMB
	}
	if cfg.LogLevel == "" {
		cfg.LogLevel = Default().LogLevel
	}
	if cfg.IOCFeedInterval == 0 {
		cfg.IOCFeedInterval = Default().IOCFeedInterval
	}
	return cfg, nil
}

func parseYAML(data []byte, cfg *Config) error {
	scanner := bufio.NewScanner(strings.NewReader(string(data)))
	var currentList *string
	for scanner.Scan() {
		line := strings.TrimSpace(scanner.Text())
		if line == "" || strings.HasPrefix(line, "#") {
			continue
		}
		if strings.HasPrefix(line, "-") && currentList != nil {
			value := strings.TrimSpace(strings.TrimPrefix(line, "-"))
			if *currentList == "watched_paths" {
				cfg.WatchedPaths = append(cfg.WatchedPaths, value)
			}
			continue
		}
		parts := strings.SplitN(line, ":", 2)
		if len(parts) != 2 {
			continue
		}
		key := strings.TrimSpace(parts[0])
		value := strings.TrimSpace(parts[1])
		currentList = nil
		switch key {
		case "server_url":
			cfg.ServerURL = value
		case "api_key":
			cfg.APIKey = value
		case "enrollment_key":
			cfg.EnrollmentKey = value
		case "server_agent_id":
			cfg.ServerAgentID = value
		case "heartbeat_interval":
			if parsed, err := time.ParseDuration(value); err == nil {
				cfg.HeartbeatInterval = parsed
			}
		case "inventory_interval":
			if parsed, err := time.ParseDuration(value); err == nil {
				cfg.InventoryInterval = parsed
			}
		case "max_spool_mb":
			if parsed, err := parseInt(value); err == nil {
				cfg.MaxSpoolMB = parsed
			}
		case "log_level":
			cfg.LogLevel = value
		case "enable_file_hashing":
			cfg.EnableFileHashing = strings.EqualFold(value, "true")
		case "ioc_feed_interval":
			if parsed, err := time.ParseDuration(value); err == nil {
				cfg.IOCFeedInterval = parsed
			}
		case "watched_paths":
			currentList = &key
		}
	}
	return scanner.Err()
}

func parseInt(value string) (int, error) {
	trimmed := strings.TrimSpace(value)
	if trimmed == "" {
		return 0, errors.New("empty")
	}
	var num int
	for _, r := range trimmed {
		if r < '0' || r > '9' {
			return 0, errors.New("invalid number")
		}
		num = num*10 + int(r-'0')
	}
	return num, nil
}
