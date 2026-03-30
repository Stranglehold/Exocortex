---
name: "api_calls"
description: "Make HTTP requests (GET, POST, PUT, DELETE) to external APIs with error handling and response parsing. Use when users need to interact with web services, fetch data from endpoints, or send API requests."
version: "1.0.0"
author: "agent"
tags: ["api", "http", "requests", "networking", "web"]
trigger_patterns:
  - "make api call"
  - "fetch from endpoint"
  - "call web service"
  - "get data from url"
  - "post to api"
---
# API Calls Skill

## Purpose
Enables the agent to make HTTP requests (GET, POST, PUT, DELETE) to external APIs and web services with proper error handling, response parsing, timeout management, and retry logic.

## When to Use
- User wants to fetch data from a URL or API endpoint
- Need to send POST/PUT requests with JSON payloads
- Making calls to REST APIs, GraphQL endpoints, or webhooks
- Fetching real-time data (weather, prices, news, etc.)
- Interacting with third-party services

## Instructions

### Step 1: Import the API Caller Module
```python
from api_caller import APICaller
client = APICaller(timeout=30, max_retries=3)
```

### Step 2: Make HTTP Requests

**GET Request:**
```python
response = client.get(
    url="https://api.example.com/data",
    params={"key": "value"},  # Query parameters
    headers={"Authorization": "Bearer token"}
)
data = response.json()  # Parse JSON response
```

**POST Request:**
```python
response = client.post(
    url="https://api.example.com/submit",
    json={"field1": "value1", "field2": 123},  # JSON body
    headers={"Content-Type": "application/json"}
)
result = response.json()
```

**PUT Request:**
```python
response = client.put(
    url="https://api.example.com/resource/123",
    json={"updated_field": "new_value"}
)
```

**DELETE Request:**
```python
response = client.delete(url="https://api.example.com/resource/123")
```

### Step 3: Handle Responses
```python
if response.status_code == 200:
    data = response.json()
    print(f"Success: {data}")
elif response.status_code == 401:
    print("Authentication failed")
elif response.status_code == 429:
    print("Rate limited - waiting...")
else:
    print(f"Error {response.status_code}: {response.text}")
```

### Step 4: Error Handling
```python
try:
    response = client.get(url, timeout=10)
    response.raise_for_status()  # Raises exception for 4xx/5xx status codes
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.ConnectionError:
    print("Connection failed")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
```

## Output Format
After making API calls, provide:
1. **Endpoint**: The URL that was called
2. **Method**: HTTP method used (GET/POST/PUT/DELETE)
3. **Status Code**: Response status code
4. **Response Data**: Parsed JSON or text content
5. **Error Details**: If request failed, explain why and suggest fixes

## Example Usage Patterns

### Fetching Weather Data
```python
response = client.get(
    "https://api.openweathermap.org/data/2.5/weather",
    params={"q": "London", "appid": "your_api_key"}
)
weather = response.json()
print(f"Temperature: {weather['main']['temp']}K")
```

### Posting to a Webhook
```python
response = client.post(
    "https://hooks.slack.com/services/xxx",
    json={"text": "Alert message here"}
)
print(f"Webhook status: {response.status_code}")
```

### Paginated API Calls
```python
all_data = []
page = 1
while True:
    response = client.get(url, params={"page": page})
    data = response.json()
    all_data.extend(data["items"])
    if not data.get("has_more"):
        break
    page += 1
```

## Notes
- Always use `response.json()` for JSON APIs, `response.text` for plain text
- Set appropriate timeouts based on expected response times
- Handle rate limiting (429 status) with exponential backoff
- Store API keys in environment variables, never hardcode them
- Use session objects for multiple requests to same endpoint
