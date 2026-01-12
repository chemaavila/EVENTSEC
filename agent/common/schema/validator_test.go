package schema

import "testing"

func TestValidateEvent(t *testing.T) {
	event := NewEvent("inventory", "agent-1", "host", "linux", map[string]interface{}{"ok": true})
	if err := Validate(event); err != nil {
		t.Fatalf("expected valid event, got %v", err)
	}
}

func TestValidateEventMissingFields(t *testing.T) {
	err := Validate(Event{})
	if err == nil {
		t.Fatal("expected error")
	}
}
