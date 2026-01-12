package main

import (
	"context"
	"encoding/json"
	"errors"
	"flag"
	"fmt"
	"net"
	"os"
	"os/signal"
	"path/filepath"
	"runtime"
	"strconv"
	"syscall"
	"time"

	"eventsec/agent/common/config"
	"eventsec/agent/common/logging"
	"eventsec/agent/common/queue"
	"eventsec/agent/common/schema"
	"eventsec/agent/common/transport"
	"eventsec/agent/platform"
)

var version = "dev"

func main() {
	if len(os.Args) < 2 {
		fmt.Fprintln(os.Stderr, "usage: eventsec-agent <run|enroll|diagnose|replay>")
		os.Exit(1)
	}

	cmd := os.Args[1]
	switch cmd {
	case "run":
		runCmd(os.Args[2:])
	case "enroll":
		enrollCmd(os.Args[2:])
	case "diagnose":
		diagnoseCmd(os.Args[2:])
	case "replay":
		replayCmd(os.Args[2:])
	default:
		fmt.Fprintln(os.Stderr, "unknown command")
		os.Exit(1)
	}
}

func runCmd(args []string) {
	fs := flag.NewFlagSet("run", flag.ExitOnError)
	cfgPath := fs.String("config", config.DefaultConfigPath(), "Path to agent config")
	stateDir := fs.String("state-dir", config.DefaultStateDir(), "State directory")
	fs.Parse(args)

	cfg, err := config.Load(*cfgPath)
	exitIf(err)
	logger, err := logging.New(cfg.LogLevel)
	exitIf(err)

	localID, err := config.EnsureAgentID(*stateDir)
	exitIf(err)

	exitIf(config.EnsureDir(*stateDir))
	spoolDir := filepath.Join(*stateDir, "spool")
	spool, err := queue.NewDiskQueue(spoolDir, cfg.MaxSpoolMB, 7*24*time.Hour)
	exitIf(err)

	apiKey := cfg.APIKey
	if apiKey == "" {
		if stored, err := config.LoadAPIKey(*stateDir); err == nil {
			apiKey = stored
		}
	}

	client, err := transport.NewClient(cfg.ServerURL, apiKey)
	exitIf(err)

	serverID, err := ensureEnrollment(context.Background(), cfg, client, *stateDir, logger)
	exitIf(err)

	agentID, _ := strconv.Atoi(serverID)

	ctx, stop := signal.NotifyContext(context.Background(), syscall.SIGINT, syscall.SIGTERM)
	defer stop()

	heartbeatTicker := time.NewTicker(cfg.HeartbeatInterval)
	inventoryTicker := time.NewTicker(cfg.InventoryInterval)
	defer heartbeatTicker.Stop()
	defer inventoryTicker.Stop()

	logger.Info(fmt.Sprintf("agent started (id=%s)", localID))

	for {
		select {
		case <-ctx.Done():
			logger.Info("shutting down")
			return
		case <-heartbeatTicker.C:
			if err := sendHeartbeat(ctx, client, agentID); err != nil {
				logger.Warn(fmt.Sprintf("heartbeat failed: %v", err))
			}
		case <-inventoryTicker.C:
			if err := sendInventory(ctx, client, agentID, spool, logger); err != nil {
				logger.Warn(fmt.Sprintf("inventory failed: %v", err))
			}
		default:
			if err := flushSpool(ctx, client, agentID, spool, logger); err != nil {
				logger.Warn(fmt.Sprintf("flush failed: %v", err))
			}
			time.Sleep(2 * time.Second)
		}
	}
}

func enrollCmd(args []string) {
	fs := flag.NewFlagSet("enroll", flag.ExitOnError)
	cfgPath := fs.String("config", config.DefaultConfigPath(), "Path to agent config")
	stateDir := fs.String("state-dir", config.DefaultStateDir(), "State directory")
	fs.Parse(args)

	cfg, err := config.Load(*cfgPath)
	exitIf(err)
	logger, err := logging.New(cfg.LogLevel)
	exitIf(err)

	client, err := transport.NewClient(cfg.ServerURL, cfg.APIKey)
	exitIf(err)
	_, err = ensureEnrollment(context.Background(), cfg, client, *stateDir, logger)
	exitIf(err)
}

func diagnoseCmd(args []string) {
	fs := flag.NewFlagSet("diagnose", flag.ExitOnError)
	cfgPath := fs.String("config", config.DefaultConfigPath(), "Path to agent config")
	stateDir := fs.String("state-dir", config.DefaultStateDir(), "State directory")
	fs.Parse(args)

	cfg, err := config.Load(*cfgPath)
	exitIf(err)

	apiKey, _ := config.LoadAPIKey(*stateDir)
	agentID, _ := config.LoadServerAgentID(*stateDir)
	spool, _ := queue.NewDiskQueue(filepath.Join(*stateDir, "spool"), cfg.MaxSpoolMB, 7*24*time.Hour)
	depth := 0
	if spool != nil {
		depth, _ = spool.Depth()
	}
	output := map[string]interface{}{
		"server_url":         cfg.ServerURL,
		"agent_id":           agentID,
		"api_key_set":        apiKey != "",
		"spool_depth":        depth,
		"heartbeat_interval": cfg.HeartbeatInterval.String(),
		"inventory_interval": cfg.InventoryInterval.String(),
	}
	_ = json.NewEncoder(os.Stdout).Encode(output)
}

func replayCmd(args []string) {
	fs := flag.NewFlagSet("replay", flag.ExitOnError)
	cfgPath := fs.String("config", config.DefaultConfigPath(), "Path to agent config")
	stateDir := fs.String("state-dir", config.DefaultStateDir(), "State directory")
	input := fs.String("input", "", "Path to JSON file")
	fs.Parse(args)

	if *input == "" {
		exitIf(errors.New("input required"))
	}

	cfg, err := config.Load(*cfgPath)
	exitIf(err)
	apiKey, _ := config.LoadAPIKey(*stateDir)
	client, err := transport.NewClient(cfg.ServerURL, apiKey)
	exitIf(err)
	data, err := os.ReadFile(*input)
	exitIf(err)

	var events []schema.Event
	exitIf(json.Unmarshal(data, &events))
	exitIf(client.SendEvents(context.Background(), events))
}

func ensureEnrollment(ctx context.Context, cfg config.Config, client *transport.Client, stateDir string, logger *logging.Logger) (string, error) {
	if cfg.EnrollmentKey == "" && cfg.APIKey == "" {
		return "", errors.New("enrollment_key or api_key required")
	}
	if cfg.APIKey != "" && cfg.ServerAgentID != "" {
		_ = config.SaveAPIKey(stateDir, cfg.APIKey)
		_ = config.SaveServerAgentID(stateDir, cfg.ServerAgentID)
		return cfg.ServerAgentID, nil
	}
	if stored, err := config.LoadServerAgentID(stateDir); err == nil && stored != "" {
		if cfg.APIKey != "" {
			return stored, nil
		}
		if _, err := config.LoadAPIKey(stateDir); err == nil {
			return stored, nil
		}
	}

	hostname, _ := os.Hostname()
	ip := firstIP()
	resp, err := client.Enroll(ctx, transport.EnrollRequest{
		EnrollmentKey: cfg.EnrollmentKey,
		Name:          hostname,
		OS:            runtime.GOOS,
		IPAddress:     ip,
		Version:       version,
	})
	if err != nil {
		return "", err
	}
	client.SetAPIKey(resp.APIKey)
	logger.Info(fmt.Sprintf("enrolled agent_id=%d", resp.AgentID))
	if err := config.SaveAPIKey(stateDir, resp.APIKey); err != nil {
		return "", err
	}
	if err := config.SaveServerAgentID(stateDir, strconv.Itoa(resp.AgentID)); err != nil {
		return "", err
	}
	return strconv.Itoa(resp.AgentID), nil
}

func sendHeartbeat(ctx context.Context, client *transport.Client, agentID int) error {
	return client.Heartbeat(ctx, agentID, transport.HeartbeatRequest{
		Status:   "online",
		LastSeen: time.Now().UTC(),
		Version:  version,
	})
}

func sendInventory(ctx context.Context, client *transport.Client, agentID int, spool *queue.DiskQueue, logger *logging.Logger) error {
	snapshots, err := platform.InventorySnapshots()
	if err != nil {
		return err
	}
	if err := client.SendInventory(ctx, agentID, snapshots); err != nil {
		for _, snap := range snapshots {
			if err := spool.Enqueue(snap); err != nil {
				logger.Warn(fmt.Sprintf("spool enqueue failed: %v", err))
			}
		}
		return err
	}
	return nil
}

func flushSpool(ctx context.Context, client *transport.Client, agentID int, spool *queue.DiskQueue, logger *logging.Logger) error {
	items, err := spool.DequeueBatch(50)
	if err != nil {
		return err
	}
	if len(items) == 0 {
		return nil
	}
	snapshots := make([]map[string]interface{}, 0, len(items))
	for _, item := range items {
		var snap map[string]interface{}
		if err := json.Unmarshal(item.Data, &snap); err != nil {
			logger.Warn(fmt.Sprintf("invalid spool item: %v", err))
			_ = spool.Ack(item.Path)
			continue
		}
		snapshots = append(snapshots, snap)
	}
	if err := client.SendInventory(ctx, agentID, snapshots); err != nil {
		return err
	}
	for _, item := range items {
		_ = spool.Ack(item.Path)
	}
	return nil
}

func firstIP() string {
	addrs, err := net.InterfaceAddrs()
	if err != nil {
		return ""
	}
	for _, addr := range addrs {
		if ipNet, ok := addr.(*net.IPNet); ok && !ipNet.IP.IsLoopback() {
			if ipNet.IP.To4() != nil {
				return ipNet.IP.String()
			}
		}
	}
	return ""
}

func exitIf(err error) {
	if err != nil {
		fmt.Fprintln(os.Stderr, err)
		os.Exit(1)
	}
}
