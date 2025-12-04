package main

import (
	"fmt"
	"os"
	"os/exec"
	"path/filepath"
	"strings"
	"sync"

	"github.com/schollz/progressbar/v3"
)

type Downloader struct {
	config      *Config
	progressBar *progressbar.ProgressBar
}

func NewDownloader(config *Config) *Downloader {
	return &Downloader{
		config: config,
	}
}

func (d *Downloader) DownloadImages(imageURLs []string) error {
	if len(imageURLs) == 0 {
		return fmt.Errorf("no images to download")
	}

	d.progressBar = progressbar.NewOptions(len(imageURLs),
		progressbar.OptionSetDescription("Downloading images"),
		progressbar.OptionSetWidth(40),
		progressbar.OptionShowCount(),
		progressbar.OptionShowBytes(true),
		progressbar.OptionSetTheme(progressbar.Theme{
			Saucer:        "=",
			SaucerHead:    ">",
			SaucerPadding: " ",
			BarStart:      "[",
			BarEnd:        "]",
		}),
	)

	semaphore := make(chan struct{}, d.config.Concurrency)
	var wg sync.WaitGroup
	var successCount int
	var failCount int
	var filteredCount int
	var mu sync.Mutex

	for _, imageURL := range imageURLs {
		wg.Add(1)
		semaphore <- struct{}{}

		go func(url string) {
			defer wg.Done()
			defer func() { <-semaphore }()

			result := d.downloadImage(url)
			mu.Lock()
			if result == 0 {
				successCount++
			} else if result == 1 {
				failCount++
			} else if result == 2 {
				filteredCount++
			}
			mu.Unlock()

			d.progressBar.Add(1)
		}(imageURL)
	}

	wg.Wait()
	d.progressBar.Finish()

	fmt.Printf("\n\nDownload complete:\n")
	fmt.Printf("  Successful: %d\n", successCount)
	fmt.Printf("  Failed:     %d\n", failCount)
	if d.config.MinWidth > 0 || d.config.MinHeight > 0 {
		fmt.Printf("  Filtered:   %d (below min resolution)\n", filteredCount)
	}

	return nil
}

func (d *Downloader) downloadImage(imageURL string) int {
	filename := extractFilenameFromURL(imageURL)
	outputPath := filepath.Join(d.config.OutputDir, filename)

	if _, err := os.Stat(outputPath); err == nil {
		logVerbose(d.config, "File already exists, skipping: %s", filename)
		return 0
	}

	var cmd *exec.Cmd

	switch d.config.Downloader {
	case "curl":
		cmd = exec.Command("curl",
			"-s",
			"-L",
			"-o", outputPath,
			"--user-agent", d.config.UserAgent,
			"--referer", imageURL,
			"-H", "Accept: image/webp,image/apng,image/*,*/*;q=0.8",
			"-H", "Accept-Language: en-US,en;q=0.9",
			"--compressed",
			"--connect-timeout", "10",
			"--max-time", fmt.Sprintf("%d", int(d.config.Timeout.Seconds())),
			"--max-redirs", "10",
			imageURL,
		)
	case "wget":
		cmd = exec.Command("wget",
			"-q",
			"-O", outputPath,
			"--user-agent="+d.config.UserAgent,
			"--referer="+imageURL,
			"--header=Accept: image/webp,image/apng,image/*,*/*;q=0.8",
			"--header=Accept-Language: en-US,en;q=0.9",
			"--timeout=10",
			"--tries=3",
			"--max-redirect=10",
			imageURL,
		)
	default:
		return 1
	}

	if err := cmd.Run(); err != nil {
		os.Remove(outputPath)
		return 1
	}

	fileInfo, err := os.Stat(outputPath)
	if err != nil {
		return 1
	}

	if fileInfo.Size() == 0 {
		os.Remove(outputPath)
		return 1
	}

	if d.config.MinWidth > 0 || d.config.MinHeight > 0 {
		width, height, err := getImageDimensions(outputPath)
		if err != nil {
			logVerbose(d.config, "Failed to get dimensions for %s: %v", filename, err)
			os.Remove(outputPath)
			return 1
		}

		if (d.config.MinWidth > 0 && width < d.config.MinWidth) ||
			(d.config.MinHeight > 0 && height < d.config.MinHeight) {
			logVerbose(d.config, "Filtered %s: %dx%d (below minimum)", filename, width, height)
			os.Remove(outputPath)
			return 2
		}
	}

	return 0
}
func getImageDimensions(imagePath string) (int, int, error) {
	cmd := exec.Command("identify", "-ping", "-format", "%w %h", imagePath)
	output, err := cmd.CombinedOutput()
	if err != nil {
		return 0, 0, fmt.Errorf("identify failed: %w (output: %s)", err, string(output))
	}

	outputStr := strings.TrimSpace(string(output))
	if outputStr == "" {
		return 0, 0, fmt.Errorf("empty output from identify")
	}

	var width, height int
	n, err := fmt.Sscanf(outputStr, "%d %d", &width, &height)
	if err != nil || n != 2 {
		return 0, 0, fmt.Errorf("failed to parse dimensions from: %s", outputStr)
	}

	if width <= 0 || height <= 0 {
		return 0, 0, fmt.Errorf("invalid dimensions: %dx%d", width, height)
	}

	return width, height, nil
}
