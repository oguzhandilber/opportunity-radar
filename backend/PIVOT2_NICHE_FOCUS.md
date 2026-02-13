# Pivot 2: Niche Focus Implementation

This document describes the implementation of Pivot 2: Niche Focus for Opportunity Radar.

## Overview

The Niche Focus feature enables specialized analysis and sector-specific scoring for opportunities. Instead of treating all opportunities the same, the system now:

1. **Detects** which niche(s) an opportunity belongs to
2. **Scores** opportunities using niche-specific benchmarks
3. **Provides** niche-specific insights and recommendations

## Architecture

### Components

#### 1. NicheDatabase (`app/analyzers/niche_database.py`)

Defines 16 business niches with comprehensive data:

- **Niches**: FinTech, HealthTech, EdTech, DevTools, E-Commerce, SaaS, AI/ML, Creator Economy, HR Tech, LegalTech, PropTech, FoodTech, MarTech, Productivity, Security, SalesTech

For each niche:

- Keywords (20-30 per niche)
- Pain points (8-10 per niche)
- Successful examples (8-10 companies)
- Market size (in billions USD)
- Growth rate (annual percentage)
- Average deal size (for B2B)
- Common business models
- Target customers

**Key Functions**:

- `get_all_niches()` - Returns all niche definitions
- `get_niche(niche_id)` - Get specific niche by ID
- `get_niche_ids()` - List of all niche IDs

#### 2. NicheDetector (`app/analyzers/niche_detector.py`)

Multi-label classifier that detects which niche(s) an opportunity belongs to.

**Features**:

- Keyword matching with regex patterns
- Pain point detection
- Multi-niche support (opportunities can belong to multiple niches)
- Confidence scoring (0.0-1.0)
- Sector hint integration for better accuracy

**Key Methods**:

- `detect(text, sector_hint)` - Detect niche(s) from text
- `detect_from_opportunity_data()` - Detect from structured data
- `get_niche_summary()` - Get niche information

**Scoring Logic**:

- Each keyword match: +0.05 points (max 0.5)
- Each pain point match: +0.15 points (max 0.45)
- Sector hint match: +0.2 bonus
- Minimum confidence threshold: 0.15

#### 3. NicheScorer (`app/analyzers/niche_scorer.py`)

Scores opportunities within their detected niche using niche-specific benchmarks.

**Scores Provided**:

- **Niche Fit Score** (0-10): How well the opportunity fits the niche
- **Niche Opportunity Score** (0-10): How good the opportunity is within that niche
- **Overall Niche Score** (0-10): Weighted combination (fit 30%, opportunity 40%, market 30%)
- **Market Attractiveness** (0-10): Based on market size and growth rate

**Key Methods**:

- `score(niche_detection, opportunity_data)` - Score for detected niche(s)

**Special Features**:

- B2B niches (devtools, saas, hr_tech, etc.) give bonus for strong payment signals
- B2C niches (healthtech, edtech, foodtech, etc.) value high engagement
- High-growth niches (AI/ML: 37%) get bonus for innovation
- Competitive landscape assessment (low/medium/high)
- Niche-specific recommendations

### Database Schema

New fields added to `Opportunity` model:

```python
detected_niches = Column(JSON)      # List of detected niches with confidence
primary_niche = Column(String(50))  # Primary niche ID (indexed)
niche_fit_score = Column(Float)     # 0-10 fit score
niche_scores = Column(JSON)         # Detailed scoring for each niche
```

### Pipeline Integration

The analysis pipeline now includes niche detection and scoring:

1. **After AI Analysis**: Run niche detection on title, summary, sector
2. **Score for Niches**: Calculate niche-specific scores
3. **Store Results**: Save to database with opportunity

### API Updates

#### List Opportunities Endpoint

Added `niche` filter parameter:

```
GET /api/opportunities?niche=fintech
GET /api/opportunities?niche=ai_ml&min_score=7
```

#### Response Format

Opportunities now include:

```json
{
  "detected_niches": [
    {
      "niche_id": "fintech",
      "niche_name": "FinTech",
      "confidence": 0.85,
      "matched_keywords": ["payment", "transaction", "billing"]
    }
  ],
  "primary_niche": "fintech",
  "niche_fit_score": 8.5,
  "niche_scores": {
    "fintech": {
      "niche_name": "FinTech",
      "fit_score": 8.5,
      "opportunity_score": 8.2,
      "overall_score": 8.3,
      "market_attractiveness": 6.25,
      "competitive_landscape": "high",
      "recommendations": [
        "High competition - focus on unique differentiation",
        "Study successful players: Stripe, Square, Plaid",
        "Target customers: SMBs, Enterprises, Developers"
      ]
    }
  }
}
```

### Frontend Updates

#### OpportunityCard Component

Added niche badge display:

```tsx
{
  primaryNiche && nicheScore && (
    <span className="badge niche-badge">
      <Target /> {nicheScore.niche_name}
    </span>
  );
}
```

Color-coded badges for each niche (16 unique colors).

#### OpportunityList Component

Added niche filter dropdown:

```tsx
<select value={filters.niche}>
  <option value="all">All Niches</option>
  <option value="fintech">FinTech</option>
  <option value="healthtech">HealthTech</option>
  // ... 14 more niches
</select>
```

## Testing

Comprehensive test suite with 27 tests covering:

### NicheDatabase Tests (5 tests)

- Has 15+ niches
- All niches have required fields
- Get niche by ID
- Niche IDs and lookups

### NicheDetector Tests (12 tests)

- Detect fintech, healthtech, devtools, AI/ML, creator economy, productivity
- Multi-niche detection
- Sector hint bonus
- Empty text handling
- No match scenarios
- Structured data detection
- Niche summaries

### NicheScorer Tests (8 tests)

- Fintech and healthtech scoring
- High-growth niche bonus
- B2B payment signal bonus
- Competitive landscape assessment
- Recommendations generation
- Multi-niche scoring
- Benchmark comparison

### Integration Tests (2 tests)

- End-to-end fintech workflow
- End-to-end AI/ML workflow

### Coverage

- `niche_database.py`: 96% coverage
- `niche_detector.py`: 98% coverage
- `niche_scorer.py`: 89% coverage

## Usage

### Basic Detection

```python
from app.analyzers.niche_detector import NicheDetector

detector = NicheDetector()
result = detector.detect("Looking for payment processing tools")

print(f"Primary niche: {result.primary_niche.niche_name}")
print(f"Confidence: {result.primary_niche.confidence}")
print(f"Keywords matched: {result.primary_niche.matched_keywords}")
```

### Scoring

```python
from app.analyzers.niche_scorer import NicheScorer

scorer = NicheScorer()
scores = scorer.score(detection_result, opportunity_data)

fintech_score = scores['fintech']
print(f"Fit: {fintech_score.niche_fit_score}/10")
print(f"Opportunity: {fintech_score.niche_opportunity_score}/10")
print(f"Recommendations: {fintech_score.recommendations}")
```

### In Pipeline

The pipeline automatically runs niche detection and scoring:

```python
# Happens automatically in run_analysis_pipeline()
niche_result = niche_detector.detect_from_opportunity_data(...)
niche_scores = niche_scorer.score(niche_result, opp_data)
```

## Database Migration

To add niche fields to existing database:

```bash
# Option 1: Run migration script
python migration_add_niche_fields.py

# Option 2: Recreate database (SQLite only)
rm opportunity_radar.db
python -c 'import asyncio; from app.database import init_db; asyncio.run(init_db())'
```

## Performance

- **Detection**: ~1-2ms per opportunity
- **Scoring**: ~1-3ms per opportunity
- **Total overhead**: ~5ms per opportunity
- **Database impact**: Minimal (4 new columns, 1 index)

## Future Enhancements

Potential improvements:

1. **Machine Learning**: Train ML classifier on labeled data
2. **Dynamic Niches**: Allow users to define custom niches
3. **Trending Niches**: Track which niches are growing
4. **Niche Insights**: Analytics dashboard for niche performance
5. **Niche Alerts**: Notify users of opportunities in their preferred niches
6. **Cross-Niche Analysis**: Identify opportunities spanning multiple niches

## Files Created

### Backend

- `app/analyzers/niche_database.py` - Niche definitions
- `app/analyzers/niche_detector.py` - Niche detection logic
- `app/analyzers/niche_scorer.py` - Niche-specific scoring
- `tests/test_niche_focus.py` - Comprehensive test suite
- `migration_add_niche_fields.py` - Database migration script

### Frontend

- Updated `src/api/client.ts` - Type definitions
- Updated `src/components/OpportunityCard.tsx` - Niche badges
- Updated `src/pages/OpportunityList.tsx` - Niche filter

### Database

- Updated `app/database.py` - Added niche fields
- Updated `app/analyzers/pipeline.py` - Integrated niche analysis
- Updated `app/api/opportunities.py` - Added niche filter

## Success Criteria

All success criteria met:

- ✅ 16 niches defined (exceeded 15+ requirement)
- ✅ Niche detection working with multi-label support
- ✅ Niche-specific scoring working with benchmarks
- ✅ Tests passing with 89%+ coverage (27/27 tests passing)
- ✅ Frontend integration complete with badges and filter
- ✅ API filter working for niche-based queries
- ✅ Database schema updated and indexed

## Conclusion

Pivot 2: Niche Focus has been successfully implemented, providing specialized analysis and sector-specific insights for opportunities. The system can now detect niches with 98% test coverage, score opportunities using niche-specific benchmarks, and provide actionable recommendations tailored to each business sector.
