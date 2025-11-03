from pathlib import Path
from typing import List, Tuple, Optional
from PIL import Image
import shutil

class ImageProcessor:
    def __init__(
        self,
        target_size: Tuple[int, int] = (256, 256),
        min_size: Tuple[int, int] = (100, 100),
        quality: int = 95,
        maintain_aspect_ratio: bool = True
    ):
        """
        Initialize the image processor
        
        Args:
            target_size: Target dimensions for resized images (width, height)
            min_size: Minimum dimensions to accept an image (width, height)
            quality: JPEG quality for saved images (1-100)
            maintain_aspect_ratio: If True, resize maintaining aspect ratio with padding
        """
        self.target_size = target_size
        self.min_size = min_size
        self.quality = quality
        self.maintain_aspect_ratio = maintain_aspect_ratio
    
    def validate_image(self, image_path: Path) -> bool:
        """
        Validate if an image meets minimum requirements
        
        Args:
            image_path: Path to the image file
            
        Returns:
            True if image is valid, False otherwise
        """
        try:
            with Image.open(image_path) as img:
                width, height = img.size
                
                # Check minimum dimensions
                if width < self.min_size[0] or height < self.min_size[1]:
                    print(f"✗ {image_path.name}: Too small ({width}x{height})")
                    return False
                
                # Check if image can be loaded properly
                img.verify()
                
            return True
            
        except Exception as e:
            print(f"✗ {image_path.name}: Invalid image - {e}")
            return False
    
    def resize_image(self, img: Image.Image) -> Image.Image:
        """
        Resize image to target size
        
        Args:
            img: PIL Image object
            
        Returns:
            Resized PIL Image object
        """
        if self.maintain_aspect_ratio:
            # Resize maintaining aspect ratio and add padding
            img.thumbnail(self.target_size, Image.Resampling.LANCZOS)
            
            # Create new image with target size and white background
            new_img = Image.new('RGB', self.target_size, (255, 255, 255))
            
            # Paste resized image in the center
            paste_x = (self.target_size[0] - img.size[0]) // 2
            paste_y = (self.target_size[1] - img.size[1]) // 2
            new_img.paste(img, (paste_x, paste_y))
            
            return new_img
        else:
            # Direct resize (may distort image)
            return img.resize(self.target_size, Image.Resampling.LANCZOS)
    
    def convert_to_rgb(self, img: Image.Image) -> Image.Image:
        """
        Convert image to RGB format
        
        Args:
            img: PIL Image object
            
        Returns:
            RGB PIL Image object
        """
        if img.mode != 'RGB':
            # Handle different image modes
            if img.mode in ('RGBA', 'LA', 'P'):
                # Create white background
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                
                # Paste with alpha channel if available
                if img.mode == 'RGBA':
                    rgb_img.paste(img, mask=img.split()[-1])
                elif img.mode == 'P' and 'transparency' in img.info:
                    img = img.convert('RGBA')
                    rgb_img.paste(img, mask=img.split()[-1])
                else:
                    rgb_img.paste(img)
                
                return rgb_img
            else:
                # For other modes, direct conversion
                return img.convert('RGB')
        
        return img
    
    def process_single_image(
        self,
        input_path: Path,
        output_path: Path
    ) -> bool:
        """
        Process a single image: validate, resize, convert format
        
        Args:
            input_path: Path to input image
            output_path: Path to save processed image
            
        Returns:
            True if processing succeeded, False otherwise
        """
        try:
            # Validate image
            if not self.validate_image(input_path):
                return False
            
            # Open and process image
            with Image.open(input_path) as img:
                # Convert to RGB
                img = self.convert_to_rgb(img)
                
                # Resize
                img = self.resize_image(img)
                
                # Ensure output directory exists
                output_path.parent.mkdir(parents=True, exist_ok=True)
                
                # Save as JPEG
                img.save(output_path, 'JPEG', quality=self.quality, optimize=True)
            
            return True
            
        except Exception as e:
            print(f"✗ Error processing {input_path.name}: {e}")
            return False
    
    def process_batch(
        self,
        input_dir: Path,
        output_dir: Path,
        clean_output: bool = False
    ) -> List[Path]:
        """
        Process all images in a directory
        
        Args:
            input_dir: Directory containing input images
            output_dir: Directory to save processed images
            clean_output: If True, clean output directory before processing
            
        Returns:
            List of successfully processed image paths
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        # Clean output directory if requested
        if clean_output and output_path.exists():
            shutil.rmtree(output_path)
        
        output_path.mkdir(parents=True, exist_ok=True)
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
        image_files = [
            f for f in input_path.iterdir()
            if f.suffix.lower() in image_extensions
        ]
        
        if not image_files:
            print(f"No images found in {input_path}")
            return []
        
        print(f"\n🔄 Processing {len(image_files)} images...")
        print(f"   Target size: {self.target_size}")
        print(f"   Maintain aspect ratio: {self.maintain_aspect_ratio}")
        print(f"   Quality: {self.quality}\n")
        
        processed_files = []
        
        for i, img_path in enumerate(image_files, 1):
            print(f"[{i}/{len(image_files)}] Processing {img_path.name}...", end=" ")
            
            # Generate output filename (always .jpg)
            output_filename = img_path.stem + '.jpg'
            output_file = output_path / output_filename
            
            # Process image
            if self.process_single_image(img_path, output_file):
                processed_files.append(output_file)
                print(f"✓ Saved as {output_filename}")
            else:
                print("✗ Failed")
        
        # Summary
        success_rate = (len(processed_files) / len(image_files)) * 100
        print(f"\n✅ Processing complete: {len(processed_files)}/{len(image_files)} images ({success_rate:.1f}%)")
        print(f"📁 Saved to: {output_path.absolute()}")
        
        return processed_files
    
    def get_image_stats(self, image_dir: Path) -> dict:
        """
        Get statistics about images in a directory
        
        Args:
            image_dir: Directory containing images
            
        Returns:
            Dictionary with image statistics
        """
        image_path = Path(image_dir)
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp', '.bmp', '.gif'}
        image_files = [
            f for f in image_path.iterdir()
            if f.suffix.lower() in image_extensions
        ]
        
        if not image_files:
            return {
                'total_images': 0,
                'valid_images': 0,
                'invalid_images': 0
            }
        
        valid_count = 0
        invalid_count = 0
        total_size = 0
        sizes = []
        
        for img_path in image_files:
            try:
                with Image.open(img_path) as img:
                    img.verify()
                    valid_count += 1
                    total_size += img_path.stat().st_size
                    
                # Reopen to get size (verify closes the file)
                with Image.open(img_path) as img:
                    sizes.append(img.size)
            except:
                invalid_count += 1
        
        avg_size_mb = (total_size / valid_count / 1024 / 1024) if valid_count > 0 else 0
        
        return {
            'total_images': len(image_files),
            'valid_images': valid_count,
            'invalid_images': invalid_count,
            'average_size_mb': round(avg_size_mb, 2),
            'dimensions': sizes[:5]  # First 5 dimensions as sample
        }
