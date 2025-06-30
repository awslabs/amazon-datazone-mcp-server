# API Classification CI Pipeline Guide

This guide explains how to set up and use the API classification accuracy testing in your CI pipeline, including GitHub Actions integration, secure API key handling, and result analysis.

## Overview

The API classification CI pipeline tests how accurately the AI agent can classify user questions to the correct DataZone API calls. It integrates with your existing GitHub Actions workflow and provides detailed analysis of the results.

## Table of Contents

1. [Setup & Configuration](#setup--configuration)
2. [GitHub Actions Integration](#github-actions-integration)
3. [Secure API Key Management](#secure-api-key-management)
4. [Running Tests Locally](#running-tests-locally)
5. [Result Analysis](#result-analysis)
6. [Understanding the Metrics](#understanding-the-metrics)
7. [Troubleshooting](#troubleshooting)

## Setup & Configuration

### Prerequisites

1. **Python 3.10+** with the dev dependencies installed
2. **Anthropic API Key** for Claude integration
3. **Test dataset** at `tests/agent/smus_test.csv`

### Installation

Install the development dependencies that include the API classification testing tools:

```bash
# Install using uv
uv sync --frozen --all-extras --dev

# Or install manually with pip
pip install -e ".[dev]"
```

### File Structure

The CI pipeline includes these key files:

```
tests/
├── agent/
│   ├── agent.py                    # Main agent implementation
│   ├── config.py                   # Configuration management
│   └── smus_test.csv              # Test dataset
├── test_api_classification_accuracy.py  # Main CI test
└── test_datazone_api_call.py      # Original interactive test

scripts/
└── analyze_api_classification_results.py  # Analysis script

.github/workflows/
└── python.yml                     # Updated GitHub Actions workflow
```

## GitHub Actions Integration

### How It Works

The CI pipeline is automatically integrated into your existing `python.yml` workflow. Here's what happens:

1. **Standard tests run first** (existing functionality)
2. **API classification test runs** if `ANTHROPIC_API_KEY` is available
3. **Results are saved** as GitHub Actions artifacts
4. **Basic validation test runs** even without API key

### Workflow Steps

The workflow includes these steps:

```yaml
- name: Run API Classification Accuracy Test
  env:
    ANTHROPIC_API_KEY: ${{ secrets.ANTHROPIC_API_KEY }}
  run: |
    if [ -n "$ANTHROPIC_API_KEY" ]; then
      echo "Running API classification accuracy test with Anthropic API key"
      uv run --frozen pytest tests/test_api_classification_accuracy.py::TestAPIClassificationAccuracy::test_api_classification_accuracy -v
    else
      echo "ANTHROPIC_API_KEY not available, skipping API classification test"
      uv run --frozen pytest tests/test_api_classification_accuracy.py::test_dataset_structure -v
    fi

- name: Upload API Classification Test Results
  if: always()
  uses: actions/upload-artifact@v4.6.2
  with:
    name: api-classification-results
    path: |
      test_results/
      coverage.xml
    retention-days: 30
```

### What Gets Tested

- **Dataset structure validation** (always runs)
- **API classification accuracy** (when API key is available)
- **Accuracy threshold check** (70% minimum)
- **Per-API performance** analysis

## Secure API Key Management

### Setting Up GitHub Secrets

GitHub handles the `ANTHROPIC_API_KEY` securely using repository secrets:

1. **Go to your repository settings**
2. **Navigate to Secrets and variables > Actions**
3. **Click "New repository secret"**
4. **Add the secret:**
   - Name: `ANTHROPIC_API_KEY`
   - Value: Your actual Anthropic API key

### How GitHub Secures API Keys

✅ **Secure practices:**
- Secrets are **encrypted at rest**
- Only available during workflow execution
- **Not exposed in logs** or output
- Automatically **masked in console output**
- Only accessible to repository collaborators with appropriate permissions

✅ **CI behavior:**
- **With API key**: Full accuracy testing runs
- **Without API key**: Basic dataset validation only
- **Never fails** due to missing API key

### Local Development

For local testing, create a `.env` file:

```bash
# .env file (not committed to repo)
ANTHROPIC_API_KEY=your_api_key_here
DEFAULT_MODEL=claude-3-5-sonnet-20241022
MAX_TOKENS=4096
TEMPERATURE=0.1
```

## Running Tests Locally

### Run the Full Test Suite

```bash
# Run all tests including API classification
pytest tests/test_api_classification_accuracy.py -v

# Run just the accuracy test
pytest tests/test_api_classification_accuracy.py::TestAPIClassificationAccuracy::test_api_classification_accuracy -v

# Run dataset validation only (no API key needed)
pytest tests/test_api_classification_accuracy.py::test_dataset_structure -v
```

### Run the Interactive Version

```bash
# Original interactive test
python tests/test_datazone_api_call.py
```

### View Results Locally

```bash
# Results are saved to test_results/ directory
ls test_results/
# api_classification_results.csv
# accuracy_metrics.json
# test_summary.md
```

## Result Analysis

### Automatic Analysis in CI

The CI pipeline automatically generates:

1. **CSV results file** with detailed predictions
2. **JSON metrics file** with accuracy statistics
3. **Markdown summary** with human-readable report

### Manual Analysis

Download the artifacts from GitHub Actions and run the analysis script:

```bash
# Download artifacts from GitHub Actions UI
# Extract to a directory (e.g., downloaded_results/)

# Run analysis
python scripts/analyze_api_classification_results.py downloaded_results/

# With custom output directory
python scripts/analyze_api_classification_results.py downloaded_results/ --output-dir my_analysis/
```

### Analysis Output

The analysis script generates:

```
analysis_output/
├── detailed_analysis_report.md      # Comprehensive report
├── classification_analysis_dashboard.png  # Visualizations
├── processed_results.csv            # Enhanced results
└── final_metrics.json              # Complete metrics
```

## Understanding the Metrics

### Overall Accuracy

```
Overall Accuracy = Correct Classifications / Total Questions
```

**Example:** 850 correct out of 1000 questions = 85% accuracy

### Per-API Accuracy

Individual accuracy for each API type:

```
GetAsset Accuracy = Correct GetAsset Classifications / Total GetAsset Questions
```

### Confusion Matrix

Shows where misclassifications occur:

```
Expected    | Predicted
GetAsset    | GetAsset: 45, GetDomain: 3, GetConnection: 2
GetDomain   | GetDomain: 38, GetAsset: 1, None: 1
```

### Key Metrics Explained

- **Total Questions**: Number of test cases processed
- **Correct Classifications**: Questions correctly mapped to expected API
- **Overall Accuracy**: Percentage of correct classifications
- **Accuracy by API**: Per-API performance breakdown
- **Common Misclassifications**: Most frequent error patterns

## Analyzing Results by Comparing Expected vs Actual

The analysis compares the `api_name` column (expected) with the `api_called` column (actual):

### Normalization Process

The system normalizes both columns for comparison:
- Removes underscores: `Get_Asset` → `GetAsset`
- Converts to lowercase: `GetAsset` → `getasset`
- Handles variations: `get_asset`, `GetAsset`, `getasset` all match

### Accuracy Calculation

```python
# Simplified accuracy calculation
df['correct'] = (df['api_name_normalized'] == df['api_called_normalized'])
accuracy = df['correct'].sum() / len(df)
```

### Analysis Features

1. **Confusion Matrix**: Shows classification patterns
2. **Error Analysis**: Identifies common misclassification patterns
3. **Per-API Performance**: Breaks down accuracy by API type
4. **Sample Errors**: Shows specific misclassified questions
5. **Recommendations**: Suggests improvements based on results

## Troubleshooting

### Common Issues

#### 1. "ANTHROPIC_API_KEY not available"

**Cause**: API key not set in GitHub secrets or local environment

**Solution**:
- For GitHub: Add the secret in repository settings
- For local: Create `.env` file with your API key

#### 2. "Agent test did not produce results"

**Cause**: Agent failed to run or save results

**Solution**:
- Check agent dependencies are installed
- Verify dataset file exists at `tests/agent/smus_test.csv`
- Check for error messages in test output

#### 3. "Overall accuracy below 70% threshold"

**Cause**: AI agent performance is below expectations

**Solution**:
- Review the detailed analysis report
- Check for systematic errors in specific API types
- Consider improving prompts or training data

#### 4. Import errors for pandas/matplotlib

**Cause**: Dev dependencies not installed

**Solution**:
```bash
# Install dev dependencies
uv sync --frozen --all-extras --dev

# Or manually install missing packages
pip install pandas matplotlib seaborn
```

### Debug Tips

1. **Check test logs** in GitHub Actions for detailed error messages
2. **Run tests locally** first to debug issues
3. **Use dataset validation test** to check basic setup
4. **Review analysis reports** for performance insights

### Getting Help

1. **Check the test output** for specific error messages
2. **Review the analysis reports** for performance insights
3. **Look at sample misclassifications** to understand patterns
4. **Check dependencies** are properly installed

## Advanced Configuration

### Customizing Accuracy Thresholds

Edit the test file to adjust thresholds:

```python
# In tests/test_api_classification_accuracy.py
assert accuracy_results['overall_accuracy'] >= 0.8  # Change from 0.7 to 0.8
```

### Adding New Metrics

Extend the `calculate_accuracy` method to include additional metrics:

```python
def calculate_accuracy(self, df):
    # ... existing code ...
    
    # Add custom metrics
    results['precision_by_api'] = calculate_precision(df)
    results['recall_by_api'] = calculate_recall(df)
    
    return results
```

### Custom Analysis

Create your own analysis scripts using the saved results:

```python
import pandas as pd
import json

# Load results
df = pd.read_csv('test_results/api_classification_results.csv')
with open('test_results/accuracy_metrics.json', 'r') as f:
    metrics = json.load(f)

# Custom analysis
# ... your analysis code ...
```

## Best Practices

1. **Run tests regularly** to catch performance regressions
2. **Monitor accuracy trends** over time
3. **Investigate sudden drops** in performance
4. **Use analysis reports** to guide improvements
5. **Keep test datasets updated** with new question patterns
6. **Review misclassifications** to improve agent prompts

---

## Quick Reference

### Essential Commands

```bash
# Run full test locally
pytest tests/test_api_classification_accuracy.py -v

# Analyze downloaded results
python scripts/analyze_api_classification_results.py results_directory/

# Check dataset only
pytest tests/test_api_classification_accuracy.py::test_dataset_structure -v
```

### Key Files

- `tests/test_api_classification_accuracy.py` - Main CI test
- `scripts/analyze_api_classification_results.py` - Analysis script
- `tests/agent/smus_test.csv` - Test dataset
- `.github/workflows/python.yml` - CI configuration

### GitHub Setup

1. Add `ANTHROPIC_API_KEY` to repository secrets
2. Push changes to trigger workflow
3. Download artifacts from Actions tab
4. Run analysis script on downloaded results

This completes the integration of API classification testing into your CI pipeline with comprehensive analysis capabilities. 