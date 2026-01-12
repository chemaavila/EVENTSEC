package schema

import "time"

const CurrentSchemaVersion = "1.0.0"

type Event struct {
	SchemaVersion string                 `json:"schema_version"`
	EventType     string                 `json:"event_type"`
	EventID       string                 `json:"event_id"`
	AgentID       string                 `json:"agent_id"`
	Host          string                 `json:"host"`
	OS            string                 `json:"os"`
	TimestampUTC  time.Time              `json:"timestamp_utc"`
	Severity      string                 `json:"severity,omitempty"`
	Attributes    map[string]interface{} `json:"attributes"`
}

func NewEvent(eventType, agentID, host, osName string, attributes map[string]interface{}) Event {
	return Event{
		SchemaVersion: CurrentSchemaVersion,
		EventType:     eventType,
		EventID:       newUUID(),
		AgentID:       agentID,
		Host:          host,
		OS:            osName,
		TimestampUTC:  time.Now().UTC(),
		Attributes:    attributes,
	}
}
