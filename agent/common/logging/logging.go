package logging

import (
	"log"
	"os"
	"strings"
)

type Logger struct {
	*log.Logger
	level string
}

func New(level string) (*Logger, error) {
	return &Logger{
		Logger: log.New(os.Stdout, "", log.LstdFlags|log.LUTC),
		level:  strings.ToLower(level),
	}, nil
}

func (l *Logger) Debug(msg string) {
	if l.level == "debug" {
		l.Printf("debug: %s", msg)
	}
}

func (l *Logger) Info(msg string) {
	l.Printf("info: %s", msg)
}

func (l *Logger) Warn(msg string) {
	l.Printf("warn: %s", msg)
}

func (l *Logger) Error(msg string) {
	l.Printf("error: %s", msg)
}
