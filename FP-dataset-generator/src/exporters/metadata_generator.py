from pathlib import Path
from typing import Dict, List, Optional
import json
from datetime import datetime
from PIL import Image

class MetadataGenerator:
    def __init__(self): 
            """ 
            Initialize the metadata generator 
            """ 
            self.supported_formats = {'.jpg', '.jpeg', '.png', '.webp'} 

    def get_image_info(self, image_path: Path) -> Optional[Dict]: 
            """ 
            Get detailed information about a single image 
            
            Args: 
                image_path: Path to the image file 
                
            Returns: 
                Dictionary with image information or None if error 
            """ 
            try: 
                with Image.open(image_path) as img: 
                    return { 
                        'filename': image_path.name, 
                        'format': img.format, 
                        'mode': img.mode, 
                        'width': img.size[0], 
                        'height': img.size[1], 
                        'size_bytes': image_path.stat().st_size, 
                        'size_kb': round(image_path.stat().st_size / 1024, 2) 
                    } 
            except Exception as e: 
                print(f"✗ Error reading {image_path.name}: {e}") 
                return None

    def scan_directory(self, directory: Path) -> List[Dict]: 
            """ 
            Scan a directory and get info for all images 
            
            Args: 
                directory: Directory to scan 
                
            Returns: 
                List of image information dictionaries 
            """ 
            dir_path = Path(directory) 
            
            if not dir_path.exists(): 
                return [] 
            
            images_info = [] 
            
            for file_path in dir_path.iterdir(): 
                if file_path.is_file() and file_path.suffix.lower() in self.supported_formats: 
                    img_info = self.get_image_info(file_path) 
                    if img_info: 
                        images_info.append(img_info) 
            
            return images_info

    def calculate_split_stats(self, images_info: List[Dict]) -> Dict: 
            """ 
            Calculate statistics for a split (train/val/test) 
            
            Args: 
                images_info: List of image information dictionaries 
                
            Returns: 
                Dictionary with statistics 
            """ 
            if not images_info: 
                return { 
                    'count': 0, 
                    'total_size_mb': 0, 
                    'average_size_kb': 0, 
                    'formats': {}, 
                    'average_dimensions': {'width': 0, 'height': 0} 
                } 
            
            total_size_bytes = sum(img['size_bytes'] for img in images_info) 
            total_width = sum(img['width'] for img in images_info) 
            total_height = sum(img['height'] for img in images_info)
            
            # Count formats 
            formats = {} 
            for img in images_info: 
                fmt = img['format'] 
                formats[fmt] = formats.get(fmt, 0) + 1 
            
            return { 
                'count': len(images_info),
                'total_size_mb': round(total_size_bytes / (1024 * 1024), 2), 
                'average_size_kb': round((total_size_bytes / len(images_info)) / 1024, 2), 
                'formats': formats, 
                'average_dimensions': { 
                    'width': round(total_width / len(images_info)), 
                    'height': round(total_height / len(images_info))
                } 
            }

    def generate_dataset_metadata(
            self, 
            dataset_dir: Path, 
            dataset_name: str, 
            description: str = "", 
            source: str = "openverse", 
            additional_info: Optional[Dict] = None 
        ) -> Dict: 
            """ 
            Generate complete metadata for a dataset 
            
            Args: 
                dataset_dir: Root directory of the organized dataset 
                dataset_name: Name of the dataset 
                description: Description of the dataset 
                source: Source of the images (e.g., 'openverse', 'upload') 
                additional_info: Additional information to include in metadata 
                
            Returns: 
                Dictionary with complete dataset metadata 
            """ 
            dataset_path = Path(dataset_dir) 
            
            print("\n" + "=" * 70) 
            print("GENERATING METADATA") 
            print("=" * 70) 
            
            if not dataset_path.exists(): 
                print(f"✗ Dataset directory does not exist: {dataset_path}") 
                return {} 
            
            metadata = { 
                'dataset_name': dataset_name, 
                'description': description, 
                'source': source, 
                'created_at': datetime.now().isoformat(), 
                'root_path': str(dataset_path.absolute()), 
                'splits': {}, 
                'statistics': { 
                    'total_images': 0, 
                    'total_size_mb': 0, 
                    'categories': [] 
                } 
            } 
            
            # Add additional info if provided 
            if additional_info: 
                metadata['additional_info'] = additional_info 
            
            
            # Scan each split 
            print("\n Scanning dataset structure...") 
            
            for split in ['train', 'val', 'test']: 
                split_path = dataset_path / split 
                
                if not split_path.exists(): 
                    print(f"   ⚠ {split} directory not found, skipping...") 
                    continue 
                
                print(f"   Scanning {split}/ directory...") 
                
                split_metadata = { 
                    'path': str(split_path.relative_to(dataset_path)), 
                    'categories': {} 
                } 
                
                # Get categories in this split 
                categories = [d for d in split_path.iterdir() if d.is_dir()] 
                
                for category_dir in categories: 
                    category_name = category_dir.name 
                    
                    # Add category to global list if not present 
                    if category_name not in metadata['statistics']['categories']: 
                        metadata['statistics']['categories'].append(category_name) 
                    
                    # Scan images in category 
                    images_info = self.scan_directory(category_dir) 
                    
                    # Calculate stats for this category 
                    category_stats = self.calculate_split_stats(images_info) 
                    
                    split_metadata['categories'][category_name] = { 
                        'path': str(category_dir.relative_to(dataset_path)), 
                        'statistics': category_stats, 
                        'images': [ 
                            { 
                                'filename': img['filename'], 
                                'dimensions': f"{img['width']}x{img['height']}", 
                                'size_kb': img['size_kb'] 
                            } 
                            for img in images_info 
                        ] 
                    } 
                    
                    # Update global statistics 
                    metadata['statistics']['total_images'] += category_stats['count'] 
                    metadata['statistics']['total_size_mb'] += category_stats['total_size_mb'] 
                
                # Add split statistics summary 
                split_total = sum( 
                    cat['statistics']['count'] 
                    for cat in split_metadata['categories'].values() 
                ) 
                split_metadata['total_images'] = split_total 
                
                metadata['splits'][split] = split_metadata 
                
                print(f"      Found {split_total} images in {len(categories)} category(ies)") 
            
            # Round total size 
            metadata['statistics']['total_size_mb'] = round( 
                metadata['statistics']['total_size_mb'], 2 
            ) 
            
            # Sort categories 
            metadata['statistics']['categories'].sort() 
            
            print(f"\n Metadata generated successfully") 
            print(f"   Total images: {metadata['statistics']['total_images']}") 
            print(f"   Total size: {metadata['statistics']['total_size_mb']} MB") 
            print(f"   Categories: {', '.join(metadata['statistics']['categories'])}") 
            
            return metadata

    def save_metadata( 
            self, 
            metadata: Dict, 
            output_path: Path, 
            pretty: bool = True 
        ) -> bool: 
            """ 
            Save metadata to a JSON file 
            
            Args: 
                metadata: Metadata dictionary to save 
                output_path: Path where to save the JSON file 
                pretty: If True, format JSON with indentation 
                
            Returns: 
                True if successful, False otherwise 
            """ 
            try: 
                output_file = Path(output_path) 
                output_file.parent.mkdir(parents=True, exist_ok=True) 
                
                with open(output_file, 'w', encoding='utf-8') as f: 
                    if pretty: 
                        json.dump(metadata, f, indent=2, ensure_ascii=False) 
                    else: 
                        json.dump(metadata, f, ensure_ascii=False) 
                
                print(f"\n Metadata saved to: {output_file.absolute()}") 
                return True 
                
            except Exception as e: 
                print(f"\n✗ Error saving metadata: {e}") 
                return False
            
    def generate_readme( 
            self, 
            metadata: Dict, 
            output_path: Path 
        ) -> bool: 
            """ 
            Generate a README file for the dataset 
            
            Args: 
                metadata: Dataset metadata dictionary 
                output_path: Path where to save the README file 
                
            Returns: 
                True if successful, False otherwise 
            """ 
            try: 
                readme_content = f"""# {metadata['dataset_name']} 

                ## Description 
                {metadata.get('description', 'No description provided')} 

                ## Dataset Information 
                - **Source**: {metadata.get('source', 'Unknown')} 
                - **Created**: {metadata['created_at']} 
                - **Total Images**: {metadata['statistics']['total_images']} 
                - **Total Size**: {metadata['statistics']['total_size_mb']} MB 
                - **Categories**: {', '.join(metadata['statistics']['categories'])} 

                ## Dataset Structure 

                """
                
                # Build tree structure 
                readme_content += f"```\n{metadata['dataset_name']}/\n" 
                
                # Train section 
                readme_content += "├── train/\n"
                if 'train' in metadata['splits']:
                    train_cats = list(metadata['splits']['train']['categories'].items())
                    for idx, (cat_name, cat_info) in enumerate(train_cats):
                        count = cat_info['statistics']['count'] 
                        prefix = "│   └──" if idx == len(train_cats) - 1 else "│   ├──" 
                        readme_content += f"{prefix} {cat_name}/ ({count} images)\n" 
                
                # Val section 
                readme_content += "├── val/\n" 
                if 'val' in metadata['splits']: 
                    val_cats = list(metadata['splits']['val']['categories'].items()) 
                    for idx, (cat_name, cat_info) in enumerate(val_cats): 
                        count = cat_info['statistics']['count'] 
                        prefix = "│   └──" if idx == len(val_cats) - 1 else "│   ├──" 
                        readme_content += f"{prefix} {cat_name}/ ({count} images)\n" 
                
                # Test section 
                readme_content += "└── test/\n" 
                if 'test' in metadata['splits']: 
                    test_cats = list(metadata['splits']['test']['categories'].items()) 
                    for idx, (cat_name, cat_info) in enumerate(test_cats): 
                        count = cat_info['statistics']['count'] 
                        prefix = "    └──" if idx == len(test_cats) - 1 else "    ├──" 
                        readme_content += f"{prefix} {cat_name}/ ({count} images)\n" 
                
                readme_content += "```\n\n## Split Distribution\n\n" 
                
                # Add split statistics 
                for split_name, split_data in metadata['splits'].items(): 
                    total = split_data['total_images'] 
                    percentage = (total / metadata['statistics']['total_images']) * 100 
                    readme_content += f"- **{split_name.capitalize()}**: {total} images ({percentage:.1f}%)\n" 
                
                # Add category details 
                readme_content += "\n## Categories\n\n" 
                
                for category in metadata['statistics']['categories']: 
                    readme_content += f"### {category}\n\n" 
                    
                    for split_name, split_data in metadata['splits'].items(): 
                        if category in split_data['categories']: 
                            cat_info = split_data['categories'][category] 
                            stats = cat_info['statistics'] 
                            avg_w = stats['average_dimensions']['width'] 
                            avg_h = stats['average_dimensions']['height'] 
                            readme_content += f"- **{split_name.capitalize()}**: {stats['count']} images " 
                            readme_content += f"(avg: {avg_w}x{avg_h})\n" 
                    
                    readme_content += "\n" 
                
                # Add usage instructions 
                readme_content += """## Usage 

                This dataset is organized in a standard format compatible with most ML frameworks. 
                ### PyTorch Example 
                ```python 
                from torchvision import datasets, transforms 

                transform = transforms.Compose([ 
                    transforms.Resize((224, 224)), 
                    transforms.ToTensor(), 
                ]) 

                train_dataset = datasets.ImageFolder('train/', transform=transform) 
                val_dataset = datasets.ImageFolder('val/', transform=transform) 
                test_dataset = datasets.ImageFolder('test/', transform=transform) 
                ``` 

                ### TensorFlow Example 
                ```python 
                import tensorflow as tf 

                train_ds = tf.keras.preprocessing.image_dataset_from_directory( 
                    'train/', 
                    image_size=(224, 224), 
                    batch_size=32 
                ) 

                val_ds = tf.keras.preprocessing.image_dataset_from_directory( 
                    'val/', 
                    image_size=(224, 224), 
                    batch_size=32 
                ) 
                ``` 

                ## Metadata 
                For detailed metadata, see `dataset_info.json` 
                """ 
                
                # Save README 
                readme_file = Path(output_path) 
                with open(readme_file, 'w', encoding='utf-8') as f: 
                    f.write(readme_content) 
                
                print(f" README saved to: {readme_file.absolute()}") 
                return True 
                
            except Exception as e: 
                print(f"✗ Error generating README: {e}") 
                return False 

    def export_complete_metadata( 
            self, 
            dataset_dir: Path, 
            dataset_name: str, 
            description: str = "", 
            source: str = "openverse", 
            additional_info: Optional[Dict] = None 
        ) -> bool: 
            """ 
            Generate and export complete metadata package (JSON + README) 
            
            Args: 
                dataset_dir: Root directory of the organized dataset 
                dataset_name: Name of the dataset 
                description: Description of the dataset 
                source: Source of the images 
                additional_info: Additional information to include 
                
            Returns: 
                True if successful, False otherwise 
            """ 
            # Generate metadata 
            metadata = self.generate_dataset_metadata( 
                dataset_dir=dataset_dir, 
                dataset_name=dataset_name, 
                description=description, 
                source=source, 
                additional_info=additional_info 
            ) 
            
            if not metadata: 
                return False 
            
            dataset_path = Path(dataset_dir) 
            
            # Save JSON metadata 
            json_path = dataset_path / 'dataset_info.json' 
            json_success = self.save_metadata(metadata, json_path, pretty=True) 
            
            # Generate README 
            readme_path = dataset_path / 'README.md' 
            readme_success = self.generate_readme(metadata, readme_path) 
            
            print("\n" + "=" * 70) 
            
            return json_success and readme_success 


