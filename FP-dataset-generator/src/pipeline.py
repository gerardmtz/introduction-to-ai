from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import shutil

from src.downloaders.openverse_downloader import OpenverseDownloader
from src.processors.image_processor import ImageProcessor
from src.organizers.dataset_organizer import DatasetOrganizer
from src.exporters.metadata_generator import MetadataGenerator


class DatasetPipeline:
    def __init__(
        self,
        target_size: tuple = (256, 256),
        min_size: tuple = (100, 100),
        quality: int = 90,
        train_ratio: float = 0.7,
        val_ratio: float = 0.15,
        test_ratio: float = 0.15,
        seed: int = 42
    ):
        """
        Initialize the complete dataset generation pipeline
        
        Args:
            target_size: Target dimensions for images (width, height)
            min_size: Minimum acceptable dimensions (width, height)
            quality: JPEG quality (1-100)
            train_ratio: Proportion for training set
            val_ratio: Proportion for validation set
            test_ratio: Proportion for test set
            seed: Random seed for reproducibility
        """
        self.downloader = OpenverseDownloader()
        self.processor = ImageProcessor(
            target_size=target_size,
            min_size=min_size,
            quality=quality,
            maintain_aspect_ratio=True
        )
        self.organizer = DatasetOrganizer(
            train_ratio=train_ratio,
            val_ratio=val_ratio,
            test_ratio=test_ratio,
            seed=seed
        )
        self.metadata_generator = MetadataGenerator()
        
        # Pipeline configuration
        self.config = {
            'target_size': target_size,
            'min_size': min_size,
            'quality': quality,
            'train_ratio': train_ratio,
            'val_ratio': val_ratio,
            'test_ratio': test_ratio,
            'seed': seed
        }
    
    def generate_dataset(
        self,
        query: str,
        num_images: int,
        dataset_name: str,
        description: str = "",
        output_base_dir: str = "data/processed",
        keep_temp_files: bool = False
    ) -> Dict:
        """
        Complete end-to-end dataset generation pipeline
        
        Args:
            query: Search query for images
            num_images: Number of images to download
            dataset_name: Name for the dataset
            description: Dataset description
            output_base_dir: Base directory for final dataset
            keep_temp_files: If True, keep intermediate files
            
        Returns:
            Dictionary with pipeline results and statistics
        """
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        # Create temporary directories
        temp_raw_dir = Path(f"data/temp/{timestamp}_raw")
        temp_processed_dir = Path(f"data/temp/{timestamp}_processed")
        final_dataset_dir = Path(output_base_dir) / dataset_name.lower().replace(" ", "_")
        
        # Sanitize category name from query
        category_name = query.lower().replace(" ", "_")
        
        print("\n" + "=" * 70)
        print("DATASET GENERATION PIPELINE")
        print("=" * 70)
        print(f"\nQuery: {query}")
        print(f"Images: {num_images}")
        print(f"Dataset name: {dataset_name}")
        print(f"Category: {category_name}")
        print(f"Output: {final_dataset_dir}")
        
        results = {
            'success': False,
            'query': query,
            'dataset_name': dataset_name,
            'category': category_name,
            'stages': {}
        }
        
        try:
            # Stage 1: Download images
            print("\n" + "=" * 70)
            print("STAGE 1/4: DOWNLOADING IMAGES")
            print("=" * 70)
            
            downloaded_files = self.downloader.download_dataset(
                query=query,
                num_images=num_images,
                save_dir=str(temp_raw_dir)
            )
            
            if not downloaded_files:
                print("\n✗ Pipeline failed: No images downloaded")
                return results
            
            results['stages']['download'] = {
                'status': 'success',
                'images_downloaded': len(downloaded_files),
                'location': str(temp_raw_dir)
            }
            
            # Stage 2: Process images
            print("\n" + "=" * 70)
            print("STAGE 2/4: PROCESSING IMAGES")
            print("=" * 70)
            
            processed_files = self.processor.process_batch(
                input_dir=temp_raw_dir,
                output_dir=temp_processed_dir,
                clean_output=True
            )
            
            if not processed_files:
                print("\n✗ Pipeline failed: No images processed successfully")
                return results
            
            results['stages']['process'] = {
                'status': 'success',
                'images_processed': len(processed_files),
                'location': str(temp_processed_dir)
            }
            
            # Stage 3: Organize dataset
            print("\n" + "=" * 70)
            print("STAGE 3/4: ORGANIZING DATASET")
            print("=" * 70)
            
            dataset_info = self.organizer.organize_dataset(
                input_dir=temp_processed_dir,
                output_dir=final_dataset_dir,
                category_name=category_name,
                clean_output=True,
                move_files=False
            )
            
            if not dataset_info:
                print("\n✗ Pipeline failed: Dataset organization failed")
                return results
            
            results['stages']['organize'] = {
                'status': 'success',
                'dataset_info': dataset_info
            }
            
            # Stage 4: Generate metadata
            print("\n" + "=" * 70)
            print("STAGE 4/4: GENERATING METADATA")
            print("=" * 70)
            
            metadata_success = self.metadata_generator.export_complete_metadata(
                dataset_dir=final_dataset_dir,
                dataset_name=dataset_name,
                description=description,
                source="openverse",
                additional_info={
                    'query': query,
                    'processing': {
                        'target_size': f"{self.config['target_size'][0]}x{self.config['target_size'][1]}",
                        'min_size': f"{self.config['min_size'][0]}x{self.config['min_size'][1]}",
                        'quality': self.config['quality'],
                        'maintain_aspect_ratio': True
                    },
                    'split_ratios': {
                        'train': self.config['train_ratio'],
                        'val': self.config['val_ratio'],
                        'test': self.config['test_ratio']
                    },
                    'random_seed': self.config['seed']
                }
            )
            
            results['stages']['metadata'] = {
                'status': 'success' if metadata_success else 'failed'
            }
            
            # Clean up temporary files if requested
            if not keep_temp_files:
                print("\n🧹 Cleaning up temporary files...")
                if temp_raw_dir.exists():
                    shutil.rmtree(temp_raw_dir)
                    print(f"   ✓ Removed {temp_raw_dir}")
                if temp_processed_dir.exists():
                    shutil.rmtree(temp_processed_dir)
                    print(f"   ✓ Removed {temp_processed_dir}")
            
            # Final summary
            results['success'] = True
            results['output_directory'] = str(final_dataset_dir.absolute())
            
            print("\n" + "=" * 70)
            print("PIPELINE COMPLETED SUCCESSFULLY!")
            print("=" * 70)
            print(f"\n Dataset location: {final_dataset_dir.absolute()}")
            print(f" Total images: {dataset_info['total_images']}")
            print(f"   - Train: {dataset_info['splits']['train']['count']}")
            print(f"   - Val:   {dataset_info['splits']['val']['count']}")
            print(f"   - Test:  {dataset_info['splits']['test']['count']}")
            print(f"\n Files generated:")
            print(f"   - dataset_info.json")
            print(f"   - README.md")
            print("\n" + "=" * 70)
            
            return results
            
        except Exception as e:
            print(f"\n✗ Pipeline failed with error: {e}")
            results['error'] = str(e)
            return results
