# install gcloud
	https://cloud.google.com/sdk/docs/#linux

	wget https://dl.google.com/dl/cloudsdk/channels/rapid/downloads/google-cloud-sdk-164.0.0-linux-x86.tar.gz
	tar zxvf google-cloud-sdk-164.0.0-linux-x86.tar.gz
	./google-cloud-sdk/install.sh

	# reopen terminal
	gcloud init

	# get images of google-containers
	gcloud alpha container images list --repository=gcr.io/google-containers


## crontab

Set Git remeber git password!
```
51 15 * * * cd /root/google-containers && PATH=/root/google-cloud-sdk/bin/:$PATH ./mirror-google-containers.py docker-user docker-password > ../a.log 2>&1 && ./submit-update-history.sh

```