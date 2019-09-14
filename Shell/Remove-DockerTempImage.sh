#!/bin/sh

# Clean up docker temp images
docker images | awk '$1=="<none>"{system("docker rmi "$3) fi}'