#!/bin/bash

PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin

dock=$(which docker)
if [ $? -eq 1 ]; then
  echo "docker not found. Check if it is installed."
  exit 1
fi

docker build -t djing:latest .
docker tag djing:latest nerosketch/djing:latest
docker push nerosketch/djing:latest
docker rmi djing:latest

