import json
import os
import sys
import re
from py_common import graphql
from py_common import log

REMOVE_EXT = True

def scrape_filename(js):
    scene_id = js.get("id")
    
    response = graphql.callGraphQL(
        """
        query FilenameBySceneId($id: ID){
          findScene(id: $id){
            files {
              path
            }
          }
        }""",
        {"id": scene_id},
    )
    
    if not response or not response.get("findScene"):
        return None

    files = response["findScene"]["files"]
    if not files:
        return None

    filename = os.path.basename(files[0]["path"])
    if REMOVE_EXT:
        filename = os.path.splitext(filename)[0]

    scraped = {}
    working_name = filename

    # 1. Extract Studio (e.g., "(Studio).")
    # We look for the pattern at the very start
    studio_match = re.match(r"^\((?P<studio>.*?)\)\.", working_name)
    if studio_match:
        scraped["studio"] = {"name": studio_match.group("studio").strip()}
        working_name = working_name[studio_match.end():]

    # 2. Extract Date (YYYY-MM-DD)
    # We look for the date anywhere in the remaining string
    date_match = re.search(r"(?P<date>\d{4}-\d{2}-\d{2})", working_name)
    if date_match:
        scraped["date"] = date_match.group("date")
        # Remove the date and the dot following it if there is one
        start, end = date_match.span()
        # If there is a dot immediately after the date, remove it too
        if end < len(working_name) and working_name[end] == ".":
            end += 1
        # If there is a dot immediately before the date, remove it
        if start > 0 and working_name[start-1] == ".":
            start -= 1
            
        working_name = working_name[:start] + working_name[end:]

    # 3. Handle Tags (e.g., "[Tag1 Tag2]")
    if " [" in working_name:
        tag_start = working_name.rfind(" [")
        tag_content = working_name[tag_start + 2:].rstrip("]")
        t_names = re.split(r',|\s', tag_content)
        scraped["tags"] = [{"name": t.strip()} for t in t_names if t.strip()]
        working_name = working_name[:tag_start]

    # 4. Separate Performer and Title
    # Clean up any double dots left over from removing the date
    working_name = working_name.replace("..", ".").strip(".")
    
    if "." in working_name:
        # We split on the LAST dot to keep "Ep.841" together in the title
        parts = working_name.rsplit(".", 1)
        scraped["performers"] = [{"name": n.strip()} for n in re.split(r',|&', parts[0]) if n.strip()]
        scraped["title"] = parts[1].strip()
    else:
        # If no dot remains, the whole thing is the title
        scraped["title"] = working_name.strip()

    return scraped

if __name__ == "__main__":
    input_data = sys.stdin.read()
    if input_data:
        try:
            js = json.loads(input_data)
            if len(sys.argv) > 1 and sys.argv[1] == "scrape_filename":
                print(json.dumps(scrape_filename(js)))
        except Exception as e:
            log.error(f"Scraper error: {e}")