import json
import sys
import difflib

try:
    import requests
except ModuleNotFoundError:
    print("You need to install the requests module: pip install requests", file=sys.stderr)
    sys.exit()

class SceneMultiplexer:
    url = "http://localhost:9999/graphql"
    headers = {"Content-Type": "application/json"}

    # =========================================================================
    # SCRAPER CONFIGURATION
    # =========================================================================
    scrapers = ["Bang", "Eporner", "Fapality", "Lesbian8", "Mylust", "Pornhub", "Pornlib", "Spizoo", "W4nkr", "Xgroovy", "Xhamster", "Xnxx", "Xxxshake"]
    
    # Matches scoring below this are discarded.
    SIMILARITY_THRESHOLD = 0.8
    # =========================================================================

    def __call_graphql(self, query, variables=None):
        payload = {'query': query, 'variables': variables}
        try:
            response = requests.post(self.url, json=payload, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                if "errors" in result:
                    print(f"GraphQL Errors: {json.dumps(result['errors'])}", file=sys.stderr)
                    return None
                return result.get("data")
            else:
                print(f"Query failed with status {response.status_code}: {response.text}", file=sys.stderr)
                return None
        except Exception as e:
            print(f"Request Exception: {e}", file=sys.stderr)
            return None

    def search_scene(self, scraper_id, term):
        query = """
        query ScrapeSingleScene($source: ScraperSourceInput!, $input: ScrapeSingleSceneInput!) {
          scrapeSingleScene(source: $source, input: $input) {
            title
            url
            date
            image
          }
        }
        """
        variables = {
            "source": { "scraper_id": scraper_id },
            "input": { "query": term }
        }
        result = self.__call_graphql(query, variables)
        if result and "scrapeSingleScene" in result:
            return result["scrapeSingleScene"]
        return []
        
    def fetch_scene_details(self, scraper_id, scene_data):
        query = """
        query ScrapeSceneURL($url: String!) {
          scrapeSceneURL(url: $url) {
            title
            details
            date
            url
            image
            studio { name }
            tags { name }
            performers { name }
          }
        }
        """
        variables = {"url": scene_data.get("url")}
        result = self.__call_graphql(query, variables)
        if result and "scrapeSceneURL" in result:
            return result["scrapeSceneURL"]
        return None

    def get_similarity(self, a, b):
        return difflib.SequenceMatcher(None, str(a).lower(), str(b).lower()).ratio()

    def run(self, target_title):
        clean_target = target_title.strip().lower()
        print(f"Aggregating all matches for: '{clean_target}'", file=sys.stderr)
        
        all_results = []
        seen_urls = set()

        for scraper_name in self.scrapers:
            print(f"Querying {scraper_name}...", file=sys.stderr)
            found_items = self.search_scene(scraper_name, target_title)
            
            if not found_items:
                continue

            for item in found_items:
                # Get the title directly from the search result first
                search_title = item.get('title', '')
                found_title_lower = search_title.strip().lower()
                score = self.get_similarity(clean_target, found_title_lower)

                if score >= self.SIMILARITY_THRESHOLD:
                    details = self.fetch_scene_details(scraper_name, item)
                    
                    if details:
                        # CRITICAL FIX: If the details fetch returned an empty title, 
                        # use the title we already found during the search phase.
                        if not details.get('title') or details.get('title') == "Unnamed":
                            details['title'] = search_title
                        
                        if details.get('url') not in seen_urls:
                            print(f" MATCH: '{details['title']}' ({score:.2f})", file=sys.stderr)
                            all_results.append(details)
                            seen_urls.add(details.get('url'))

        return all_results

# --- STASH INTERFACE ---
if len(sys.argv) < 2:
    sys.exit(0)

mode = sys.argv[1]

try:
    input_raw = sys.stdin.read().strip()
    if not input_raw:
        print("[]" if mode == "query" else "{}")
        sys.exit(0)
        
    fragment = json.loads(input_raw)
    scene_name = fragment.get('title') or fragment.get('name')

    if not scene_name:
        print("[]" if mode == "query" else "{}")
        sys.exit(0)

    mux = SceneMultiplexer()
    matches = mux.run(scene_name)

    if matches:
        # Since we are returning a list, mode doesn't change the list structure
        # but the Tagger UI expects a list for search results.
        print(json.dumps(matches if isinstance(matches, list) else [matches]))
    else:
        print("[]" if mode == "query" else "{}")

except Exception as e:
    print(f"Top-level Error: {e}", file=sys.stderr)
    print("[]" if mode == "query" else "{}")