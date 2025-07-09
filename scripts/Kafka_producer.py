from kafka import KafkaProducer
import json
import time

producer = KafkaProducer(
    bootstrap_servers='localhost:9092',
    value_serializer=lambda v: json.dumps(v).encode('utf-8')
)

sample_data = [
    {"product": "iPhone 15", "review": "Amazing camera!", "sentiment": "positive"},
    {"product": "PS5", "review": "Still sold out", "sentiment": "neutral"},
    {"product": "MacBook Pro", "review": "Battery life disappointing", "sentiment": "negative"},
]

for msg in sample_data:
    producer.send("social_media_stream", value=msg)
    print(f"Sent: {msg}")
    time.sleep(1)

producer.flush()
producer.close()