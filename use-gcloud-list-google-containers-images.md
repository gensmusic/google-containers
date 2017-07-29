# install gcloud
	https://cloud.google.com/sdk/docs/#linux

	wget https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-164.0.0-linux-x86.tar.gz
	tar zxvf google-cloud-sdk-164.0.0-linux-x86.tar.gz
	./google-cloud-sdk/install.sh

	# reopen terminal
	gcloud init

	# get images of google-containers
	gcloud alpha container images list --repository=gcr.io/google-containers
