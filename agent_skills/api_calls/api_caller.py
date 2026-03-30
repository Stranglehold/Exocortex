#!/usr/bin/env python3
import requests
import json
import sys
from typing import Dict, Any, Optional

def make_api_call(
    url: str,
    method: str = "GET",
    headers: Optional[Dict[str, str]] = None,
    params: Optional[Dict[str, str]] = None,
    json_data: Optional[Dict[str, Any]] = None,
    timeout: int = 30
) -> Dict[str, Any]:
    """
    Make an HTTP request and return structured response.

    Args:
        url: Target endpoint URL
        method: HTTP method (GET, POST, PUT, DELETE)
        headers: Request headers dictionary
        params: Query parameters for GET requests
        json_data: JSON payload for POST/PUT requests
        timeout: Request timeout in seconds

    Returns:
        Dictionary with status_code, success, response_body, error_message
    """
    try:
        response = requests.request(
            method=method.upper(),
            url=url,
            headers=headers or {},
            params=params,
            json=json_data,
            timeout=timeout
        )

        result = {
            "status_code": response.status_code,
            "success": 200 <= response.status_code < 300,
            "response_body": None,
            "error_message": None
        }

        try:
            result["response_body"] = response.json()
        except json.JSONDecodeError:
            result["response_body"] = response.text

        if not result["success"]:
            result["error_message"] = f"HTTP {response.status_code}: {response.reason}"

        return result

    except requests.exceptions.Timeout:
        return {
            "status_code": None,
            "success": False,
            "response_body": None,
            "error_message": "Request timed out after {} seconds".format(timeout)
        }
    except requests.exceptions.ConnectionError as e:
        return {
            "status_code": None,
            "success": False,
            "response_body": None,
            "error_message": f"Connection error: {str(e)}"
        }
    except Exception as e:
        return {
            "status_code": None,
            "success": False,
            "response_body": None,
            "error_message": f"Unexpected error: {str(e)}"
        }

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: api_caller.py URL [METHOD] [headers_json] [params_json] [json_data]")
        sys.exit(1)

    url = sys.argv[1]
    method = sys.argv[2] if len(sys.argv) > 2 else "GET"
    headers = json.loads(sys.argv[3]) if len(sys.argv) > 3 and sys.argv[3] != "{}" else None
    params = json.loads(sys.argv[4]) if len(sys.argv) > 4 and sys.argv[4] != "{}" else None
    json_data = json.loads(sys.argv[5]) if len(sys.argv) > 5 and sys.argv[5] != "{}" else None

    result = make_api_call(url, method, headers, params, json_data)
    print(json.dumps(result, indent=2))
