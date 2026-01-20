package main

import (
	"context"
	"encoding/json"
	"fmt"
	"log"
	"net/http"
	"os"
	"path/filepath"
	"time"

	"github.com/gin-gonic/gin"
	amqp "github.com/rabbitmq/amqp091-go"
	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"

	pb "neuro_search/gateway/pkg/api/v1"
)

type TaskMessage struct {
	TaskID   string `json:"task_id"`
	FilePath string `json:"file_path"`
}

func main() {
	rabbitURL := os.Getenv("RABBITMQ_URL")
	if rabbitURL == "" {
		rabbitURL = "amqp://guest:guest@localhost:5672/"
	}

	var rabbitConn *amqp.Connection
	var err error
	for i := 0; i < 5; i++ {
		rabbitConn, err = amqp.Dial(rabbitURL)
		if err == nil {
			break
		}
		log.Printf("Waiting for RabbitMQ... (%v)", err)
		time.Sleep(2 * time.Second)
	}
	if err != nil {
		log.Fatalf("Failed to connect to RabbitMQ: %v", err)
	}
	defer rabbitConn.Close()

	ch, err := rabbitConn.Channel()
	if err != nil {
		log.Fatalf("Failed to open a channel: %v", err)
	}
	defer ch.Close()

	q, err := ch.QueueDeclare(
		"ingestion_queue",
		true,
		false,
		false,
		false,
		nil,
	)
	if err != nil {
		log.Fatalf("Failed to declare a queue: %v", err)
	}

	ragServiceAddr := os.Getenv("RAG_SERVICE_URL")
	if ragServiceAddr == "" {
		ragServiceAddr = "localhost:50051"
	}
	conn, err := grpc.Dial(ragServiceAddr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		log.Fatalf("Did not connect to RAG Service: %v", err)
	}
	defer conn.Close()
	grpcClient := pb.NewRagServiceClient(conn)

	r := gin.Default()
	r.MaxMultipartMemory = 8 << 20

	r.POST("/api/v1/chat", func(c *gin.Context) {
		var req struct {
			Message string `json:"message"`
		}

		if err := c.ShouldBindJSON(&req); err != nil {
			c.JSON(http.StatusBadRequest, gin.H{"error": "Invalid request"})
			return
		}

		ctx, cancel := context.WithTimeout(context.Background(), 10*time.Second)
		defer cancel()

		grpcReq := &pb.ChatRequest{
			Message: req.Message,
			History: []*pb.MessageHistory{},
		}

		resp, err := grpcClient.GetAnswer(ctx, grpcReq)
		if err != nil {
			log.Printf("Error calling RAG service: %v", err)
			c.JSON(http.StatusInternalServerError, gin.H{"error": "RAG Service unavailable"})
			return
		}

		c.JSON(http.StatusOK, gin.H{
			"answer":  resp.Answer,
			"sources": resp.Sources,
		})
	})

	r.POST("/api/v1/ingest", func(c *gin.Context) {
		form, _ := c.MultipartForm()
		files := form.File["files"]

		var taskIDs []string
		uploadPath := "/app/uploads"
		if _, err := os.Stat(uploadPath); os.IsNotExist(err) {
			os.MkdirAll(uploadPath, os.ModePerm)
		}

		for _, file := range files {
			filename := fmt.Sprintf("%d_%s", time.Now().UnixNano(), file.Filename)
			dst := filepath.Join(uploadPath, filename)

			if err := c.SaveUploadedFile(file, dst); err != nil {
				log.Printf("Failed to save file: %v", err)
				continue
			}

			taskID := fmt.Sprintf("task_%d", time.Now().UnixNano())
			msg := TaskMessage{
				TaskID:   taskID,
				FilePath: dst,
			}
			body, _ := json.Marshal(msg)

			err = ch.PublishWithContext(context.Background(),
				"",
				q.Name,
				false,
				false,
				amqp.Publishing{
					DeliveryMode: amqp.Persistent,
					ContentType:  "application/json",
					Body:         body,
				})

			if err != nil {
				log.Printf("Failed to publish task: %v", err)
			} else {
				taskIDs = append(taskIDs, taskID)
			}
		}

		c.JSON(http.StatusAccepted, gin.H{
			"status":   "processing",
			"task_ids": taskIDs,
		})
	})

	port := os.Getenv("PORT")
	if port == "" {
		port = "8080"
	}
	log.Printf("Gateway running on port %s", port)
	r.Run(":" + port)
}
