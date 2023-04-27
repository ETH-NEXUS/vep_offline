include .env

default:
	@echo "USAGE: make build|docker"
docker: build
	docker push ${DOCKER_IMAGE}:${VEP_VERSION}
build: 
	docker build . --build-arg VEP_VERSION=${VEP_VERSION} -t ${DOCKER_IMAGE}:${VEP_VERSION}
