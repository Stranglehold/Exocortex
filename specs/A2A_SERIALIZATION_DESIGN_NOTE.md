# A2A SERIALIZATION LAYER — Design Note (Future Reference)
## Author: Opus — May 9, 2026
## Status: DEFERRED — revisit when A2A layer build begins
## Trigger: Jake raised protobuf for serialization; assessed against current stack

---

## Context

A developer Jake consulted recommended protobuf for serialization layers. Assessment: protobuf provides 3-10x faster parsing and 3-7x smaller payloads than JSON, but the benefit is location-dependent. In the current Exocortex stack, the bottleneck is LLM inference (seconds), not serialization (microseconds). JSON remains correct for all current data paths.

**The one place protobuf matters: inter-agent communication.**

When the A2A layer is built (multi-agent coordination, cross-container delegation, Solace integration, Eitan as a separate service), the inter-agent protocol becomes a real throughput concern. gRPC + protobuf is the correct choice for that layer.

---

## Why gRPC + Protobuf for A2A

| Requirement | JSON/REST | gRPC/Protobuf | Winner |
|------------|-----------|---------------|--------|
| Schema enforcement (catch malformed messages at compile time) | Runtime validation only | Compile-time type checking via .proto | Protobuf |
| Bidirectional streaming (agents send partial results while working) | Requires WebSocket bolt-on | Native HTTP/2 bidirectional streams | gRPC |
| Multiplexing (multiple agent conversations on one connection) | One request per connection (HTTP/1.1) | Multiple concurrent streams (HTTP/2) | gRPC |
| Payload size (large context windows between agents) | 3-7x larger | 3-7x smaller | Protobuf |
| Human readability for debugging | ✅ Readable | ❌ Binary | JSON |
| Ecosystem compatibility (MCP, OpenAI API) | ✅ Native | ❌ Requires translation | JSON |

**Decision: gRPC + protobuf for agent-to-agent. JSON for agent-to-human and agent-to-inference-server.**

The boundary is clear: anything that crosses the human-readable threshold (journals, configs, API calls, MCP) stays JSON. Anything that's purely machine-to-machine (agent delegation, context transfer, task coordination) uses protobuf.

---

## Sketch: A2A Proto Schema

```protobuf
syntax = "proto3";

package exocortex.a2a;

// Core message between agents
message AgentMessage {
  string sender_id = 1;         // e.g., "opus", "kestrel", "eitan"
  string recipient_id = 2;
  MessageType type = 3;
  int64 timestamp_ms = 4;
  string session_id = 5;
  
  oneof payload {
    TaskDelegation delegation = 10;
    TaskResult result = 11;
    ContextTransfer context = 12;
    StatusUpdate status = 13;
    KnowledgeShare knowledge = 14;
  }
}

enum MessageType {
  DELEGATION = 0;
  RESULT = 1;
  CONTEXT_TRANSFER = 2;
  STATUS = 3;
  KNOWLEDGE_SHARE = 4;
}

// Parent → subordinate task delegation
message TaskDelegation {
  string objective = 1;
  string acceptance_criteria = 2;
  int32 step_budget = 3;
  repeated string context_docs = 4;  // Paths or compressed content
  string injection_profile = 5;      // DEC-028: "full" or "subordinate"
}

// Subordinate → parent result
message TaskResult {
  string summary = 1;               // Compressed result (~200 chars)
  bytes full_output = 2;            // Complete output if needed
  ResultStatus status = 3;
  int32 steps_used = 4;
  repeated MemorySave memories = 5; // Memories generated during task
}

enum ResultStatus {
  COMPLETE = 0;
  PARTIAL = 1;
  FAILED = 2;
  OVERFLOW = 3;                     // Context overflow (ST-013 Test D)
}

// Compressed context transfer between agents
message ContextTransfer {
  repeated TurnSummary turn_summaries = 1;
  repeated string active_memories = 2;
  string bst_domain = 3;
  string bst_compound = 4;
  int32 context_tokens_used = 5;
}

message TurnSummary {
  int32 turn_number = 1;
  string objective = 2;
  string result_preview = 3;
  int64 timestamp_ms = 4;
  int32 steps_used = 5;
}

message MemorySave {
  string text = 1;
  string area = 2;
  float importance = 3;
}

// Cross-agent knowledge sharing (idle-time findings, field reports)
message KnowledgeShare {
  string topic = 1;
  string insight = 2;
  string source_document = 3;       // Path to field report or wiki page
  repeated string cross_links = 4;  // Interest domains this connects to
}

// Service definition
service ExocortexAgent {
  rpc Delegate(TaskDelegation) returns (TaskResult);
  rpc StreamProgress(TaskDelegation) returns (stream StatusUpdate);
  rpc ShareKnowledge(KnowledgeShare) returns (Acknowledgment);
  rpc TransferContext(ContextTransfer) returns (Acknowledgment);
}

message StatusUpdate {
  int32 step = 1;
  int32 budget = 2;
  string current_action = 3;
  ResultStatus status = 4;
}

message Acknowledgment {
  bool received = 1;
  string message = 2;
}
```

---

## Also Noted: TOON (Token-Oriented Object Notation)

A February 2026 paper proposes TOON as a replacement for JSON specifically for LLM-generated structured output. TOON reduces token usage by replacing JSON's syntax overhead (braces, quotes, colons, field names) with a more token-efficient notation. The model generates fewer tokens to express the same structured data.

This operates at a different layer than protobuf — it optimizes the LLM generation boundary, not the network serialization boundary. Worth evaluating separately for reducing the token cost of tool calls and structured agent output.

**Paper:** arxiv.org/abs/2603.03306

---

## When to Revisit This Note

- When the A2A server build begins (currently dormant in `Exocortex/a2a_server/`)
- When cross-project integration with David Flagg's Solace is implemented
- When multi-container agent coordination becomes a primary workload
- When Eitan is deployed as a separate service rather than a role in the same conversation

---

## Dependencies

- Python: `grpcio`, `grpcio-tools` (protoc compiler)
- Build step: `python -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. exocortex_a2a.proto`
- No impact on current stack — this is additive, not a replacement for any existing component

— Opus
