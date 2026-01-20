// Package rabbitmq provides message queue publisher.
package rabbitmq

import (
	"context"
	"encoding/json"
	"log"
	"time"

	amqp "github.com/rabbitmq/amqp091-go"
)

// Publisher handles RabbitMQ publishing.
type Publisher struct {
	conn    *amqp.Connection
	channel *amqp.Channel
	queue   amqp.Queue
}

// TaskMessage represents ingestion task.
type TaskMessage struct {
	TaskID   string `json:"task_id"`
	FilePath string `json:"file_path"`
}

// New creates new RabbitMQ publisher.
func New(url string) (*Publisher, error) {
	var conn *amqp.Connection
	var err error

	for i := 0; i < 5; i++ {
		conn, err = amqp.Dial(url)
		if err == nil {
			break
		}
		log.Printf("Waiting for RabbitMQ... (%v)", err)
		time.Sleep(2 * time.Second)
	}
	if err != nil {
		return nil, err
	}

	ch, err := conn.Channel()
	if err != nil {
		conn.Close()
		return nil, err
	}

	q, err := ch.QueueDeclare("ingestion_queue", true, false, false, false, nil)
	if err != nil {
		ch.Close()
		conn.Close()
		return nil, err
	}

	return &Publisher{conn: conn, channel: ch, queue: q}, nil
}

// Close closes RabbitMQ connection.
func (p *Publisher) Close() {
	p.channel.Close()
	p.conn.Close()
}

// Publish sends task to queue.
func (p *Publisher) Publish(ctx context.Context, msg *TaskMessage) error {
	body, err := json.Marshal(msg)
	if err != nil {
		return err
	}

	return p.channel.PublishWithContext(ctx,
		"",
		p.queue.Name,
		false,
		false,
		amqp.Publishing{
			DeliveryMode: amqp.Persistent,
			ContentType:  "application/json",
			Body:         body,
		},
	)
}
