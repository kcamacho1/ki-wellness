#!/usr/bin/env python3
"""
Training File Management for Ki Wellness AI
Simple interface to manage training files and run AI training
"""

import os
import shutil
from pathlib import Path
from ai_training_system import AITrainingSystem

def setup_training_directory():
    """Create training files directory and show instructions"""
    training_dir = Path("training_files")
    training_dir.mkdir(exist_ok=True)
    
    print("📁 Training files directory created: training_files/")
    print("\n📋 Instructions:")
    print("1. Place your PDF, DOCX, and TXT files in the 'training_files/' directory")
    print("2. Run this script to process them")
    print("3. The AI will learn from your documents to provide better responses")
    print("\n📄 Supported file types:")
    print("   - PDF files (*.pdf)")
    print("   - Word documents (*.docx)")
    print("   - Text files (*.txt)")
    
    return training_dir

def list_training_files():
    """List all files in the training directory"""
    training_dir = Path("training_files")
    
    if not training_dir.exists():
        print("❌ Training files directory not found")
        return []
    
    files = []
    for file_path in training_dir.iterdir():
        if file_path.is_file():
            files.append(file_path)
    
    if files:
        print(f"\n📚 Found {len(files)} training files:")
        for file_path in files:
            print(f"   - {file_path.name}")
    else:
        print("\n📚 No training files found in training_files/ directory")
    
    return files

def run_training():
    """Run the AI training system"""
    print("\n🚀 Starting AI Training Process...")
    
    # Initialize training system
    trainer = AITrainingSystem()
    
    # Process training files
    print("\n📚 Processing training files...")
    trainer.process_training_files()
    
    # Add custom training examples (you can modify these)
    custom_qa_pairs = [
        {
            "question": "How can I improve my water intake?",
            "answer": "To improve water intake, try setting daily goals, using a water bottle with measurements, adding flavor with lemon or cucumber, setting reminders, and tracking your intake. Aim for 8-10 glasses (64-80 oz) per day.",
            "context": "Water intake optimization strategies",
            "source_file": "hydration_guide.pdf"
        },
        {
            "question": "What should I eat for better mood?",
            "answer": "Foods that support better mood include omega-3 rich fish, dark chocolate, berries, nuts, leafy greens, and complex carbohydrates. These foods support serotonin production and brain health.",
            "context": "Nutrition and mental health",
            "source_file": "mood_nutrition.pdf"
        },
        {
            "question": "How can I track my nutrition better?",
            "answer": "To track nutrition better, log all meals and snacks, use measuring tools, read food labels, track macronutrients (protein, carbs, fat), and use apps or journals. Be consistent and honest with your logging.",
            "context": "Nutrition tracking strategies",
            "source_file": "nutrition_tracking.pdf"
        }
    ]
    
    # Add training examples
    print("\n📝 Adding training examples...")
    trainer.create_training_dataset(custom_qa_pairs)
    
    # Generate fine-tuning data
    print("\n🔄 Generating fine-tuning dataset...")
    training_data_file = trainer.generate_fine_tuning_data()
    
    # Fine-tune model
    print("\n🎯 Fine-tuning model...")
    success = trainer.fine_tune_model(training_data_file)
    
    if success:
        print("\n✅ AI Training completed successfully!")
        print(f"📊 Fine-tuned model: {trainer.fine_tuned_model}")
        print("🔧 Your AI responses will now be enhanced with your training data")
    else:
        print("\n❌ Fine-tuning failed, but knowledge base is ready")
        print("💡 You can still use the enhanced responses with RAG")

def test_enhanced_responses():
    """Test the enhanced AI responses"""
    print("\n🧪 Testing Enhanced AI Responses...")
    
    trainer = AITrainingSystem()
    
    test_questions = [
        "How can I improve my water intake?",
        "What foods help with mood?",
        "How should I track my nutrition?",
        "What are good protein sources?",
        "How can I maintain a healthy diet?"
    ]
    
    for question in test_questions:
        print(f"\n❓ Question: {question}")
        response = trainer.enhanced_ai_response(question)
        print(f"🤖 Response: {response[:200]}...")
        print("-" * 50)

def main():
    """Main function"""
    print("🎯 Ki Wellness AI Training System")
    print("=" * 40)
    
    while True:
        print("\n📋 Options:")
        print("1. Setup training directory")
        print("2. List training files")
        print("3. Run AI training")
        print("4. Test enhanced responses")
        print("5. Exit")
        
        choice = input("\nSelect an option (1-5): ").strip()
        
        if choice == "1":
            setup_training_directory()
        elif choice == "2":
            list_training_files()
        elif choice == "3":
            run_training()
        elif choice == "4":
            test_enhanced_responses()
        elif choice == "5":
            print("👋 Goodbye!")
            break
        else:
            print("❌ Invalid option. Please select 1-5.")

if __name__ == "__main__":
    main()
