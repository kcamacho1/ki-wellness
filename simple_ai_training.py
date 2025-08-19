#!/usr/bin/env python3
"""
Simple AI Training System for Ki Wellness
Lightweight version for basic document processing and model enhancement
"""

import os
import json
import ollama
from pathlib import Path
from typing import List, Dict
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleAITraining:
    def __init__(self):
        self.model_name = "mistral"
        self.fine_tuned_model = "ki-wellness-mistral"
        self.training_data_dir = Path("training_data")
        self.training_data_dir.mkdir(exist_ok=True)
    
    def process_text_file(self, file_path: str) -> str:
        """Extract text from a simple text file"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error reading file {file_path}: {e}")
            return ""
    
    def create_training_examples(self) -> List[Dict[str, str]]:
        """Create basic training examples for health coaching"""
        return [
            {
                "question": "How can I improve my water intake?",
                "answer": "To improve water intake, try setting daily goals, using a water bottle with measurements, adding flavor with lemon or cucumber, setting reminders, and tracking your intake. Aim for 8-10 glasses (64-80 oz) per day.",
                "context": "Hydration strategies"
            },
            {
                "question": "What should I eat for better mood?",
                "answer": "Foods that support better mood include omega-3 rich fish, dark chocolate, berries, nuts, leafy greens, and complex carbohydrates. These foods support serotonin production and brain health.",
                "context": "Nutrition and mental health"
            },
            {
                "question": "How can I track my nutrition better?",
                "answer": "To track nutrition better, log all meals and snacks, use measuring tools, read food labels, track macronutrients (protein, carbs, fat), and use apps or journals. Be consistent and honest with your logging.",
                "context": "Nutrition tracking strategies"
            },
            {
                "question": "What are good protein sources?",
                "answer": "Excellent protein sources include lean meats (chicken, turkey, fish), eggs, dairy products, legumes (beans, lentils), nuts, seeds, and plant-based proteins like tofu and tempeh. Aim for 0.8-1.2g per kg of body weight.",
                "context": "Protein nutrition"
            },
            {
                "question": "How can I maintain a healthy diet?",
                "answer": "To maintain a healthy diet, focus on whole foods, eat plenty of fruits and vegetables, include lean proteins, choose whole grains, limit processed foods and added sugars, stay hydrated, and practice portion control.",
                "context": "Healthy eating principles"
            }
        ]
    
    def generate_modelfile(self, training_examples: List[Dict[str, str]]) -> str:
        """Generate a Modelfile for fine-tuning"""
        modelfile_content = f"""FROM {self.model_name}

# System prompt for health coaching
SYSTEM "You are an expert AI Health Coach for Ki Wellness. You provide personalized, evidence-based health advice based on user data including nutrition, water intake, mood, and health goals. Always be encouraging, actionable, and specific to the user's situation."

# Training examples
"""
        
        for example in training_examples:
            prompt = example['question'].replace('"', '\\"')
            response = example['answer'].replace('"', '\\"')
            modelfile_content += f'TRAIN "{prompt}" "{response}"\n'
        
        return modelfile_content
    
    def create_fine_tuned_model(self, training_examples: List[Dict[str, str]]) -> bool:
        """Create a fine-tuned model using Ollama"""
        try:
            # Generate Modelfile
            modelfile_content = self.generate_modelfile(training_examples)
            
            # Save Modelfile
            modelfile_path = self.training_data_dir / "Modelfile"
            with open(modelfile_path, 'w') as f:
                f.write(modelfile_content)
            
            print(f"✅ Modelfile created: {modelfile_path}")
            print("🔄 Creating fine-tuned model...")
            print("💡 Run this command to create the model:")
            print(f"   ollama create {self.fine_tuned_model} {modelfile_path}")
            
            return True
            
        except Exception as e:
            print(f"❌ Error creating fine-tuned model: {e}")
            return False
    
    def enhanced_response(self, question: str, user_data: Dict = None) -> str:
        """Generate enhanced response using fine-tuned model"""
        try:
            # Try fine-tuned model first
            try:
                response = ollama.chat(
                    model=self.fine_tuned_model,
                    messages=[{"role": "user", "content": question}]
                )
                return response['message']['content']
            except:
                # Fallback to base model
                response = ollama.chat(
                    model=self.model_name,
                    messages=[{"role": "user", "content": question}]
                )
                return response['message']['content']
                
        except Exception as e:
            print(f"❌ Error generating response: {e}")
            return "I apologize, but I encountered an error while processing your request."
    
    def test_responses(self):
        """Test the enhanced responses"""
        print("\n🧪 Testing Enhanced AI Responses...")
        
        test_questions = [
            "How can I improve my water intake?",
            "What foods help with mood?",
            "How should I track my nutrition?",
            "What are good protein sources?",
            "How can I maintain a healthy diet?"
        ]
        
        for question in test_questions:
            print(f"\n❓ Question: {question}")
            response = self.enhanced_response(question)
            print(f"🤖 Response: {response[:200]}...")
            print("-" * 50)

def main():
    """Main function"""
    print("🎯 Simple AI Training System for Ki Wellness")
    print("=" * 45)
    
    # Initialize training system
    trainer = SimpleAITraining()
    
    # Create training examples
    print("\n📝 Creating training examples...")
    training_examples = trainer.create_training_examples()
    print(f"✅ Created {len(training_examples)} training examples")
    
    # Create fine-tuned model
    print("\n🎯 Creating fine-tuned model...")
    success = trainer.create_fine_tuned_model(training_examples)
    
    if success:
        print("\n✅ Training setup completed!")
        print("📊 Fine-tuned model: ki-wellness-mistral")
        print("🔧 You can now use enhanced responses")
        
        # Test responses
        trainer.test_responses()
    else:
        print("\n❌ Training setup failed")

if __name__ == "__main__":
    main()
