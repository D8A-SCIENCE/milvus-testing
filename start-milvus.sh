#!/bin/bash
set -e

# Create necessary config
echo "common:
  storageType: local
etcd:
  endpoints:
    - localhost:2379
minio:
  address: localhost:9000
  accessKeyID: minioadmin
  secretAccessKey: minioadmin
  useSSL: false
local:
  dataPath: /tmp/milvus/data" > /tmp/user.yaml

# Make sure directory exists
mkdir -p /tmp/milvus/data

# Copy config to appropriate location
cp /tmp/user.yaml /milvus/configs/user.yaml

# Start embedded etcd
/milvus/bin/etcd > /tmp/etcd.log 2>&1 &

# Start embedded MinIO
/milvus/bin/minio server /tmp/minio > /tmp/minio.log 2>&1 &

# Wait for services to start
sleep 5

# Start Milvus
cd /milvus && ./bin/milvus run standalone
