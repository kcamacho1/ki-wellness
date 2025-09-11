#!/usr/bin/env python3
"""
Image Processing Service for Ki Wellness
Handles image compression, conversion, and optimization for recipe images
"""

import io
import os
from PIL import Image, ImageOps
from typing import Tuple, Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)


class ImageProcessor:
    """
    Image processing service for optimizing recipe images
    """
    
    def __init__(self):
        # Mobile-friendly image optimization settings
        self.max_width = 600  # Max width for mobile recipe cards
        self.max_height = 450  # Max height for mobile recipe cards
        self.quality = 80  # WebP quality (0-100) - slightly lower for mobile
        self.max_file_size = 500 * 1024  # 500KB max file size after transformation
        self.thumbnail_size = (300, 225)  # Mobile-friendly thumbnail size
        
        # Supported formats
        self.supported_formats = {'JPEG', 'PNG', 'WEBP', 'GIF'}
        self.output_format = 'WEBP'  # Convert all to WebP for better compression
    
    def process_recipe_image(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Process and optimize a recipe image for storage
        
        Args:
            file_data: Original image data
            filename: Original filename
            
        Returns:
            Dict with processed image data and metadata
        """
        try:
            # Open image
            image = Image.open(io.BytesIO(file_data))
            
            # For very large images, use progressive resizing
            if image.width > 2000 or image.height > 2000:
                image = self._progressive_resize(image)
            
            # Convert to RGB if necessary (for WebP compatibility)
            if image.mode in ('RGBA', 'LA', 'P'):
                # Create white background for transparent images
                background = Image.new('RGB', image.size, (255, 255, 255))
                if image.mode == 'P':
                    image = image.convert('RGBA')
                background.paste(image, mask=image.split()[-1] if image.mode == 'RGBA' else None)
                image = background
            elif image.mode != 'RGB':
                image = image.convert('RGB')
            
            # Get original dimensions
            original_width, original_height = image.size
            original_size = len(file_data)
            
            # Calculate optimal dimensions while maintaining aspect ratio
            new_width, new_height = self._calculate_optimal_dimensions(
                original_width, original_height
            )
            
            # Resize image
            if (new_width, new_height) != (original_width, original_height):
                image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            
            # Optimize image
            optimized_data = self._optimize_image(image, filename)
            
            # If still too large, reduce quality further
            if len(optimized_data) > self.max_file_size:
                optimized_data = self._compress_aggressively(image, filename)
            
            # Generate thumbnail for cards
            thumbnail_data = self._generate_thumbnail(image)
            
            # Calculate compression ratio
            compression_ratio = (1 - len(optimized_data) / original_size) * 100
            
            result = {
                'success': True,
                'optimized_data': optimized_data,
                'thumbnail_data': thumbnail_data,
                'original_size': original_size,
                'optimized_size': len(optimized_data),
                'thumbnail_size': len(thumbnail_data),
                'compression_ratio': round(compression_ratio, 1),
                'dimensions': {
                    'original': (original_width, original_height),
                    'optimized': (new_width, new_height),
                    'thumbnail': self.thumbnail_size
                },
                'format': self.output_format,
                'filename': self._generate_optimized_filename(filename)
            }
            
            logger.info(f"Image processed: {original_size} -> {len(optimized_data)} bytes "
                       f"({compression_ratio:.1f}% reduction)")
            
            return result
            
        except Exception as e:
            logger.error(f"Error processing image {filename}: {e}")
            return {
                'success': False,
                'error': f'Image processing failed: {str(e)}'
            }
    
    def _calculate_optimal_dimensions(self, width: int, height: int) -> Tuple[int, int]:
        """
        Calculate optimal dimensions while maintaining aspect ratio
        """
        # Calculate scaling factor
        width_scale = self.max_width / width
        height_scale = self.max_height / height
        scale = min(width_scale, height_scale, 1.0)  # Don't upscale
        
        new_width = int(width * scale)
        new_height = int(height * scale)
        
        # Ensure dimensions are even numbers (better for compression)
        new_width = new_width - (new_width % 2)
        new_height = new_height - (new_height % 2)
        
        return new_width, new_height
    
    def _optimize_image(self, image: Image.Image, filename: str) -> bytes:
        """
        Optimize image with standard settings
        """
        output = io.BytesIO()
        
        # Save as WebP with optimization
        image.save(
            output,
            format=self.output_format,
            quality=self.quality,
            method=6,  # Best compression method
            optimize=True
        )
        
        return output.getvalue()
    
    def _compress_aggressively(self, image: Image.Image, filename: str) -> bytes:
        """
        Apply aggressive compression to meet file size limits
        """
        output = io.BytesIO()
        
        # Start with lower quality
        quality = 70
        
        # Try different quality levels until we meet size requirements
        for q in range(quality, 30, -10):
            output.seek(0)
            output.truncate(0)
            
            image.save(
                output,
                format=self.output_format,
                quality=q,
                method=6,
                optimize=True
            )
            
            if len(output.getvalue()) <= self.max_file_size:
                break
        
        return output.getvalue()
    
    def _generate_thumbnail(self, image: Image.Image) -> bytes:
        """
        Generate thumbnail for recipe cards
        """
        # Create thumbnail
        thumbnail = image.copy()
        thumbnail.thumbnail(self.thumbnail_size, Image.Resampling.LANCZOS)
        
        # Center crop if necessary
        if thumbnail.size != self.thumbnail_size:
            thumbnail = ImageOps.fit(thumbnail, self.thumbnail_size, Image.Resampling.LANCZOS)
        
        output = io.BytesIO()
        thumbnail.save(
            output,
            format=self.output_format,
            quality=80,  # Slightly lower quality for thumbnails
            method=6,
            optimize=True
        )
        
        return output.getvalue()
    
    def _generate_optimized_filename(self, original_filename: str) -> str:
        """
        Generate optimized filename with WebP extension
        """
        name, _ = os.path.splitext(original_filename)
        return f"{name}_optimized.webp"
    
    def validate_image_for_processing(self, file_data: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate if image can be processed
        """
        try:
            image = Image.open(io.BytesIO(file_data))
            
            # Check format
            if image.format not in self.supported_formats:
                return {
                    'valid': False,
                    'error': f'Unsupported image format: {image.format}'
                }
            
            # Check dimensions
            width, height = image.size
            if width < 100 or height < 100:
                return {
                    'valid': False,
                    'error': 'Image too small (min 100x100 pixels)'
                }
            
            # Allow very large images since we'll resize them progressively
            if width > 8000 or height > 8000:
                return {
                    'valid': False,
                    'error': 'Image too large (max 8000x8000 pixels). Please use a smaller image or compress it.'
                }
            
            # Check file size (very generous limit since we'll transform images)
            if len(file_data) > 100 * 1024 * 1024:  # 100MB max input
                return {
                    'valid': False,
                    'error': 'Image file too large (max 100MB). Try: 1) Compress the image on your device, 2) Use a photo editing app to reduce quality, or 3) Take a new photo with lower resolution settings.'
                }
            
            return {
                'valid': True,
                'dimensions': (width, height),
                'format': image.format,
                'size': len(file_data)
            }
            
        except Exception as e:
            return {
                'valid': False,
                'error': f'Invalid image file: {str(e)}'
            }
    
    def get_compression_stats(self, original_size: int, optimized_size: int) -> Dict[str, Any]:
        """
        Get compression statistics
        """
        reduction = original_size - optimized_size
        reduction_percent = (reduction / original_size) * 100 if original_size > 0 else 0
        
        return {
            'original_size_mb': round(original_size / (1024 * 1024), 2),
            'optimized_size_mb': round(optimized_size / (1024 * 1024), 2),
            'reduction_mb': round(reduction / (1024 * 1024), 2),
            'reduction_percent': round(reduction_percent, 1),
            'compression_ratio': round(optimized_size / original_size, 3) if original_size > 0 else 0
        }
    
    def _progressive_resize(self, image: Image.Image) -> Image.Image:
        """
        Progressively resize very large images to prevent memory issues
        """
        original_width, original_height = image.size
        target_width, target_height = self.max_width, self.max_height
        
        # Calculate scale factor
        scale_factor = min(target_width / original_width, target_height / original_height)
        
        # If image is already small enough, return as is
        if scale_factor >= 1.0:
            return image
        
        # Progressive resizing for very large images
        current_image = image
        current_scale = 1.0
        
        # Resize in steps to avoid memory issues
        while current_scale > scale_factor:
            # Calculate next step (reduce by half each time)
            next_scale = max(scale_factor, current_scale * 0.5)
            
            # Calculate new dimensions
            new_width = int(original_width * next_scale)
            new_height = int(original_height * next_scale)
            
            # Resize
            current_image = current_image.resize((new_width, new_height), Image.Resampling.LANCZOS)
            current_scale = next_scale
            
            # If we've reached the target, break
            if current_scale <= scale_factor:
                break
        
        return current_image


# Global instance
image_processor = ImageProcessor()
