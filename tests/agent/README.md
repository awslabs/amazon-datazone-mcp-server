# Agent Testing Framework

This directory contains the API classification testing framework for the DataZone MCP server.

## Files

- **`agent.py`** - Main AI agent implementation using LangChain and LangGraph
- **`config.py`** - Configuration management for the agent
- **`smus_test.csv`** - Test dataset with 1000+ questions and expected API classifications

## Purpose

The agent tests how accurately an AI model can classify user questions to the correct DataZone API calls. This is useful for:

- Validating AI-powered API routing accuracy
- Monitoring performance over time
- Identifying common misclassification patterns
- Improving prompt engineering and training data

## Usage

The agent is primarily used through the CI pipeline test at `tests/test_api_classification_accuracy.py`, but can also be run interactively:

```bash
# Interactive mode
python tests/test_datazone_api_call.py

# Programmatic use
from tests.agent.agent import SMUSAdminAgent
agent = SMUSAdminAgent()
await agent.test_response("session_id", output_path="results.csv")
```

## Dataset Format

The CSV dataset contains:
- `api_name` - Expected API to be called
- `question` - User question to classify
- `query_id` - Unique identifier
- `explanation` - Context about the question
- `api_called` - Populated by the agent during testing

## Environment Variables

- `ANTHROPIC_API_KEY` - Required for Claude API access
- `DEFAULT_MODEL` - Model to use (default: claude-3-5-sonnet-20241022)
- `MAX_TOKENS` - Token limit (default: 4096)
- `TEMPERATURE` - Sampling temperature (default: 0.1)

See the [CI Pipeline Guide](../../docs/API_CLASSIFICATION_CI_GUIDE.md) for complete setup instructions. 