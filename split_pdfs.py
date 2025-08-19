#!/usr/bin/env python3
"""
PDF Splitting Utility for Ki Wellness AI Training
Splits large PDFs into smaller chunks for easier processing
"""

import os
import PyPDF2
from pathlib import Path
import shutil

def split_pdf(input_path: Path, output_dir: Path, pages_per_chunk: int = 50):
    """Split a large PDF into smaller chunks"""
    try:
        print(f"📄 Splitting {input_path.name}...")
        
        with open(input_path, 'rb') as file:
            pdf_reader = PyPDF2.PdfReader(file)
            total_pages = len(pdf_reader.pages)
            
            print(f"   📊 Total pages: {total_pages}")
            print(f"   📊 Pages per chunk: {pages_per_chunk}")
            
            # Calculate number of chunks
            num_chunks = (total_pages + pages_per_chunk - 1) // pages_per_chunk
            print(f"   📊 Will create {num_chunks} chunks")
            
            # Create chunks
            for chunk_num in range(num_chunks):
                start_page = chunk_num * pages_per_chunk
                end_page = min((chunk_num + 1) * pages_per_chunk, total_pages)
                
                # Create PDF writer for this chunk
                pdf_writer = PyPDF2.PdfWriter()
                
                # Add pages to this chunk
                for page_num in range(start_page, end_page):
                    pdf_writer.add_page(pdf_reader.pages[page_num])
                
                # Generate output filename
                base_name = input_path.stem
                chunk_filename = f"{base_name}_part_{chunk_num + 1:03d}.pdf"
                output_path = output_dir / chunk_filename
                
                # Save the chunk
                with open(output_path, 'wb') as output_file:
                    pdf_writer.write(output_file)
                
                chunk_size = output_path.stat().st_size / (1024 * 1024)  # MB
                print(f"   ✅ Created {chunk_filename} ({chunk_size:.1f}MB, pages {start_page + 1}-{end_page})")
            
            return num_chunks
            
    except Exception as e:
        print(f"   ❌ Error splitting {input_path.name}: {e}")
        return 0

def main():
    """Main function to split large PDFs"""
    print("🔧 PDF Splitting Utility for Ki Wellness")
    print("=" * 50)
    
    training_dir = Path("training_files")
    if not training_dir.exists():
        print("❌ Training files directory not found")
        return
    
    # Find all PDF files
    pdf_files = list(training_dir.glob("*.pdf"))
    
    if not pdf_files:
        print("❌ No PDF files found")
        return
    
    # Calculate file sizes and identify large PDFs
    large_pdfs = []
    small_pdfs = []
    
    for pdf_file in pdf_files:
        size_mb = pdf_file.stat().st_size / (1024 * 1024)
        if size_mb > 50:
            large_pdfs.append((pdf_file, size_mb))
        else:
            small_pdfs.append((pdf_file, size_mb))
    
    print(f"📊 Found {len(pdf_files)} PDF files:")
    print(f"   📄 Small PDFs (< 50MB): {len(small_pdfs)}")
    print(f"   📄 Large PDFs (≥ 50MB): {len(large_pdfs)}")
    
    if not large_pdfs:
        print("✅ No large PDFs to split")
        return
    
    print(f"\n📄 Large PDFs that will be split:")
    for pdf_file, size_mb in large_pdfs:
        print(f"   📄 {pdf_file.name} ({size_mb:.1f}MB)")
    
    # Create backup directory for original large PDFs
    backup_dir = training_dir / "original_large_pdfs"
    backup_dir.mkdir(exist_ok=True)
    
    # Split large PDFs
    total_chunks_created = 0
    
    for pdf_file, size_mb in large_pdfs:
        print(f"\n🔄 Processing {pdf_file.name} ({size_mb:.1f}MB)...")
        
        # Move original to backup
        backup_path = backup_dir / pdf_file.name
        shutil.move(str(pdf_file), str(backup_path))
        print(f"   📦 Moved original to backup: {backup_path}")
        
        # Split the PDF
        chunks_created = split_pdf(backup_path, training_dir, pages_per_chunk=50)
        total_chunks_created += chunks_created
        
        if chunks_created > 0:
            print(f"   ✅ Successfully split into {chunks_created} chunks")
        else:
            print(f"   ❌ Failed to split {pdf_file.name}")
    
    print(f"\n🎉 PDF splitting completed!")
    print(f"📊 Total chunks created: {total_chunks_created}")
    print(f"📦 Original large PDFs backed up to: {backup_dir}")
    
    # Show final file count
    final_pdfs = list(training_dir.glob("*.pdf"))
    print(f"📄 Final PDF count: {len(final_pdfs)}")
    
    # List all files by size
    print(f"\n📋 Final file list by size:")
    all_files = []
    for pdf_file in final_pdfs:
        size_mb = pdf_file.stat().st_size / (1024 * 1024)
        all_files.append((pdf_file, size_mb))
    
    all_files.sort(key=lambda x: x[1])  # Sort by size
    
    for pdf_file, size_mb in all_files:
        print(f"   📄 {pdf_file.name} ({size_mb:.1f}MB)")

if __name__ == "__main__":
    main()
