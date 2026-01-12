package main

import (
	"encoding/json"
	"log"
	"net/http"
	"sync/atomic"
	"time"
)

type enrollRequest struct {
	EnrollmentKey string `json:"enrollment_key"`
	Name          string `json:"name"`
	OS            string `json:"os"`
	IPAddress     string `json:"ip_address"`
	Version       string `json:"version"`
}

type enrollResponse struct {
	AgentID int    `json:"agent_id"`
	APIKey  string `json:"api_key"`
}

type inventoryRequest struct {
	Snapshots []map[string]interface{} `json:"snapshots"`
}

type heartbeatRequest struct {
	Status   string    `json:"status"`
	LastSeen time.Time `json:"last_seen"`
	Version  string    `json:"version"`
}

func main() {
	var agentCounter int64
	mux := http.NewServeMux()

	mux.HandleFunc("/agents/enroll", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		var req enrollRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "invalid request", http.StatusBadRequest)
			return
		}
		if req.EnrollmentKey == "" {
			http.Error(w, "missing enrollment_key", http.StatusUnauthorized)
			return
		}
		id := int(atomic.AddInt64(&agentCounter, 1))
		resp := enrollResponse{AgentID: id, APIKey: "mock-api-key"}
		_ = json.NewEncoder(w).Encode(resp)
	})

	mux.HandleFunc("/agents/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		if !checkAgentKey(r) {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"detail":"ok"}`))
	})

	mux.HandleFunc("/inventory/", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		if !checkAgentKey(r) {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		var req inventoryRequest
		if err := json.NewDecoder(r.Body).Decode(&req); err != nil {
			http.Error(w, "invalid request", http.StatusBadRequest)
			return
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`[]`))
	})

	mux.HandleFunc("/events", func(w http.ResponseWriter, r *http.Request) {
		if r.Method != http.MethodPost {
			http.Error(w, "method not allowed", http.StatusMethodNotAllowed)
			return
		}
		if !checkAgentKey(r) {
			http.Error(w, "unauthorized", http.StatusUnauthorized)
			return
		}
		w.WriteHeader(http.StatusOK)
		_, _ = w.Write([]byte(`{"detail":"accepted"}`))
	})

	addr := ":8081"
	log.Printf("mock collector listening on %s", addr)
	log.Fatal(http.ListenAndServe(addr, mux))
}

func checkAgentKey(r *http.Request) bool {
	return r.Header.Get("X-Agent-Key") != "" || r.Header.Get("X-Agent-Token") != ""
}
