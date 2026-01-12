//go:build linux

package linux

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
				"kernel":   runtime.GOARCH,
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
	output := runCommand("ps", "-eo", "pid,ppid,comm")
	scanner := bufio.NewScanner(bytes.NewReader(output))
	processes := []map[string]interface{}{}
	first := true
	for scanner.Scan() {
		line := strings.Fields(scanner.Text())
		if first {
			first = false
			continue
		}
		if len(line) < 3 {
			continue
		}
		processes = append(processes, map[string]interface{}{
			"pid":  line[0],
			"ppid": line[1],
			"name": line[2],
		})
	}
	return processes
}

func networkSnapshot() []map[string]interface{} {
	output := runCommand("netstat", "-an")
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
		localAddr := fields[3]
		remoteAddr := fields[4]
		connections = append(connections, map[string]interface{}{
			"type":        proto,
			"local_addr":  localAddr,
			"remote_addr": remoteAddr,
		})
	}
	return connections
}

func loggedInUsers() []map[string]interface{} {
	output := runCommand("who")
	scanner := bufio.NewScanner(bytes.NewReader(output))
	users := []map[string]interface{}{}
	for scanner.Scan() {
		fields := strings.Fields(scanner.Text())
		if len(fields) < 3 {
			continue
		}
		users = append(users, map[string]interface{}{
			"user":        fields[0],
			"terminal":    fields[1],
			"logged_in":   strings.Join(fields[2:], " "),
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
