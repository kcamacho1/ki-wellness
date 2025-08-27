#!/usr/bin/env python3
"""
Smart Training Script for Ki Wellness AI
Processes files in order of size with progress tracking and error handling
"""

import os
import time
from pathlib import Path
from ai_training_system import AITrainingSystem

def get_file_size_mb(file_path: Path) -> float:
    """Get file size in MB"""
    return file_path.stat().st_size / (1024 * 1024)

def categorize_files(files_dir: str = "training_files"):
    """Categorize files by type and size"""
    files_path = Path(files_dir)
    
    if not files_path.exists():
        print(f"❌ Training files directory '{files_dir}' not found")
        return None
    
    # Get all supported files
    all_files = []
    
    # PDF files
    for pdf_file in files_path.glob("*.pdf"):
        size_mb = get_file_size_mb(pdf_file)
        all_files.append({
            'path': pdf_file,
            'type': 'pdf',
            'size_mb': size_mb,
            'priority': 1 if size_mb < 10 else (2 if size_mb < 50 else 3)
        })
    
    # Markdown files (small, high priority)
    for md_file in files_path.glob("*.md"):
        size_mb = get_file_size_mb(md_file)
        all_files.append({
            'path': md_file,
            'type': 'markdown',
            'size_mb': size_mb,
            'priority': 1  # High priority
        })
    
    # JSON files (small, high priority)
    for json_file in files_path.glob("*.json"):
        size_mb = get_file_size_mb(json_file)
        all_files.append({
            'path': json_file,
            'type': 'json',
            'size_mb': size_mb,
            'priority': 1  # High priority
        })
    
    # CSV files (small, high priority)
    for csv_file in files_path.glob("*.csv"):
        size_mb = get_file_size_mb(csv_file)
        all_files.append({
            'path': csv_file,
            'type': 'csv',
            'size_mb': size_mb,
            'priority': 1  # High priority
        })
    
    # Image files (medium priority)
    for img_file in files_path.glob("*.jpg"):
        size_mb = get_file_size_mb(img_file)
        all_files.append({
            'path': img_file,
            'type': 'image',
            'size_mb': size_mb,
            'priority': 2  # Medium priority
        })
    
    # Sort by priority and size
    all_files.sort(key=lambda x: (x['priority'], x['size_mb']))
    
    return all_files

def process_files_smart(trainer, files_dir="training_files", batch_size=3):
    """Process files in smart order with progress tracking"""
    print("🧠 Smart File Processing Strategy")
    print("=" * 50)
    
    # Categorize files
    all_files = categorize_files(files_dir)
    if not all_files:
        return False
    
    print(f"📚 Found {len(all_files)} files to process")
    
    # Group by priority
    priority_groups = {}
    for file_info in all_files:
        priority = file_info['priority']
        if priority not in priority_groups:
            priority_groups[priority] = []
        priority_groups[priority].append(file_info)
    
    print(f"\n📊 File breakdown by priority:")
    for priority in sorted(priority_groups.keys()):
        files = priority_groups[priority]
        total_size = sum(f['size_mb'] for f in files)
        priority_name = {1: "High (Small files)", 2: "Medium", 3: "Low (Large files)"}[priority]
        print(f"   Priority {priority} ({priority_name}): {len(files)} files, {total_size:.1f}MB total")
    
    # Process by priority
    total_processed = 0
    total_chunks = 0
    
    for priority in sorted(priority_groups.keys()):
        files = priority_groups[priority]
        priority_name = {1: "High", 2: "Medium", 3: "Low"}[priority]
        
        print(f"\n🔄 Processing Priority {priority} ({priority_name}) - {len(files)} files")
        print("-" * 60)
        
        # Process files in this priority group
        for i in range(0, len(files), batch_size):
            batch = files[i:i + batch_size]
            batch_num = i // batch_size + 1
            total_batches = (len(files) + batch_size - 1) // batch_size
            
            print(f"\n📦 Batch {batch_num}/{total_batches} (Priority {priority})")
            
            batch_chunks = []
            
            for file_info in batch:
                file_path = file_info['path']
                file_type = file_info['type']
                size_mb = file_info['size_mb']
                
                try:
                    print(f"   📄 Processing: {file_path.name} ({size_mb:.1f}MB)")
                    start_time = time.time()
                    
                    # Process based on file type
                    if file_type == 'pdf':
                        chunks = trainer.process_pdf(file_path)
                    elif file_type == 'markdown':
                        chunks = trainer.process_markdown(file_path)
                    elif file_type == 'json':
                        chunks = trainer.process_json(file_path)
                    elif file_type == 'csv':
                        chunks = trainer.process_csv(file_path)
                    elif file_type == 'image':
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
                try:
                    trainer.store_knowledge_base(batch_chunks)
                    total_chunks += len(batch_chunks)
                    print(f"   ✅ Successfully stored batch")
                except Exception as e:
                    print(f"   ❌ Error storing batch: {e}")
            
            print(f"   📊 Progress: {total_processed}/{len(all_files)} files processed")
            
            # Small delay between batches
            time.sleep(1)
    
    print(f"\n🎉 Smart processing completed!")
    print(f"📊 Total files processed: {total_processed}/{len(all_files)}")
    print(f"📊 Total chunks stored: {total_chunks}")
    
    return True

def main():
    """Main smart training function"""
    print("🚀 Smart Ki Wellness AI Training System")
    print("=" * 60)
    
    # Initialize trainer
    print("\n🔧 Initializing AI Training System...")
    try:
        trainer = AITrainingSystem()
        print("✅ PostgreSQL connection successful!")
    except Exception as e:
        print(f"❌ Failed to initialize training system: {e}")
        print("Please check your DATABASE_URL environment variable")
        return
    
    # Process files smartly
    print("\n📚 Processing training files with smart strategy...")
    success = process_files_smart(trainer, batch_size=2)  # Smaller batches for safety
    
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
    
    print("\n🎉 Smart training process completed!")

if __name__ == "__main__":
    main()
