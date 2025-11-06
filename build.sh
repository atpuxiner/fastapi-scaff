#!/bin/bash

# =================== Configuration Variables ===================
IMAGE_NAME="fastapi-scaff"
IMAGE_DEFAULT_TAG="latest"

# Dockerfile and build context
DOCKERFILE_PATH="./Dockerfile"
DOCKERFILE_CONTEXT="./"

# ================ User Input for Tag ==================
echo "Current image name: $IMAGE_NAME"
read -p "Please enter the image tag to build [默认: $IMAGE_DEFAULT_TAG]: " IMAGE_TAG_INPUT

if [ -z "$IMAGE_TAG_INPUT" ]; then
    IMAGE_TAG="$IMAGE_DEFAULT_TAG"
else
    IMAGE_TAG="$IMAGE_TAG_INPUT"
fi

# ================ Build Image ==================
echo "=> Building image: $IMAGE_NAME:$IMAGE_TAG using Dockerfile: $DOCKERFILE_PATH"

docker build -f "$DOCKERFILE_PATH" -t "$IMAGE_NAME:$IMAGE_TAG" "$DOCKERFILE_CONTEXT"

if [ $? -ne 0 ]; then
    echo "Docker build failed!"
    exit 1
fi

echo "Image built successfully: $IMAGE_NAME:$IMAGE_TAG"
