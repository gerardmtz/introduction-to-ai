from pathlib import Path
from src.processors.image_processor import ImageProcessor


def main():
    # Configuration
    input_dir = "data/raw/test"  # Directory with downloaded images
    output_dir = "data/temp/processed_test"
    
    # Initialize processor with different configurations
    print("=" * 70)
    print("IMAGE PROCESSING TEST")
    print("=" * 70)
    
    # Option 1: Maintain aspect ratio (recommended)
    processor = ImageProcessor(
        target_size=(256, 256),
        min_size=(100, 100),
        quality=90,
        maintain_aspect_ratio=True
    )
    
    # Option 2: Direct resize (uncomment to try)
    # processor = ImageProcessor(
    #     target_size=(256, 256),
    #     min_size=(100, 100),
    #     quality=90,
    #     maintain_aspect_ratio=False
    # )
    
    # Get stats before processing
    print("\n📊 INPUT DIRECTORY STATS:")
    stats = processor.get_image_stats(input_dir)
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    # Process images
    processed_files = processor.process_batch(
        input_dir=input_dir,
        output_dir=output_dir,
        clean_output=True  # Clean output directory before processing
    )
    
    # Get stats after processing
    print("\n📊 OUTPUT DIRECTORY STATS:")
    stats = processor.get_image_stats(output_dir)
    for key, value in stats.items():
        print(f"   {key}: {value}")
    
    print("\n" + "=" * 70)
    print(f"RESULT: {len(processed_files)} images processed successfully")
    print("=" * 70)


if __name__ == "__main__":
    main()
