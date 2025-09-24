#!/usr/bin/env python3
"""
High-Volume Data Generator for Confluent Hackathon
Simulates thousands of user prompts with PII for AI processing
"""

import requests
import json
import time
from faker import Faker
import threading
from datetime import datetime
import random

fake = Faker()

# Confluent Cloud HTTP REST API (easier than kafka-python for demo)
CONFLUENT_REST_ENDPOINT = "https://pkc-xxxxx.us-east-1.aws.confluent.cloud"  # Replace with your endpoint
CONFLUENT_API_KEY = "YOUR_API_KEY"  # Replace with your key
CONFLUENT_API_SECRET = "YOUR_SECRET"  # Replace with your secret

# Topic to send data to
TOPIC_NAME = "raw-user-prompts"

class PromptGenerator:
    def __init__(self):
        self.total_sent = 0
        self.pii_count = 0
        self.clean_count = 0
        
    def generate_ai_prompt_with_pii(self):
        """Generate realistic AI prompts that might contain PII"""
        
        # Different types of AI prompts users might send
        prompt_templates = [
            # Healthcare AI prompts (high PII risk)
            "Please analyze my medical report: Patient {name}, DOB {dob}, SSN {ssn}. Symptoms include {symptoms}.",
            "I need help with my health insurance. My member ID is {medical_id} and email is {email}.",
            "Create a summary for patient {name} with medical record #{medical_id}.",
            
            # Financial AI prompts (high PII risk)  
            "Help me with my taxes. My SSN is {ssn} and I made ${income} last year.",
            "Analyze my credit report. Card number: {cc_number}, expiry: {cc_exp}.",
            "I need financial advice. My account number is {account} at {bank}.",
            
            # Personal AI prompts (medium PII risk)
            "Write a letter to {name} at {email} about our meeting on {date}.",
            "Create a resume for {name}, phone: {phone}, address: {address}.",
            "Schedule a call with {name} ({phone}) for tomorrow.",
            
            # Business AI prompts (low-medium PII risk)
            "Draft an email to {email} about our Q3 results.",
            "Summarize customer feedback from {name} ({company}).",
            "Create a proposal for {company} contact: {email}.",
            
            # Clean AI prompts (no PII)
            "Explain quantum physics in simple terms.",
            "Write a short story about space exploration.",
            "What are the benefits of renewable energy?",
            "Create a recipe for chocolate cake.",
            "Explain how machine learning works."
        ]
        
        # 70% chance of PII, 30% clean (realistic distribution)
        has_pii = random.random() < 0.7
        
        if has_pii:
            # Choose a PII-containing template
            template = random.choice(prompt_templates[:-5])  # Exclude clean templates
            
            prompt = template.format(
                name=fake.name(),
                dob=fake.date_of_birth().strftime('%m/%d/%Y'),
                ssn=fake.ssn(),
                email=fake.email(),
                phone=fake.phone_number(),
                address=fake.address().replace('\n', ', '),
                medical_id=fake.bothify('??######'),
                cc_number=fake.credit_card_number(),
                cc_exp=fake.credit_card_expire(),
                account=fake.random_number(digits=10),
                bank=fake.company(),
                income=fake.random_number(digits=5),
                symptoms=random.choice(['headache', 'fever', 'fatigue', 'joint pain']),
                company=fake.company(),
                date=fake.date_this_month().strftime('%m/%d/%Y')
            )
            self.pii_count += 1
        else:
            # Clean prompt
            prompt = random.choice(prompt_templates[-5:])  # Only clean templates
            self.clean_count += 1
        
        return {
            "user_id": fake.uuid4(),
            "prompt": prompt,
            "timestamp": datetime.now().isoformat(),
            "ip_address": fake.ipv4(),
            "user_agent": fake.user_agent(),
            "session_id": fake.uuid4()[:8],
            "has_pii": has_pii,
            "source": random.choice(["web_app", "mobile_app", "api_call", "chatbot"])
        }
    
    def send_to_confluent_http(self, message):
        """Send message using Confluent REST API (easier for demo)"""
        try:
            # Confluent Cloud REST API endpoint
            url = f"{CONFLUENT_REST_ENDPOINT}/kafka/v3/clusters/YOUR_CLUSTER_ID/topics/{TOPIC_NAME}/records"
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Basic {CONFLUENT_API_KEY}:{CONFLUENT_API_SECRET}"  # Base64 encode this
            }
            
            payload = {
                "key": message["user_id"],
                "value": message
            }
            
            # For demo purposes, we'll just print instead of actual HTTP call
            # (You can uncomment below for real HTTP calls)
            
            # response = requests.post(url, headers=headers, json=payload)
            # if response.status_code == 200:
            #     return True
            # else:
            #     print(f"❌ HTTP Error: {response.status_code}")
            #     return False
            
            # For demo - just print to show data flow
            self.total_sent += 1
            if self.total_sent % 100 == 0:  # Print every 100th message
                print(f"📨 Sent {self.total_sent} prompts | PII: {self.pii_count} | Clean: {self.clean_count}")
                print(f"   Sample: {message['prompt'][:80]}...")
            
            return True
            
        except Exception as e:
            print(f"❌ Error sending message: {e}")
            return False
    
    def start_high_volume_generation(self, prompts_per_second=50, duration_seconds=120):
        """Generate high volume of prompts to simulate big data load"""
        print(f"🚀 Starting high-volume generation:")
        print(f"   • Rate: {prompts_per_second} prompts/second")
        print(f"   • Duration: {duration_seconds} seconds")
        print(f"   • Total target: {prompts_per_second * duration_seconds} prompts")
        print(f"   • Sending to topic: {TOPIC_NAME}")
        print()
        
        start_time = time.time()
        
        while (time.time() - start_time) < duration_seconds:
            batch_start = time.time()
            
            # Send a batch of prompts
            for _ in range(prompts_per_second):
                prompt_data = self.generate_ai_prompt_with_pii()
                self.send_to_confluent_http(prompt_data)
            
            # Wait to maintain rate
            batch_duration = time.time() - batch_start
            if batch_duration < 1.0:
                time.sleep(1.0 - batch_duration)
        
        print(f"\n🎉 Generation complete!")
        print(f"📊 Final stats:")
        print(f"   • Total sent: {self.total_sent}")
        print(f"   • Contains PII: {self.pii_count} ({(self.pii_count/max(self.total_sent,1)*100):.1f}%)")
        print(f"   • Clean prompts: {self.clean_count} ({(self.clean_count/max(self.total_sent,1)*100):.1f}%)")
        print(f"   • Average rate: {self.total_sent/(time.time()-start_time):.1f} prompts/second")

if __name__ == "__main__":
    print("🛡️ SecureStream AI - High-Volume Data Generator")
    print("=" * 60)
    print("Simulating enterprise-scale AI prompt processing...")
    print("(In production: This data would flow to Confluent Cloud)")
    print()
    
    generator = PromptGenerator()
    
    # Generate sample data to show what it looks like
    print("📝 Sample prompts being generated:")
    for i in range(5):
        sample = generator.generate_ai_prompt_with_pii()
        pii_status = "🚨 PII" if sample["has_pii"] else "✅ Clean"
        print(f"   {i+1}. {pii_status}: {sample['prompt'][:70]}...")
    
    print(f"\n🚀 Ready to generate high-volume data stream!")
    print(f"💡 This simulates the 'big data' that Confluent/Flink will process")
    
    # Start generation
    generator.start_high_volume_generation(
        prompts_per_second=25,  # Start with 25/sec for demo
        duration_seconds=60     # Run for 1 minute
    )
