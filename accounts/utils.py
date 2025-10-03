from PIL import Image, ImageOps
import io
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys


def optimize_image(image_file, max_width=800, max_height=600, quality=85, format='JPEG'):
    """
    Optimize and compress an uploaded image file.
    
    Args:
        image_file: Django UploadedFile object
        max_width: Maximum width in pixels
        max_height: Maximum height in pixels
        quality: JPEG quality (1-100)
        format: Output format ('JPEG', 'PNG', 'WEBP')
    
    Returns:
        InMemoryUploadedFile: Optimized image file
    """
    try:
        # Open the image
        img = Image.open(image_file)
        
        # Convert RGBA to RGB if saving as JPEG
        if format == 'JPEG' and img.mode in ('RGBA', 'LA', 'P'):
            # Create a white background
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Auto-orient the image based on EXIF data
        img = ImageOps.exif_transpose(img)
        
        # Calculate new dimensions while maintaining aspect ratio
        original_width, original_height = img.size
        
        # Only resize if image is larger than max dimensions
        if original_width > max_width or original_height > max_height:
            # Calculate scaling factor
            width_ratio = max_width / original_width
            height_ratio = max_height / original_height
            scale_ratio = min(width_ratio, height_ratio)
            
            new_width = int(original_width * scale_ratio)
            new_height = int(original_height * scale_ratio)
            
            # Resize with high-quality resampling
            img = img.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        # Save to BytesIO
        output = io.BytesIO()
        
        # Set save parameters based on format
        save_kwargs = {}
        if format == 'JPEG':
            save_kwargs = {
                'format': format,
                'quality': quality,
                'optimize': True,
                'progressive': True
            }
        elif format == 'PNG':
            save_kwargs = {
                'format': format,
                'optimize': True
            }
        elif format == 'WEBP':
            save_kwargs = {
                'format': format,
                'quality': quality,
                'optimize': True
            }
        
        img.save(output, **save_kwargs)
        output.seek(0)
        
        # Create new InMemoryUploadedFile
        file_extension = format.lower()
        if file_extension == 'jpeg':
            file_extension = 'jpg'
            
        # Generate new filename
        original_name = image_file.name
        name_parts = original_name.rsplit('.', 1)
        if len(name_parts) > 1:
            new_name = f"{name_parts[0]}_optimized.{file_extension}"
        else:
            new_name = f"{original_name}_optimized.{file_extension}"
        
        return InMemoryUploadedFile(
            output,
            'ImageField',
            new_name,
            f'image/{file_extension}',
            sys.getsizeof(output),
            None
        )
        
    except Exception as e:
        # If optimization fails, return original file
        print(f"Image optimization failed: {e}")
        return image_file


def optimize_profile_picture(image_file):
    """
    Optimize profile picture with specific settings.
    Square crop and resize to 400x400 pixels.
    """
    try:
        img = Image.open(image_file)
        
        # Convert RGBA to RGB if needed
        if img.mode in ('RGBA', 'LA', 'P'):
            background = Image.new('RGB', img.size, (255, 255, 255))
            if img.mode == 'P':
                img = img.convert('RGBA')
            background.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
            img = background
        
        # Auto-orient based on EXIF
        img = ImageOps.exif_transpose(img)
        
        # Make square crop from center
        width, height = img.size
        size = min(width, height)
        
        left = (width - size) // 2
        top = (height - size) // 2
        right = left + size
        bottom = top + size
        
        img = img.crop((left, top, right, bottom))
        
        # Resize to 400x400
        img = img.resize((400, 400), Image.Resampling.LANCZOS)
        
        # Save optimized image
        output = io.BytesIO()
        img.save(output, format='JPEG', quality=90, optimize=True, progressive=True)
        output.seek(0)
        
        # Generate new filename
        original_name = image_file.name
        name_parts = original_name.rsplit('.', 1)
        if len(name_parts) > 1:
            new_name = f"{name_parts[0]}_profile.jpg"
        else:
            new_name = f"{original_name}_profile.jpg"
        
        return InMemoryUploadedFile(
            output,
            'ImageField',
            new_name,
            'image/jpeg',
            sys.getsizeof(output),
            None
        )
        
    except Exception as e:
        print(f"Profile picture optimization failed: {e}")
        return image_file


def optimize_portfolio_image(image_file):
    """
    Optimize portfolio image with specific settings.
    Maintain aspect ratio, max 1200x900 pixels.
    """
    return optimize_image(
        image_file,
        max_width=1200,
        max_height=900,
        quality=88,
        format='JPEG'
    )


def optimize_review_image(image_file):
    """
    Optimize review image with specific settings.
    Maintain aspect ratio, max 1000x750 pixels.
    """
    return optimize_image(
        image_file,
        max_width=1000,
        max_height=750,
        quality=85,
        format='JPEG'
    )