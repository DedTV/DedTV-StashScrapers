import json
import sys

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
    # To ADD a scraper: 
    #   1. Go to Settings > Scrapers in your Stash UI.
    #   2. Find the "ID" column for the scraper you want (e.g., "ThePornDB").
    #   3. Add that exact string to the list below.
    #
    # To REMOVE a scraper: 
    #   Simply delete the string from this list.
    #
    # To CHANGE PRIORITY: 
    #   The script checks these in order. Move your preferred scrapers 
    #   to the top of the list to find matches there first.
    # =========================================================================
    scrapers = ["Anysex", "Pornlib", "Eporner"]

    def __call_graphql(self, query, variables=None):
        payload = {'query': query, 'variables': variables}
        try:
            response = requests.post(self.url, json=payload, headers=self.headers)
            if response.status_code == 200:
                result = response.json()
                if "errors" in result:
                    # Log internal GraphQL errors to Stash logs
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
        """Standard search logic for v0.31.1 using nested source/input."""
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
        """
        Final fix for v0.31.1-42: 
        The 'scrapeSceneURL' field now only accepts 'url'. 
        The scraper is automatically determined by Stash from the URL domain.
        """
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
        variables = {
            "url": scene_data.get("url")
        }
        
        result = self.__call_graphql(query, variables)
        if result and "scrapeSceneURL" in result:
            return result["scrapeSceneURL"]
        return None

    def run(self, target_title):
        clean_target = target_title.strip().lower()
        print(f"Searching for exact match: '{clean_target}'", file=sys.stderr)
        
        for scraper_name in self.scrapers:
            print(f"Querying {scraper_name}...", file=sys.stderr)
            results = self.search_scene(scraper_name, target_title)
            
            if not results:
                continue

            for res in results:
                if res.get('title') and res['title'].strip().lower() == clean_target:
                    print(f"MATCH FOUND in {scraper_name}!", file=sys.stderr)
                    # Pulling full metadata using the corrected fetch function
                    return self.fetch_scene_details(scraper_name, res)
        return None

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
    match = mux.run(scene_name)

    if match:
        if mode == "query":
            # Output MUST be a list for the Scrape (Search) UI
            print(json.dumps([match]))
        else:
            # Output MUST be a single object for the URL/Fetch UI
            print(json.dumps(match))
    else:
        print("[]" if mode == "query" else "{}")

except Exception as e:
    print(f"Top-level Error: {e}", file=sys.stderr)
    print("[]" if mode == "query" else "{}")