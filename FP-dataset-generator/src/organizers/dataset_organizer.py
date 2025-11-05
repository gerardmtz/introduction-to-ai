from pathlib import Path
from typing import List, Tuple, Dict, Optional
import shutil
import random
from datetime import datetime


class DatasetOrganizer:
    def __init__(
        self,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42
    ):
        """
        Initialize the dataset organizer
        
        Args:
            train_ratio: Proportion of data for training (0.0-1.0)
            val_ratio: Proportion of data for validation (0.0-1.0)
            test_ratio: Proportion of data for testing (0.0-1.0)
            seed: Random seed for reproducibility
        """
        # Validate ratios
        total = train_ratio + val_ratio + test_ratio
        if not (0.99 <= total <= 1.01):  # Allow small floating point errors
            raise ValueError(f"Ratios must sum to 1.0, got {total}")
        
        self.train_ratio = train_ratio
        self.val_ratio = val_ratio
        self.test_ratio = test_ratio
        self.seed = seed
        
        # Set random seed for reproducibility
        random.seed(seed)
    
    def split_files(
        self,
        files: List[Path]
    ) -> Tuple[List[Path], List[Path], List[Path]]:
        """
        Split files into train, validation, and test sets
        
        Args:
            files: List of file paths to split
            
        Returns:
            Tuple of (train_files, val_files, test_files)
        """
        # Shuffle files
        shuffled_files = files.copy()
        random.shuffle(shuffled_files)
        
        total_files = len(shuffled_files)
        
        # Calculate split indices
        train_end = int(total_files * self.train_ratio)
        val_end = train_end + int(total_files * self.val_ratio)
        
        # Split files
        train_files = shuffled_files[:train_end]
        val_files = shuffled_files[train_end:val_end]
        test_files = shuffled_files[val_end:]
        
        return train_files, val_files, test_files
    
    def create_dataset_structure(
        self,
        output_dir: Path,
        category_name: str,
        clean_output: bool = False
    ) -> Dict[str, Path]:
        """
        Create the train/val/test directory structure
        
        Args:
            output_dir: Root directory for the dataset
            category_name: Name of the category (e.g., 'cats', 'dogs')
            clean_output: If True, clean output directory before creating structure
            
        Returns:
            Dictionary with paths to train/val/test directories
        """
        output_path = Path(output_dir)
        
        # Clean output directory if requested
        if clean_output and output_path.exists():
            shutil.rmtree(output_path)
        
        # Create directory structure
        structure = {
            'train': output_path / 'train' / category_name,
            'val': output_path / 'val' / category_name,
            'test': output_path / 'test' / category_name
        }
        
        for split_path in structure.values():
            split_path.mkdir(parents=True, exist_ok=True)
        
        return structure
    
    def copy_files_to_split(
        self,
        files: List[Path],
        destination_dir: Path,
        move: bool = False
    ) -> List[Path]:
        """
        Copy or move files to a destination directory
        
        Args:
            files: List of files to copy/move
            destination_dir: Destination directory
            move: If True, move files instead of copying
            
        Returns:
            List of destination file paths
        """
        destination_files = []
        
        for file_path in files:
            dest_file = destination_dir / file_path.name
            
            try:
                if move:
                    shutil.move(str(file_path), str(dest_file))
                else:
                    shutil.copy2(str(file_path), str(dest_file))
                
                destination_files.append(dest_file)
            except Exception as e:
                print(f"✗ Error copying {file_path.name}: {e}")
        
        return destination_files
    
    def organize_dataset(
        self,
        input_dir: Path,
        output_dir: Path,
        category_name: str,
        clean_output: bool = False,
        move_files: bool = False
    ) -> Dict:
        """
        Organize images into train/val/test structure
        
        Args:
            input_dir: Directory containing processed images
            output_dir: Root directory for organized dataset
            category_name: Name of the category
            clean_output: If True, clean output directory before organizing
            move_files: If True, move files instead of copying
            
        Returns:
            Dictionary with dataset information and statistics
        """
        input_path = Path(input_dir)
        output_path = Path(output_dir)
        
        print("\n" + "=" * 70)
        print("DATASET ORGANIZATION")
        print("=" * 70)
        
        # Get all image files
        image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
        image_files = [
            f for f in input_path.iterdir()
            if f.is_file() and f.suffix.lower() in image_extensions
        ]
        
        if not image_files:
            print(f"✗ No images found in {input_path}")
            return {}
        
        print(f"\n📊 Found {len(image_files)} images to organize")
        print(f"   Category: {category_name}")
        print(f"   Split ratios: train={self.train_ratio}, val={self.val_ratio}, test={self.test_ratio}")
        
        # Split files
        print(f"\n🔀 Splitting dataset...")
        train_files, val_files, test_files = self.split_files(image_files)
        
        print(f"   Train: {len(train_files)} images ({len(train_files)/len(image_files)*100:.1f}%)")
        print(f"   Val:   {len(val_files)} images ({len(val_files)/len(image_files)*100:.1f}%)")
        print(f"   Test:  {len(test_files)} images ({len(test_files)/len(image_files)*100:.1f}%)")
        
        # Create directory structure
        print(f"\n📁 Creating directory structure...")
        structure = self.create_dataset_structure(
            output_path,
            category_name,
            clean_output
        )
        
        # Copy/move files to respective directories
        action = "Moving" if move_files else "Copying"
        print(f"\n📋 {action} files to splits...")
        
        print(f"   [1/3] {action} training images...")
        train_dest = self.copy_files_to_split(
            train_files,
            structure['train'],
            move=move_files
        )
        
        print(f"   [2/3] {action} validation images...")
        val_dest = self.copy_files_to_split(
            val_files,
            structure['val'],
            move=move_files
        )
        
        print(f"   [3/3] {action} test images...")
        test_dest = self.copy_files_to_split(
            test_files,
            structure['test'],
            move=move_files
        )
        
        # Prepare dataset info
        dataset_info = {
            'category': category_name,
            'total_images': len(image_files),
            'splits': {
                'train': {
                    'count': len(train_dest),
                    'path': str(structure['train'].relative_to(output_path))
                },
                'val': {
                    'count': len(val_dest),
                    'path': str(structure['val'].relative_to(output_path))
                },
                'test': {
                    'count': len(test_dest),
                    'path': str(structure['test'].relative_to(output_path))
                }
            },
            'ratios': {
                'train': self.train_ratio,
                'val': self.val_ratio,
                'test': self.test_ratio
            },
            'random_seed': self.seed,
            'created_at': datetime.now().isoformat(),
            'root_path': str(output_path.absolute())
        }
        
        # Summary
        print(f"\n✅ Dataset organized successfully!")
        print(f"📁 Root directory: {output_path.absolute()}")
        print(f"\n   Structure:")
        print(f"   ├── train/{category_name}/ ({len(train_dest)} images)")
        print(f"   ├── val/{category_name}/   ({len(val_dest)} images)")
        print(f"   └── test/{category_name}/  ({len(test_dest)} images)")
        
        print("\n" + "=" * 70)
        
        return dataset_info
    
    def get_dataset_summary(self, dataset_dir: Path) -> Dict:
        """
        Get summary statistics of an organized dataset
        
        Args:
            dataset_dir: Root directory of the organized dataset
            
        Returns:
            Dictionary with dataset summary
        """
        dataset_path = Path(dataset_dir)
        
        if not dataset_path.exists():
            return {'error': 'Dataset directory does not exist'}
        
        summary = {
            'splits': {},
            'total_images': 0,
            'categories': set()
        }
        
        # Check each split
        for split in ['train', 'val', 'test']:
            split_path = dataset_path / split
            
            if not split_path.exists():
                continue
            
            # Get categories in this split
            categories = [
                d for d in split_path.iterdir()
                if d.is_dir()
            ]
            
            split_info = {
                'categories': {},
                'total': 0
            }
            
            for category_dir in categories:
                category_name = category_dir.name
                summary['categories'].add(category_name)
                
                # Count images in category
                image_extensions = {'.jpg', '.jpeg', '.png', '.webp'}
                image_count = len([
                    f for f in category_dir.iterdir()
                    if f.is_file() and f.suffix.lower() in image_extensions
                ])
                
                split_info['categories'][category_name] = image_count
                split_info['total'] += image_count
            
            summary['splits'][split] = split_info
            summary['total_images'] += split_info['total']
        
        summary['categories'] = sorted(list(summary['categories']))
        
        return summary
