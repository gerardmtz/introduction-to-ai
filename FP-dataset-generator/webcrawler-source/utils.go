package main

import (
	"fmt"
	"net/url"
	"os/exec"
	"path"
	"strings"
)

var (
	skipThumbnailFiltering bool

	imageExtensions = []string{
		".jpg",
		".jpeg",
		".png",
		".gif",
		".bmp",
		".svg",
		".ico",
		".tiff",
		".tif",
	}
)

// SetSkipThumbnails enables or disables thumbnail filtering globally.
func SetSkipThumbnails(enabled bool) {
	skipThumbnailFiltering = enabled
}

// isImageURL returns true when the provided URL appears to reference an image
// asset that we support downloading. WebP assets are always excluded.
func isImageURL(raw string) bool {
	if raw == "" {
		return false
	}

	normalized := strings.TrimSpace(raw)
	if normalized == "" {
		return false
	}

	if isPotentialDataURI(normalized) || isScriptURL(normalized) {
		return false
	}

	if isWebPImage(normalized) {
		return false
	}

	if isEphemeralImageURL(normalized) {
		return false
	}

	if skipThumbnailFiltering && isThumbnailImage(normalized) {
		return false
	}

	u, err := url.Parse(normalized)
	if err == nil && u.Scheme != "" && u.Host != "" {
		if hasImageExtension(u.Path) {
			return true
		}
		if candidate := stripQueryParams(u); candidate != "" {
			return hasImageExtension(candidate)
		}
	}

	return hasImageExtension(normalized)
}

// isWebPImage checks if the URL or filename indicates a WebP image.
func isWebPImage(raw string) bool {
	lower := strings.ToLower(raw)
	return strings.HasSuffix(lower, ".webp") ||
		strings.Contains(lower, ".webp?") ||
		strings.Contains(lower, "format=webp") ||
		strings.Contains(lower, "fm=webp")
}

// isThumbnailImage tries to detect common thumbnail naming conventions.
func isThumbnailImage(raw string) bool {
	lower := strings.ToLower(raw)

	parts := strings.Split(lower, "/")
	filename := parts[len(parts)-1]

	if strings.Contains(filename, "px_") || strings.Contains(filename, "px-") {
		return true
	}

	if strings.Contains(lower, "/thumb/") ||
		strings.Contains(lower, "/thumbnail/") ||
		strings.Contains(lower, "_thumb.") ||
		strings.Contains(lower, "_thumbnail.") ||
		strings.Contains(lower, "-thumb.") ||
		strings.Contains(lower, "-thumbnail.") {
		return true
	}

	if strings.Contains(filename, "_small.") ||
		strings.Contains(filename, "_tiny.") ||
		strings.Contains(filename, "_preview.") ||
		strings.Contains(filename, "-small.") ||
		strings.Contains(filename, "-tiny.") ||
		strings.Contains(filename, "-preview.") {
		return true
	}

	return false
}

func isEphemeralImageURL(raw string) bool {
	lower := strings.ToLower(raw)
	if strings.Contains(lower, "deviantart.com/strp/") {
		return true
	}

	u, err := url.Parse(raw)
	if err != nil {
		return false
	}

	if !strings.Contains(strings.ToLower(u.Host), "deviantart.com") {
		return false
	}

	return strings.Contains(strings.ToLower(u.RawQuery), "token=")
}

// containsKeyword checks if the URL contains the keyword.
func containsKeyword(raw, keyword string) bool {
	return strings.Contains(strings.ToLower(raw), strings.ToLower(keyword))
}

// normalizeURL removes fragments and trims whitespace.
func normalizeURL(raw string) string {
	if idx := strings.Index(raw, "#"); idx != -1 {
		raw = raw[:idx]
	}
	return strings.TrimSpace(raw)
}

// execCommand executes a shell command and returns an error if it fails.
func execCommand(name string, args ...string) error {
	return exec.Command(name, args...).Run()
}

// execCommandOutput executes a shell command and returns its combined output.
func execCommandOutput(name string, args ...string) (string, error) {
	cmd := exec.Command(name, args...)
	output, err := cmd.CombinedOutput()
	return string(output), err
}

// checkCommandExists returns true when the command is available on PATH.
func checkCommandExists(name string) bool {
	_, err := exec.LookPath(name)
	return err == nil
}

// sanitizeFilename removes or replaces invalid filename characters.
func sanitizeFilename(filename string) string {
	replacements := map[string]string{
		"/":  "_",
		"\\": "_",
		":":  "_",
		"*":  "_",
		"?":  "_",
		"\"": "_",
		"<":  "_",
		">":  "_",
		"|":  "_",
		" ":  "_",
	}

	result := filename
	for old, repl := range replacements {
		result = strings.ReplaceAll(result, old, repl)
	}

	for strings.Contains(result, "__") {
		result = strings.ReplaceAll(result, "__", "_")
	}

	result = strings.Trim(result, "_")

	if len(result) > 200 {
		result = result[:200]
	}

	if result == "" {
		return "image"
	}

	return result
}

// extractFilenameFromURL extracts a sanitized filename from a URL.
func extractFilenameFromURL(raw string) string {
	if idx := strings.Index(raw, "?"); idx != -1 {
		raw = raw[:idx]
	}

	if parsed, err := url.Parse(raw); err == nil && parsed.Path != "" {
		raw = parsed.Path
	}

	filename := path.Base(raw)
	if filename == "." || filename == "/" || filename == "" {
		return "image"
	}

	return sanitizeFilename(filename)
}

// getHostFromURL extracts the host from a URL string.
func getHostFromURL(raw string) string {
	raw = strings.TrimPrefix(raw, "http://")
	raw = strings.TrimPrefix(raw, "https://")

	if idx := strings.Index(raw, "/"); idx != -1 {
		raw = raw[:idx]
	}

	if idx := strings.Index(raw, ":"); idx != -1 {
		raw = raw[:idx]
	}

	return raw
}

// isSameDomain checks if two URLs are from the same domain.
func isSameDomain(a, b string) bool {
	return getHostFromURL(a) == getHostFromURL(b)
}

// isSubdomain checks if urlB is a subdomain of urlA's domain.
func isSubdomain(parentURL, childURL string) bool {
	parent := strings.TrimPrefix(getHostFromURL(parentURL), "www.")
	child := strings.TrimPrefix(getHostFromURL(childURL), "www.")
	return strings.HasSuffix(child, parent)
}

// log helpers ---------------------------------------------------------------

func logVerbose(cfg *Config, format string, args ...interface{}) {
	if cfg.Verbose {
		fmt.Printf("[VERBOSE] "+format+"\n", args...)
	}
}

func logInfo(format string, args ...interface{}) {
	fmt.Printf("[INFO] "+format+"\n", args...)
}

func logError(format string, args ...interface{}) {
	fmt.Printf("[ERROR] "+format+"\n", args...)
}

func logSuccess(format string, args ...interface{}) {
	fmt.Printf("[✓] "+format+"\n", args...)
}

func logWarning(format string, args ...interface{}) {
	fmt.Printf("[⚠] "+format+"\n", args...)
}

// internal helpers ----------------------------------------------------------

func hasImageExtension(candidate string) bool {
	lower := strings.ToLower(candidate)
	for _, ext := range imageExtensions {
		if strings.HasSuffix(lower, ext) {
			return true
		}
		if strings.Contains(lower, ext+"?") {
			return true
		}
	}
	return false
}

func stripQueryParams(u *url.URL) string {
	if u == nil {
		return ""
	}
	if u.RawQuery == "" {
		return u.Path
	}
	cloned := *u
	cloned.RawQuery = ""
	return cloned.Path
}

func isPotentialDataURI(raw string) bool {
	return strings.HasPrefix(strings.ToLower(raw), "data:")
}

func isScriptURL(raw string) bool {
	lower := strings.ToLower(strings.TrimSpace(raw))
	return strings.HasPrefix(lower, "javascript:") || strings.HasPrefix(lower, "vbscript:")
}
