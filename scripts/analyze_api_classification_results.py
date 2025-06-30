#!/usr/bin/env python3
# Copyright Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

"""
Script to analyze API classification test results.
This script calculates accuracy metrics and generates detailed analysis reports.

Usage:
    python scripts/analyze_api_classification_results.py [results_directory]

The script expects the following files in the results directory:
- api_classification_results.csv (detailed results with predictions)
- accuracy_metrics.json (summary metrics)
"""

import argparse
import json
import pandas as pd
import sys
from pathlib import Path
from datetime import datetime
import matplotlib.pyplot as plt
import seaborn as sns
from typing import Dict, List, Tuple


def load_results(results_dir: Path) -> Tuple[pd.DataFrame, Dict]:
    """Load test results from the specified directory."""
    
    # Load the detailed results CSV
    csv_path = results_dir / "api_classification_results.csv"
    if not csv_path.exists():
        raise FileNotFoundError(f"Results CSV not found: {csv_path}")
    
    df = pd.read_csv(csv_path)
    
    # Load the accuracy metrics JSON
    json_path = results_dir / "accuracy_metrics.json"
    if json_path.exists():
        with open(json_path, 'r') as f:
            metrics = json.load(f)
    else:
        # Calculate metrics if JSON doesn't exist
        metrics = calculate_metrics_from_df(df)
    
    return df, metrics


def calculate_metrics_from_df(df: pd.DataFrame) -> Dict:
    """Calculate accuracy metrics from the dataframe."""
    # Ensure we have the required columns
    if 'api_called' not in df.columns:
        df['api_called'] = 'None'
    
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


def analyze_confusion_patterns(df: pd.DataFrame) -> pd.DataFrame:
    """Analyze confusion patterns in the predictions."""
    # Create confusion matrix
    confusion_data = []
    
    for _, row in df.iterrows():
        expected = row['api_name']
        actual = row.get('api_called', 'None')
        confusion_data.append({
            'expected': expected,
            'actual': actual,
            'correct': expected.lower().replace('_', '') == actual.lower().replace('_', ''),
            'question': row.get('question', ''),
            'query_id': row.get('query_id', '')
        })
    
    confusion_df = pd.DataFrame(confusion_data)
    
    # Create confusion matrix summary
    confusion_matrix = pd.crosstab(
        confusion_df['expected'], 
        confusion_df['actual'], 
        margins=True
    )
    
    return confusion_df, confusion_matrix


def generate_detailed_report(df: pd.DataFrame, metrics: Dict, output_dir: Path):
    """Generate a detailed analysis report."""
    
    confusion_df, confusion_matrix = analyze_confusion_patterns(df)
    
    report_path = output_dir / "detailed_analysis_report.md"
    
    with open(report_path, 'w') as f:
        f.write("# API Classification Detailed Analysis Report\n\n")
        f.write(f"**Analysis Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n\n")
        
        # Overall Summary
        f.write("## Overall Performance Summary\n\n")
        f.write(f"- **Total Questions Tested:** {metrics['total_questions']}\n")
        f.write(f"- **Correct Classifications:** {metrics['correct_classifications']}\n")
        f.write(f"- **Overall Accuracy:** {metrics['overall_accuracy']:.2%}\n\n")
        
        # Performance by API
        f.write("## Performance by API Type\n\n")
        f.write("| API Type | Accuracy | Questions Tested |\n")
        f.write("|----------|----------|------------------|\n")
        
        for api, accuracy in sorted(metrics['accuracy_by_api'].items()):
            count = len(df[df['api_name'] == api])
            f.write(f"| {api} | {accuracy:.2%} | {count} |\n")
        
        # Confusion Matrix
        f.write("\n## Confusion Matrix\n\n")
        f.write("```\n")
        f.write(str(confusion_matrix))
        f.write("\n```\n\n")
        
        # Common Misclassifications
        f.write("## Common Misclassifications\n\n")
        misclassified = confusion_df[~confusion_df['correct']]
        if len(misclassified) > 0:
            misclass_patterns = misclassified.groupby(['expected', 'actual']).size().reset_index(name='count')
            misclass_patterns = misclass_patterns.sort_values('count', ascending=False)
            
            f.write("| Expected | Actual | Count | Frequency |\n")
            f.write("|----------|--------|-------|----------|\n")
            
            for _, row in misclass_patterns.head(10).iterrows():
                freq = row['count'] / len(misclassified) * 100
                f.write(f"| {row['expected']} | {row['actual']} | {row['count']} | {freq:.1f}% |\n")
        else:
            f.write("No misclassifications found! Perfect accuracy.\n")
        
        # Detailed Error Analysis
        f.write("\n## Detailed Error Analysis\n\n")
        if len(misclassified) > 0:
            f.write("### Sample Misclassified Questions\n\n")
            for _, row in misclassified.head(5).iterrows():
                f.write(f"**Expected:** {row['expected']}  \n")
                f.write(f"**Actual:** {row['actual']}  \n")
                f.write(f"**Question:** {row['question'][:200]}...  \n")
                f.write(f"**Query ID:** {row['query_id']}  \n\n")
        
        # Recommendations
        f.write("## Recommendations\n\n")
        
        if metrics['overall_accuracy'] < 0.8:
            f.write("- **Overall accuracy is below 80%.** Consider:\n")
            f.write("  - Reviewing the training prompts for better API classification\n")
            f.write("  - Adding more examples for underperforming API types\n")
            f.write("  - Analyzing the question patterns that lead to misclassification\n\n")
        
        if len(metrics['accuracy_by_api']) > 0:
            worst_performing = min(metrics['accuracy_by_api'].items(), key=lambda x: x[1])
            if worst_performing[1] < 0.7:
                f.write(f"- **{worst_performing[0]} has low accuracy ({worst_performing[1]:.2%}).** Consider:\n")
                f.write("  - Adding more training examples for this API type\n")
                f.write("  - Reviewing the question patterns and improving classification logic\n\n")
    
    print(f"Detailed report saved to: {report_path}")


def create_visualizations(df: pd.DataFrame, metrics: Dict, output_dir: Path):
    """Create visualization charts for the analysis."""
    try:
        # Set up the plotting style
        plt.style.use('seaborn-v0_8')
        fig, axes = plt.subplots(2, 2, figsize=(15, 12))
        fig.suptitle('API Classification Analysis Dashboard', fontsize=16)
        
        # 1. Overall Accuracy Bar Chart
        ax1 = axes[0, 0]
        categories = ['Correct', 'Incorrect']
        values = [metrics['correct_classifications'], 
                 metrics['total_questions'] - metrics['correct_classifications']]
        colors = ['#2ecc71', '#e74c3c']
        
        ax1.bar(categories, values, color=colors, alpha=0.7)
        ax1.set_title('Overall Classification Results')
        ax1.set_ylabel('Number of Questions')
        
        # Add percentage labels
        total = sum(values)
        for i, v in enumerate(values):
            percentage = v / total * 100
            ax1.text(i, v + total * 0.01, f'{v}\n({percentage:.1f}%)', 
                    ha='center', va='bottom', fontweight='bold')
        
        # 2. Accuracy by API Type
        ax2 = axes[0, 1]
        apis = list(metrics['accuracy_by_api'].keys())
        accuracies = [metrics['accuracy_by_api'][api] for api in apis]
        
        bars = ax2.bar(range(len(apis)), accuracies, alpha=0.7, color='#3498db')
        ax2.set_title('Accuracy by API Type')
        ax2.set_ylabel('Accuracy')
        ax2.set_xticks(range(len(apis)))
        ax2.set_xticklabels(apis, rotation=45, ha='right')
        ax2.set_ylim(0, 1)
        
        # Add percentage labels on bars
        for bar, acc in zip(bars, accuracies):
            height = bar.get_height()
            ax2.text(bar.get_x() + bar.get_width()/2., height + 0.01,
                    f'{acc:.1%}', ha='center', va='bottom', fontsize=9)
        
        # 3. Question Distribution by API
        ax3 = axes[1, 0]
        api_counts = df['api_name'].value_counts()
        
        wedges, texts, autotexts = ax3.pie(api_counts.values, labels=api_counts.index, 
                                          autopct='%1.1f%%', startangle=90)
        ax3.set_title('Question Distribution by API Type')
        
        # 4. Confusion Heatmap (simplified for top APIs)
        ax4 = axes[1, 1]
        confusion_df, confusion_matrix = analyze_confusion_patterns(df)
        
        # Get top 5 most common APIs for readability
        top_apis = df['api_name'].value_counts().head(5).index.tolist()
        filtered_matrix = confusion_matrix.loc[top_apis, :]
        
        sns.heatmap(filtered_matrix.iloc[:-1, :-1], annot=True, fmt='d', 
                   cmap='Blues', ax=ax4, cbar_kws={'shrink': 0.8})
        ax4.set_title('Confusion Matrix (Top 5 APIs)')
        ax4.set_xlabel('Predicted')
        ax4.set_ylabel('Expected')
        
        plt.tight_layout()
        
        # Save the visualization
        viz_path = output_dir / "classification_analysis_dashboard.png"
        plt.savefig(viz_path, dpi=300, bbox_inches='tight')
        plt.close()
        
        print(f"Visualization saved to: {viz_path}")
        
    except ImportError:
        print("Warning: matplotlib/seaborn not available. Skipping visualizations.")
        print("Install with: pip install matplotlib seaborn")


def main():
    """Main analysis function."""
    parser = argparse.ArgumentParser(description="Analyze API classification test results")
    parser.add_argument("results_dir", nargs="?", default="test_results",
                       help="Directory containing test results (default: test_results)")
    parser.add_argument("--output-dir", "-o", default="analysis_output",
                       help="Output directory for analysis results (default: analysis_output)")
    
    args = parser.parse_args()
    
    results_dir = Path(args.results_dir)
    output_dir = Path(args.output_dir)
    
    if not results_dir.exists():
        print(f"Error: Results directory not found: {results_dir}")
        print("Make sure you've downloaded the test artifacts from GitHub Actions.")
        sys.exit(1)
    
    # Create output directory
    output_dir.mkdir(exist_ok=True)
    
    try:
        # Load results
        print(f"Loading results from: {results_dir}")
        df, metrics = load_results(results_dir)
        
        # Print summary to console
        print("\n" + "="*60)
        print("API CLASSIFICATION ANALYSIS SUMMARY")
        print("="*60)
        print(f"Total Questions: {metrics['total_questions']}")
        print(f"Correct Classifications: {metrics['correct_classifications']}")
        print(f"Overall Accuracy: {metrics['overall_accuracy']:.2%}")
        print("\nAccuracy by API Type:")
        for api, acc in sorted(metrics['accuracy_by_api'].items()):
            count = len(df[df['api_name'] == api])
            print(f"  {api:<20}: {acc:>6.1%} ({count:>3} questions)")
        
        # Generate detailed report
        print(f"\nGenerating detailed analysis report...")
        generate_detailed_report(df, metrics, output_dir)
        
        # Create visualizations
        print("Creating visualizations...")
        create_visualizations(df, metrics, output_dir)
        
        # Save processed data
        processed_csv = output_dir / "processed_results.csv"
        df.to_csv(processed_csv, index=False)
        
        processed_json = output_dir / "final_metrics.json"
        with open(processed_json, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        print(f"\nAnalysis complete! Results saved to: {output_dir}")
        print(f"View the detailed report: {output_dir / 'detailed_analysis_report.md'}")
        
        # Return exit code based on accuracy threshold
        if metrics['overall_accuracy'] < 0.7:
            print(f"\nWarning: Overall accuracy ({metrics['overall_accuracy']:.2%}) is below 70% threshold")
            sys.exit(1)
        else:
            print(f"\nSuccess: Overall accuracy ({metrics['overall_accuracy']:.2%}) meets the 70% threshold")
            
    except Exception as e:
        print(f"Error during analysis: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main() 