import argparse
from pathlib import Path
from src.pipeline import DatasetPipeline


def main():
    parser = argparse.ArgumentParser(
        description='Dataset Generator - Automated dataset creation from web images',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Basic usage
  python main.py --query "orange cats" --num 50 --name "Orange Cats Dataset"
  
  # With custom settings
  python main.py --query "red flowers" --num 100 --name "Flowers" \\
    --description "Dataset of red flowers" --size 512 --quality 95
  
  # Keep temporary files
  python main.py --query "mountains" --num 30 --name "Mountains" --keep-temp
        """
    )
    
    # Required arguments
    parser.add_argument(
        '--query', '-q',
        type=str,
        required=True,
        help='Search query for images (e.g., "orange cats", "red flowers")'
    )
    
    parser.add_argument(
        '--num', '-n',
        type=int,
        required=True,
        help='Number of images to download'
    )
    
    parser.add_argument(
        '--name',
        type=str,
        required=True,
        help='Name for the dataset (e.g., "Orange Cats Dataset")'
    )
    
    # Optional arguments
    parser.add_argument(
        '--description', '-d',
        type=str,
        default="",
        help='Description of the dataset'
    )
    
    parser.add_argument(
        '--output', '-o',
        type=str,
        default="data/processed",
        help='Output base directory (default: data/processed)'
    )
    
    parser.add_argument(
        '--size', '-s',
        type=int,
        default=256,
        help='Target image size in pixels (square) (default: 256)'
    )
    
    parser.add_argument(
        '--quality',
        type=int,
        default=90,
        choices=range(1, 101),
        metavar="[1-100]",
        help='JPEG quality (1-100) (default: 90)'
    )
    
    parser.add_argument(
        '--train-ratio',
        type=float,
        default=0.7,
        help='Training set ratio (default: 0.7)'
    )
    
    parser.add_argument(
        '--val-ratio',
        type=float,
        default=0.15,
        help='Validation set ratio (default: 0.15)'
    )
    
    parser.add_argument(
        '--test-ratio',
        type=float,
        default=0.15,
        help='Test set ratio (default: 0.15)'
    )
    
    parser.add_argument(
        '--seed',
        type=int,
        default=42,
        help='Random seed for reproducibility (default: 42)'
    )
    
    parser.add_argument(
        '--keep-temp',
        action='store_true',
        help='Keep temporary files after pipeline completion'
    )
    
    parser.add_argument(
        '--min-size',
        type=int,
        default=100,
        help='Minimum image size to accept (default: 100)'
    )
    
    args = parser.parse_args()
    
    # Validate ratios
    total_ratio = args.train_ratio + args.val_ratio + args.test_ratio
    if not (0.99 <= total_ratio <= 1.01):
        parser.error(f"Split ratios must sum to 1.0, got {total_ratio}")
    
    # Print configuration
    print("\n" + "=" * 70)
    print("CONFIGURATION")
    print("=" * 70)
    print(f"Query:           {args.query}")
    print(f"Images:          {args.num}")
    print(f"Dataset name:    {args.name}")
    print(f"Description:     {args.description or '(none)'}")
    print(f"Output dir:      {args.output}")
    print(f"Image size:      {args.size}x{args.size}")
    print(f"Quality:         {args.quality}")
    print(f"Min size:        {args.min_size}x{args.min_size}")
    print(f"Split ratios:    train={args.train_ratio}, val={args.val_ratio}, test={args.test_ratio}")
    print(f"Random seed:     {args.seed}")
    print(f"Keep temp files: {args.keep_temp}")
    print("=" * 70)
    
    # Initialize pipeline
    pipeline = DatasetPipeline(
        target_size=(args.size, args.size),
        min_size=(args.min_size, args.min_size),
        quality=args.quality,
        train_ratio=args.train_ratio,
        val_ratio=args.val_ratio,
        test_ratio=args.test_ratio,
        seed=args.seed
    )
    
    # Run pipeline
    results = pipeline.generate_dataset(
        query=args.query,
        num_images=args.num,
        dataset_name=args.name,
        description=args.description,
        output_base_dir=args.output,
        keep_temp_files=args.keep_temp
    )
    
    # Exit with appropriate code
    if results['success']:
        print("\n Dataset generation completed successfully!")
        exit(0)
    else:
        print("\n✗ Dataset generation failed!")
        if 'error' in results:
            print(f"Error: {results['error']}")
        exit(1)


if __name__ == "__main__":
    main()
