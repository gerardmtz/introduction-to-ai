package main

import (
	"flag"
	"fmt"
	"os"
	"path/filepath"
	"runtime"
	"strings"
	"time"
)

const (
	version            = "1.1.0"
	defaultUserAgent   = "Mozilla/5.0 (compatible; ImageCrawler/1.0; +https://example.com/bot)"
	defaultRateLimitMs = 1000
	defaultTimeoutSec  = 30
	defaultMaxPages    = 50
	defaultMaxDepth    = 3
	defaultConcurrency = 5
)

var (
	builtinSites = []string{
		"wikimedia",
		"pexels",
		"pixabay",
		"freeimages",
		"unsplash",
		"flickr",
		"deviantart",
		"pinterest",
		"imgur",
		"reddit",
	}
	builtinSiteSet = func() map[string]struct{} {
		m := make(map[string]struct{}, len(builtinSites))
		for _, site := range builtinSites {
			m[site] = struct{}{}
		}
		return m
	}()
)

type Config struct {
	Keyword          string
	OutputDir        string
	MaxPages         int
	MaxDepth         int
	Concurrency      int
	Timeout          time.Duration
	UserAgent        string
	RateLimitMs      int
	Downloader       string
	SeedURLs         []string
	DefaultSites     []string
	FollowSubdomains bool
	IgnoreRobots     bool
	MinWidth         int
	MinHeight        int
	SkipThumbnails   bool
	Verbose          bool

	invalidSites []string
}

func main() {
	cfg := parseFlags()
	if err := validateConfig(cfg); err != nil {
		fmt.Fprintf(os.Stderr, "Configuration error: %v\n", err)
		os.Exit(1)
	}

	printBanner()
	printConfig(cfg)

	if err := run(cfg); err != nil {
		fmt.Fprintf(os.Stderr, "\nError: %v\n", err)
		os.Exit(1)
	}

	fmt.Println("\n✓ Crawling completed successfully!")
}

func parseFlags() *Config {
	cfg := &Config{
		MaxPages:     defaultMaxPages,
		MaxDepth:     defaultMaxDepth,
		Concurrency:  defaultConcurrency,
		UserAgent:    defaultUserAgent,
		RateLimitMs:  defaultRateLimitMs,
		Downloader:   "auto",
		DefaultSites: defaultSites(),
	}

	var (
		timeoutSeconds = defaultTimeoutSec
		seedList       string
		siteList       string
		showVersion    bool
	)

	fs := flag.NewFlagSet(filepath.Base(os.Args[0]), flag.ContinueOnError)
	fs.SetOutput(os.Stderr)
	fs.Usage = func() {
		printUsage()
	}

	sitesHelp := fmt.Sprintf("Comma-separated default sites to use (available: %s)", strings.Join(builtinSites, ","))

	fs.StringVar(&cfg.Keyword, "keyword", cfg.Keyword, "Keyword to search for in image filenames (required)")
	fs.StringVar(&cfg.Keyword, "k", cfg.Keyword, "Keyword to search for (shorthand)")

	fs.StringVar(&cfg.OutputDir, "output", cfg.OutputDir, "Output directory (default: ./<keyword>)")
	fs.StringVar(&cfg.OutputDir, "o", cfg.OutputDir, "Output directory (shorthand)")

	fs.IntVar(&cfg.MaxPages, "max-pages", cfg.MaxPages, "Maximum number of pages to crawl")
	fs.IntVar(&cfg.MaxPages, "p", cfg.MaxPages, "Maximum pages (shorthand)")

	fs.IntVar(&cfg.MaxDepth, "max-depth", cfg.MaxDepth, "Maximum crawl depth")
	fs.IntVar(&cfg.MaxDepth, "d", cfg.MaxDepth, "Maximum depth (shorthand)")

	fs.IntVar(&cfg.Concurrency, "concurrency", cfg.Concurrency, "Number of concurrent workers")
	fs.IntVar(&cfg.Concurrency, "c", cfg.Concurrency, "Concurrency (shorthand)")

	fs.IntVar(&timeoutSeconds, "timeout", timeoutSeconds, "Request timeout in seconds")
	fs.IntVar(&timeoutSeconds, "t", timeoutSeconds, "Timeout (shorthand)")

	fs.StringVar(&cfg.UserAgent, "user-agent", cfg.UserAgent, "User agent string")
	fs.StringVar(&cfg.UserAgent, "ua", cfg.UserAgent, "User agent (shorthand)")

	fs.IntVar(&cfg.RateLimitMs, "rate-limit", cfg.RateLimitMs, "Rate limit between requests in milliseconds")
	fs.IntVar(&cfg.RateLimitMs, "r", cfg.RateLimitMs, "Rate limit (shorthand)")

	fs.StringVar(&cfg.Downloader, "downloader", cfg.Downloader, "Downloader to use: curl, wget, or auto")

	fs.StringVar(&seedList, "seeds", seedList, "Comma-separated list of seed URLs to start crawling")
	fs.StringVar(&seedList, "s", seedList, "Seed URLs (shorthand)")

	fs.StringVar(&siteList, "sites", siteList, sitesHelp)

	fs.BoolVar(&cfg.FollowSubdomains, "follow-subdomains", cfg.FollowSubdomains, "Follow links to subdomains")
	fs.BoolVar(&cfg.IgnoreRobots, "ignore-robots", cfg.IgnoreRobots, "Ignore robots.txt restrictions")

	fs.IntVar(&cfg.MinWidth, "min-width", cfg.MinWidth, "Minimum image width in pixels (0 = no limit)")
	fs.IntVar(&cfg.MinHeight, "min-height", cfg.MinHeight, "Minimum image height in pixels (0 = no limit)")

	fs.BoolVar(&cfg.SkipThumbnails, "skip-thumbnails", cfg.SkipThumbnails, "Skip images likely to be thumbnails")
	fs.BoolVar(&cfg.Verbose, "verbose", cfg.Verbose, "Enable verbose output")
	fs.BoolVar(&cfg.Verbose, "v", cfg.Verbose, "Verbose (shorthand)")

	fs.BoolVar(&showVersion, "version", showVersion, "Show version information and exit")

	if err := fs.Parse(os.Args[1:]); err != nil {
		if err == flag.ErrHelp {
			os.Exit(0)
		}
		fmt.Fprintf(os.Stderr, "Error parsing flags: %v\n\n", err)
		printUsage()
		os.Exit(2)
	}

	if showVersion {
		printVersion()
		os.Exit(0)
	}

	cfg.Keyword = strings.TrimSpace(cfg.Keyword)
	cfg.OutputDir = strings.TrimSpace(cfg.OutputDir)
	cfg.Downloader = strings.TrimSpace(strings.ToLower(cfg.Downloader))
	cfg.UserAgent = strings.TrimSpace(cfg.UserAgent)

	cfg.Timeout = time.Duration(timeoutSeconds) * time.Second
	cfg.SeedURLs = splitCSV(seedList)

	if cfg.OutputDir == "" && cfg.Keyword != "" {
		dirName := sanitizeFilename(cfg.Keyword)
		if dirName == "" {
			dirName = cfg.Keyword
		}
		cfg.OutputDir = filepath.Join(".", dirName)
	}

	if siteList != "" {
		cfg.DefaultSites, cfg.invalidSites = parseSiteList(siteList)
	} else {
		cfg.DefaultSites = defaultSites()
		cfg.invalidSites = nil
	}

	return cfg
}

func defaultSites() []string {
	sites := make([]string, len(builtinSites))
	copy(sites, builtinSites)
	return sites
}

func splitCSV(value string) []string {
	if strings.TrimSpace(value) == "" {
		return nil
	}
	parts := strings.Split(value, ",")
	seen := make(map[string]struct{}, len(parts))
	result := make([]string, 0, len(parts))
	for _, part := range parts {
		trimmed := strings.TrimSpace(part)
		if trimmed == "" {
			continue
		}
		key := strings.ToLower(trimmed)
		if _, ok := seen[key]; ok {
			continue
		}
		seen[key] = struct{}{}
		result = append(result, trimmed)
	}
	if len(result) == 0 {
		return nil
	}
	return result
}

func parseSiteList(value string) (valid []string, invalid []string) {
	for _, entry := range splitCSV(value) {
		normalized := strings.ToLower(entry)
		if _, ok := builtinSiteSet[normalized]; ok {
			valid = append(valid, normalized)
			continue
		}
		invalid = append(invalid, entry)
	}
	return valid, invalid
}

func validateConfig(cfg *Config) error {
	var problems []string

	if cfg.Keyword == "" {
		problems = append(problems, "keyword is required (use -keyword or -k)")
	}

	if cfg.OutputDir == "" {
		problems = append(problems, "output directory could not be determined")
	}

	if cfg.MaxPages < 1 {
		problems = append(problems, "max-pages must be at least 1")
	}

	if cfg.MaxDepth < 1 {
		problems = append(problems, "max-depth must be at least 1")
	}

	if cfg.Concurrency < 1 {
		problems = append(problems, "concurrency must be at least 1")
	}

	if cfg.Timeout <= 0 {
		problems = append(problems, "timeout must be greater than 0 seconds")
	}

	if cfg.RateLimitMs < 0 {
		problems = append(problems, "rate-limit cannot be negative")
	}

	if cfg.MinWidth < 0 {
		problems = append(problems, "min-width cannot be negative")
	}

	if cfg.MinHeight < 0 {
		problems = append(problems, "min-height cannot be negative")
	}

	validDownloaders := map[string]struct{}{
		"auto": {},
		"curl": {},
		"wget": {},
	}
	if _, ok := validDownloaders[cfg.Downloader]; !ok {
		problems = append(problems, "downloader must be one of: auto, curl, wget")
	}

	for _, seed := range cfg.SeedURLs {
		if !strings.HasPrefix(seed, "http://") && !strings.HasPrefix(seed, "https://") {
			problems = append(problems, fmt.Sprintf("invalid seed URL (must start with http:// or https://): %s", seed))
		}
	}

	if len(cfg.invalidSites) > 0 {
		problems = append(problems, fmt.Sprintf("unknown site(s) provided to -sites: %s", strings.Join(cfg.invalidSites, ", ")))
	}

	for _, site := range cfg.DefaultSites {
		if _, ok := builtinSiteSet[site]; !ok {
			problems = append(problems, fmt.Sprintf("unsupported site in configuration: %s", site))
		}
	}

	if len(cfg.SeedURLs) == 0 && len(cfg.DefaultSites) == 0 {
		problems = append(problems, "no seed URLs or default sites provided")
	}

	if len(problems) > 0 {
		return fmt.Errorf(strings.Join(problems, "; "))
	}
	return nil
}

func printUsage() {
	fmt.Fprintf(os.Stderr, `webcrawler-ai - A CLI web crawler for images

Usage:
  %[1]s -keyword <keyword> [options]

Required Flags:
  -keyword, -k <string>     Keyword to search for in image filenames

Optional Flags:
  -output, -o <string>      Output directory (default: ./<keyword>)
  -max-pages, -p <int>      Maximum number of pages to crawl (default: %[2]d)
  -max-depth, -d <int>      Maximum crawl depth (default: %[3]d)
  -concurrency, -c <int>    Number of concurrent workers (default: %[4]d)
  -timeout, -t <int>        Request timeout in seconds (default: %[5]d)
  -rate-limit, -r <int>     Rate limit between requests in ms (default: %[6]d)
  -user-agent, -ua <string> User agent string
  -downloader <string>      Downloader: curl, wget, or auto (default: auto)
  -seeds, -s <string>       Comma-separated seed URLs to start crawling
  -sites <string>           Comma-separated default sites to use (available: %[7]s)
  -min-width <int>          Minimum image width in pixels (default: 0)
  -min-height <int>         Minimum image height in pixels (default: 0)
  -skip-thumbnails          Skip images likely to be thumbnails (default: false)
  -follow-subdomains        Follow links to subdomains (default: false)
  -ignore-robots            Ignore robots.txt restrictions (default: false)
  -verbose, -v              Enable verbose output (default: false)
  -version                  Show version information

Examples:
  %[1]s -k dog
  %[1]s -k cat -o ./cats -p 100
  %[1]s -k nature -s "https://example.com,https://photos.example.com"
  %[1]s -k landscape -c 10 -downloader curl -v

Notes:
  - WebP images are automatically excluded
  - robots.txt is respected unless -ignore-robots is specified
  - Progress bars show crawling and download progress

`, filepath.Base(os.Args[0]), defaultMaxPages, defaultMaxDepth, defaultConcurrency, defaultTimeoutSec, defaultRateLimitMs, strings.Join(builtinSites, ","))
}

func printBanner() {
	fmt.Println(`
                                              ████
                                             ░░███
  ██████  ████████   ██████   █████ ███ █████ ░███  █████ ████
 ███░░███░░███░░███ ░░░░░███ ░░███ ░███░░███  ░███ ░░███ ░███
░███ ░░░  ░███ ░░░   ███████  ░███ ░███ ░███  ░███  ░███ ░███
░███  ███ ░███      ███░░███  ░░███████████   ░███  ░███ ░███
░░██████  █████    ░░████████  ░░████░████    █████ ░░███████
 ░░░░░░  ░░░░░      ░░░░░░░░    ░░░░ ░░░░    ░░░░░   ░░░░░███
                                                     ███ ░███
                                                    ░░██████
                                                     ░░░░░░
`)
}

func printConfig(cfg *Config) {
	fmt.Println("Configuration:")
	fmt.Printf("  Keyword:           %s\n", cfg.Keyword)
	fmt.Printf("  Output Directory:  %s\n", cfg.OutputDir)
	fmt.Printf("  Max Pages:         %d\n", cfg.MaxPages)
	fmt.Printf("  Max Depth:         %d\n", cfg.MaxDepth)
	fmt.Printf("  Concurrency:       %d\n", cfg.Concurrency)
	fmt.Printf("  Timeout:           %s\n", cfg.Timeout)
	fmt.Printf("  Rate Limit:        %dms\n", cfg.RateLimitMs)
	fmt.Printf("  Downloader:        %s\n", cfg.Downloader)

	if cfg.MinWidth > 0 || cfg.MinHeight > 0 {
		fmt.Printf("  Min Resolution:    %dx%d\n", cfg.MinWidth, cfg.MinHeight)
	} else {
		fmt.Printf("  Min Resolution:    No limit\n")
	}

	if len(cfg.SeedURLs) > 0 {
		fmt.Printf("  Seed URLs:         %d provided\n", len(cfg.SeedURLs))
		if cfg.Verbose {
			for i, url := range cfg.SeedURLs {
				fmt.Printf("    %d. %s\n", i+1, url)
			}
		}
	} else {
		switch {
		case len(cfg.DefaultSites) == 0:
			fmt.Println("  Seed URLs:         None (crawler will not start)")
		case usingAllDefaultSites(cfg.DefaultSites):
			fmt.Println("  Seed URLs:         None (using all default sites)")
		default:
			fmt.Printf("  Seed URLs:         None (using sites: %s)\n", strings.Join(cfg.DefaultSites, ", "))
		}
	}

	fmt.Printf("  Skip Thumbnails:   %t\n", cfg.SkipThumbnails)
	fmt.Printf("  Follow Subdomains: %t\n", cfg.FollowSubdomains)
	fmt.Printf("  Ignore Robots:     %t\n", cfg.IgnoreRobots)
	fmt.Printf("  Verbose:           %t\n", cfg.Verbose)
	fmt.Println()
}

func printVersion() {
	fmt.Printf("webcrawler-ai v%s\n", version)
	fmt.Printf("Go version: %s\n", runtime.Version())
}

func run(cfg *Config) error {
	if err := os.MkdirAll(cfg.OutputDir, 0755); err != nil {
		return fmt.Errorf("failed to create output directory %s: %w", cfg.OutputDir, err)
	}
	fmt.Printf("✓ Created output directory: %s\n", cfg.OutputDir)

	if cfg.Downloader == "auto" {
		detected, err := detectDownloader()
		if err != nil {
			return err
		}
		cfg.Downloader = detected
		fmt.Printf("✓ Detected downloader: %s\n", cfg.Downloader)
	} else {
		if err := verifyDownloader(cfg.Downloader); err != nil {
			return err
		}
		fmt.Printf("✓ Using downloader: %s\n", cfg.Downloader)
	}

	if (cfg.MinWidth > 0 || cfg.MinHeight > 0) && !checkCommandExists("identify") {
		return fmt.Errorf("minimum dimension filters require ImageMagick 'identify' command; please install ImageMagick")
	}

	SetSkipThumbnails(cfg.SkipThumbnails)

	fmt.Println()

	crawler := NewCrawler(cfg)
	if err := crawler.Start(); err != nil {
		return fmt.Errorf("crawling failed: %w", err)
	}

	imageURLs := crawler.GetImageURLs()
	if len(imageURLs) == 0 {
		fmt.Println("\nNo images found matching criteria")
		return nil
	}

	fmt.Println()

	downloader := NewDownloader(cfg)
	if err := downloader.DownloadImages(imageURLs); err != nil {
		return fmt.Errorf("download failed: %w", err)
	}

	return nil
}

func detectDownloader() (string, error) {
	if err := verifyDownloader("curl"); err == nil {
		return "curl", nil
	}

	if err := verifyDownloader("wget"); err == nil {
		return "wget", nil
	}

	return "", fmt.Errorf("neither curl nor wget found in PATH")
}

func verifyDownloader(downloader string) error {
	if !checkCommandExists(downloader) {
		return fmt.Errorf("%s not found", downloader)
	}
	return nil
}

func usingAllDefaultSites(sites []string) bool {
	if len(sites) != len(builtinSites) {
		return false
	}
	seen := make(map[string]struct{}, len(sites))
	for _, site := range sites {
		seen[strings.ToLower(site)] = struct{}{}
	}
	for _, site := range builtinSites {
		if _, ok := seen[site]; !ok {
			return false
		}
	}
	return true
}
