# milvus-testing

Instructions for getting a stand-alone Milvus pod running.  Replication is turned off for this example.

# Setup
1) Edit milvusEtcd.yml, milvusMinio.yml, and milvusCoreServer.yml to match your nfs server, namespace and securitycontext.

2) Create directories that Etcd, Minio and Milvus need.  I setup:
   
   2a) /sciclone/geograd/test/milvus/
   
   2b) /sciclone/geograd/test/milvus/var/lib/milvus
   
   2c) /sciclone/geograd/test/milvus/etcd
   
   2d) /sciclone/geograd/test/milvus/minio
   
4) Update the directories being used in milvusEtcd, milvusMinio, and milvusCoreServer.yml files (i.e., "/sciclone/geograd/test/milvus/etcd", "/sciclone/geograd/test/milvus/minio", etc.)

5) Update the service resolution addresses to match your namespace in each of the three yml files (i.e., milvus-etcd.dsmillerrunfol.svc.cluster.local:2379, milvus-minio.dsmillerrunfol.svc.cluster.local:9000, milvus-core.dsmillerrunfol.svc.cluster.local:19530)

6) Run kubectl create -f milvusEtcd.yml and kubectl create -f milvusMinio.yml

7) Run kubectl create -f milvusCoreServer.yml

8) Update the python-client-pod.yml with your security context/NFS/etc.  This has a milvus python module for the test inserts and queries.

9) Run (from exampleUse folder) kubectl create -f python-client-pod.yml

10) kubectl exec -it milvus-python-client -- /bin/bash

11) CD to wherever milvus_social_posts.py is

12) Update the server DNS string in milvus_social_posts.py (it's pointing to a service in my namespace)

13) python milvus_social_posts.py

Output if everything is happy:
```bash
71032@milvus-python-client:/sciclone/geograd/milvus-testing/exampleUse$ python milvus_social_posts.py
INFO:root:PyMilvus version: 2.2.11
INFO:__main__:Successfully connected to Milvus at milvus-core.dsmillerrunfol.svc.cluster.local:19530
INFO:__main__:⏱️ connect_to_milvus completed in 0.0134 seconds
INFO:__main__:Collection social_posts already exists. Dropping it.
INFO:__main__:Successfully created collection social_posts
INFO:__main__:⏱️ create_collection completed in 0.5767 seconds
INFO:__main__:Inserted batch of 50 posts
INFO:__main__:Inserted batch of 50 posts
INFO:__main__:Successfully created 100 sample posts
INFO:__main__:⏱️ create_sample_data completed in 3.0527 seconds
INFO:__main__:⏱️ Collection loaded successfully in 3.0512 seconds
INFO:__main__:Posts from ['alice', 'bob']:
INFO:__main__:1. [ID: 10002] alice (2025-03-10 16:22:00): Working on a new project today. Excited!
INFO:__main__:2. [ID: 10005] bob (2025-03-13 23:32:56): Just announced: big news in the tech world today.
INFO:__main__:3. [ID: 10008] alice (2025-03-03 15:08:31): Just announced: big news in the tech world today.
INFO:__main__:4. [ID: 10009] alice (2025-03-21 01:11:30): Anyone else watching the new show everyone's talking about?
INFO:__main__:5. [ID: 10012] alice (2025-03-23 05:07:16): @charlie Made a delicious dinner tonight. Recipe in comments!
INFO:__main__:
Conversation thread:
INFO:__main__:Original post [ID: 10001] dave: Happy birthday to my best friend!
INFO:__main__:  Reply 1 [ID: 10041] heidi (2025-03-03 14:25:57): @dave Made a delicious dinner tonight. Recipe in comments!
INFO:__main__:  Reply 2 [ID: 10047] charlie (2025-03-07 14:50:54): @dave Finished reading an incredible book. Highly recommend!
INFO:__main__:  Reply 3 [ID: 10095] eve (2025-03-13 11:05:15): @dave Finished reading an incredible book. Highly recommend!
INFO:__main__:
Recent posts from the last week:
INFO:__main__:1. [ID: 10007] grace (2025-03-27 20:13:58): @dave Made a delicious dinner tonight. Recipe in comments!
INFO:__main__:2. [ID: 10016] frank (2025-03-27 21:33:48): @bob Happy birthday to my best friend!
INFO:__main__:3. [ID: 10017] ivan (2025-03-30 14:39:23): @frank Happy birthday to my best friend!
INFO:__main__:4. [ID: 10019] charlie (2025-03-30 06:22:06): @dave Just announced: big news in the tech world today.
INFO:__main__:5. [ID: 10020] bob (2025-03-26 18:25:32): Happy birthday to my best friend!
INFO:__main__:
Posts similar to: 'Looking forward to the weekend plans!'
INFO:__main__:1. [Distance: 64.7637] [ID: 10091] heidi (2025-03-30 20:18:48): @alice Anyone else watching the new show everyone's talking about?
INFO:__main__:2. [Distance: 67.6157] [ID: 10027] bob (2025-03-24 13:21:10): Made a delicious dinner tonight. Recipe in comments!
INFO:__main__:3. [Distance: 67.6157] [ID: 10028] charlie (2025-03-18 19:40:07): Made a delicious dinner tonight. Recipe in comments!
INFO:__main__:4. [Distance: 67.6157] [ID: 10011] heidi (2025-03-16 13:09:40): Made a delicious dinner tonight. Recipe in comments!
INFO:__main__:5. [Distance: 67.6157] [ID: 10029] frank (2025-03-18 18:52:05): Made a delicious dinner tonight. Recipe in comments!
INFO:__main__:⏱️ query_posts completed in 3.0715 seconds
INFO:__main__:
==== PERFORMANCE SUMMARY =====
INFO:__main__:Connection Operations:
INFO:__main__:  - connect_to_milvus: 0.0134 seconds
INFO:__main__:Schema Operations:
INFO:__main__:  - create_collection: 0.5767 seconds
INFO:__main__:Data Operations:
INFO:__main__:  - create_sample_data: 3.0527 seconds
INFO:__main__:Query Operations:
INFO:__main__:  - collection_load: 3.0512 seconds
INFO:__main__:  - query_posts: 3.0715 seconds
INFO:__main__:Total execution time: 6.7143 seconds
INFO:__main__:============================
INFO:__main__:Example completed successfully in 6.7145 seconds
```


