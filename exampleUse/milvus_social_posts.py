#!/usr/bin/env python3

import random
import time
from datetime import datetime, timedelta
import numpy as np
import json
import logging
import functools

# Import Milvus Python client library
from pymilvus import (
    connections,
    utility,
    FieldSchema, CollectionSchema, DataType,
    Collection,
)

# Try to get version info
try:
    from pymilvus import __version__ as pymilvus_version
    logging.info(f"PyMilvus version: {pymilvus_version}")
except ImportError:
    pymilvus_version = "Unknown"
    
# Dictionary to store timing metrics
performance_metrics = {}

# Timing decorator
def timing_decorator(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        end_time = time.time()
        elapsed = end_time - start_time
        func_name = func.__name__
        performance_metrics[func_name] = elapsed
        logger.info(f"⏱️ {func_name} completed in {elapsed:.4f} seconds")
        return result
    return wrapper

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
)
logger = logging.getLogger(__name__)

# Global variables for Milvus connection
MILVUS_HOST = "milvus-core.dsmillerrunfol.svc.cluster.local"
MILVUS_PORT = "19530"
COLLECTION_NAME = "social_posts"

# Sample data for generation
USERS = ["alice", "bob", "charlie", "dave", "eve", "frank", "grace", "heidi", "ivan", "judy"]
POST_TOPICS = [
    "Just had a great coffee at my favorite cafe!",
    "Working on a new project today. Excited!",
    "This weather is amazing! Going for a hike.",
    "Finished reading an incredible book. Highly recommend!",
    "Anyone else watching the new show everyone's talking about?",
    "Made a delicious dinner tonight. Recipe in comments!",
    "Having technical issues with my laptop. Any suggestions?",
    "Happy birthday to my best friend!",
    "Just announced: big news in the tech world today.",
    "Looking forward to the weekend plans!",
]

@timing_decorator
def connect_to_milvus():
    """Connect to Milvus server and return connection status"""
    try:
        # Connect to Milvus
        connections.connect(
            alias="default", 
            host=MILVUS_HOST,
            port=MILVUS_PORT
        )
        logger.info(f"Successfully connected to Milvus at {MILVUS_HOST}:{MILVUS_PORT}")
        return True
    except Exception as e:
        logger.error(f"Failed to connect to Milvus: {e}")
        return False

@timing_decorator
def create_collection():
    """Create a collection for social media posts if it doesn't exist"""
    if utility.has_collection(COLLECTION_NAME):
        logger.info(f"Collection {COLLECTION_NAME} already exists. Dropping it.")
        utility.drop_collection(COLLECTION_NAME)
    
    # Define schema fields
    fields = [
        FieldSchema(name="post_id", dtype=DataType.INT64, is_primary=True, auto_id=False),
        FieldSchema(name="user_name", dtype=DataType.VARCHAR, max_length=128),
        FieldSchema(name="post_text", dtype=DataType.VARCHAR, max_length=1024),
        FieldSchema(name="preceding_post_id", dtype=DataType.INT64),  # ID of the post this one replies to
        # Store proceeding post IDs as a JSON string since ARRAY type isn't available
        FieldSchema(name="proceeding_post_ids_json", dtype=DataType.VARCHAR, max_length=256),
        FieldSchema(name="post_timestamp", dtype=DataType.INT64),  # Unix timestamp
        FieldSchema(name="post_embedding", dtype=DataType.FLOAT_VECTOR, dim=128)  # Vector representation of post content
    ]
    
    # Create collection schema
    schema = CollectionSchema(fields=fields, description="Social media posts collection")
    
    # Create collection
    collection = Collection(name=COLLECTION_NAME, schema=schema)
    
    # Create index on the vector field (for similarity search)
    index_params = {
        "metric_type": "L2",
        "index_type": "IVF_FLAT",
        "params": {"nlist": 128}
    }
    collection.create_index(field_name="post_embedding", index_params=index_params)
    logger.info(f"Successfully created collection {COLLECTION_NAME}")
    
    return collection

@timing_decorator
def generate_post_embedding(text):
    """Generate a mock embedding vector for a post text"""
    # In a real application, you would use a text embedding model
    # For this example, we'll generate random vectors deterministically based on the text
    random.seed(hash(text) % 10000)
    return [random.uniform(-1, 1) for _ in range(128)]

@timing_decorator
def create_sample_data(collection, num_posts=100):
    """Generate and insert sample social media post data"""
    posts_data = []
    post_id_counter = 10000
    post_lookup = {}  # For tracking posts to build relationships
    start_time = datetime.now() - timedelta(days=30)  # Start from 30 days ago
    
    # First pass: create basic posts without relationships
    for i in range(num_posts):
        post_id = post_id_counter
        post_id_counter += 1
        user = random.choice(USERS)
        post_text = random.choice(POST_TOPICS)
        
        # Generate random timestamp between start_time and now
        random_time = start_time + timedelta(
            seconds=random.randint(0, int((datetime.now() - start_time).total_seconds()))
        )
        timestamp = int(random_time.timestamp())
        
        # Store in lookup for relationship building
        post_lookup[post_id] = {
            "user": user,
            "timestamp": timestamp,
            "preceding": None,
            "proceeding": []
        }
        
    # Need to import json for proceeding post IDs serialization
    import json
    
    # Second pass: build relationships between posts
    # Assign ~40% of posts as replies to other posts
    post_ids = list(post_lookup.keys())
    for post_id in post_ids:
        # ~40% chance this post is a reply to another post
        if random.random() < 0.4 and len(post_ids) > 1:
            # Find valid posts to reply to (posted earlier)
            potential_preceding = [
                pid for pid in post_ids 
                if pid != post_id and post_lookup[pid]["timestamp"] < post_lookup[post_id]["timestamp"]
            ]
            
            if potential_preceding:
                preceding_id = random.choice(potential_preceding)
                post_lookup[post_id]["preceding"] = preceding_id
                post_lookup[preceding_id]["proceeding"].append(post_id)
    
    # Third pass: prepare data for insertion
    for post_id, post_data in post_lookup.items():
        user = post_data["user"]
        # Generate post text that sometimes references preceding posts
        if post_data["preceding"] is not None:
            preceding_user = post_lookup[post_data["preceding"]]["user"]
            post_text = f"@{preceding_user} " + random.choice(POST_TOPICS)
        else:
            post_text = random.choice(POST_TOPICS)
            
        posts_data.append({
            "post_id": post_id,
            "user_name": user,
            "post_text": post_text,
            "preceding_post_id": post_data["preceding"] if post_data["preceding"] else 0,  # 0 means no preceding post
            "proceeding_post_ids_json": json.dumps(post_data["proceeding"]),  # Store as JSON string
            "post_timestamp": post_data["timestamp"],
            "post_embedding": generate_post_embedding(post_text)
        })
        
        # Insert in batches of 50 to avoid potential memory issues
        if len(posts_data) >= 50:
            try:
                collection.insert(posts_data)
                logger.info(f"Inserted batch of {len(posts_data)} posts")
                posts_data = []
            except Exception as e:
                logger.error(f"Error inserting batch: {e}")
    
    # Insert any remaining posts
    if posts_data:
        try:
            collection.insert(posts_data)
            logger.info(f"Inserted final batch of {len(posts_data)} posts")
        except Exception as e:
            logger.error(f"Error inserting final batch: {e}")
    
    # Flush the collection to ensure all data is persisted
    collection.flush()
    logger.info(f"Successfully created {num_posts} sample posts")

@timing_decorator
def query_posts(collection):
    """Demonstrate different query patterns on the posts collection"""
    # Ensure the collection is loaded for searching
    try:
        start_time = time.time()
        collection.load()
        load_time = time.time() - start_time
        performance_metrics["collection_load"] = load_time
        logger.info(f"⏱️ Collection loaded successfully in {load_time:.4f} seconds")
    except Exception as e:
        logger.error(f"Failed to load collection: {e}")
        return
    
    # 1. Query posts from specific users
    try:
        target_users = ["alice", "bob"]
        expr = f"user_name in {target_users}"
        results = collection.query(expr=expr, output_fields=["post_id", "user_name", "post_text", "post_timestamp"], limit=5)
        
        logger.info(f"Posts from {target_users}:")
        for i, post in enumerate(results):
            post_time = datetime.fromtimestamp(post["post_timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"{i+1}. [ID: {post['post_id']}] {post['user_name']} ({post_time}): {post['post_text']}")
    except Exception as e:
        logger.error(f"Error querying posts by users: {e}")
    
    # 2. Query conversation thread (a post and all its replies)
    try:
        import json
        # Find a post that has replies (JSON array not empty)
        posts_with_replies = collection.query(
            expr="proceeding_post_ids_json != '[]'", 
            output_fields=["post_id", "user_name", "post_text", "proceeding_post_ids_json"],
            limit=1
        )
        
        if posts_with_replies:
            origin_post = posts_with_replies[0]
            reply_ids = json.loads(origin_post["proceeding_post_ids_json"])
            
            logger.info("\nConversation thread:")
            logger.info(f"Original post [ID: {origin_post['post_id']}] {origin_post['user_name']}: {origin_post['post_text']}")
            
            if reply_ids:
                # Get the replies
                if len(reply_ids) > 0:
                    reply_expr = f"post_id in {reply_ids}"
                    replies = collection.query(
                        expr=reply_expr,
                        output_fields=["post_id", "user_name", "post_text", "post_timestamp"]
                    )
                
                    # Sort replies by timestamp
                    replies.sort(key=lambda x: x["post_timestamp"])
                    
                    for i, reply in enumerate(replies):
                        post_time = datetime.fromtimestamp(reply["post_timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
                        logger.info(f"  Reply {i+1} [ID: {reply['post_id']}] {reply['user_name']} ({post_time}): {reply['post_text']}")
    except Exception as e:
        logger.error(f"Error querying conversation thread: {e}")
    
    # 3. Query posts within a specific time range
    try:
        # Query posts from the last week
        one_week_ago = int((datetime.now() - timedelta(days=7)).timestamp())
        time_expr = f"post_timestamp >= {one_week_ago}"
        
        recent_posts = collection.query(
            expr=time_expr,
            output_fields=["post_id", "user_name", "post_text", "post_timestamp"],
            limit=5
        )
        
        logger.info("\nRecent posts from the last week:")
        for i, post in enumerate(recent_posts):
            post_time = datetime.fromtimestamp(post["post_timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"{i+1}. [ID: {post['post_id']}] {post['user_name']} ({post_time}): {post['post_text']}")
    except Exception as e:
        logger.error(f"Error querying recent posts: {e}")
    
    # 4. Vector similarity search - find similar posts
    try:
        # Find posts similar to a reference post
        reference_post = "Looking forward to the weekend plans!"
        reference_vector = generate_post_embedding(reference_post)
        
        search_params = {
            "metric_type": "L2",
            "params": {"nprobe": 10},
        }
        
        logger.info(f"\nPosts similar to: '{reference_post}'")
        results = collection.search(
            data=[reference_vector],
            anns_field="post_embedding",
            param=search_params,
            limit=5,
            output_fields=["post_id", "user_name", "post_text", "post_timestamp"]
        )
        
        for i, result in enumerate(results[0]):
            post = result.entity._row_data
            post_time = datetime.fromtimestamp(post["post_timestamp"]).strftime('%Y-%m-%d %H:%M:%S')
            logger.info(f"{i+1}. [Distance: {result.distance:.4f}] [ID: {post['post_id']}] {post['user_name']} ({post_time}): {post['post_text']}")
    except Exception as e:
        logger.error(f"Error performing vector similarity search: {e}")

def print_performance_summary():
    """Print a summary of all performance metrics"""
    logger.info("\n==== PERFORMANCE SUMMARY =====")
    # Group metrics by operation type
    connection_metrics = {k: v for k, v in performance_metrics.items() if k in ["connect_to_milvus"]}
    schema_metrics = {k: v for k, v in performance_metrics.items() if k in ["create_collection"]}
    data_metrics = {k: v for k, v in performance_metrics.items() if k in ["create_sample_data", "generate_post_embedding"]}
    query_metrics = {k: v for k, v in performance_metrics.items() if k in ["query_posts", "collection_load"]}
    
    # Print metrics by group
    logger.info("Connection Operations:")
    for op, time_taken in connection_metrics.items():
        logger.info(f"  - {op}: {time_taken:.4f} seconds")
        
    logger.info("Schema Operations:")
    for op, time_taken in schema_metrics.items():
        logger.info(f"  - {op}: {time_taken:.4f} seconds")
        
    logger.info("Data Operations:")
    for op, time_taken in data_metrics.items():
        if op != "generate_post_embedding":  # Skip individual embedding generations
            logger.info(f"  - {op}: {time_taken:.4f} seconds")
    
    logger.info("Query Operations:")
    for op, time_taken in query_metrics.items():
        logger.info(f"  - {op}: {time_taken:.4f} seconds")
    
    # Calculate total time
    main_ops = ["connect_to_milvus", "create_collection", "create_sample_data", "query_posts"]
    total_time = sum(performance_metrics.get(op, 0) for op in main_ops)
    logger.info(f"Total execution time: {total_time:.4f} seconds")
    logger.info("============================")

def main():
    """Main function to run the example"""
    main_start_time = time.time()
    
    # Connect to Milvus
    if not connect_to_milvus():
        return
    
    # Create collection
    collection = create_collection()
    
    # Generate and insert sample data
    create_sample_data(collection, num_posts=100)
    
    # Run query examples
    query_posts(collection)
    
    # Calculate and store total execution time
    main_execution_time = time.time() - main_start_time
    performance_metrics["total_execution"] = main_execution_time
    
    # Print performance summary
    print_performance_summary()
    
    logger.info(f"Example completed successfully in {main_execution_time:.4f} seconds")

if __name__ == "__main__":
    main()
