from pathlib import Path
from src.organizers.dataset_organizer import DatasetOrganizer


def main():
    # Configuration
    input_dir = "data/temp/processed_test"  # Directory with processed images
    output_dir = "data/processed/orange_cats_dataset"
    category_name = "orange_cats"
    
    print("=" * 70)
    print("DATASET ORGANIZATION TEST")
    print("=" * 70)
    
    # Initialize organizer
    organizer = DatasetOrganizer(
        train_ratio=0.7,
        val_ratio=0.15,
        test_ratio=0.15,
        seed=42  # For reproducibility
    )
    
    # Organize dataset
    dataset_info = organizer.organize_dataset(
        input_dir=input_dir,
        output_dir=output_dir,
        category_name=category_name,
        clean_output=True,  # Clean output directory before organizing
        move_files=False    # Copy files (set to True to move instead)
    )
    
    # Print dataset info
    if dataset_info:
        print("\n📊 DATASET INFORMATION:")
        print(f"   Category: {dataset_info['category']}")
        print(f"   Total images: {dataset_info['total_images']}")
        print(f"   Random seed: {dataset_info['random_seed']}")
        print(f"   Created at: {dataset_info['created_at']}")
        
        print("\n📈 SPLIT DETAILS:")
        for split_name, split_data in dataset_info['splits'].items():
            percentage = (split_data['count'] / dataset_info['total_images']) * 100
            print(f"   {split_name.upper():5s}: {split_data['count']:3d} images ({percentage:5.1f}%)")
    
    # Get dataset summary
    print("\n🔍 VERIFYING DATASET STRUCTURE...")
    summary = organizer.get_dataset_summary(output_dir)
    
    print(f"\n   Total images in dataset: {summary['total_images']}")
    print(f"   Categories: {', '.join(summary['categories'])}")
    
    for split, split_info in summary['splits'].items():
        print(f"\n   {split.upper()} split:")
        for category, count in split_info['categories'].items():
            print(f"      - {category}: {count} images")


if __name__ == "__main__":
    main()
