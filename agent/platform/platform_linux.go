//go:build linux

package platform

import "eventsec/agent/platform/linux"

func InventorySnapshots() ([]map[string]interface{}, error) {
	return linux.InventorySnapshots()
}
