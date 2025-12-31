# ACM Group Project - Reddit Data Analysis

This project analyzes Reddit data from the r/PolitikBRD subreddit, with a focus on activity patterns around the 2024 European Championship (EURO 2024).

## Project Structure

```
ACM_group_project/
├── data/
│   ├── raw/              # Raw data files
│   │   ├── r_PolitikBRD_posts.jsonl      # Original JSONL export of Reddit posts
│   │   ├── r_PolitikBRD_comments.jsonl   # Original JSONL export of Reddit comments
│   │   ├── posts.parquet                 # Processed posts in Parquet format
│   │   └── comments.parquet              # Processed comments in Parquet format
│   └── clean/            # Cleaned/processed data (for future use)
├── scrape/               # Data processing scripts
│   ├── ingest_posts_jsonl.py    # Converts posts JSONL → Parquet
│   ├── ingest_comments_jsonl.py # Converts comments JSONL → Parquet
│   └── sanity_checks.py         # Data quality validation
├── notebooks/
│   └── exploration.ipynb        # Jupyter notebook for exploratory analysis
├── requirements.txt      # Python dependencies
└── README.md            # This file
```

## Setup

1. Create and activate a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

## Usage

### Data Ingestion

Convert JSONL files to Parquet format for efficient processing:

**Process posts:**
```bash
python scrape/ingest_posts_jsonl.py --in data/raw/r_PolitikBRD_posts.jsonl --out data/raw/posts.parquet
```

**Process comments:**
```bash
python scrape/ingest_comments_jsonl.py --in data/raw/r_PolitikBRD_comments.jsonl --out data/raw/comments.parquet
```

### Data Validation

Run sanity checks on the processed data:
```bash
python scrape/sanity_checks.py --posts data/raw/posts.parquet --comments data/raw/comments.parquet
```

This will display:
- Row counts for posts and comments
- Time ranges of the data
- Deleted/removed comment ratios
- Join coverage between posts and comments
- Daily counts

### Analysis

Open the Jupyter notebook for exploratory analysis:
```bash
jupyter notebook notebooks/exploration.ipynb
```

The notebook includes:
- Loading posts and comments from Parquet files
- Date/time processing
- Period categorization (pre-EURO, during EURO, post-EURO)
- EURO 2024 period: June 14 - July 14, 2024

## Data Processing Pipeline

1. **Raw Data**: JSONL files exported from Reddit (r/PolitikBRD)
2. **Ingestion**: Scripts convert JSONL → Parquet with normalization and deduplication
3. **Validation**: Sanity checks validate data quality
4. **Analysis**: Jupyter notebook for exploratory data analysis

## Key Features

- **Streaming Processing**: Handles large JSONL files efficiently with chunked processing
- **Data Normalization**: Standardizes field names across different export formats
- **Deduplication**: Removes duplicate entries based on IDs
- **Time-based Analysis**: Categorizes data into periods relative to EURO 2024

## Dependencies

- `praw>=7.7.0` - Reddit API wrapper
- `pandas>=1.5.0` - Data manipulation
- `python-dotenv>=0.21.0` - Environment variable management
- `jupyter>=1.0.0` - Interactive notebooks
- `matplotlib>=3.6.0` - Plotting
- `numpy>=1.23.0` - Numerical computing
- `pyarrow` - Parquet file support (installed as dependency)

## Notes

- The project focuses on analyzing r/PolitikBRD activity patterns around EURO 2024
- Data is categorized into three periods: pre-EURO, during EURO, and post-EURO
- Parquet format is used for efficient storage and fast loading of large datasets

