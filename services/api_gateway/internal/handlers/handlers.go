// Package handlers provides HTTP handlers.
package handlers

import (
	"context"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"strings"
	"time"

	"neuro_search/gateway/internal/grpc_client"
	"neuro_search/gateway/internal/rabbitmq"

	"github.com/gin-gonic/gin"
)

// Handler contains HTTP handler dependencies.
type Handler struct {
	ragClient  *grpc_client.Client
	publisher  *rabbitmq.Publisher
	uploadPath string
}

// New creates new handler.
func New(ragClient *grpc_client.Client, publisher *rabbitmq.Publisher, uploadPath string) *Handler {
	return &Handler{
		ragClient:  ragClient,
		publisher:  publisher,
		uploadPath: uploadPath,
	}
}

// Health returns service health status.
func (h *Handler) Health(c *gin.Context) {
	c.JSON(http.StatusOK, gin.H{
		"status":  "healthy",
		"version": "1.0.0",
	})
}

// ChatRequest represents chat API request body.
type ChatRequest struct {
	Message   string `json:"message" binding:"required"`
	SessionID string `json:"session_id,omitempty"`
}

// Chat handles chat requests.
func (h *Handler) Chat(c *gin.Context) {
	var req ChatRequest
	if err := c.ShouldBindJSON(&req); err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
		return
	}

	resp, err := h.ragClient.Chat(c.Request.Context(), &grpc_client.ChatRequest{
		Message:   req.Message,
		SessionID: req.SessionID,
	})
	if err != nil {
		log.Printf("RAG service error: %v", err)
		c.JSON(http.StatusInternalServerError, gin.H{"error": "RAG Service unavailable"})
		return
	}

	c.JSON(http.StatusOK, gin.H{
		"answer":     resp.Answer,
		"sources":    resp.Sources,
		"session_id": resp.SessionID,
	})
}

var allowedExtensions = map[string]bool{
	".pdf":  true,
	".docx": true,
	".txt":  true,
}

// Ingest handles file upload for processing.
func (h *Handler) Ingest(c *gin.Context) {
	form, err := c.MultipartForm()
	if err != nil {
		c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid form data"})
		return
	}

	files := form.File["files"]
	if len(files) == 0 {
		c.JSON(http.StatusBadRequest, gin.H{"error": "No files provided"})
		return
	}

	if err := os.MkdirAll(h.uploadPath, os.ModePerm); err != nil {
		c.JSON(http.StatusInternalServerError, gin.H{"error": "Failed to create upload directory"})
		return
	}

	var taskIDs []string

	for _, file := range files {
		ext := strings.ToLower(filepath.Ext(file.Filename))
		if !allowedExtensions[ext] {
			log.Printf("Unsupported file format: %s", ext)
			continue
		}

		filename := fmt.Sprintf("%d_%s", time.Now().UnixNano(), file.Filename)
		dst := filepath.Join(h.uploadPath, filename)

		if err := c.SaveUploadedFile(file, dst); err != nil {
			log.Printf("Failed to save file: %v", err)
			continue
		}

		taskID := fmt.Sprintf("task_%d", time.Now().UnixNano())
		err := h.publisher.Publish(context.Background(), &rabbitmq.TaskMessage{
			TaskID:   taskID,
			FilePath: dst,
		})
		if err != nil {
			log.Printf("Failed to publish task: %v", err)
			continue
		}

		taskIDs = append(taskIDs, taskID)
	}

	c.JSON(http.StatusAccepted, gin.H{
		"status":   "processing",
		"task_ids": taskIDs,
	})
}
