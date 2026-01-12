package transport

import (
	"bytes"
	"compress/gzip"
	"context"
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"math/rand"
	"net/http"
	"net/url"
	"time"

	"eventsec/agent/common/schema"
)

type Client struct {
	baseURL   *url.URL
	apiKey    string
	userAgent string
	client    *http.Client
}

type EnrollRequest struct {
	EnrollmentKey string `json:"enrollment_key"`
	Name          string `json:"name"`
	OS            string `json:"os"`
	IPAddress     string `json:"ip_address,omitempty"`
	Version       string `json:"version"`
}

type EnrollResponse struct {
	AgentID int    `json:"agent_id"`
	APIKey  string `json:"api_key"`
}

type HeartbeatRequest struct {
	Status    string    `json:"status"`
	LastSeen  time.Time `json:"last_seen"`
	Version   string    `json:"version"`
	IPAddress string    `json:"ip_address,omitempty"`
}

func NewClient(rawURL, apiKey string) (*Client, error) {
	parsed, err := url.Parse(rawURL)
	if err != nil {
		return nil, err
	}
	if parsed.Scheme != "https" && parsed.Scheme != "http" {
		return nil, errors.New("invalid server_url")
	}
	return &Client{
		baseURL: parsed,
		apiKey:  apiKey,
		client: &http.Client{
			Timeout: 15 * time.Second,
		},
		userAgent: "eventsec-agent/1.0",
	}, nil
}

func (c *Client) SetAPIKey(apiKey string) {
	c.apiKey = apiKey
}

func (c *Client) Enroll(ctx context.Context, req EnrollRequest) (EnrollResponse, error) {
	var resp EnrollResponse
	err := c.doJSON(ctx, http.MethodPost, "/agents/enroll", req, &resp, "")
	return resp, err
}

func (c *Client) Heartbeat(ctx context.Context, agentID int, req HeartbeatRequest) error {
	path := fmt.Sprintf("/agents/%d/heartbeat", agentID)
	return c.doJSON(ctx, http.MethodPost, path, req, nil, c.apiKey)
}

func (c *Client) SendEvents(ctx context.Context, events []schema.Event) error {
	for _, event := range events {
		payload := map[string]interface{}{
			"event_type": event.EventType,
			"severity":   event.Severity,
			"category":   "agent",
			"details":    event.Attributes,
		}
		if err := c.doJSON(ctx, http.MethodPost, "/events", payload, nil, c.apiKey); err != nil {
			return err
		}
	}
	return nil
}

func (c *Client) SendInventory(ctx context.Context, agentID int, snapshots []map[string]interface{}) error {
	payload := map[string]interface{}{
		"snapshots": snapshots,
	}
	path := fmt.Sprintf("/inventory/%d", agentID)
	return c.doJSON(ctx, http.MethodPost, path, payload, nil, c.apiKey)
}

func (c *Client) doJSON(ctx context.Context, method, path string, payload interface{}, out interface{}, apiKey string) error {
	endpoint := c.baseURL.ResolveReference(&url.URL{Path: path})
	body, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	compressed, contentEncoding := gzipPayload(body)
	req, err := http.NewRequestWithContext(ctx, method, endpoint.String(), bytes.NewReader(compressed))
	if err != nil {
		return err
	}
	req.Header.Set("Content-Type", "application/json")
	req.Header.Set("User-Agent", c.userAgent)
	if contentEncoding != "" {
		req.Header.Set("Content-Encoding", contentEncoding)
	}
	if apiKey != "" {
		req.Header.Set("X-Agent-Key", apiKey)
	}

	resp, err := c.client.Do(req)
	if err != nil {
		return err
	}
	defer resp.Body.Close()

	if resp.StatusCode >= 400 {
		data, _ := io.ReadAll(resp.Body)
		return fmt.Errorf("request failed: %s", string(data))
	}
	if out != nil {
		return json.NewDecoder(resp.Body).Decode(out)
	}
	return nil
}

func gzipPayload(data []byte) ([]byte, string) {
	if len(data) < 512 {
		return data, ""
	}
	var buf bytes.Buffer
	writer := gzip.NewWriter(&buf)
	_, _ = writer.Write(data)
	_ = writer.Close()
	return buf.Bytes(), "gzip"
}

func BackoffDelay(attempt int) time.Duration {
	if attempt <= 0 {
		attempt = 1
	}
	base := time.Duration(attempt*attempt) * time.Second
	jitter := time.Duration(rand.Intn(500)) * time.Millisecond
	return base + jitter
}
