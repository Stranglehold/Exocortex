# Skill: API Caller

## Trigger
User asks to call an API, fetch data from a URL, make HTTP requests, or interact with web services. Keywords: "call API", "fetch from URL", "make HTTP request", "GET/POST request", "API endpoint", "webhook", "REST API", "GraphQL query".

## Inputs Required
- **HTTP method** — GET, POST, PUT, DELETE, PATCH (default: GET)
- **URL or endpoint** — full URL or relative path with base URL context
- **Headers** — Content-Type, Authorization, custom headers if needed
- **Query parameters** — for GET requests (dict format)
- **Request body** — JSON payload for POST/PUT/PATCH requests
- **Authentication details** — API key, Bearer token, OAuth credentials if required
- **Expected response format** — JSON, text, binary, or unknown

## Procedure

### Phase 1: Construct the Request
Build the HTTP request with proper structure and error handling.

1. **Import requests library:**
   ```python
   import requests
   from requests.exceptions import Timeout, ConnectionError, HTTPError, RequestException
   ```

2. **Set up base configuration:**
   ```python
   BASE_URL = "https://api.example.com"  # Replace with actual base URL
   ENDPOINT = "/v1/resource"
   TIMEOUT = 30  # seconds - adjust based on API expectations
   ```

3. **Build headers dictionary:**
   ```python
   headers = {
       "Content-Type": "application/json",
       "Accept": "application/json",
       # Add custom headers as needed
   }

   # Add authentication if required
   if api_key:
       headers["Authorization"] = f"Bearer {api_key}"
   elif username and password:
       # For basic auth, use requests built-in or header
       pass
   ```

4. **Prepare request parameters:**
   ```python
   params = None  # For GET query parameters
   data = None    # For POST/PUT/PATCH body (will be JSON serialized)

   if method == "GET" and query_params:
       params = query_params
   elif method in ["POST", "PUT", "PATCH"] and request_body:
       data = request_body  # requests will serialize to JSON if json=data is used
   ```

### Phase 2: Execute the Request with Error Handling
Make the HTTP call with comprehensive error handling.

1. **Use try/except for all exception types:**
   ```python
   url = f"{BASE_URL}{ENDPOINT}"

   try:
       response = requests.request(
           method=method,
           url=url,
           headers=headers,
           params=params,
           json=data if data else None,  # Use json= for automatic serialization
           timeout=TIMEOUT,
           verify=True  # Set to False only for self-signed certs (not recommended)
       )
   except Timeout:
       print(f"[API] Request timed out after {TIMEOUT}s")
       return None, "timeout"
   except ConnectionError as e:
       print(f"[API] Connection error: {e}")
       return None, "connection_error"
   except RequestException as e:
       print(f"[API] Request failed: {type(e).__name__}: {e}")
       return None, f"request_error_{type(e).__name__.lower()}"
   ```

2. **Check HTTP status codes:**
   ```python
   try:
       response.raise_for_status()  # Raises HTTPError for 4xx/5xx responses
   except HTTPError as e:
       status_code = e.response.status_code

       if 400 <= status_code < 500:
           print(f"[API] Client error {status_code}: {e.response.text[:200]}")
           return None, f"client_error_{status_code}"
       elif 500 <= status_code < 600:
           print(f"[API] Server error {status_code}: {e.response.text[:200]}")
           return None, f"server_error_{status_code}"
   ```

### Phase 3: Parse and Validate Response
Extract data from response with validation.

1. **Parse JSON response:**
   ```python
   try:
       if response.headers.get("Content-Type", "").startswith("application/json"):
           data = response.json()
       else:
           data = response.text
   except ValueError as e:
       print(f"[API] Failed to parse JSON: {e}")
       return None, "parse_error"
   ```

2. **Validate response structure:**
   ```python
   # Check for expected fields or error indicators
   if isinstance(data, dict):
       if "error" in data or "errors" in data:
           print(f"[API] API returned error: {data['error']}")
           return None, "api_error"

       # Validate required fields exist
       required_fields = ["id", "name"]  # Adjust based on expected response
       missing = [field for field in required_fields if field not in data]
       if missing:
           print(f"[API] Missing expected fields: {missing}")
   ```

3. **Handle pagination if applicable:**
   ```python
   # Check for pagination metadata
   if isinstance(data, dict) and "data" in data and "pagination" in data:
       items = data["data"]
       page = data["pagination"].get("page", 1)
       total_pages = data["pagination"].get("total_pages")

       if page < total_pages:
           print(f"[API] More pages available ({page}/{total_pages})")
   ```

### Phase 4: Handle Rate Limiting and Retries
Implement retry logic for transient failures.

1. **Check rate limit headers:**
   ```python
   remaining = response.headers.get("X-RateLimit-Remaining")
   reset_time = response.headers.get("X-RateLimit-Reset")

   if remaining == "0":
       print(f"[API] Rate limit exceeded. Reset at: {reset_time}")
       return None, "rate_limited"
   ```

2. **Implement exponential backoff for retries:**
   ```python
   import time
   from tenacity import retry, stop_after_attempt, wait_exponential

   @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=2, max=10))
   def make_request_with_retry():
       return requests.request(
           method=method,
           url=url,
           headers=headers,
           params=params,
           json=data if data else None,
           timeout=TIMEOUT
       )

   try:
       response = make_request_with_retry()
   except Exception as e:
       print(f"[API] Max retries exceeded: {e}")
       return None, "max_retries_exceeded"
   ```

### Phase 5: Return Results and Metadata
Provide structured output with success/failure status.

1. **Return tuple with result and metadata:**
   ```python
   result = {
       "success": True,
       "status_code": response.status_code,
       "data": data,
       "headers": dict(response.headers),
       "elapsed_time": response.elapsed.total_seconds()
   }

   return result, None  # (result, error_type)
   ```

2. **For errors, return structured failure:**
   ```python
   result = {
       "success": False,
       "status_code": getattr(response, "status_code", None),
       "error_type": error_type,
       "error_message": str(e) if 'e' in locals() else "Unknown error"
   }

   return result, error_type
   ```

## Key Patterns

### GET with Query Parameters
```python
response = requests.get(
    "https://api.example.com/v1/users",
    headers={"Authorization": f"Bearer {token}"},
    params={"page": 1, "limit": 20, "status": "active"}
)
data = response.json()
```

### POST with JSON Body
```python
response = requests.post(
    "https://api.example.com/v1/users",
    headers={
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    },
    json={
        "name": "John Doe",
        "email": "john@example.com",
        "role": "user"
    }
)
data = response.json()
```

### Authentication with API Key Header
```python
headers = {
    "X-API-Key": api_key,
    "Content-Type": "application/json"
}
response = requests.post(url, headers=headers, json=payload)
```

### Basic Auth
```python
from requests.auth import HTTPBasicAuth

response = requests.get(
    url,
    auth=HTTPBasicAuth(username, password),
    headers={"Accept": "application/json"}
)
```

## Error Handling Guidance

### Connection Timeouts (408, 504)
- **Cause:** Server didn't respond within timeout period
- **Action:** Increase timeout or implement retry with exponential backoff
- **Retry strategy:** Wait 2s, 4s, 8s before retrying (max 3 attempts)

### Client Errors (4xx)
- **400 Bad Request:** Invalid parameters, malformed JSON
  - Action: Validate input data structure and required fields
- **401 Unauthorized:** Missing or invalid authentication
  - Action: Verify API key/token validity and expiration
- **403 Forbidden:** Valid auth but insufficient permissions
  - Action: Check user roles and resource access rights
- **404 Not Found:** Resource doesn't exist
  - Action: Verify URL path and resource ID correctness
- **429 Too Many Requests:** Rate limit exceeded
  - Action: Implement rate limiting, check X-RateLimit headers

### Server Errors (5xx)
- **500 Internal Server Error:** Generic server failure
  - Action: Retry with exponential backoff, may be transient
- **502 Bad Gateway:** Upstream service failed
  - Action: Retry after brief delay, check upstream status
- **503 Service Unavailable:** Maintenance or overload
  - Action: Check retry-after header if present, wait and retry
- **504 Gateway Timeout:** Upstream timeout
  - Action: Increase client timeout or implement async polling

### Rate Limiting Best Practices
1. Always check `X-RateLimit-*` headers in responses
2. Implement token bucket or sliding window rate limiting on client side
3. Respect `Retry-After` header when present (429 responses)
4. Cache GET requests when appropriate to reduce API calls
5. Batch operations when API supports bulk endpoints

## Quality Checks
- [ ] Always use `timeout` parameter — never make unbounded HTTP requests
- [ ] Use `json=` parameter instead of manually serializing with `data=json.dumps()`
- [ ] Check response status code before parsing body
- [ ] Validate JSON structure against expected schema when possible
- [ ] Log full error context: method, URL, status_code, error_type
- [ ] Implement retry logic for transient errors (5xx, 429)
- [ ] Never expose secrets in logs — mask API keys and tokens
- [ ] Use environment variables or secret management for credentials
- [ ] Verify SSL certificates (`verify=True`) unless explicitly disabled for testing
- [ ] Handle both `response.json()` success and failure cases

## Anti-Patterns
- **Making requests without timeout.** Unbounded requests can hang indefinitely, blocking execution.
- **Ignoring HTTP status codes.** Always check `raise_for_status()` or manually verify status before parsing body.
- **Using `data=json.dumps()` instead of `json=` parameter.** The `json=` parameter handles serialization and sets Content-Type automatically.
- **Catching all exceptions with bare `except:`.** Catch specific exception types to handle different failure modes appropriately.
- **Hardcoding API keys in code.** Use environment variables, secret management, or Agent Zero secrets system.
- **Not implementing retry logic for transient errors.** 5xx and 429 responses often resolve on retry.
- **Assuming response structure.** Always validate expected fields exist before accessing them.
- **Making sequential requests without rate limiting.** Implement client-side rate limiting to avoid triggering API limits.
- **Logging sensitive data.** Never log full request/response bodies that may contain secrets or PII.
- **Using `verify=False` in production.** Disabling SSL verification exposes you to man-in-the-middle attacks.
