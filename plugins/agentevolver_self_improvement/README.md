# AgentEvolver Self-Improvement Plugin

Implements AgentEvolver's self-evolving mechanisms for Agent Zero AI agents, enabling autonomous self-improvement through three key mechanisms:

## 🧠 Three Self-Evolving Mechanisms

### 1. Self-Questioning (Automatic Task Generation)
Agents can generate their own improvement tasks based on performance gaps and learning needs.

### 2. Self-Navigating (Experience-guided Exploration)
Agents learn from past experiences and apply that knowledge to navigate new tasks more effectively.

### 3. Self-Attributing (Credit Assignment)
Agents analyze which actions contribute to success/failure for fine-grained policy optimization.

## 🚀 Features

- **8 Self-Questioning Tools**: Complete toolset for task generation, experience logging, and improvement analysis
- **Web UI Settings**: Configurable parameters for each self-evolving mechanism
- **Experience Database**: Persistent storage of learning experiences in JSON format
- **Performance Statistics**: Track success rates, tasks completed, and learning progress
- **Improvement Suggestions**: AI-powered recommendations for skill development

## 📁 Plugin Structure

```
agentevolver_self_improvement/
├── plugin.yaml              # Plugin manifest
├── README.md                # This file
├── LICENSE                  # MIT License
├── hooks.py                 # Plugin lifecycle hooks
├── test_plugin.py           # Test suite
├── webui/
│   └── config.html          # Settings UI
├── helpers/
│   ├── __init__.py
│   └── self_improvement.py  # Core engine (274 lines)
└── tools/
    ├── __init__.py
    └── self_questioning_tool.py  # Tool interface (157 lines)
```

## 🛠️ Installation

### Method 1: Plugin Hub (Recommended)
1. Open Agent Zero UI
2. Go to Plugins → Plugin Hub
3. Search for "AgentEvolver"
4. Click "Install"

### Method 2: Manual Installation
```bash
# Clone the repository to your plugins directory
cd /a0/usr/plugins/
git clone https://github.com/your-username/agentevolver_self_improvement.git
```

## ⚙️ Configuration

After installation, configure the plugin via Settings → Agent → AgentEvolver Self-Improvement:

- **Self-Questioning**: Enable/disable automatic task generation
- **Self-Navigating**: Set experience pool size and learning parameters
- **Self-Attributing**: Configure credit assignment depth
- **Auto-scheduling**: Set up automatic self-improvement sessions

## 🧪 Usage Examples

### Generate a self-improvement task:
```json
{
  "tool_name": "self_questioning_generate_task",
  "tool_args": {
    "category": "coding",
    "difficulty": "medium"
  }
}
```

### Record a learning experience:
```json
{
  "tool_name": "self_questioning_add_experience",
  "tool_args": {
    "task_type": "research",
    "task_description": "Study AI agent frameworks",
    "actions": ["Search", "Read", "Summarize"],
    "outcome": "success",
    "lessons_learned": ["Found 5 frameworks", "Identified key features"]
  }
}
```

### Get improvement suggestions:
```json
{
  "tool_name": "self_questioning_get_improvement_suggestions",
  "tool_args": {}
}
```

## 📊 Performance Tracking

The plugin maintains detailed statistics:
- Success rate across task categories
- Total experiences and tasks completed
- Learning progress over time
- Pattern analysis for improvement areas

## 🔧 Development

### Running Tests
```bash
cd /a0/usr/plugins/agentevolver_self_improvement
python test_plugin.py
```

### Extending the Plugin
1. Add new task categories in `helpers/self_improvement.py`
2. Create new tools in `tools/` directory
3. Extend the Web UI in `webui/`

## 🤝 Contributing

Contributions are welcome! Please:
1. Fork the repository
2. Create a feature branch
3. Submit a pull request with tests

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgements

Based on the [AgentEvolver](https://github.com/modelscope/AgentEvolver) research paper:
> "AgentEvolver: Towards Efficient Self-Evolving Agent System"
> Yunpeng Zhai et al., 2025

This plugin adapts the three self-evolving mechanisms for the Agent Zero framework.
