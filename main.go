package registry

import (
	"encoding/json"
	"log"
	"net/http"
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

func fetchManifest(repository string, tag string, repo *Repository, totalSizeMap map[string]int64, wg *sync.WaitGroup) {
	manifest, _ := hub.ManifestV2(repository, tag)
	layerMap := make(map[string]int64)
	layerMap[manifest.Config.Digest.String()] = manifest.Config.Size
	totalSizeMap[manifest.Config.Digest.String()] = manifest.Config.Size
	for _, layer := range manifest.Layers {
		layerMap[layer.Digest.String()] = layer.Size
		totalSizeMap[layer.Digest.String()] = layer.Size
	}
	repo.Tags = append(repo.Tags, Tag{Tag: tag, Layers: layerMap, Repo: repository})
	wg.Done()
}

func fetchTags(hub *registry.Registry, repository string, m map[string]*Repository, i int, wg *sync.WaitGroup) {

	var wgTags sync.WaitGroup

	repo := Repository{Name: repository}
	tags, _ := hub.Tags(repository)

	totalSizeMap := make(map[string]int64)

	log.Printf("Fetching repository %s with %d tags.", repository, len(tags))

	for _, tag := range tags {
		wgTags.Add(1)
		go fetchManifest(repository, tag, &repo, totalSizeMap, &wgTags)
	}
	wgTags.Wait()

	for _, size := range totalSizeMap {
		repo.TotalSize += size
	}
	m[repository] = &repo
	wg.Done()
}

func fetchRepositories() time.Duration {
	start := time.Now()
	repositories, err := hub.Repositories()
	m = make(map[string]*Repository, len(repositories))
	if err != nil {
		log.Fatal("Could not retrieve repositories")
	}
	var wg sync.WaitGroup
	for index, repository := range repositories {
		wg.Add(1)
		go fetchTags(hub, repository, m, index, &wg)
	}
	wg.Wait()
	return time.Since(start)
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

	flag.StringVar(&url, "registry", "", "Address of the registry, including protocol prefix")
	flag.StringVar(&username, "username", "", "Username for the registry")
	flag.StringVar(&password, "password", "", "Password for the registry")
	flag.Parse()

	log.Print("Starting Registry UI server...")

	hub, err = registry.New(url, username, password)
	hub.Logf = registry.Quiet

	if err != nil {
		log.Fatal("Could not connect to registry.")
	}

	duration := fetchRepositories()

	log.Printf("Happily serving %d repositories, took %s.", len(m), duration)

	router := mux.NewRouter()
	router.HandleFunc("/api/repositories", getRepositories).Methods("GET")
	router.HandleFunc("/api/tags/{repo:(?:.+/)?(?:[^:]+)(?::.+)?}", getTags).Methods("GET")
	router.HandleFunc("/api/manifest/{repo:(?:.+/)?(?:[^:]+)(?::.+)?}/{tag}", getManifest).Methods("GET")
	router.PathPrefix("/").Handler(http.FileServer(http.Dir("./frontend/build/")))
	router.Use(simpleMw)
	log.Fatal(http.ListenAndServe(":8000", router))
}

func simpleMw(next http.Handler) http.Handler {
	return http.HandlerFunc(func(w http.ResponseWriter, r *http.Request) {
		// Do stuff here
		log.Println(r.RequestURI)
		// Call the next handler, which can be another middleware in the chain, or the final handler.
		next.ServeHTTP(w, r)
	})
}
