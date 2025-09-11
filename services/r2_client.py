#!/usr/bin/env python3
"""
Cloudflare R2 Client for Ki Wellness
Handles object storage for recipe images and dynamic images
"""

import boto3
import requests
import hashlib
import mimetypes
import os
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple
from botocore.exceptions import ClientError, NoCredentialsError
from config.environment import get_environment_detector
from .image_processor import image_processor


class R2Client:
    """
    Cloudflare R2 client for storing and managing recipe images
    """
    
    def __init__(self):
        self.env_detector = get_environment_detector()
        self.config = self.env_detector.get_r2_config()
        
        # R2 credentials
        self.account_id = self.config.get('R2_ACCOUNT_ID')
        self.access_key_id = self.config.get('R2_ACCESS_KEY_ID')
        self.secret_access_key = self.config.get('R2_SECRET_ACCESS_KEY')
        self.bucket_name = self.config.get('R2_BUCKET_NAME')
        self.public_url = self.config.get('R2_PUBLIC_URL')
        self.region = self.config.get('R2_REGION', 'auto')
        self.endpoint_url = self.config.get('R2_ENDPOINT_URL')
        
        # File constraints (very generous limit since we'll transform images)
        self.max_file_size = self.config.get('R2_MAX_FILE_SIZE', 100 * 1024 * 1024)  # 100MB max since we'll transform images
        self.allowed_extensions = self.config.get('R2_ALLOWED_EXTENSIONS', {'png', 'jpg', 'jpeg', 'gif', 'webp'})
        self.folder_prefix = self.config.get('R2_FOLDER_PREFIX', 'ki-wellness/recipes/')
        
        # Initialize S3 client for R2
        self.s3_client = None
        self._initialize_client()
    
    def _initialize_client(self):
        """Initialize the S3 client for R2"""
        if not all([self.account_id, self.access_key_id, self.secret_access_key, self.bucket_name]):
            print("⚠️ R2 credentials not fully configured. R2 storage will be disabled.")
            return
        
        try:
            self.s3_client = boto3.client(
                's3',
                endpoint_url=self.endpoint_url,
                aws_access_key_id=self.access_key_id,
                aws_secret_access_key=self.secret_access_key,
                region_name=self.region
            )
            
            # Test connection
            self.s3_client.head_bucket(Bucket=self.bucket_name)
            print("✅ R2 client initialized successfully")
            
        except NoCredentialsError:
            print("❌ R2 credentials not found")
        except ClientError as e:
            error_code = e.response['Error']['Code']
            if error_code == '404':
                print(f"❌ R2 bucket '{self.bucket_name}' not found")
            else:
                print(f"❌ R2 connection error: {e}")
        except Exception as e:
            print(f"❌ Failed to initialize R2 client: {e}")
    
    def is_available(self) -> bool:
        """Check if R2 storage is available"""
        return self.s3_client is not None
    
    def _generate_object_key(self, filename: str, folder: str = None) -> str:
        """Generate a unique object key for R2 storage"""
        # Create timestamp-based prefix
        timestamp = datetime.utcnow().strftime('%Y/%m/%d')
        
        # Generate unique filename to avoid conflicts
        name, ext = os.path.splitext(filename)
        unique_id = hashlib.md5(f"{name}{timestamp}".encode()).hexdigest()[:8]
        unique_filename = f"{name}_{unique_id}{ext}"
        
        # Build full path
        if folder:
            return f"{self.folder_prefix}{folder}/{timestamp}/{unique_filename}"
        else:
            return f"{self.folder_prefix}{timestamp}/{unique_filename}"
    
    def _get_content_type(self, filename: str) -> str:
        """Get content type for file"""
        content_type, _ = mimetypes.guess_type(filename)
        return content_type or 'application/octet-stream'
    
    def _validate_file_content(self, file_data: bytes, filename: str) -> bool:
        """
        Validate file content to ensure it's a safe image file
        """
        try:
            # Check file size
            if len(file_data) > self.max_file_size:
                return False
            
            # Check file signature (magic bytes)
            if len(file_data) < 4:
                return False
            
            # Image file signatures
            image_signatures = {
                b'\xFF\xD8\xFF': 'jpeg',
                b'\x89PNG\r\n\x1a\n': 'png',
                b'GIF87a': 'gif',
                b'GIF89a': 'gif',
                b'RIFF': 'webp',  # WebP starts with RIFF
            }
            
            # Check for valid image signatures
            is_valid_image = False
            for signature, file_type in image_signatures.items():
                if file_data.startswith(signature):
                    is_valid_image = True
                    break
            
            if not is_valid_image:
                return False
            
            # Additional validation for WebP
            if file_data.startswith(b'RIFF') and b'WEBP' not in file_data[:12]:
                return False
            
            # Check file extension matches content
            file_ext = os.path.splitext(filename)[1].lower()
            allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
            
            if file_ext not in allowed_extensions:
                return False
            
            # Basic content validation - check for executable content
            dangerous_patterns = [
                b'<script',
                b'javascript:',
                b'vbscript:',
                b'data:text/html',
                b'<?php',
                b'#!/bin/',
                b'MZ',  # PE executable
            ]
            
            for pattern in dangerous_patterns:
                if pattern in file_data.lower():
                    return False
            
            return True
            
        except Exception as e:
            print(f"❌ File validation error: {e}")
            return False
    
    def _validate_food_image(self, file_data: bytes, filename: str) -> dict:
        """
        Validate that the uploaded image is actually a food image
        Returns dict with 'valid' boolean and 'error' message
        """
        try:
            # First, basic file validation
            if not self._validate_file_content(file_data, filename):
                return {'valid': False, 'error': 'Invalid file type or content'}
            
            # Check file size (removed mobile restriction since we'll transform images)
            if len(file_data) > self.max_file_size:
                return {'valid': False, 'error': f'File too large (max {self.max_file_size // (1024*1024)}MB)'}
            
            if len(file_data) < 1024:  # At least 1KB
                return {'valid': False, 'error': 'File too small (min 1KB)'}
            
            # Check filename for food-related keywords
            filename_lower = filename.lower()
            food_keywords = [
                'food', 'meal', 'dish', 'recipe', 'cooking', 'kitchen', 'dinner', 'lunch', 'breakfast',
                'snack', 'dessert', 'soup', 'salad', 'pasta', 'pizza', 'burger', 'sandwich',
                'chicken', 'beef', 'fish', 'vegetable', 'fruit', 'bread', 'cake', 'cookie'
            ]
            
            # Check if filename contains food-related keywords
            has_food_keyword = any(keyword in filename_lower for keyword in food_keywords)
            
            # Check for non-food keywords that should be rejected
            non_food_keywords = [
                'document', 'pdf', 'text', 'screenshot', 'photo', 'image', 'picture', 'selfie',
                'portrait', 'landscape', 'nature', 'animal', 'person', 'face', 'body',
                'logo', 'icon', 'banner', 'advertisement', 'ad', 'promo'
            ]
            
            has_non_food_keyword = any(keyword in filename_lower for keyword in non_food_keywords)
            
            # If filename has non-food keywords but no food keywords, reject
            if has_non_food_keyword and not has_food_keyword:
                return {'valid': False, 'error': 'Please upload food-related images only'}
            
            # Check image dimensions (basic validation)
            try:
                from PIL import Image
                import io
                
                # Open image to check dimensions
                image = Image.open(io.BytesIO(file_data))
                width, height = image.size
                
                # Check if image is too small (likely not a proper food photo)
                if width < 100 or height < 100:
                    return {'valid': False, 'error': 'Image too small (min 100x100 pixels)'}
                
                # Check if image is too large (allow larger images since we'll resize them)
                if width > 8000 or height > 8000:
                    return {'valid': False, 'error': 'Image too large (max 8000x8000 pixels). Please use a smaller image.'}
                
                # Check aspect ratio (food images should be reasonable)
                aspect_ratio = width / height
                if aspect_ratio > 5 or aspect_ratio < 0.2:  # Very wide or very tall
                    return {'valid': False, 'error': 'Please upload properly proportioned food images'}
                
            except ImportError:
                # PIL not available, skip dimension checks
                pass
            except Exception as e:
                # If we can't read the image, it's probably not a valid image
                return {'valid': False, 'error': 'Invalid image format'}
            
            # Basic content analysis for food-related patterns
            content_lower = file_data.lower()
            
            # Check for common non-food content patterns
            non_food_patterns = [
                b'screenshot', b'desktop', b'window', b'dialog', b'menu',
                b'button', b'text', b'document', b'pdf', b'office',
                b'person', b'face', b'portrait', b'selfie'
            ]
            
            for pattern in non_food_patterns:
                if pattern in content_lower:
                    return {'valid': False, 'error': 'Please upload food-related images only'}
            
            # If we get here, the image passes basic validation
            return {'valid': True, 'error': None}
            
        except Exception as e:
            print(f"❌ Food image validation error: {e}")
            return {'valid': False, 'error': 'Image validation failed'}
    
    def upload_file(self, file_data: bytes, filename: str, folder: str = None, 
                   content_type: str = None, process_image: bool = True) -> Optional[Dict[str, Any]]:
        """
        Upload file to R2 storage with enhanced security and image processing
        
        Args:
            file_data: File content as bytes
            filename: Original filename
            folder: Optional folder name
            content_type: MIME type (auto-detected if not provided)
            process_image: Whether to process/compress the image
        
        Returns:
            Dict with upload info or None if failed
        """
        if not self.is_available():
            print("❌ R2 storage not available")
            return None
        
        # Validate file size
        if len(file_data) > self.max_file_size:
            print(f"❌ File too large: {len(file_data)} bytes (max: {self.max_file_size})")
            return None
        
        # Validate file extension
        file_ext = os.path.splitext(filename)[1].lower().lstrip('.')
        if file_ext not in self.allowed_extensions:
            print(f"❌ File type not allowed: {file_ext}")
            return None
        
        # Additional security: Validate file content and food image
        validation_result = self._validate_food_image(file_data, filename)
        if not validation_result['valid']:
            print(f"❌ Food image validation failed: {filename} - {validation_result['error']}")
            return None
        
        try:
            # Process image if requested
            if process_image:
                print(f"🔄 Processing image: {filename}")
                processed_result = image_processor.process_recipe_image(file_data, filename)
                
                if not processed_result['success']:
                    print(f"❌ Image processing failed: {processed_result['error']}")
                    return None
                
                # Use processed image data
                processed_data = processed_result['optimized_data']
                processed_filename = processed_result['filename']
                compression_stats = image_processor.get_compression_stats(
                    processed_result['original_size'], 
                    processed_result['optimized_size']
                )
                
                print(f"✅ Image compressed: {compression_stats['original_size_mb']}MB -> "
                      f"{compression_stats['optimized_size_mb']}MB "
                      f"({compression_stats['reduction_percent']}% reduction)")
                
                # Update content type for WebP
                content_type = 'image/webp'
                filename = processed_filename
                file_data = processed_data
            else:
                compression_stats = None
            
            # Generate object key
            object_key = self._generate_object_key(filename, folder)
            
            # Get content type
            if not content_type:
                content_type = self._get_content_type(filename)
            
            # Upload to R2
            self.s3_client.put_object(
                Bucket=self.bucket_name,
                Key=object_key,
                Body=file_data,
                ContentType=content_type,
                Metadata={
                    'original_filename': filename,
                    'uploaded_at': datetime.utcnow().isoformat(),
                    'source': 'ki-wellness',
                    'processed': str(process_image).lower()
                }
            )
            
            # Generate public URL
            if self.public_url:
                public_url = f"{self.public_url.rstrip('/')}/{object_key}"
            else:
                public_url = f"https://{self.bucket_name}.{self.account_id}.r2.cloudflarestorage.com/{object_key}"
            
            result = {
                'object_key': object_key,
                'public_url': public_url,
                'filename': filename,
                'size': len(file_data),
                'content_type': content_type,
                'uploaded_at': datetime.utcnow().isoformat(),
                'compression_stats': compression_stats
            }
            
            print(f"✅ Uploaded to R2: {object_key}")
            return result
            
        except ClientError as e:
            print(f"❌ R2 upload error: {e}")
            return None
        except Exception as e:
            print(f"❌ Upload failed: {e}")
            return None
    
    def upload_from_url(self, url: str, filename: str, folder: str = None) -> Optional[Dict[str, Any]]:
        """
        Download file from URL and upload to R2
        
        Args:
            url: Source URL
            filename: Desired filename
            folder: Optional folder name
        
        Returns:
            Dict with upload info or None if failed
        """
        try:
            # Download file
            response = requests.get(url, timeout=30)
            response.raise_for_status()
            
            # Upload to R2
            return self.upload_file(
                file_data=response.content,
                filename=filename,
                folder=folder,
                content_type=response.headers.get('content-type')
            )
            
        except requests.RequestException as e:
            print(f"❌ Failed to download from URL: {e}")
            return None
        except Exception as e:
            print(f"❌ Upload from URL failed: {e}")
            return None
    
    def delete_file(self, object_key: str) -> bool:
        """
        Delete file from R2 storage
        
        Args:
            object_key: R2 object key
        
        Returns:
            True if successful, False otherwise
        """
        if not self.is_available():
            print("❌ R2 storage not available")
            return False
        
        try:
            self.s3_client.delete_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            print(f"✅ Deleted from R2: {object_key}")
            return True
            
        except ClientError as e:
            print(f"❌ R2 delete error: {e}")
            return False
        except Exception as e:
            print(f"❌ Delete failed: {e}")
            return False
    
    def get_file_info(self, object_key: str) -> Optional[Dict[str, Any]]:
        """
        Get file information from R2
        
        Args:
            object_key: R2 object key
        
        Returns:
            Dict with file info or None if not found
        """
        if not self.is_available():
            return None
        
        try:
            response = self.s3_client.head_object(
                Bucket=self.bucket_name,
                Key=object_key
            )
            
            return {
                'size': response['ContentLength'],
                'content_type': response['ContentType'],
                'last_modified': response['LastModified'],
                'metadata': response.get('Metadata', {})
            }
            
        except ClientError as e:
            if e.response['Error']['Code'] == '404':
                return None
            print(f"❌ R2 info error: {e}")
            return None
        except Exception as e:
            print(f"❌ Get file info failed: {e}")
            return None
    
    def list_files(self, folder: str = None, max_files: int = 100) -> list:
        """
        List files in R2 bucket
        
        Args:
            folder: Optional folder prefix
            max_files: Maximum number of files to return
        
        Returns:
            List of file objects
        """
        if not self.is_available():
            return []
        
        try:
            prefix = f"{self.folder_prefix}{folder}/" if folder else self.folder_prefix
            
            response = self.s3_client.list_objects_v2(
                Bucket=self.bucket_name,
                Prefix=prefix,
                MaxKeys=max_files
            )
            
            files = []
            for obj in response.get('Contents', []):
                files.append({
                    'key': obj['Key'],
                    'size': obj['Size'],
                    'last_modified': obj['LastModified'],
                    'public_url': f"{self.public_url.rstrip('/')}/{obj['Key']}" if self.public_url else None
                })
            
            return files
            
        except ClientError as e:
            print(f"❌ R2 list error: {e}")
            return []
        except Exception as e:
            print(f"❌ List files failed: {e}")
            return []
    
    def get_storage_stats(self) -> Dict[str, Any]:
        """
        Get storage statistics
        
        Returns:
            Dict with storage stats
        """
        if not self.is_available():
            return {'error': 'R2 not available'}
        
        try:
            files = self.list_files(max_files=1000)
            
            total_files = len(files)
            total_size = sum(f['size'] for f in files)
            
            return {
                'total_files': total_files,
                'total_size_bytes': total_size,
                'total_size_mb': round(total_size / (1024 * 1024), 2),
                'bucket_name': self.bucket_name,
                'folder_prefix': self.folder_prefix
            }
            
        except Exception as e:
            return {'error': str(e)}


# Global instance
r2_client = R2Client()
