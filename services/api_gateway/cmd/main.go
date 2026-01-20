// Package main is the entry point for API Gateway.
package main

import (
	"log"

	"neuro_search/gateway/internal/config"
	"neuro_search/gateway/internal/grpc_client"
	"neuro_search/gateway/internal/handlers"
	"neuro_search/gateway/internal/rabbitmq"

	"github.com/gin-gonic/gin"
)

func main() {
	cfg := config.Load()

	publisher, err := rabbitmq.New(cfg.RabbitMQURL)
	if err != nil {
		log.Fatalf("Failed to connect to RabbitMQ: %v", err)
	}
	defer publisher.Close()

	ragClient, err := grpc_client.New(cfg.RAGServiceAddr)
	if err != nil {
		log.Fatalf("Failed to connect to RAG service: %v", err)
	}
	defer ragClient.Close()

	h := handlers.New(ragClient, publisher, cfg.UploadPath)

	r := gin.Default()
	r.MaxMultipartMemory = 8 << 20

	r.GET("/api/v1/health", h.Health)
	r.POST("/api/v1/chat", h.Chat)
	r.POST("/api/v1/ingest", h.Ingest)

	log.Printf("Gateway running on port %s", cfg.Port)
	r.Run(":" + cfg.Port)
}
