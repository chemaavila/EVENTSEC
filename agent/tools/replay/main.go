package main

import (
	"context"
	"encoding/json"
	"flag"
	"log"
	"os"

	"eventsec/agent/common/schema"
	"eventsec/agent/common/transport"
)

func main() {
	var serverURL string
	var apiKey string
	var input string
	flag.StringVar(&serverURL, "server", "http://localhost:8081", "Server URL")
	flag.StringVar(&apiKey, "api-key", "", "Agent API key")
	flag.StringVar(&input, "input", "", "Path to JSON file")
	flag.Parse()

	if input == "" {
		log.Fatal("input required")
	}

	client, err := transport.NewClient(serverURL, apiKey)
	if err != nil {
		log.Fatal(err)
	}

	data, err := os.ReadFile(input)
	if err != nil {
		log.Fatal(err)
	}

	var events []schema.Event
	if err := json.Unmarshal(data, &events); err != nil {
		log.Fatal(err)
	}

	if err := client.SendEvents(context.Background(), events); err != nil {
		log.Fatal(err)
	}
}
