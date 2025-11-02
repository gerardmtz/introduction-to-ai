from src.downloaders.openverse_downloader import OpenverseDownloader

def main():
    # Start the download
    downloader = OpenverseDownloader()
    
    # Setup the download test
    query = "orange cats"
    num_images = 10
    save_dir = "data/raw/test"
    
    # Download
    print("=" * 60)
    print("DOWNLOAD TEST WITH OPENVERSE")
    print("=" * 60)
    
    downloaded_files = downloader.download_dataset(
        query=query,
        num_images=num_images,
        save_dir=save_dir
    )
    
    print("\n" + "=" * 60)
    print(f"RESULTS: {len(downloaded_files)} successfully downloaded images")
    print("=" * 60)

if __name__ == "__main__":
    main()
