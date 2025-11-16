from pathlib import Path 
from src.exporters.metadata_generator import MetadataGenerator 


def main(): 
    # Configuration 
    dataset_dir = "data/processed/orange_cats_dataset" 
    dataset_name = "Orange Cats Dataset" 
    description = "A collection of orange cat images for ML training" 
    
    print("=" * 70) 
    print("METADATA GENERATION TEST") 
    print("=" * 70) 
    
    # Initialize metadata generator 
    generator = MetadataGenerator() 
    
    # Generate and export complete metadata 
    success = generator.export_complete_metadata( 
        dataset_dir=dataset_dir, 
        dataset_name=dataset_name, 
        description=description, 
        source="openverse", 
        additional_info={ 
            'processing': { 
                'resized_to': '256x256', 
                'format': 'JPEG', 
                'quality': 90 
            }, 
            'search_query': 'orange cats', 
            'notes': 'Images automatically downloaded and processed' 
        } 
    ) 
    
    if success: 
        print("\n  Metadata export completed successfully!") 
        print(f"\n Files created:") 
        print(f"   - {dataset_dir}/dataset_info.json") 
        print(f"   - {dataset_dir}/README.md") 
    else: 
        print("\n✗ Metadata export failed") 


if __name__ == "__main__": 
    main() 