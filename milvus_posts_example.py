#!/usr/bin/env python3
import random
import time
from datetime import datetime, timedelta
from pymilvus import connections, FieldSchema, CollectionSchema, DataType, Collection, utility

# Connect to Milvus server
def connect_to_milvus():
    print("Connecting to Milvus...")
    connections.connect(
        alias="default", 
        host="milvus",  # Service name in Kubernetes
        port="19530"
    )
    print("Successfully connected to Milvus!")

# Create a collection for social media posts
def create_posts_collection():
    print("Creating posts collection...")
    
    # Check if collection already exists
    if utility.has_collection("posts"):
        print("Collection already exists, dropping it...")
        utility.drop_collection("posts")
    
    # Define collection schema
    fields = [
        FieldSchema(name="post_id", dtype=DataType.INT64, is_primary=True, auto_id=True),
        FieldSchema(name="user_id", dtype=DataType.INT64),
        FieldSchema(name="post_text", dtype=DataType.VARCHAR, max_length=500),  # Text limited to 500 chars
        FieldSchema(name="preceding_post_id", dtype=DataType.INT64),  # ID of the post before this one
        FieldSchema(name="proceeding_post_ids", dtype=DataType.ARRAY, element_type=DataType.INT64, max_capacity=50),  # IDs of posts after this one
        FieldSchema(name="post_timestamp", dtype=DataType.INT64),  # Unix timestamp of post
    ]
    
    schema = CollectionSchema(fields=fields, description="Social media posts collection")
    posts = Collection(name="posts", schema=schema)
    
    # Create an index on user_id for faster querying
    index_params = {
        "index_type": "IVF_FLAT",
        "metric_type": "L2",
        "params": {"nlist": 128}
    }
    posts.create_index(field_name="user_id", index_params=index_params)
    
    print("Collection created successfully!")
    return posts

# Generate sample post data
def generate_sample_data(num_users=10, num_posts=100):
    print(f"Generating sample data with {num_users} users and {num_posts} posts...")
    
    # Generate random user IDs
    users = [i+1 for i in range(num_users)]
    
    # Sample text content for posts
    sample_texts = [
        "Just had an amazing coffee!",
        "Working on a new project today.",
        "Can't wait for the weekend!",
        "Check out this cool article I found.",
        "Thinking about learning a new language.",
        "This weather is perfect today!",
        "Just finished reading an interesting book.",
        "Anyone have recommendations for lunch?",
        "Made significant progress on my research today!",
        "Excited about the upcoming conference.",
    ]
    
    # Generate post data
    post_records = []
    post_lookup = {}  # To track post IDs for linking
    
    # Generate base timestamp (30 days ago)
    base_timestamp = int((datetime.now() - timedelta(days=30)).timestamp())
    
    # First create posts without proceeding IDs - we'll update later
    for i in range(num_posts):
        user_id = random.choice(users)
        post_text = random.choice(sample_texts)
        
        # For preceding post, choose a random earlier post by same user (if any)
        preceding_post_id = -1  # -1 means no preceding post
        user_previous_posts = [p for p_id, p in post_lookup.items() if p['user_id'] == user_id]
        if user_previous_posts:
            preceding_post = random.choice(user_previous_posts)
            preceding_post_id = preceding_post['post_id']
        
        # Generate a timestamp that's moving forward
        timestamp = base_timestamp + (i * 60 * 10)  # Each post 10 minutes apart
        
        # For now, proceeding_post_ids is empty
        post_record = {
            'user_id': user_id,
            'post_text': post_text,
            'preceding_post_id': preceding_post_id,
            'proceeding_post_ids': [],
            'post_timestamp': timestamp
        }
        
        # Record synthetic post_id for linking
        post_record['post_id'] = i + 1
        post_lookup[i + 1] = post_record
        post_records.append(post_record)
    
    # Now update proceeding_post_ids
    for post in post_records:
        if post['preceding_post_id'] != -1:
            preceding_post = post_lookup[post['preceding_post_id']]
            preceding_post['proceeding_post_ids'].append(post['post_id'])
    
    print("Sample data generated!")
    return post_records

# Insert data into the collection
def insert_data(collection, data):
    print(f"Inserting {len(data)} records into collection...")
    
    # Extract fields
    user_ids = [record['user_id'] for record in data]
    post_texts = [record['post_text'] for record in data]
    preceding_post_ids = [record['preceding_post_id'] for record in data]
    proceeding_post_ids = [record['proceeding_post_ids'] for record in data]
    post_timestamps = [record['post_timestamp'] for record in data]
    
    # Insert data
    collection.insert([
        user_ids,
        post_texts, 
        preceding_post_ids,
        proceeding_post_ids,
        post_timestamps
    ])
    
    # Ensure data is immediately available for search
    collection.flush()
    print(f"Successfully inserted {len(data)} records!")

# Perform various queries
def perform_queries(collection):
    print("\nPerforming example queries:")
    
    # Load the collection
    collection.load()
    
    # Query 1: Find the 5 most recent posts
    print("\nQuery 1: 5 most recent posts")
    results = collection.query(
        expr="",
        output_fields=["post_id", "user_id", "post_text", "post_timestamp"],
        limit=5,
        sort="post_timestamp desc"
    )
    for result in results:
        post_time = datetime.fromtimestamp(result['post_timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Post {result['post_id']} by User {result['user_id']} at {post_time}: {result['post_text']}")
    
    # Query 2: Find all posts by a specific user
    random_user = random.randint(1, 10)
    print(f"\nQuery 2: All posts by User {random_user}")
    results = collection.query(
        expr=f"user_id == {random_user}",
        output_fields=["post_id", "post_text", "post_timestamp"],
        sort="post_timestamp"
    )
    for result in results:
        post_time = datetime.fromtimestamp(result['post_timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Post {result['post_id']} at {post_time}: {result['post_text']}")
    
    # Query 3: Find a post and all its replies (proceeding posts)
    print("\nQuery 3: Find a post and its replies")
    # First, find a post that has proceeding posts
    posts_with_replies = collection.query(
        expr="array_length(proceeding_post_ids) > 0",
        output_fields=["post_id", "user_id", "post_text", "proceeding_post_ids"],
        limit=1
    )
    
    if posts_with_replies:
        post = posts_with_replies[0]
        print(f"Original Post {post['post_id']} by User {post['user_id']}: {post['post_text']}")
        
        # Query the proceeding posts
        if post['proceeding_post_ids']:
            proc_ids = post['proceeding_post_ids']
            proc_ids_str = ",".join(str(id) for id in proc_ids)
            replies = collection.query(
                expr=f"post_id in [{proc_ids_str}]",
                output_fields=["post_id", "user_id", "post_text"]
            )
            print("Replies:")
            for reply in replies:
                print(f"  Reply Post {reply['post_id']} by User {reply['user_id']}: {reply['post_text']}")
    
    # Query 4: Find posts within a particular time range
    print("\nQuery 4: Posts from a specific time range")
    # Random time range in the last two weeks
    end_time = int(datetime.now().timestamp())
    start_time = end_time - (14 * 24 * 60 * 60)  # Two weeks ago
    
    results = collection.query(
        expr=f"post_timestamp >= {start_time} and post_timestamp <= {end_time}",
        output_fields=["post_id", "user_id", "post_text", "post_timestamp"],
        limit=5
    )
    for result in results:
        post_time = datetime.fromtimestamp(result['post_timestamp']).strftime('%Y-%m-%d %H:%M:%S')
        print(f"Post {result['post_id']} by User {result['user_id']} at {post_time}: {result['post_text']}")

def main():
    try:
        # Connect to Milvus
        connect_to_milvus()
        
        # Create collection
        posts_collection = create_posts_collection()
        
        # Generate and insert sample data
        sample_data = generate_sample_data()
        insert_data(posts_collection, sample_data)
        
        # Wait a moment for data to be fully available
        print("Waiting for data to be fully indexed...")
        time.sleep(2)
        
        # Perform example queries
        perform_queries(posts_collection)
        
        print("\nAll operations completed successfully!")
        
    except Exception as e:
        print(f"An error occurred: {e}")
    finally:
        # Disconnect from Milvus
        connections.disconnect("default")
        print("Disconnected from Milvus")

if __name__ == "__main__":
    main()
