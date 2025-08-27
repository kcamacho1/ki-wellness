#!/usr/bin/env python3
"""
Custom PDF Training Script for Ki Wellness
Simplified interface for training the AI model with your PDFs
"""

import os
import sys
from pathlib import Path
from ai_training_system import AITrainingSystem

def check_ollama():
    """Check if Ollama is running"""
    try:
        import ollama
        ollama.list()
        print("✅ Ollama is running and accessible")
        return True
    except Exception as e:
        print("❌ Ollama is not running or not accessible")
        print("Please start Ollama first: ollama serve")
        return False

def check_training_files():
    """Check if training files exist"""
    training_dir = Path("training_files")
    
    if not training_dir.exists():
        print("❌ Training files directory not found")
        print("Creating training_files directory...")
        training_dir.mkdir(exist_ok=True)
        return False
    
    pdf_files = list(training_dir.glob("*.pdf"))
    docx_files = list(training_dir.glob("*.docx"))
    txt_files = list(training_dir.glob("*.txt"))
    md_files = list(training_dir.glob("*.md"))
    json_files = list(training_dir.glob("*.json"))
    csv_files = list(training_dir.glob("*.csv"))
    jpg_files = list(training_dir.glob("*.jpg"))
    
    total_files = len(pdf_files) + len(docx_files) + len(txt_files) + len(md_files) + len(json_files) + len(csv_files) + len(jpg_files)
    
    if total_files == 0:
        print("❌ No training files found in training_files directory")
        print("\n📁 Please add your PDFs, DOCX, or TXT files to the training_files directory")
        print("   Example: cp ~/Downloads/*.pdf training_files/")
        return False
    
    print(f"✅ Found {total_files} training files:")
    for pdf in pdf_files:
        print(f"   📄 {pdf.name}")
    for docx in docx_files:
        print(f"   📝 {docx.name}")
    for txt in txt_files:
        print(f"   📄 {txt.name}")
    for md in md_files:
        print(f"   📝 {md.name}")
    for json_file in json_files:
        print(f"   📊 {json_file.name}")
    for csv in csv_files:
        print(f"   📊 {csv.name}")
    for jpg in jpg_files:
        print(f"   🖼️ {jpg.name}")
    
    return True

def interactive_training():
    """Interactive training process"""
    print("🚀 Ki Wellness AI Training System")
    print("=" * 50)
    
    # Step 1: Check prerequisites
    print("\n🔍 Checking prerequisites...")
    if not check_ollama():
        return False
    
    if not check_training_files():
        return False
    
    # Step 2: Initialize training system
    print("\n🔧 Initializing AI Training System...")
    trainer = AITrainingSystem()
    
    # Step 3: Process training files
    print("\n📚 Processing your training files...")
    trainer.process_training_files()
    
    # Step 4: Add custom Q&A pairs (optional)
    print("\n❓ Would you like to add custom Q&A pairs for training? (y/n): ", end="")
    response = input().lower().strip()
    
    if response in ['y', 'yes']:
        qa_pairs = []
        print("\n📝 Adding custom Q&A pairs...")
        print("Enter 'done' when finished adding pairs")
        
        while True:
            print("\n--- New Q&A Pair ---")
            question = input("Question: ").strip()
            if question.lower() == 'done':
                break
            
            answer = input("Answer: ").strip()
            if answer.lower() == 'done':
                break
            
            context = input("Context (optional): ").strip()
            source = input("Source file (optional): ").strip()
            
            qa_pairs.append({
                "question": question,
                "answer": answer,
                "context": context,
                "source_file": source if source else "manual"
            })
        
        if qa_pairs:
            trainer.create_training_dataset(qa_pairs)
    
    # Step 5: Generate fine-tuning data
    print("\n🔄 Generating fine-tuning dataset...")
    training_data_file = trainer.generate_fine_tuning_data()
    
    # Step 6: Fine-tune the model
    print("\n🎯 Starting model fine-tuning...")
    print("This may take several minutes depending on your data size...")
    
    success = trainer.fine_tune_model(training_data_file)
    
    if success:
        print("\n✅ Training completed successfully!")
        print(f"📊 Your fine-tuned model: {trainer.fine_tuned_model}")
        print("\n🔧 You can now use the enhanced AI responses in your application")
        print("   Example: trainer.enhanced_ai_response('How can I improve my health?')")
        
        # Test the model
        print("\n🧪 Testing the fine-tuned model...")
        test_question = "How can I improve my water intake?"
        response = trainer.enhanced_ai_response(test_question)
        print(f"Test Question: {test_question}")
        print(f"AI Response: {response[:200]}...")
        
        return True
    else:
        print("\n❌ Training failed, but knowledge base is ready")
        return False

def main():
    """Main function"""
    try:
        success = interactive_training()
        if success:
            print("\n🎉 Training process completed successfully!")
        else:
            print("\n⚠️  Training process completed with some issues")
            print("   Check the logs above for details")
    except KeyboardInterrupt:
        print("\n\n⏹️  Training interrupted by user")
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}")
        print("Please check your setup and try again")

if __name__ == "__main__":
    main()
