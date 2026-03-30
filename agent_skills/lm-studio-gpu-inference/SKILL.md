---
name: "lm-studio-gpu-inference"
description: "Core skill for leveraging local GPU processing via LM Studio. Enables chat completions, model listing, and embedding generation through the OpenAI-compatible API at http://host.docker.internal:1234/v1. Use when projects need GPU-accelerated LLM inference or to run programs like OpenPlanter inside the container."
version: "1.0.0"
author: "agent"
tags: ["gpu", "llm", "inference", "lm-studio", "local"]
trigger_patterns:
  - "use lm studio"
  - "local gpu inference"
  - "call local llm"
  - "run on host gpu"
  - "openplanter mode"
---
# LM Studio GPU Inference Skill

## Purpose
Provides a unified interface for leveraging the host machine's GPU processing power through LM Studio's OpenAI-compatible API. This skill enables:
- Chat completions using locally-hosted models
- Listing available models on the host
- Embedding generation (if supported by the model)
- Running GPU-intensive programs like OpenPlanter from within the container

## When to Use
Load this skill when:
1. A project requires GPU-accelerated LLM inference
2. You need to call local models instead of cloud APIs
3. Building tools that require repeated LLM calls (e.g., OpenPlanter, code generation pipelines)
4. Cost-sensitive operations where free local inference is preferred
5. Privacy-sensitive tasks requiring data to stay on-host

## Instructions

### 1. Configuration
The skill uses these defaults:
- **Base URL**: `http://host.docker.internal:1234/v1`
- **Default Model**: check active model with `list_models()` below — model name changes with LM Studio load. Do not hardcode.
- **Timeout**: 120 seconds
- **Max Tokens**: 8192 (adjustable)

### 2. Available Operations

#### List Models
```python
import requests
response = requests.get("http://host.docker.internal:1234/v1/models")
available_models = response.json()["data"]
```

#### Chat Completion
```python
from openai import OpenAI
client = OpenAI(
    base_url="http://host.docker.internal:1234/v1",
    api_key="not-needed"
)
response = client.chat.completions.create(
    model=MODEL_NAME  # get from list_models() — do not hardcode,
    messages=[{"role": "user", "content": "Your prompt here"}],
    temperature=0.7,
    max_tokens=8192
)
print(response.choices[0].message.content)
```

#### Streaming Chat Completion
```python
for chunk in client.chat.completions.create(
    model=MODEL_NAME  # get from list_models() — do not hardcode,
    messages=[{"role": "user", "content": "Your prompt"}],
    stream=True
):
    if chunk.choices[0].delta.content:
        print(chunk.choices[0].delta.content, end="")
```

#### Embedding Generation (if model supports it)
```python
response = client.embeddings.create(
    model="your-embedding-model",
    input=["text to embed"]
)
embeddings = response.data[0].embedding
```

### 3. Error Handling
- **Model Unloaded**: LM Studio may unload models from memory. Re-trigger inference or send a warm-up request.
- **Context Window Exceeded**: Reduce prompt length or use `max_tokens` parameter
- **Connection Errors**: Verify LM Studio is running on port 1234

### 4. For OpenPlanter-style Programs
When building programs that require multiple LLM calls:
1. Initialize the OpenAI client once at startup
2. Reuse the client across requests (connection pooling)
3. Use streaming for better memory efficiency
4. Implement retry logic with exponential backoff
5. Monitor token usage to stay within context limits

## Output Format
- **Chat responses**: Plain text or JSON depending on prompt
- **Model list**: Array of model objects with `id`, `object`, `owned_by`
- **Embeddings**: Float arrays (dimension varies by model)

## Example Triggers
- "Run OpenPlanter using local GPU"
- "Make a chat completion request to LM Studio"
- "List available models on the host"
- "Generate embeddings using the local model"
