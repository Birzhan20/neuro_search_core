// Package config provides application configuration.
package config

import "os"

// Config holds application settings.
type Config struct {
	Port           string
	RabbitMQURL    string
	RAGServiceAddr string
	UploadPath     string
}

// Load reads configuration from environment.
func Load() *Config {
	return &Config{
		Port:           getEnv("PORT", "8080"),
		RabbitMQURL:    getEnv("RABBITMQ_URL", "amqp://guest:guest@localhost:5672/"),
		RAGServiceAddr: getEnv("RAG_SERVICE_URL", "localhost:50051"),
		UploadPath:     getEnv("UPLOAD_PATH", "/app/uploads"),
	}
}

func getEnv(key, defaultVal string) string {
	if val := os.Getenv(key); val != "" {
		return val
	}
	return defaultVal
}
