from kafka import KafkaConsumer
import json

consumer = KafkaConsumer(
    'social_media_stream',
    bootstrap_servers='localhost:9092',
    auto_offset_reset='earliest',
    enable_auto_commit=True,
    value_deserializer=lambda x: json.loads(x.decode('utf-8'))
)

print("Listening to Kafka topic...")
for message in consumer:
    print(f"Received: {message.value}")