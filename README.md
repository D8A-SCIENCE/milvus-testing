# milvus-testing

Instructions for getting a stand-alone Milvus pod running.  Replication is turned off for this example.

# Setup
1) Edit milvusEtcd.yml, milvusMinio.yml, and milvusCoreServer.yml to match your nfs server, namespace and securitycontext.

2) Create directories that Etcd, Minio and Milvus need.  I setup:
   
   2a) /sciclone/geograd/test/milvus/
   
   2b) /sciclone/geograd/test/milvus/var/lib/milvus
   
   2c) /sciclone/geograd/test/milvus/etcd
   
   2d) /sciclone/geograd/test/milvus/minio
   
4) Update the directories being used in milvusEtcd, milvusMinio, and milvusCoreServer (i.e., "/sciclone/geograd/test/milvus/etcd", "/sciclone/geograd/test/milvus/minio", etc.)

5) Update the service resolution addresses to match your namespace (i.e., milvus-etcd.dsmillerrunfol.svc.cluster.local:2379, milvus-minio.dsmillerrunfol.svc.cluster.local:9000, milvus-core.dsmillerrunfol.svc.cluster.local:19530)

6) Run kubectl create -f milvusEtcd.yml and kubectl create -f milvusMinio.yml

7) Run kubectl create -f milvusCoreServer.yml

8) Run (from exampleUse folder) kubectl create -f python-client-pod.yml

9) Update the python-client-pod.yml with your security context/NFS/etc.  This has a milvus python module for the test inserts and queries.

10) kubectl exec -it milvus-python-client -- /bin/bash

11) CD to wherever milvus_social_posts.py is

12) Update the server DNS string in milvus_social_posts.py (it's pointing to a service in my namespace)

13) python milvus_social_posts.py




