//go:build windows

package platform

import "eventsec/agent/platform/windows"

func InventorySnapshots() ([]map[string]interface{}, error) {
	return windows.InventorySnapshots()
}
