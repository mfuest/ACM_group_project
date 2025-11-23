# Political Polarization Research Pipeline

A research pipeline for measuring changes in political polarization in Reddit data before, during, and after EURO 2024, comparing Germany (host country) with the Netherlands and France (control countries).

## Project Structure

```
ACM_group_project/
├── data/
│   ├── raw/              # Raw scraped Reddit posts
│   └── clean/            # Filtered and cleaned datasets
├── scripts/
│   └── reddit_scraper.py # Reddit data collection script
├── notebooks/
│   └── preprocessing.ipynb # Data cleaning and preprocessing notebook
├── config/               # Configuration files (optional)
├── .env                  # Environment variables (create from .env.example)
├── .env.example          # Example environment variables template
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Reddit API Setup

1. Go to https://www.reddit.com/prefs/apps
2. Click "create another app" or "create app"
3. Fill in:
   - **Name**: PoliticalPolarizationResearch (or any name)
   - **Type**: script
   - **Description**: Research project
   - **Redirect URI**: http://localhost:8080 (or any valid URL)
4. Note your **Client ID** (under the app name) and **Client Secret**
5. Create a `.env` file in the project root:

```bash
cp .env.example .env
```

6. Edit `.env` and add your credentials:

```
REDDIT_CLIENT_ID=your_client_id_here
REDDIT_CLIENT_SECRET=your_client_secret_here
REDDIT_USER_AGENT=PoliticalPolarizationResearch/1.0
```

## Usage

### Step 1: Scrape Reddit Data

Run the scraper to collect posts from r/de, r/thenetherlands, and r/france:

```bash
python scripts/reddit_scraper.py
```

This will:
- Fetch posts from three time windows:
  - **Pre-EURO**: 2024-05-15 to 2024-06-13
  - **During EURO**: 2024-06-14 to 2024-07-14
  - **Post-EURO**: 2024-07-15 to 2024-08-15
- Save raw posts to `data/raw/{country}_{phase}.csv`
- Filter political posts and save to `data/clean/{country}_{phase}_politics.csv`

### Step 2: Preprocess Data

Open and run the Jupyter notebook:

```bash
jupyter notebook notebooks/preprocessing.ipynb
```

The notebook will:
1. Load all scraped CSV files
2. Merge into a single DataFrame
3. Clean text (lowercase, remove URLs)
4. Create `full_text` column (title + selftext)
5. Mark political posts
6. Export final cleaned dataset to `data/clean/all_countries_clean.csv`

## Data Collection Details

### Subreddits
- **Germany**: r/de
- **Netherlands**: r/thenetherlands
- **France**: r/france

### Political Keywords

**German**: afd, cdu, spd, csu, gruene, grüne, linke, merz, scholz, habeck, migration, flüchtlinge, asyl, klima, heizungsgesetz, bundestag, ampel

**Dutch**: vvd, d66, pvv, wilders, rutte, klimaat, immigratie, verkiezingen, kabinet

**French**: macron, rn, mélenchon, melenchon, immigration, climat, gouvernement, élection, election, assemblée, assemblee

### Time Windows

- **Pre-EURO**: May 15 - June 13, 2024
- **During EURO**: June 14 - July 14, 2024
- **Post-EURO**: July 15 - August 15, 2024

## Output Files

### Raw Data (`data/raw/`)
- `{country}_{phase}.csv` - All posts for each country/phase combination

### Clean Data (`data/clean/`)
- `{country}_{phase}_politics.csv` - Filtered political posts
- `all_countries_clean.csv` - Final unified dataset with all preprocessing

## Notes

- The Reddit API has rate limits. The script includes delays to be respectful.
- Reddit's API doesn't support direct date filtering, so the script fetches recent posts and filters by date.
- Some posts may be missed if they're not in the "new" or "top" feeds.
- Make sure to respect Reddit's API terms of service and rate limits.

## Dependencies

- `praw` - Python Reddit API Wrapper
- `pandas` - Data manipulation
- `python-dotenv` - Environment variable management
- `jupyter` - For running notebooks
- `matplotlib` - For visualizations (optional, in notebook)

## License

This project is for academic research purposes.

