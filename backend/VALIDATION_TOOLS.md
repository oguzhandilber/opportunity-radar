# Validation Tools Integration (Pivot 5)

## Overview

The Validation Tools framework provides a simulation-based system for tracking validation activities and estimating outcomes when testing opportunity hypotheses. Since real validation tool integrations require API access and external services, this implementation simulates what those integrations would provide.

## Features

### 1. Validation Toolkit

Defines 8 types of validation tools with their characteristics:

- Landing Page Test
- Email List Building
- Paid Ad Campaign
- Customer Survey
- MVP (Minimum Viable Product)
- Social Media Test
- Cold Outreach Campaign
- Pre-Launch Waitlist

Each tool includes:

- Setup steps
- Expected metrics
- Cost estimates (min/max)
- Time estimates
- Difficulty level
- Best use cases

### 2. Validation Simulator

Simulates validation results based on opportunity quality signals:

- Payment intent score (0-1)
- Success prediction (0-100)
- Niche fit score (0-10)

The simulator generates realistic metrics with variance, for example:

- Landing page: conversion rate, signups, bounce rate
- Ad campaign: CTR, CPC, conversions, CPA
- MVP: retention rates, conversion to paid

### 3. Validation Recommender

Recommends the best validation approach based on:

- Budget constraints (low/medium/high)
- Time available (short/medium/long)
- Risk tolerance (low/medium/high)
- Opportunity characteristics (payment intent, success prediction, product type)

Returns a prioritized validation plan with:

- Ordered validation steps
- Reasoning for each recommendation
- Expected outcomes
- Risk mitigation strategies
- Overall strategy description

### 4. Validation Tracker

Database model for tracking validation activities:

- Tool type and configuration
- Status (planned, in_progress, completed, failed)
- Results (manually entered or simulated)
- Timestamps

## API Endpoints

### List Available Tools

```
GET /api/validation-tools/tools
```

Returns all available validation tools with their characteristics.

### Get Specific Tool

```
GET /api/validation-tools/tools/{tool_type}
```

Get detailed information about a specific validation tool.

### Create Validation Tracker

```
POST /api/validation-tools/opportunities/{opportunity_id}/validation
{
  "tool_type": "landing_page",
  "config": {"traffic_volume": 1000},
  "notes": "Testing core value proposition"
}
```

### List Validation Trackers

```
GET /api/validation-tools/opportunities/{opportunity_id}/validation
```

Get all validation trackers for an opportunity.

### Simulate Validation

```
POST /api/validation-tools/opportunities/{opportunity_id}/validation/simulate
{
  "tool_type": "landing_page",
  "config": {"traffic_volume": 1000}
}
```

Run a simulation to estimate validation outcomes.

### Get Validation Recommendation

```
POST /api/validation-tools/opportunities/{opportunity_id}/validation/recommend
{
  "budget": "medium",
  "time_available": "medium",
  "risk_tolerance": "medium"
}
```

Get a recommended validation plan tailored to the opportunity.

### Update Tracker Results

```
PATCH /api/validation-tools/validation/{tracker_id}
{
  "status": "completed",
  "results": {
    "signups": 50,
    "conversion_rate": 2.5
  }
}
```

### Simulate Tracker Validation

```
POST /api/validation-tools/validation/{tracker_id}/simulate
```

Run simulation on an existing tracker and store simulated results.

## Usage Example

```python
# 1. Get recommendations for an opportunity
response = await client.post(
    "/api/validation-tools/opportunities/123/validation/recommend",
    json={
        "budget": "low",
        "time_available": "short",
        "risk_tolerance": "low"
    }
)
plan = response.json()["plan"]
# Returns: Social media test -> Landing page -> Email list

# 2. Create a tracker for the first recommended step
response = await client.post(
    "/api/validation-tools/opportunities/123/validation",
    json={
        "tool_type": "social_post",
        "config": {},
        "notes": "Testing on r/SaaS and r/startups"
    }
)
tracker_id = response.json()["id"]

# 3. Run simulation to estimate outcomes
response = await client.post(
    f"/api/validation-tools/validation/{tracker_id}/simulate"
)
simulated = response.json()["simulation"]
# Returns estimated engagement, reach, etc.

# 4. Record actual results after running the validation
response = await client.patch(
    f"/api/validation-tools/validation/{tracker_id}",
    json={
        "status": "completed",
        "results": {
            "views": 1200,
            "likes": 45,
            "comments": 12,
            "dms": 3
        }
    }
)
```

## Database Schema

### ValidationTracker Table

- `id`: Primary key
- `opportunity_id`: Foreign key to opportunities
- `tool_type`: Type of validation tool
- `status`: planned, in_progress, completed, failed
- `config`: JSON - tool-specific settings
- `results`: JSON - manually entered results
- `simulated_results`: JSON - simulation output
- `is_simulated`: 0 = real, 1 = simulated
- `notes`: Text notes
- Timestamps: created_at, updated_at, started_at, completed_at

## Simulation Accuracy

The simulator uses opportunity quality signals to estimate outcomes:

**High Quality Opportunity** (payment_intent=0.8, success_prediction=75):

- Landing page: 3-5% conversion rate
- Ad campaign: 2-4% CTR
- MVP: 50-70% day 1 retention

**Medium Quality Opportunity** (payment_intent=0.5, success_prediction=50):

- Landing page: 1.5-3% conversion rate
- Ad campaign: 1-2% CTR
- MVP: 30-50% day 1 retention

**Low Quality Opportunity** (payment_intent=0.2, success_prediction=30):

- Landing page: 0.5-1.5% conversion rate
- Ad campaign: 0.5-1% CTR
- MVP: 20-35% day 1 retention

Simulations include realistic variance (+/- 30%) to reflect real-world uncertainty.

## Testing

Run validation tools tests:

```bash
pytest tests/test_validation_tools.py -v
```

Coverage: 73%+ on validation modules

## Future Enhancements

1. Real integrations with validation platforms:
   - Carrd/Unicorn Platform for landing pages
   - ConvertKit/Mailchimp for email lists
   - Google Ads/Facebook Ads APIs

2. A/B test tracking and analysis

3. Validation experiment templates

4. Automatic metric collection

5. Machine learning model for better simulation accuracy based on historical data
