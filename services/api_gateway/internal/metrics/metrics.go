// Package metrics provides Prometheus metrics.
package metrics

import (
	"github.com/prometheus/client_golang/prometheus"
	"github.com/prometheus/client_golang/prometheus/promauto"
)

var (
	RequestCount = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_requests_total",
			Help: "Total number of requests",
		},
		[]string{"endpoint", "status"},
	)

	RequestLatency = promauto.NewHistogramVec(
		prometheus.HistogramOpts{
			Name:    "gateway_request_latency_seconds",
			Help:    "Request latency in seconds",
			Buckets: []float64{0.01, 0.05, 0.1, 0.5, 1.0, 2.0, 5.0, 10.0},
		},
		[]string{"endpoint"},
	)

	FilesUploaded = promauto.NewCounterVec(
		prometheus.CounterOpts{
			Name: "gateway_files_uploaded_total",
			Help: "Total number of files uploaded",
		},
		[]string{"status"},
	)
)
