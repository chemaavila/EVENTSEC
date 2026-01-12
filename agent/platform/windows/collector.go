//go:build windows

package windows

import (
	"bufio"
	"bytes"
	"os"
	"os/exec"
	"runtime"
	"strings"
	"time"
)

func InventorySnapshots() ([]map[string]interface{}, error) {
	hostname, _ := os.Hostname()
	snapshots := []map[string]interface{}{
		{
			"category": "os",
			"data": map[string]interface{}{
				"hostname": hostname,
				"os":       runtime.GOOS,
				"arch":     runtime.GOARCH,
			},
		},
	}

	processes := processSnapshot()
	snapshots = append(snapshots, map[string]interface{}{
		"category": "processes",
		"data": map[string]interface{}{
			"processes": processes,
		},
	})

	connections := networkSnapshot()
	snapshots = append(snapshots, map[string]interface{}{
		"category": "network_connections",
		"data": map[string]interface{}{
			"connections": connections,
		},
	})

	users := loggedInUsers()
	snapshots = append(snapshots, map[string]interface{}{
		"category": "logged_in_users",
		"data": map[string]interface{}{
			"users": users,
		},
	})

	return snapshots, nil
}

func processSnapshot() []map[string]interface{} {
	output := runCommand("tasklist", "/fo", "csv", "/nh")
	scanner := bufio.NewScanner(bytes.NewReader(output))
	processes := []map[string]interface{}{}
	for scanner.Scan() {
		line := strings.Trim(scanner.Text(), "\r\n")
		parts := parseCSVLine(line)
		if len(parts) < 2 {
			continue
		}
		processes = append(processes, map[string]interface{}{
			"name": parts[0],
			"pid":  parts[1],
		})
	}
	return processes
}

func networkSnapshot() []map[string]interface{} {
	output := runCommand("netstat", "-ano")
	scanner := bufio.NewScanner(bytes.NewReader(output))
	connections := []map[string]interface{}{}
	for scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) < 4 {
			continue
		}
		proto := strings.ToLower(fields[0])
		if !strings.HasPrefix(proto, "tcp") && !strings.HasPrefix(proto, "udp") {
			continue
		}
		localAddr := fields[1]
		remoteAddr := fields[2]
		connections = append(connections, map[string]interface{}{
			"type":        proto,
			"local_addr":  localAddr,
			"remote_addr": remoteAddr,
			"pid":         fields[len(fields)-1],
		})
	}
	return connections
}

func loggedInUsers() []map[string]interface{} {
	output := runCommand("query", "user")
	scanner := bufio.NewScanner(bytes.NewReader(output))
	users := []map[string]interface{}{}
	first := true
	for scanner.Scan() {
		if first {
			first = false
			continue
		}
		fields := strings.Fields(scanner.Text())
		if len(fields) == 0 {
			continue
		}
		users = append(users, map[string]interface{}{
			"user":        fields[0],
			"recorded_at": time.Now().UTC(),
		})
	}
	return users
}

func runCommand(name string, args ...string) []byte {
	cmd := exec.Command(name, args...)
	output, err := cmd.Output()
	if err != nil {
		return []byte{}
	}
	return output
}

func parseCSVLine(line string) []string {
	trimmed := strings.TrimSpace(line)
	if trimmed == "" {
		return nil
	}
	trimmed = strings.TrimPrefix(trimmed, "\"")
	trimmed = strings.TrimSuffix(trimmed, "\"")
	parts := strings.Split(trimmed, "\",\"")
	for i, part := range parts {
		parts[i] = strings.Trim(part, "\"")
	}
	return parts
}
