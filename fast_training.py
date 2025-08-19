#!/usr/bin/env python3
"""
Fast Training Script for Ki Wellness AI
Processes files in batches with progress tracking
"""

import os
import time
from pathlib import Path
from ai_training_system import AITrainingSystem

def process_files_in_batches(trainer, files_dir="training_files", batch_size=5):
    """Process files in smaller batches to avoid timeouts"""
    files_path = Path(files_dir)
    
    if not files_path.exists():
        print(f"❌ Training files directory '{files_dir}' not found")
        return False
    
    # Get all files
    all_files = []
    all_files.extend(list(files_path.glob("*.pdf")))
    all_files.extend(list(files_path.glob("*.docx")))
    all_files.extend(list(files_path.glob("*.txt")))
    all_files.extend(list(files_path.glob("*.md")))
    all_files.extend(list(files_path.glob("*.json")))
    all_files.extend(list(files_path.glob("*.csv")))
    all_files.extend(list(files_path.glob("*.jpg")))
    
    print(f"📚 Found {len(all_files)} total files to process")
    
    # Process in batches
    total_processed = 0
    all_chunks = []
    
    for i in range(0, len(all_files), batch_size):
        batch = all_files[i:i + batch_size]
        print(f"\n🔄 Processing batch {i//batch_size + 1}/{(len(all_files) + batch_size - 1)//batch_size}")
        print(f"   Files {i+1}-{min(i+batch_size, len(all_files))} of {len(all_files)}")
        
        batch_chunks = []
        
        for file_path in batch:
            try:
                print(f"   📄 Processing: {file_path.name}")
                start_time = time.time()
                
                if file_path.suffix.lower() == '.pdf':
                    chunks = trainer.process_pdf(file_path)
                elif file_path.suffix.lower() == '.docx':
                    chunks = trainer.process_docx(file_path)
                elif file_path.suffix.lower() == '.txt':
                    chunks = trainer.process_txt(file_path)
                elif file_path.suffix.lower() == '.md':
                    chunks = trainer.process_markdown(file_path)
                elif file_path.suffix.lower() == '.json':
                    chunks = trainer.process_json(file_path)
                elif file_path.suffix.lower() == '.csv':
                    chunks = trainer.process_csv(file_path)
                elif file_path.suffix.lower() in ['.jpg', '.jpeg']:
                    chunks = trainer.process_image(file_path)
                else:
                    print(f"   ⚠️ Skipping unsupported file: {file_path.name}")
                    continue
                
                processing_time = time.time() - start_time
                print(f"   ✅ {file_path.name}: {len(chunks)} chunks in {processing_time:.2f}s")
                
                batch_chunks.extend(chunks)
                total_processed += 1
                
            except Exception as e:
                print(f"   ❌ Error processing {file_path.name}: {e}")
                continue
        
        # Store batch in knowledge base
        if batch_chunks:
            print(f"   💾 Storing {len(batch_chunks)} chunks in knowledge base...")
            trainer.store_knowledge_base(batch_chunks)
            all_chunks.extend(batch_chunks)
        
        print(f"   📊 Progress: {total_processed}/{len(all_files)} files processed")
        
        # Small delay between batches
        time.sleep(1)
    
    print(f"\n✅ Completed processing {total_processed} files")
    print(f"📊 Total chunks stored: {len(all_chunks)}")
    return True

def main():
    """Main training function with progress tracking"""
    print("🚀 Fast Ki Wellness AI Training System")
    print("=" * 50)
    
    # Initialize trainer
    print("\n🔧 Initializing AI Training System...")
    trainer = AITrainingSystem()
    
    # Process files in batches
    print("\n📚 Processing training files in batches...")
    success = process_files_in_batches(trainer, batch_size=3)  # Smaller batches for safety
    
    if not success:
        print("❌ File processing failed")
        return
    
    # Generate fine-tuning data
    print("\n🔄 Generating fine-tuning dataset...")
    try:
        training_data_file = trainer.generate_fine_tuning_data()
        print(f"✅ Generated fine-tuning dataset: {training_data_file}")
    except Exception as e:
        print(f"❌ Error generating fine-tuning data: {e}")
        return
    
    # Fine-tune model
    print("\n🎯 Starting model fine-tuning...")
    try:
        success = trainer.fine_tune_model(training_data_file)
        if success:
            print(f"✅ Fine-tuned model '{trainer.fine_tuned_model}' created successfully!")
            
            # Test the model
            print("\n🧪 Testing the fine-tuned model...")
            test_question = "How can I improve my water intake?"
            response = trainer.enhanced_ai_response(test_question)
            print(f"Test Question: {test_question}")
            print(f"AI Response: {response[:200]}...")
        else:
            print("❌ Fine-tuning failed, but knowledge base is ready")
    except Exception as e:
        print(f"❌ Error during fine-tuning: {e}")
    
    print("\n🎉 Training process completed!")

if __name__ == "__main__":
    main()
