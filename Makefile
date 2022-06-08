deploy: build
	docker push dameyerdave/vep-offline-rest
build: 
	docker build . -t dameyerdave/vep-offline-rest
