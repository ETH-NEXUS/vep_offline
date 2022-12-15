include .env

default:
	@echo "USAGE: make build|docker"
docker: build
	docker push ${DOCKER_IMAGE}:${VEP_VERSION}
build: 
	docker build . -t ${DOCKER_IMAGE}:${VEP_VERSION}
