#!/usr/bin/env python3
"""
Test for API classification accuracy using the SMUS Admin Agent.
This test verifies how accurately the agent can classify user questions
to the correct DataZone API calls.
"""

import asyncio
import os
import pytest
import pandas as pd
import tempfile
from pathlib import Path
import json
from datetime import datetime

# Skip if ANTHROPIC_API_KEY is not available (for CI without secrets)
pytest_mark_skipif = pytest.mark.skipif(
    not os.getenv("ANTHROPIC_API_KEY"),
    reason="ANTHROPIC_API_KEY not available"
)

@pytest_mark_skipif
class TestAPIClassificationAccuracy:
    """Test suite for API classification accuracy."""
    
    def setup_method(self):
        """Set up test environment."""
        # Import here to avoid import errors when ANTHROPIC_API_KEY is not set
        from tests.agent.agent import SMUSAdminAgent
        self.agent = SMUSAdminAgent()
        self.dataset_path = "tests/agent/smus_test.csv"
        self.results_file = None
        
    def teardown_method(self):
        """Clean up test environment."""
        if hasattr(self.agent, 'cleanup_mcp'):
            try:
                asyncio.run(self.agent.cleanup_mcp())
            except:
                # Ignore cleanup errors
                pass
    
    @pytest.mark.asyncio
    async def test_api_classification_accuracy(self):
        """Test the accuracy of API classification."""
        # Load the test dataset
        df = pd.read_csv(self.dataset_path)
        
        # Create temporary file for results
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as f:
            self.results_file = f.name
        
        try:
            # Create a results directory for CI
            results_dir = Path("test_results")
            results_dir.mkdir(exist_ok=True)
            ci_results_path = results_dir / "ci_api_results.csv"
            
            # Run the agent test with configurable output path
            await self.agent.test_response("ci_test_session", output_path=str(ci_results_path))
            
            # Load the results
            if ci_results_path.exists():
                df_results = pd.read_csv(ci_results_path)
            else:
                # Fallback: check if agent modified the original dataset
                df_results = pd.read_csv(self.dataset_path)
                if 'api_called' not in df_results.columns:
                    raise RuntimeError("Agent test did not produce results")
            
            # Calculate accuracy metrics
            accuracy_results = self.calculate_accuracy(df_results)
            
            # Save results for CI artifacts
            self.save_results_for_ci(df_results, accuracy_results)
            
            # Assert minimum accuracy threshold
            assert accuracy_results['overall_accuracy'] >= 0.7, f"Overall accuracy {accuracy_results['overall_accuracy']:.2%} is below 70% threshold"
            
            # Print summary for CI logs
            print(f"\n=== API Classification Test Results ===")
            print(f"Total questions tested: {accuracy_results['total_questions']}")
            print(f"Correct classifications: {accuracy_results['correct_classifications']}")
            print(f"Overall accuracy: {accuracy_results['overall_accuracy']:.2%}")
            print(f"Accuracy by API type:")
            for api, acc in accuracy_results['accuracy_by_api'].items():
                print(f"  {api}: {acc:.2%}")
            
        finally:
            # Clean up temporary file
            if self.results_file and os.path.exists(self.results_file):
                os.unlink(self.results_file)
    
    def calculate_accuracy(self, df):
        """Calculate accuracy metrics from the results dataframe."""
        # Ensure we have the required columns
        if 'api_called' not in df.columns:
            df['api_called'] = 'None'  # Default if no predictions were made
        
        # Normalize API names for comparison
        df['api_name_normalized'] = df['api_name'].str.replace('_', '').str.lower()
        df['api_called_normalized'] = df['api_called'].str.replace('_', '').str.lower()
        
        # Calculate overall accuracy
        correct_predictions = (df['api_name_normalized'] == df['api_called_normalized']).sum()
        total_questions = len(df)
        overall_accuracy = correct_predictions / total_questions if total_questions > 0 else 0
        
        # Calculate accuracy by API type
        accuracy_by_api = {}
        for api in df['api_name'].unique():
            api_subset = df[df['api_name'] == api]
            if len(api_subset) > 0:
                api_correct = (api_subset['api_name_normalized'] == api_subset['api_called_normalized']).sum()
                accuracy_by_api[api] = api_correct / len(api_subset)
        
        return {
            'total_questions': total_questions,
            'correct_classifications': correct_predictions,
            'overall_accuracy': overall_accuracy,
            'accuracy_by_api': accuracy_by_api,
            'timestamp': datetime.now().isoformat()
        }
    
    def save_results_for_ci(self, df_results, accuracy_results):
        """Save results in formats suitable for CI artifacts."""
        # Create results directory
        results_dir = Path("test_results")
        results_dir.mkdir(exist_ok=True)
        
        # Save detailed results CSV
        results_csv_path = results_dir / "api_classification_results.csv"
        df_results.to_csv(results_csv_path, index=False)
        
        # Save accuracy metrics JSON
        accuracy_json_path = results_dir / "accuracy_metrics.json"
        with open(accuracy_json_path, 'w') as f:
            json.dump(accuracy_results, f, indent=2, default=str)
        
        # Create a summary report
        summary_path = results_dir / "test_summary.md"
        with open(summary_path, 'w') as f:
            f.write("# API Classification Accuracy Test Results\n\n")
            f.write(f"**Test Date:** {accuracy_results['timestamp']}\n\n")
            f.write(f"**Overall Accuracy:** {accuracy_results['overall_accuracy']:.2%}\n\n")
            f.write(f"**Total Questions:** {accuracy_results['total_questions']}\n\n")
            f.write(f"**Correct Classifications:** {accuracy_results['correct_classifications']}\n\n")
            f.write("## Accuracy by API Type\n\n")
            for api, acc in accuracy_results['accuracy_by_api'].items():
                f.write(f"- **{api}:** {acc:.2%}\n")
            f.write("\n## Test Details\n\n")
            f.write("The test evaluates how accurately the AI agent can classify user questions to the correct DataZone API calls.\n")
            f.write("Results are saved as CSV files for detailed analysis.\n")
        
        print(f"Results saved to {results_dir}")


# Add a simple test that can run without API key for basic validation
def test_dataset_structure():
    """Test that the dataset has the expected structure (runs without API key)."""
    dataset_path = "tests/agent/smus_test.csv"
    assert os.path.exists(dataset_path), f"Dataset file {dataset_path} not found"
    
    df = pd.read_csv(dataset_path)
    
    # Check required columns
    required_columns = ['api_name', 'question']
    for col in required_columns:
        assert col in df.columns, f"Required column '{col}' not found in dataset"
    
    # Check that we have data
    assert len(df) > 0, "Dataset is empty"
    
    print(f"Dataset validation passed: {len(df)} questions across {df['api_name'].nunique()} API types") 