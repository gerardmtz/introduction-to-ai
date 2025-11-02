import requests
import time
from pathlib import Path
from PIL import Image
from io import BytesIO
from typing import List, Dict, Optional

class OpenverseDownloader:
    def __init__(self):
        self.base_url = "https://api.openverse.org/v1/images/"
        self.headers = {
            'User-Agent': 'DatasetGenerator/1.0 (Educational Project)'
        }
    
    def search_images(self, query: str, num_images: int = 50) -> List[Dict]:        
        """
        Search images in Openverse
        
        Args:
            query: search criteria
            num_images: number of images to search
            
        Returns:
            List of dictorionaries with information related to
            each image
        """
        page_size = min(num_images, 500)  # max per page
        
        params = {
            'q': query,
            'page_size': page_size
        }
        
        try:
            response = requests.get(
                self.base_url,
                params=params,
                headers=self.headers,
                timeout=10
            )
            response.raise_for_status()
            
            data = response.json()
            results = data.get('results', [])
            
            print(f"✓ Found {len(results)} images for '{query}'")
            return results[:num_images]
            
        except requests.exceptions.RequestException as e:
            print(f"✗ Error on query: {e}")
            return []
    
    def download_image(self, image_info: Dict, save_dir: Path, index: int) -> Optional[Path]:        
        """
        Download a single image
        
        Args:
            image_info: dictionary with image data
            save_dir: saving direcotry
            index: index to name the file
            
        Returns:
            Path for save files, None if download fails
        """
        url = image_info.get('url')
        if not url:
            return None
        
        try:
            # Download the image
            response = requests.get(url, timeout=10, headers=self.headers)
            response.raise_for_status()
            
            # Verify if it is a valid image
            img = Image.open(BytesIO(response.content))
            
            # Transform into RGB if necessary (to delete transparency)
            if img.mode in ('RGBA', 'LA', 'P'):
                rgb_img = Image.new('RGB', img.size, (255, 255, 255))
                rgb_img.paste(img, mask=img.split()[-1] if img.mode == 'RGBA' else None)
                img = rgb_img
            
            # Save images
            filename = f"image_{index:04d}.jpg"
            filepath = save_dir / filename
            img.save(filepath, 'JPEG', quality=95)
            
            return filepath
            
        except Exception as e:
            print(f"✗ Error while downloading the image {index}: {e}")
            return None
    
    def download_dataset(self, query: str, num_images: int, save_dir: str) -> List[Path]:
        """
        Dowloads a full set of images
        
        Args:
            query: search criteria
            num_images: total of images to download
            save_dir: save directory for downloaded images
            
        Returns:
            List all the routes of sucessfully downloaded files
        """
        save_path = Path(save_dir)
        save_path.mkdir(parents=True, exist_ok=True)
        
        # Buscar imágenes
        print(f"\n🔍 Searching '{query}' in Openverse...")
        results = self.search_images(query, num_images)
        
        if not results:
            print("Search criteria images not found")
            return []
        
        # Descargar imágenes
        print(f"\n⬇️  Downloading {len(results)} images...\n")
        downloaded = []
        
        for i, image_info in enumerate(results, 1):
            print(f"[{i}/{len(results)}] Downloading...", end=" ")
            
            filepath = self.download_image(image_info, save_path, i)
            
            if filepath:
                downloaded.append(filepath)
                print(f"✓ Saved as {filepath.name}")
            else:
                print("✗ Saving failed")
            
            # small pause to avoid overwhelm the server
            time.sleep(0.5)
        
        print(f"\n✅ Downloaded: {len(downloaded)}/{len(results)} sucessful images")
        print(f"📁 Saved in: {save_path.absolute()}")
        
        return downloaded
