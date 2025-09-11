#!/usr/bin/env python3
"""
Test script to verify R2 storage configuration and upload functionality
"""

import os
import sys
from flask import Flask
from services.r2_client import r2_client

def test_r2_configuration():
    """Test R2 configuration and connectivity"""
    print("🔍 Testing R2 Configuration...")
    
    # Check if R2 client is available
    if not r2_client.is_available():
        print("❌ R2 client is not available")
        print("Please check your R2 configuration in environment variables:")
        print("- R2_ACCOUNT_ID")
        print("- R2_ACCESS_KEY_ID") 
        print("- R2_SECRET_ACCESS_KEY")
        print("- R2_BUCKET_NAME")
        print("- R2_PUBLIC_URL (optional)")
        return False
    
    print("✅ R2 client is available")
    
    # Test bucket access
    try:
        stats = r2_client.get_storage_stats()
        if 'error' in stats:
            print(f"❌ Error accessing R2 bucket: {stats['error']}")
            return False
        
        print(f"✅ R2 bucket accessible: {stats['bucket_name']}")
        print(f"📊 Current storage: {stats['total_files']} files, {stats['total_size_mb']}MB")
        return True
        
    except Exception as e:
        print(f"❌ Error testing R2 bucket: {e}")
        return False

def test_image_upload():
    """Test uploading a sample image to R2"""
    print("\n🖼️ Testing Image Upload...")
    
    # Create a simple test image (1x1 pixel PNG)
    test_image_data = b'\x89PNG\r\n\x1a\n\x00\x00\x00\rIHDR\x00\x00\x00\x01\x00\x00\x00\x01\x08\x02\x00\x00\x00\x90wS\xde\x00\x00\x00\tpHYs\x00\x00\x0b\x13\x00\x00\x0b\x13\x01\x00\x9a\x9c\x18\x00\x00\x00\nIDATx\x9cc```\x00\x00\x00\x04\x00\x01\xdd\x8d\xb4\x1c\x00\x00\x00\x00IEND\xaeB`\x82'
    
    try:
        result = r2_client.upload_file(
            file_data=test_image_data,
            filename="test_recipe_image.png",
            folder="test-uploads",
            process_image=True
        )
        
        if result:
            print(f"✅ Test image uploaded successfully")
            print(f"📁 Object key: {result['object_key']}")
            print(f"🔗 Public URL: {result['public_url']}")
            print(f"📏 Size: {result['size']} bytes")
            if result.get('compression_stats'):
                stats = result['compression_stats']
                print(f"📊 Compression: {stats['original_size_mb']}MB -> {stats['optimized_size_mb']}MB ({stats['reduction_percent']}% reduction)")
            return True
        else:
            print("❌ Test image upload failed")
            return False
            
    except Exception as e:
        print(f"❌ Error uploading test image: {e}")
        return False

def main():
    """Main test function"""
    print("🧪 R2 Storage Test Script")
    print("=" * 50)
    
    # Test configuration
    config_ok = test_r2_configuration()
    
    if config_ok:
        # Test upload
        upload_ok = test_image_upload()
        
        if upload_ok:
            print("\n🎉 All tests passed! R2 storage is working correctly.")
            print("✅ Recipe images will be uploaded to R2 storage.")
        else:
            print("\n❌ Upload test failed. Check R2 permissions and configuration.")
            sys.exit(1)
    else:
        print("\n❌ Configuration test failed. Please check your R2 setup.")
        sys.exit(1)

if __name__ == "__main__":
    main()
