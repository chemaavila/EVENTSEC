package queue

import (
	"encoding/json"
	"errors"
	"fmt"
	"io"
	"os"
	"path/filepath"
	"sort"
	"strings"
	"time"
)

type DiskQueue struct {
	dir       string
	maxBytes  int64
	retention time.Duration
}

type Item struct {
	Path string
	Data []byte
}

func NewDiskQueue(dir string, maxMB int, retention time.Duration) (*DiskQueue, error) {
	if dir == "" {
		return nil, errors.New("spool dir required")
	}
	if maxMB <= 0 {
		maxMB = 256
	}
	if retention <= 0 {
		retention = 7 * 24 * time.Hour
	}
	if err := os.MkdirAll(dir, 0o750); err != nil {
		return nil, err
	}
	return &DiskQueue{
		dir:       dir,
		maxBytes:  int64(maxMB) * 1024 * 1024,
		retention: retention,
	}, nil
}

func (q *DiskQueue) Enqueue(payload interface{}) error {
	if payload == nil {
		return errors.New("payload required")
	}
	data, err := json.Marshal(payload)
	if err != nil {
		return err
	}
	if err := q.enforceLimits(int64(len(data))); err != nil {
		return err
	}
	filename := fmt.Sprintf("%d_%d.json", time.Now().UnixNano(), time.Now().UnixNano())
	path := filepath.Join(q.dir, filename)
	return os.WriteFile(path, data, 0o640)
}

func (q *DiskQueue) DequeueBatch(limit int) ([]Item, error) {
	if limit <= 0 {
		limit = 100
	}
	entries, err := os.ReadDir(q.dir)
	if err != nil {
		return nil, err
	}
	filenames := make([]string, 0, len(entries))
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		if strings.HasSuffix(entry.Name(), ".json") {
			filenames = append(filenames, entry.Name())
		}
	}
	sort.Strings(filenames)
	if len(filenames) > limit {
		filenames = filenames[:limit]
	}
	items := make([]Item, 0, len(filenames))
	for _, name := range filenames {
		path := filepath.Join(q.dir, name)
		data, err := os.ReadFile(path)
		if err != nil {
			return nil, err
		}
		items = append(items, Item{Path: path, Data: data})
	}
	return items, nil
}

func (q *DiskQueue) Ack(path string) error {
	if path == "" {
		return errors.New("path required")
	}
	return os.Remove(path)
}

func (q *DiskQueue) Depth() (int, error) {
	entries, err := os.ReadDir(q.dir)
	if err != nil {
		return 0, err
	}
	count := 0
	for _, entry := range entries {
		if entry.IsDir() {
			continue
		}
		if strings.HasSuffix(entry.Name(), ".json") {
			count++
		}
	}
	return count, nil
}

func (q *DiskQueue) enforceLimits(incoming int64) error {
	total, err := dirSize(q.dir)
	if err != nil {
		return err
	}
	deadline := time.Now().Add(-q.retention)
	if err := q.pruneOlderThan(deadline); err != nil {
		return err
	}
	for total+incoming > q.maxBytes {
		oldest, err := q.oldestFile()
		if err != nil {
			return err
		}
		if oldest == "" {
			return errors.New("spool is full")
		}
		info, err := os.Stat(oldest)
		if err != nil {
			return err
		}
		if err := os.Remove(oldest); err != nil {
			return err
		}
		total -= info.Size()
	}
	return nil
}

func (q *DiskQueue) oldestFile() (string, error) {
	entries, err := os.ReadDir(q.dir)
	if err != nil {
		return "", err
	}
	var oldest string
	var oldestTime time.Time
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}
		info, err := entry.Info()
		if err != nil {
			return "", err
		}
		if oldest == "" || info.ModTime().Before(oldestTime) {
			oldest = filepath.Join(q.dir, entry.Name())
			oldestTime = info.ModTime()
		}
	}
	return oldest, nil
}

func (q *DiskQueue) pruneOlderThan(cutoff time.Time) error {
	entries, err := os.ReadDir(q.dir)
	if err != nil {
		return err
	}
	for _, entry := range entries {
		if entry.IsDir() || !strings.HasSuffix(entry.Name(), ".json") {
			continue
		}
		info, err := entry.Info()
		if err != nil {
			return err
		}
		if info.ModTime().Before(cutoff) {
			if err := os.Remove(filepath.Join(q.dir, entry.Name())); err != nil {
				return err
			}
		}
	}
	return nil
}

func dirSize(path string) (int64, error) {
	var size int64
	err := filepath.Walk(path, func(_ string, info os.FileInfo, err error) error {
		if err != nil {
			return err
		}
		if !info.IsDir() {
			size += info.Size()
		}
		return nil
	})
	if errors.Is(err, io.EOF) {
		return size, nil
	}
	return size, err
}
