#!/bin/sh

# Clean up docker dangling images
docker images --quiet --filter=dangling=true | xargs --no-run-if-empty docker rmi