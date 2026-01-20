// Package grpc_client provides RAG service client.
package grpc_client

import (
	"context"
	"time"

	pb "neuro_search/gateway/pkg/api/v1"

	"google.golang.org/grpc"
	"google.golang.org/grpc/credentials/insecure"
)

// Client wraps gRPC connection to RAG service.
type Client struct {
	conn   *grpc.ClientConn
	client pb.RagServiceClient
}

// New creates new gRPC client.
func New(addr string) (*Client, error) {
	conn, err := grpc.Dial(addr, grpc.WithTransportCredentials(insecure.NewCredentials()))
	if err != nil {
		return nil, err
	}
	return &Client{
		conn:   conn,
		client: pb.NewRagServiceClient(conn),
	}, nil
}

// Close closes gRPC connection.
func (c *Client) Close() error {
	return c.conn.Close()
}

// ChatRequest represents chat API request.
type ChatRequest struct {
	Message   string
	SessionID string
}

// ChatResponse represents chat API response.
type ChatResponse struct {
	Answer    string
	Sources   []*pb.Source
	SessionID string
}

// Chat sends chat request to RAG service.
func (c *Client) Chat(ctx context.Context, req *ChatRequest) (*ChatResponse, error) {
	ctx, cancel := context.WithTimeout(ctx, 30*time.Second)
	defer cancel()

	resp, err := c.client.GetAnswer(ctx, &pb.ChatRequest{
		Message:   req.Message,
		SessionId: req.SessionID,
	})
	if err != nil {
		return nil, err
	}

	return &ChatResponse{
		Answer:    resp.Answer,
		Sources:   resp.Sources,
		SessionID: resp.SessionId,
	}, nil
}
