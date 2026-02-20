# Market Radar CLI

HeadHunter vacancies fetcher — CLI tool to search and export HH.ru vacancies to CSV.

## Requirements

- Python 3.11+
- pip

## Installation

```bash
# Option 1: Install dependencies only
pip install -r requirements.txt

# Option 2: Install as package (recommended)
pip install -e .
```

## Usage

```bash
# After pip install -e . (available system-wide)
market-radar

# Or run as module (from project directory)
python -m market_radar_cli
```

### Examples

```bash
# Default: fetch 30 "python backend" vacancies from Russia
market-radar

# Custom query, limit, and area
market-radar --query "python backend" --limit 30 --area 113

# Short form
market-radar -q "data scientist" -l 50 -a 1
```

### CLI Arguments

| Argument | Short | Default | Description |
|----------|-------|---------|-------------|
| `--query` | `-q` | `python backend` | Search query text |
| `--limit` | `-l` | `30` | Number of vacancies to fetch |
| `--area` | `-a` | `113` | Area ID (113 = Russia, 1 = Moscow) |

### Output

Creates a CSV file: `vacancies_<yyyy-mm-dd>_<query-slug>.csv`

Example: `vacancies_2026-02-20_python-backend.csv`

**CSV columns:** `id`, `title`, `description`, `key_skills`

- `id` — HH vacancy ID
- `title` — Vacancy title/name
- `description` — Vacancy description (HTML cleaned to plain text)
- `key_skills` — Key skills from the vacancy (semicolon-separated, empty if not specified by employer)

**Example output (first 3 lines):**
```csv
id,title,description,key_skills
130622182,Backend Developer (Python),"АО САПРО — это компания, занимающаяся разработкой...","Python; Django; PostgreSQL; Git"
130540433,Стажер Backend Developer (Python / DRF),"We are looking for a Python developer...","Python; FastAPI; Docker"
```

## Project Structure

```
market_radar/
├── src/market_radar_cli/
│   ├── __init__.py       # Package metadata
│   ├── __main__.py       # Entry point for -m invocation
│   ├── main.py           # CLI argument parsing
│   └── hh_client.py      # HH API client + CSV export
├── requirements.txt
├── pyproject.toml
└── README.md
```

## Notes

- Uses HH public API (anonymous access, no authentication required)
- Includes retry logic for network errors (3 attempts with exponential backoff)
- HTML descriptions are cleaned to plain text using BeautifulSoup
- Rate limiting: 0.5s delay between pages
