#!/usr/bin/env python3
"""
Working Confluent Kafka Producer
This will actually send data to your Confluent Cloud topics
"""

from confluent_kafka import Producer
import json
import time
import os
from dotenv import load_dotenv
from data_generator import PromptGenerator

load_dotenv()

# Your Confluent Cloud configuration
CONFLUENT_CONFIG = {
    'bootstrap.servers': os.getenv('CONFLUENT_BOOTSTRAP_SERVERS'),
    'security.protocol': 'SASL_SSL',
    'sasl.mechanism': 'PLAIN',
    'sasl.username': os.getenv('CONFLUENT_API_KEY'),
    'sasl.password': os.getenv('CONFLUENT_API_SECRET'),
    'client.id': 'securestream-producer'
}

class WorkingKafkaProducer:
    def __init__(self):
        # Create Kafka producer
        self.producer = Producer(CONFLUENT_CONFIG)
        self.messages_sent = 0
        self.generator = PromptGenerator()
    
    def delivery_callback(self, err, msg):
        """Callback for message delivery confirmation"""
        if err:
            print(f'❌ Message delivery failed: {err}')
        else:
            self.messages_sent += 1
            if self.messages_sent % 10 == 0:
                print(f'✅ Delivered {self.messages_sent} messages to topic {msg.topic()}')
    
    def send_message(self, topic, message):
        """Send message to Kafka topic"""
        try:
            # Convert message to JSON string
            message_json = json.dumps(message)
            
            # Send message
            self.producer.produce(
                topic=topic,
                key=message.get('user_id', 'unknown'),
                value=message_json,
                callback=self.delivery_callback
            )
            
            # Trigger delivery callbacks
            self.producer.poll(0)
            
            return True
            
        except Exception as e:
            print(f'❌ Failed to send message: {e}')
            return False
    
    def test_connection(self):
        """Test if we can connect to Confluent"""
        try:
            # Try to get metadata
            metadata = self.producer.list_topics(timeout=10)
            print(f"✅ Connected to Confluent Cloud!")
            print(f"   Available topics: {len(metadata.topics)}")
            
            # Check if our topic exists
            if 'raw_user_prompts' in metadata.topics:
                print(f"✅ Topic 'raw_user_prompts' found!")
                return True
            else:
                print(f"⚠️  Topic 'raw_user_prompts' not found")
                print(f"   Available topics: {list(metadata.topics.keys())}")
                return True  # Still proceed
                
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            return False
    
    def send_sample_data(self, num_messages=20):
        """Send sample data to Confluent"""
        print(f"\n📨 Sending {num_messages} messages to 'raw_user_prompts'...")
        
        success_count = 0
        
        for i in range(num_messages):
            # Generate realistic prompt
            message = self.generator.generate_ai_prompt_with_pii()
            
            # Add message number for tracking
            message['message_id'] = f"msg_{i+1:03d}"
            
            # Send message
            if self.send_message('raw_user_prompts', message):
                success_count += 1
                
                # Show progress
                pii_status = "🚨 PII" if message.get('has_pii', False) else "✅ Clean"
                print(f"   {i+1:2d}. {pii_status}: {message['prompt'][:60]}...")
            else:
                print(f"   {i+1:2d}. ❌ FAILED")
            
            # Small delay to see progress
            time.sleep(0.2)
        
        # Wait for all messages to be delivered
        print(f"\n⏳ Waiting for delivery confirmations...")
        self.producer.flush(10)  # Wait up to 10 seconds
        
        print(f"\n🎉 Send complete!")
        print(f"   • Attempted: {num_messages}")
        print(f"   • Confirmed delivered: {self.messages_sent}")
        print(f"   • Success rate: {(self.messages_sent/num_messages)*100:.1f}%")
        
        return self.messages_sent > 0

def main():
    print("🛡️ SecureStream AI - Confluent Kafka Producer")
    print("=" * 60)
    
    # Check credentials
    required_vars = ['CONFLUENT_BOOTSTRAP_SERVERS', 'CONFLUENT_API_KEY', 'CONFLUENT_API_SECRET']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"❌ Missing environment variables: {missing_vars}")
        print(f"💡 Make sure your .env file has all Confluent credentials")
        return False
    
    # Initialize producer
    try:
        producer = WorkingKafkaProducer()
        
        # Test connection
        print("🔧 Testing Confluent Cloud connection...")
        if not producer.test_connection():
            print("❌ Cannot connect to Confluent Cloud")
            return False
        
        # Send sample data
        success = producer.send_sample_data(20)
        
        if success:
            print(f"\n✅ SUCCESS!")
            print(f"🎯 Check your Confluent Cloud dashboard:")
            print(f"   1. Go to Topics → 'raw_user_prompts'")
            print(f"   2. Click 'Messages' tab")  
            print(f"   3. You should see {producer.messages_sent} new messages!")
            print(f"   4. Each message contains realistic user prompts with PII")
        else:
            print(f"\n❌ No messages were sent successfully")
            
        return success
        
    except Exception as e:
        print(f"❌ Producer initialization failed: {e}")
        return False

if __name__ == "__main__":
    main()
