package main

import (
	"fmt"
	"net/http"
	"net/url"
	"strings"
	"sync"
	"sync/atomic"
	"time"

	"github.com/PuerkitoBio/goquery"
	"github.com/schollz/progressbar/v3"
	"github.com/temoto/robotstxt"
)

var redundantImageQueryParams = map[string]struct{}{
	"w":        {},
	"width":    {},
	"h":        {},
	"height":   {},
	"fit":      {},
	"crop":     {},
	"auto":     {},
	"format":   {},
	"fm":       {},
	"quality":  {},
	"q":        {},
	"ixlib":    {},
	"ixid":     {},
	"cs":       {},
	"dpr":      {},
	"usm":      {},
	"compress": {},
	"token":    {},
}

type Crawler struct {
	config *Config

	client *http.Client

	taskCh chan CrawlTask
	wg     sync.WaitGroup
	taskWG sync.WaitGroup

	seenPages map[string]struct{}
	seenMutex sync.Mutex

	robotsCache map[string]*robotstxt.RobotsData
	robotsMutex sync.RWMutex

	visitedImages map[string]struct{}
	images        []string
	imagesMutex   sync.Mutex

	pagesCrawled  int32
	fetchFailures int32

	progressBar *progressbar.ProgressBar
	stopCh      chan struct{}
	stopOnce    sync.Once
}

type CrawlTask struct {
	URL   string
	Depth int
}

func NewCrawler(cfg *Config) *Crawler {
	queueCapacity := cfg.Concurrency * 4
	if queueCapacity < 128 {
		queueCapacity = 128
	}

	return &Crawler{
		config:        cfg,
		client:        &http.Client{Timeout: cfg.Timeout},
		taskCh:        make(chan CrawlTask, queueCapacity),
		seenPages:     make(map[string]struct{}),
		robotsCache:   make(map[string]*robotstxt.RobotsData),
		visitedImages: make(map[string]struct{}),
		images:        make([]string, 0, 256),
		stopCh:        make(chan struct{}),
	}
}

func (c *Crawler) Start() error {
	seeds := c.initialSeeds()
	if len(seeds) == 0 {
		return fmt.Errorf("no seed URLs available")
	}

	c.progressBar = progressbar.NewOptions(
		c.config.MaxPages,
		progressbar.OptionSetDescription("Crawling pages"),
		progressbar.OptionSetWidth(40),
		progressbar.OptionShowCount(),
		progressbar.OptionShowIts(),
		progressbar.OptionSetTheme(progressbar.Theme{
			Saucer:        "=",
			SaucerHead:    ">",
			SaucerPadding: " ",
			BarStart:      "[",
			BarEnd:        "]",
		}),
	)

	for i := 0; i < c.config.Concurrency; i++ {
		c.wg.Add(1)
		go c.worker()
	}

	logVerbose(c.config, "Seeding crawler with %d URL(s)", len(seeds))
	for _, seed := range seeds {
		c.enqueueTask(CrawlTask{URL: seed, Depth: 0})
	}

	go func() {
		c.taskWG.Wait()
		close(c.taskCh)
	}()

	c.wg.Wait()

	if c.progressBar != nil {
		c.progressBar.Finish()
	}

	fmt.Printf("\n\nCrawling complete:\n")
	fmt.Printf("  Pages crawled: %d\n", atomic.LoadInt32(&c.pagesCrawled))
	fmt.Printf("  Images found:  %d\n", c.imageCount())
	fmt.Printf("  Fetch failures: %d\n", atomic.LoadInt32(&c.fetchFailures))

	return nil
}

func (c *Crawler) GetImageURLs() []string {
	c.imagesMutex.Lock()
	defer c.imagesMutex.Unlock()

	result := make([]string, len(c.images))
	copy(result, c.images)
	return result
}

func (c *Crawler) worker() {
	defer c.wg.Done()

	for task := range c.taskCh {
		c.processTask(task)
	}
}

func (c *Crawler) processTask(task CrawlTask) {
	defer c.taskWG.Done()

	if c.shouldStopCrawling() {
		return
	}

	attempted, err := c.crawl(task)
	if err != nil {
		logVerbose(c.config, "Error crawling %s: %v", task.URL, err)
	}

	if attempted {
		c.incrementPagesCrawled()
	}

	if c.config.RateLimitMs > 0 {
		time.Sleep(time.Duration(c.config.RateLimitMs) * time.Millisecond)
	}
}

func (c *Crawler) crawl(task CrawlTask) (bool, error) {
	if !c.config.IgnoreRobots && !c.canCrawl(task.URL) {
		logVerbose(c.config, "Blocked by robots.txt: %s", task.URL)
		return false, nil
	}

	req, err := http.NewRequest("GET", task.URL, nil)
	if err != nil {
		return false, err
	}
	req.Header.Set("User-Agent", c.config.UserAgent)
	req.Header.Set("Accept", "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8")
	req.Header.Set("Accept-Language", "en-US,en;q=0.9")
	req.Header.Set("Connection", "keep-alive")
	req.Header.Set("Upgrade-Insecure-Requests", "1")

	attempted := true

	resp, err := c.client.Do(req)
	if err != nil {
		c.incrementFetchFailures()
		return attempted, err
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		switch resp.StatusCode {
		case http.StatusNotFound:
			c.incrementFetchFailures()
			logVerbose(c.config, "Page not found: %s (404)", task.URL)
			return attempted, nil
		case http.StatusForbidden, http.StatusMethodNotAllowed:
			logVerbose(c.config, "Skipping %s: status %d", task.URL, resp.StatusCode)
			return attempted, nil
		default:
			c.incrementFetchFailures()
			return attempted, fmt.Errorf("status code %d", resp.StatusCode)
		}
	}

	if !isHTMLContent(resp.Header.Get("Content-Type")) {
		return attempted, nil
	}

	doc, err := goquery.NewDocumentFromReader(resp.Body)
	if err != nil {
		return attempted, err
	}

	c.extractImages(doc, task.URL)

	if task.Depth < c.config.MaxDepth && !c.shouldStopCrawling() {
		c.extractAndQueueLinks(doc, task.URL, task.Depth+1)
	}

	return attempted, nil
}

func (c *Crawler) extractImages(doc *goquery.Document, baseURL string) {
	doc.Find("img").Each(func(_ int, sel *goquery.Selection) {
		for _, candidate := range c.collectImageCandidates(sel) {
			c.tryAddImageURL(baseURL, candidate)
		}
	})

	doc.Find("a[href]").Each(func(_ int, sel *goquery.Selection) {
		if href, exists := sel.Attr("href"); exists {
			c.tryAddImageURL(baseURL, href)
		}
	})

	doc.Find("picture source").Each(func(_ int, sel *goquery.Selection) {
		if srcset, exists := sel.Attr("srcset"); exists {
			if largest := c.extractLargestFromSrcset(srcset); largest != "" {
				c.tryAddImageURL(baseURL, largest)
			}
		}
	})

	doc.Find("meta[property='og:image'], meta[property='og:image:url'], meta[property='og:image:secure_url'], meta[name='twitter:image'], meta[name='twitter:image:src']").Each(func(_ int, sel *goquery.Selection) {
		if content, exists := sel.Attr("content"); exists {
			c.tryAddImageURL(baseURL, content)
		}
	})
}

func (c *Crawler) collectImageCandidates(sel *goquery.Selection) []string {
	attrs := []string{
		"data-src",
		"data-original",
		"data-fullsrc",
		"data-large",
		"data-lazy",
		"data-lazy-src",
		"data-thumbnail",
		"data-fallback-src",
		"data-img",
		"src",
	}

	unique := make(map[string]struct{}, len(attrs)*2)

	for _, attr := range attrs {
		if value, exists := sel.Attr(attr); exists {
			value = strings.TrimSpace(value)
			if value != "" {
				unique[value] = struct{}{}
			}
		}
	}

	if srcset, exists := sel.Attr("srcset"); exists {
		if largest := c.extractLargestFromSrcset(srcset); largest != "" {
			unique[largest] = struct{}{}
		}
	}

	if dataSrcset, exists := sel.Attr("data-srcset"); exists {
		if largest := c.extractLargestFromSrcset(dataSrcset); largest != "" {
			unique[largest] = struct{}{}
		}
	}

	result := make([]string, 0, len(unique))
	for value := range unique {
		result = append(result, value)
	}

	return result
}

func (c *Crawler) tryAddImageURL(baseURL, candidate string) {
	candidate = strings.TrimSpace(candidate)
	if candidate == "" {
		return
	}

	lower := strings.ToLower(candidate)
	if strings.HasPrefix(lower, "data:") || strings.HasPrefix(lower, "javascript:") {
		return
	}

	absolute := c.resolveURL(baseURL, candidate)
	if absolute == "" {
		return
	}

	if !isImageURL(absolute) {
		return
	}

	if !containsKeyword(absolute, c.config.Keyword) {
		return
	}

	if c.recordImage(absolute) {
		logVerbose(c.config, "Found image: %s", absolute)
	}
}

func (c *Crawler) extractAndQueueLinks(doc *goquery.Document, baseURL string, depth int) {
	doc.Find("a[href]").Each(func(_ int, sel *goquery.Selection) {
		href, exists := sel.Attr("href")
		if !exists {
			return
		}

		absolute := c.resolveURL(baseURL, href)
		if absolute == "" {
			return
		}

		if isImageURL(absolute) {
			c.tryAddImageURL(baseURL, href)
			return
		}

		if !c.shouldFollowLink(baseURL, absolute) {
			return
		}

		c.enqueueTask(CrawlTask{URL: absolute, Depth: depth})
	})
}

func (c *Crawler) recordImage(imageURL string) bool {
	canonical := canonicalizeImageURL(imageURL)
	if canonical == "" {
		canonical = imageURL
	}

	c.imagesMutex.Lock()
	defer c.imagesMutex.Unlock()

	if _, exists := c.visitedImages[canonical]; exists {
		return false
	}

	c.visitedImages[canonical] = struct{}{}
	c.images = append(c.images, imageURL)

	return true
}

func (c *Crawler) enqueueTask(task CrawlTask) {
	if c.shouldStopCrawling() {
		return
	}

	normalized := normalizeURL(strings.TrimSpace(task.URL))
	if normalized == "" {
		return
	}

	if task.Depth > c.config.MaxDepth {
		return
	}

	if !c.markPageSeen(normalized) {
		return
	}

	task.URL = normalized

	// Increment the outstanding task counter and enqueue without blocking
	// the calling worker. Sending is done in a separate goroutine so that
	// workers can continue processing other items and we avoid the case
	// where all workers block trying to enqueue new tasks (causing a
	// deadlock when the channel is full).
	c.taskWG.Add(1)

	// Fast path: if we've already been asked to stop, undo and return.
	select {
	case <-c.stopCh:
		c.taskWG.Done()
		return
	default:
	}

	go func(t CrawlTask) {
		// Ensure we account for the taskWG in all exit paths. Sending to
		// the channel may panic if it is closed concurrently; recover and
		// mark the task done in that case.
		defer func() {
			if r := recover(); r != nil {
				c.taskWG.Done()
			}
		}()

		select {
		case <-c.stopCh:
			c.taskWG.Done()
		case c.taskCh <- t:
			// successfully enqueued; the worker that processes the task
			// will call taskWG.Done() when finished (in processTask).
		}
	}(task)
}

func (c *Crawler) markPageSeen(pageURL string) bool {
	c.seenMutex.Lock()
	defer c.seenMutex.Unlock()

	if _, exists := c.seenPages[pageURL]; exists {
		return false
	}

	c.seenPages[pageURL] = struct{}{}
	return true
}

func (c *Crawler) shouldFollowLink(baseURL, targetURL string) bool {
	parsed, err := url.Parse(targetURL)
	if err != nil {
		return false
	}

	if parsed.Scheme != "http" && parsed.Scheme != "https" {
		return false
	}

	if isSameDomain(baseURL, targetURL) {
		return true
	}

	if c.config.FollowSubdomains && isSubdomain(baseURL, targetURL) {
		return true
	}

	return false
}

func (c *Crawler) resolveURL(baseURL, ref string) string {
	ref = strings.TrimSpace(ref)
	if ref == "" {
		return ""
	}

	lower := strings.ToLower(ref)
	if strings.HasPrefix(lower, "javascript:") || strings.HasPrefix(lower, "mailto:") || strings.HasPrefix(lower, "tel:") {
		return ""
	}

	base, err := url.Parse(baseURL)
	if err != nil {
		return ""
	}

	target, err := url.Parse(ref)
	if err != nil {
		return ""
	}

	resolved := base.ResolveReference(target)
	resolved.Fragment = ""
	return normalizeURL(resolved.String())
}

func (c *Crawler) incrementPagesCrawled() {
	count := atomic.AddInt32(&c.pagesCrawled, 1)
	if c.progressBar != nil {
		c.progressBar.Add(1)
	}

	if int(count) >= c.config.MaxPages {
		c.requestStop()
	}
}

func (c *Crawler) incrementFetchFailures() {
	atomic.AddInt32(&c.fetchFailures, 1)
}

func (c *Crawler) shouldStopCrawling() bool {
	select {
	case <-c.stopCh:
		return true
	default:
	}

	if int(atomic.LoadInt32(&c.pagesCrawled)) >= c.config.MaxPages {
		c.requestStop()
		return true
	}

	return false
}

func (c *Crawler) requestStop() {
	c.stopOnce.Do(func() {
		close(c.stopCh)
	})
}

func (c *Crawler) imageCount() int {
	c.imagesMutex.Lock()
	defer c.imagesMutex.Unlock()
	return len(c.images)
}

func (c *Crawler) initialSeeds() []string {
	if len(c.config.SeedURLs) > 0 {
		seeds := make([]string, 0, len(c.config.SeedURLs))
		for _, raw := range c.config.SeedURLs {
			normalized := normalizeURL(strings.TrimSpace(raw))
			if normalized != "" {
				seeds = append(seeds, normalized)
			}
		}
		return seeds
	}

	return c.buildDefaultSeeds()
}

func (c *Crawler) buildDefaultSeeds() []string {
	keyword := url.QueryEscape(c.config.Keyword)
	if keyword == "" {
		return nil
	}

	sites := c.config.DefaultSites
	if len(sites) == 0 {
		sites = defaultSites()
	}

	seeds := make([]string, 0, len(sites))
	seen := make(map[string]struct{}, len(sites))

	for _, site := range sites {
		seed := c.seedForSite(strings.ToLower(strings.TrimSpace(site)), keyword)
		if seed == "" {
			continue
		}
		if _, exists := seen[seed]; exists {
			continue
		}
		seen[seed] = struct{}{}
		seeds = append(seeds, seed)
	}

	return seeds
}

func (c *Crawler) seedForSite(site, keywordEscaped string) string {
	switch site {
	case "wikimedia":
		return fmt.Sprintf("https://commons.wikimedia.org/w/index.php?search=%s&title=Special:MediaSearch&go=Go&type=image", keywordEscaped)
	case "pexels":
		return fmt.Sprintf("https://www.pexels.com/search/%s/", keywordEscaped)
	case "pixabay":
		return fmt.Sprintf("https://pixabay.com/images/search/%s/", keywordEscaped)
	case "freeimages":
		return fmt.Sprintf("https://www.freeimages.com/search/%s", keywordEscaped)
	case "unsplash":
		return fmt.Sprintf("https://unsplash.com/s/photos/%s", keywordEscaped)
	case "flickr":
		return fmt.Sprintf("https://www.flickr.com/search/?text=%s&media=photos&license=4,5,6,9,10", keywordEscaped)
	case "deviantart":
		return fmt.Sprintf("https://www.deviantart.com/search?q=%s", keywordEscaped)
	case "pinterest":
		return fmt.Sprintf("https://www.pinterest.com/search/pins/?q=%s", keywordEscaped)
	case "imgur":
		return fmt.Sprintf("https://imgur.com/search?q=%s", keywordEscaped)
	case "reddit":
		return fmt.Sprintf("https://www.reddit.com/search/?q=%s&type=link", keywordEscaped)
	default:
		return ""
	}
}

func (c *Crawler) extractLargestFromSrcset(srcset string) string {
	var largestURL string
	var largestWidth int

	for _, part := range strings.Split(srcset, ",") {
		part = strings.TrimSpace(part)
		if part == "" {
			continue
		}

		fields := strings.Fields(part)
		if len(fields) == 0 {
			continue
		}

		urlCandidate := fields[0]
		width := 0

		if len(fields) > 1 {
			size := strings.TrimSuffix(fields[1], "w")
			size = strings.TrimSuffix(size, "x")
			fmt.Sscanf(size, "%d", &width)
		}

		if width > largestWidth {
			largestWidth = width
			largestURL = urlCandidate
		} else if largestURL == "" {
			largestURL = urlCandidate
		}
	}

	return strings.TrimSpace(largestURL)
}

func (c *Crawler) canCrawl(pageURL string) bool {
	parsed, err := url.Parse(pageURL)
	if err != nil || parsed.Host == "" {
		return false
	}

	robotsURL := fmt.Sprintf("%s://%s/robots.txt", parsed.Scheme, parsed.Host)
	data := c.getRobotsData(robotsURL)
	if data == nil {
		return true
	}

	group := data.FindGroup(c.config.UserAgent)
	if group == nil {
		group = data.FindGroup("*")
	}
	if group == nil {
		return true
	}

	return group.Test(parsed.Path)
}

func (c *Crawler) getRobotsData(robotsURL string) *robotstxt.RobotsData {
	c.robotsMutex.RLock()
	data, cached := c.robotsCache[robotsURL]
	c.robotsMutex.RUnlock()
	if cached {
		return data
	}

	data = c.fetchRobotsTxt(robotsURL)

	c.robotsMutex.Lock()
	c.robotsCache[robotsURL] = data
	c.robotsMutex.Unlock()

	return data
}

func (c *Crawler) fetchRobotsTxt(robotsURL string) *robotstxt.RobotsData {
	req, err := http.NewRequest("GET", robotsURL, nil)
	if err != nil {
		return nil
	}
	req.Header.Set("User-Agent", c.config.UserAgent)

	resp, err := c.client.Do(req)
	if err != nil {
		return nil
	}
	defer resp.Body.Close()

	if resp.StatusCode != http.StatusOK {
		return nil
	}

	data, err := robotstxt.FromResponse(resp)
	if err != nil {
		return nil
	}

	return data
}

func canonicalizeImageURL(raw string) string {
	normalized := normalizeURL(raw)
	if normalized == "" {
		return ""
	}

	parsed, err := url.Parse(normalized)
	if err != nil {
		return normalized
	}

	if parsed.RawQuery == "" {
		return parsed.String()
	}

	query := parsed.Query()
	stripped := false
	for key := range redundantImageQueryParams {
		if _, ok := query[key]; ok {
			query.Del(key)
			stripped = true
		}
	}

	if stripped {
		if len(query) == 0 {
			parsed.RawQuery = ""
		} else {
			parsed.RawQuery = query.Encode()
		}
	}

	return parsed.String()
}

func isHTMLContent(contentType string) bool {
	if contentType == "" {
		return true
	}

	contentType = strings.ToLower(contentType)
	return strings.HasPrefix(contentType, "text/html") || strings.HasPrefix(contentType, "application/xhtml+xml")
}
