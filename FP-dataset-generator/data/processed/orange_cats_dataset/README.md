# Orange Cats Dataset 

                ## Description 
                A collection of orange cat images for ML training 

                ## Dataset Information 
                - **Source**: openverse 
                - **Created**: 2025-11-16T16:40:51.684847 
                - **Total Images**: 9 
                - **Total Size**: 0.11 MB 
                - **Categories**: orange_cats 

                ## Dataset Structure 

                ```
Orange Cats Dataset/
├── train/
│   └── orange_cats/ (6 images)
├── val/
│   └── orange_cats/ (1 images)
└── test/
    └── orange_cats/ (2 images)
```

## Split Distribution

- **Train**: 6 images (66.7%)
- **Val**: 1 images (11.1%)
- **Test**: 2 images (22.2%)

## Categories

### orange_cats

- **Train**: 6 images (avg: 256x256)
- **Val**: 1 images (avg: 256x256)
- **Test**: 2 images (avg: 256x256)

## Usage 

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
                