package schema

import "errors"

func Validate(event Event) error {
	if event.SchemaVersion == "" {
		return errors.New("schema_version is required")
	}
	if event.EventType == "" {
		return errors.New("event_type is required")
	}
	if event.EventID == "" {
		return errors.New("event_id is required")
	}
	if event.AgentID == "" {
		return errors.New("agent_id is required")
	}
	if event.Host == "" {
		return errors.New("host is required")
	}
	if event.OS == "" {
		return errors.New("os is required")
	}
	if event.TimestampUTC.IsZero() {
		return errors.New("timestamp_utc is required")
	}
	if event.Attributes == nil {
		return errors.New("attributes is required")
	}
	return nil
}
