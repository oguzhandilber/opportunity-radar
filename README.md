# Opportunity Radar

A comprehensive application for discovering business opportunities from social media and trend platforms.

## Features

- **Multi-source Scraping**: Reddit, Hacker News, Google Trends, Product Hunt
- **AI-powered Analysis**: Automatic classification, scoring, and enrichment of opportunities
- **Dashboard**: Visual overview of discovered opportunities
- **Filtering**: Filter by status, sector, product type, and score
- **Detailed Views**: Full analysis including competitors, suggested features, and go-to-market strategies

## Tech Stack

- **Backend**: Python (FastAPI) + SQLite
- **Frontend**: React (Vite) + TypeScript + TailwindCSS
- **AI**: Claude API (with proxy support) / Gemini API

## Quick Start

### Prerequisites

- Docker and Docker Compose
- API keys for:
  - Anthropic Claude or Google Gemini
  - Reddit API (optional, for Reddit scraping)

### Setup

1. Clone and navigate to the project:

   ```bash
   cd opportunity-radar
   ```

2. Copy the environment file and add your API keys:

   ```bash
   cp .env.example .env
   # Edit .env with your API keys
   ```

3. Start the application:

   ```bash
   ./start.sh
   # Or manually:
   docker-compose up --build
   ```

4. Access the application:
   - Frontend: http://localhost:3000
   - Backend API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

## Development

### Backend Development

```bash
cd backend
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows
pip install -r requirements.txt
uvicorn app.main:app --reload
```

### Frontend Development

```bash
cd frontend
npm install
npm run dev
```

### Running Tests

```bash
# Backend tests
cd backend
pytest

# With coverage
pytest --cov=app --cov-report=html
```

## Project Structure

```
opportunity-radar/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI app entry
│   │   ├── config.py            # Settings
│   │   ├── database.py          # SQLAlchemy models
│   │   ├── scrapers/            # Data source scrapers
│   │   ├── analyzers/           # AI analysis pipeline
│   │   ├── api/                 # REST endpoints
│   │   └── scheduler/           # Background jobs
│   └── tests/
├── frontend/
│   ├── src/
│   │   ├── components/          # Reusable UI components
│   │   ├── pages/               # Page components
│   │   ├── hooks/               # React hooks
│   │   └── api/                 # API client
│   └── package.json
├── docker-compose.yml
├── .env.example
└── README.md
```

## API Endpoints

- `GET /health` - Health check
- `GET /api/dashboard/stats` - Dashboard statistics
- `GET /api/opportunities` - List opportunities (with filters)
- `GET /api/opportunities/{id}` - Get opportunity details
- `PATCH /api/opportunities/{id}` - Update opportunity status/notes
- `DELETE /api/opportunities/{id}` - Delete opportunity
- `POST /api/scrape/trigger` - Trigger manual scrape
- `GET /api/scrape/status` - Get scrape status
- `GET /api/settings` - List all settings
- `PUT /api/settings/{key}` - Set a setting

## Data Sources

| Platform      | Method       | Focus                                  |
| ------------- | ------------ | -------------------------------------- |
| Reddit        | PRAW API     | 20+ subreddits for ideas & pain points |
| Hacker News   | Algolia API  | Show HN, Ask HN, opportunity keywords  |
| Google Trends | pytrends     | Rising searches in US, UK, Turkey      |
| Product Hunt  | Web scraping | Daily trending products                |

## Scoring Dimensions

Each opportunity is scored on four dimensions (1-10):

1. **Demand Score**: Explicit requests, pain intensity, willingness to pay
2. **Market Score**: Market size, growth trend, competition level
3. **Feasibility Score**: Technical complexity, time to MVP, solo developer fit
4. **Revenue Score**: Monetization clarity, pricing benchmarks

## Production Deployment

### Using SQLite (Development/Small Scale)

```bash
# Build and start
docker-compose up --build

# Access at http://localhost:3000
```

### Using PostgreSQL (Production Recommended)

1. Create a `.env` file with PostgreSQL configuration:

```bash
DATABASE_TYPE=postgresql
POSTGRES_HOST=postgres
POSTGRES_PORT=5432
POSTGRES_USER=your_user
POSTGRES_PASSWORD=your_secure_password
POSTGRES_DB=opportunity_radar
API_KEY=your_secure_api_key
JWT_SECRET_KEY=generate_a_secure_key
```

2. Start with PostgreSQL:

```bash
docker-compose --profile production up -d postgres backend
```

### Generate Secure Keys

```bash
# Generate API key
python -c "import secrets; print(secrets.token_urlsafe(32))"

# Generate JWT secret
python -c "import secrets; print(secrets.token_urlsafe(48))"
```

## Environment Variables

| Variable             | Description                                             | Default      |
| -------------------- | ------------------------------------------------------- | ------------ |
| `DATABASE_TYPE`      | Database type: `sqlite` or `postgresql`                 | `sqlite`     |
| `AI_PROVIDER`        | AI provider: `openrouter`, `claude`, `gemini`, `ollama` | `openrouter` |
| `OPENROUTER_API_KEY` | OpenRouter API key (recommended for free tier)          | -            |
| `API_KEY`            | API key for protecting endpoints                        | -            |
| `JWT_SECRET_KEY`     | Secret key for JWT tokens                               | -            |

## License

MIT
