.PHONY: gen-proto

gen-proto:
	@echo "Generating Go code..."
	mkdir -p services/api_gateway/pkg/api/v1
	PATH=$$(go env GOPATH)/bin:$$PATH protoc --proto_path=protos \
		--go_out=services/api_gateway/pkg/api/v1 --go_opt=paths=source_relative \
		--go-grpc_out=services/api_gateway/pkg/api/v1 --go-grpc_opt=paths=source_relative \
		protos/rag_service.proto

	@echo "Generating Python code..."
	mkdir -p services/rag_service/proto
	# Python requires a bit of path magic, using grpc_tools module
	python3 -m grpc_tools.protoc -Iprotos \
		--python_out=services/rag_service/proto \
		--pyi_out=services/rag_service/proto \
		--grpc_python_out=services/rag_service/proto \
		protos/rag_service.proto
	
	@echo "Done!"
