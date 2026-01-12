package tests

import (
	"context"
	"encoding/json"
	"net/http"
	"net/http/httptest"
	"testing"
	"time"

	"eventsec/agent/common/schema"
	"eventsec/agent/common/transport"
)

func TestAgentIntegrationWithMockCollector(t *testing.T) {
	server := httptest.NewServer(http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		switch {
		case r.Method == http.MethodPost && r.URL.Path == "/agents/enroll":
			w.Header().Set("Content-Type", "application/json")
			_ = json.NewEncoder(w).Encode(map[string]interface{}{
				"agent_id": 1,
				"api_key":  "mock-key",
			})
		case r.Method == http.MethodPost && r.URL.Path == "/agents/1/heartbeat":
			w.WriteHeader(http.StatusOK)
		case r.Method == http.MethodPost && r.URL.Path == "/inventory/1":
			w.WriteHeader(http.StatusOK)
			_, _ = w.Write([]byte("[]"))
		case r.Method == http.MethodPost && r.URL.Path == "/events":
			w.WriteHeader(http.StatusOK)
		default:
			http.NotFound(w, r)
		}
	}))
	defer server.Close()

	client, err := transport.NewClient(server.URL, "")
	if err != nil {
		t.Fatal(err)
	}

	enrollResp, err := client.Enroll(context.Background(), transport.EnrollRequest{
		EnrollmentKey: "eventsec-enroll",
		Name:          "test-host",
		OS:            "linux",
		Version:       "dev",
	})
	if err != nil {
		t.Fatal(err)
	}
	client.SetAPIKey(enrollResp.APIKey)

	if err := client.Heartbeat(context.Background(), enrollResp.AgentID, transport.HeartbeatRequest{
		Status:   "online",
		LastSeen: time.Now().UTC(),
		Version:  "dev",
	}); err != nil {
		t.Fatal(err)
	}

	snapshots := []map[string]interface{}{{
		"category": "os",
		"data":     map[string]interface{}{"hostname": "test"},
	}}
	if err := client.SendInventory(context.Background(), enrollResp.AgentID, snapshots); err != nil {
		t.Fatal(err)
	}

	events := []schema.Event{schema.NewEvent("inventory", "agent-1", "test", "linux", map[string]interface{}{"ok": true})}
	if err := client.SendEvents(context.Background(), events); err != nil {
		t.Fatal(err)
	}
}
