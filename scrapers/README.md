# DedTV Stash Scrapers Collection

A suite of scrapers for [Stash](https://github.com/stashapp/stash).

#### NOTE: These scrapers are mostly AI generated for use with the latest Development version of Stash. They have not been fully tested and may not function on the latest Stable version or future Dev versions. **Use at your own risk!**

### Manual Installation

1. Download the desired scraper folder from this repository.
2. Place the folder inside your Stash `scrapers/` directory.
3. Go to Stash **Settings > Metadata Providers** and click **Reload Scrapers**.

### Repository Installation

Add the following URL to your Stash Plugin Repositories to receive updates and install via the UI:
`https://dedtv.github.io/DedTV-Stash/index.yml`


## ⚠️ Important Notes

* **Renaming Safety:** After running the **Filename ASCII Cleaner**, you must run a **Scan** in Stash to update the database with the new file paths.
* **FFmpeg Paths:** Ensure you edit the `FFMPEG_PATH` and `FFPROBE_PATH` variables in `video_sampler.py` to match your local installation.
