package queue

import (
	"encoding/json"
	"os"
	"path/filepath"
	"testing"
	"time"
)

func TestDiskQueueEnqueueDequeue(t *testing.T) {
	dir := filepath.Join(os.TempDir(), "eventsec-spool-test")
	_ = os.RemoveAll(dir)
	t.Cleanup(func() { _ = os.RemoveAll(dir) })

	q, err := NewDiskQueue(dir, 1, time.Hour)
	if err != nil {
		t.Fatal(err)
	}

	payload := map[string]interface{}{"category": "os"}
	if err := q.Enqueue(payload); err != nil {
		t.Fatal(err)
	}

	items, err := q.DequeueBatch(1)
	if err != nil {
		t.Fatal(err)
	}
	if len(items) != 1 {
		t.Fatalf("expected 1 item, got %d", len(items))
	}

	var decoded map[string]interface{}
	if err := json.Unmarshal(items[0].Data, &decoded); err != nil {
		t.Fatal(err)
	}
	if decoded["category"] != "os" {
		t.Fatalf("unexpected payload: %v", decoded)
	}

	if err := q.Ack(items[0].Path); err != nil {
		t.Fatal(err)
	}
}
