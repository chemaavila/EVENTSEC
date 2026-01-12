//go:build darwin

package platform

import "eventsec/agent/platform/darwin"

func InventorySnapshots() ([]map[string]interface{}, error) {
	return darwin.InventorySnapshots()
}
