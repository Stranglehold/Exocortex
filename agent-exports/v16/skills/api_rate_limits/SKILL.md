---
name: api-rate-limits
description: This skill contains knowledge about Anthropic's Claude API rate limiting
  system.
---

# Anthropic API Rate Limits

## Overview
This skill contains knowledge about Anthropic's Claude API rate limiting system.

## Rate Limit Types

### 1. Requests Per Minute (RPM)
- Limits the number of API calls within a 60-second window
- Varies by tier and organization level

### 2. Tokens Per Minute (TPM) 
- Caps total tokens (input + output) processed per minute
- Most restrictive limit shown in response headers

### 3. Daily Token Quota
- Restricts total tokens processed per day
- Build tiers: 1 to 10 million tokens/day

## Tier System

| Tier Level | Description |
|------------|-------------|
| Build Tiers (1-4) | 1-10M tokens/day, auto-advancement based on spend |
| Higher Tiers | Enterprise/high-volume users with custom limits |

## Checking Your Limits

### Via API Response Headers:
```http
anthropic-ratelimit-tokens-*    # Most restrictive token limit in effect
anthropic-ratelimit-requests-*  # Request rate limits
```

### Via Console:
Navigate to: **Claude Console → Settings → Limits**

## Key Behaviors

- ✅ Tier automatically upgrades as account accumulates spend
- ⚠️ Build tiers can be restrictive (~5 maxed messages/day at lowest tier)
- 📈 Higher spend = higher rate limits through automatic advancement

## Official Documentation

- **Rate Limits**: https://platform.claude.com/docs/en/api/rate-limits
- **Approach to Rate Limits**: https://support.claude.com/en/articles/8243635-our-approach-to-rate-limits-for-the-claude-api

## Usage Example

```python
import anthropic

c = anthropic.Anthropic()
response = c.messages.create(
    model="claude-sonnet-4-20250514",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Hello"}]
)

# Check rate limit headers
print(response.headers.get('anthropic-ratelimit-tokens-limit'))
print(response.headers.get('anthropic-ratelimit-tokens-remaining'))
```

## Tags
api, anthropic, claude, rate-limits, tokens, rpm, tpm
