package main

import (
	"encoding/json"
	"log"
	"net/http"
	"os"
	"sync"
	"time"

	"github.com/gorilla/mux"
	"github.com/heroku/docker-registry-client/registry"
	"github.com/namsral/flag"
)

// Response struct hold information about all tags plus the total size
type Response struct {
	Data []RepositorySmall `json:"data,omitempty"`
}

// Transform Transforms Repository to Repository Small format
func (r *Repository) Transform() RepositorySmall {
	val := RepositorySmall{}
	val.Repo = r.Name
	val.Tags = len(r.Tags)
	val.Size = int(r.TotalSize)
	return val
}

// RepositorySmall JSON Reponse
type RepositorySmall struct {
	Repo string `json:"repo,omitempty"`
	Tags int    `json:"tags,omitempty"`
	Size int    `json:"size,omitempty"`
}

// Repository struct hold information about all tags plus the total size
type Repository struct {
	Name      string `json:"name,omitempty"`
	TotalSize int64  `json:"totalSize,omitempty"`
	Tags      []Tag  `json:"tags,omitempty"`
}

// Tag struct holds information about tag name and it's layers
type Tag struct {
	Repo   string           `json:"repo,omitempty"`
	Tag    string           `json:"tag,omitempty"`
	Layers map[string]int64 `json:"sizes,omitempty"`
}

type semaphore struct {
}

func getRepositories(w http.ResponseWriter, r *http.Request) {
	response := &Response{}
	for _, repo := range m {
		response.Data = append(response.Data, repo.Transform())
	}
	json.NewEncoder(w).Encode(response)
}

func getTags(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	json.NewEncoder(w).Encode(m[params["repo"]])
}

func getManifest(w http.ResponseWriter, r *http.Request) {
	params := mux.Vars(r)
	manifestV1, _ := hub.Manifest(params["repo"], params["tag"])
	json.NewEncoder(w).Encode(manifestV1)
}

func fetchManifest(repository string, tag string, chTag chan<- Tag, wg *sync.WaitGroup, chSemaphore chan semaphore) {

	layerMap := make(map[string]int64)

	chSemaphore <- semaphore{}
	manifest, err := hub.ManifestV2(repository, tag)
	<-chSemaphore

	if err != nil {
		log.Print("Error while retrieving manifest, ignoring.")
		wg.Done()
		return
	}
	layerMap[manifest.Config.Digest.String()] = manifest.Config.Size
	for _, layer := range manifest.Layers {
		layerMap[layer.Digest.String()] = layer.Size
	}
	t := &Tag{Repo: repository, Tag: tag, Layers: layerMap}
	chTag <- *t
	wg.Done()
}

func fetchTags(hub *registry.Registry, repository string, chRepo chan<- *Repository, wgc *sync.WaitGroup, chSemaphore chan semaphore) {
	repo := &Repository{Name: repository}

	tags, _ := hub.Tags(repository)

	// Fetch all manifests to determine repository sizes
	var wg sync.WaitGroup
	chTag := make(chan Tag, len(tags))
	for _, tag := range tags {
		wg.Add(1)
		fetchManifest(repository, tag, chTag, &wg, chSemaphore)
	}
	wg.Wait()
	close(chTag)
	totalSizeMap := make(map[string]int64)
	for tag := range chTag {
		repo.Tags = append(repo.Tags, tag)
		for layer, size := range tag.Layers {
			totalSizeMap[layer] = size
		}
	}
	var totalSize int64
	for _, size := range totalSizeMap {
		totalSize += size
	}
	repo.TotalSize = totalSize
	chRepo <- repo
	wgc.Done()
	log.Printf("Processed repository %s with %d tags.", repo.Name, len(repo.Tags))
}

func fetchRepositories() {

	concurrencyLimit := 40

	repositories, err := hub.Repositories()

	if err != nil {
		log.Fatal("Could not retrieve repositories")
	}

	var wg sync.WaitGroup
	chRepo := make(chan *Repository, len(repositories))
	chSemaphore := make(chan semaphore, concurrencyLimit)

	for _, repository := range repositories {
		wg.Add(1)
		go fetchTags(hub, repository, chRepo, &wg, chSemaphore)
	}
	wg.Wait()
	close(chRepo)

	numberOfTags := 0

	for repo := range chRepo {
		m[repo.Name] = repo
		numberOfTags += len(repo.Tags)
	}
	log.Printf("Number of Tags served: %d", numberOfTags)
}

var (
	m   map[string]*Repository
	hub *registry.Registry
)

// Sum just to check if sonar is working
func Sum(a int, b int) int {
	return a + b
}

func main() {

	var (
		url      string
		username string
		password string
		err      error
	)

	fs := flag.NewFlagSetWithEnvPrefix(os.Args[0], "DOCKER", 0)
	fs.StringVar(&url, "registry", "", "Address of the registry, including protocol prefix")
	fs.StringVar(&username, "username", "", "Username for the registry")
	fs.StringVar(&password, "password", "", "Password for the registry")
	fs.Parse(os.Args[1:])

	log.Print("Starting Registry UI server...")

	hub, err = registry.NewInsecure(url, username, password)

	if err != nil {
		log.Fatal("Could not connect to registry.", err)
	}

	hub.Logf = registry.Quiet
	start := time.Now()

	m = make(map[string]*Repository)

	fetchRepositories()

	log.Printf("Happily serving %d repositories, took %s.", len(m), time.Since(start))

	router := mux.NewRouter()
	router.HandleFunc("/api/repositories", getRepositories).Methods("GET")
	router.HandleFunc("/api/tags/{repo:(?:.+/)?(?:[^:]+)(?::.+)?}", getTags).Methods("GET")
	router.HandleFunc("/api/manifest/{repo:(?:.+/)?(?:[^:]+)(?::.+)?}/{tag}", getManifest).Methods("GET")
	router.PathPrefix("/").Handler(http.FileServer(http.Dir("./frontend/build/")))
	log.Fatal(http.ListenAndServe(":8000", router))
}
