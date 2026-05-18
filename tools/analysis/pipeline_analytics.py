"""
🚀 EFFICIENT TESTBENCH GENERATION SYSTEM
Tier-Based Dataset-Driven Approach
====================================

This system uses a 4-tier fallback approach for generating testbenches:

TIER 1: AI Generation (30-40% success)
  └─ Attempts to generate testbench using the LLM model
     - Pros: Custom logic, handles novel designs
     - Cons: Often produces incomplete/invalid code
  
  ↓ (if fails)

TIER 2A: Final RTL-TB Dataset Matching (40-50% success)
  └─ Searches 439 pre-tested RTL+testbench pairs
     - Uses semantic similarity (prompt + RTL structure matching)
     - Threshold: 55% similarity for match acceptance
     - Reuses verified testbench code directly
     - Pros: High quality (tested), works well for sequential/complex designs
     - Cons: Only works if similar design exists in dataset
  
  ↓ (if no match)

TIER 2B: VerilogEval Dataset Matching (20-30% success)
  └─ Searches 156 reference implementations
     - Uses combinational/sequential heuristics
     - Best for simple logic designs
     - Pros: Reference quality, coverage for basic gates
     - Cons: Limited to simple combinational designs
  
  ↓ (if no match)

TIER 3: Generic Dynamic Generation (100% success)
  └─ Generates basic self-checking testbench
     - Uses rule-based templates
     - Pros: Always works (fallback guarantee)
     - Cons: Basic quality, minimal verification
"""

import json
import time
from datetime import datetime

class PipelineAnalytics:
    """Track pipeline performance across tiers"""
    
    def __init__(self):
        self.runs = []
        self.tier_stats = {
            'TIER_1_AI': {'count': 0, 'pass': 0, 'avg_time': 0},
            'TIER_2A_DATASET': {'count': 0, 'pass': 0, 'avg_time': 0},
            'TIER_2B_VERILOG_EVAL': {'count': 0, 'pass': 0, 'avg_time': 0},
            'TIER_3_GENERIC': {'count': 0, 'pass': 0, 'avg_time': 0},
        }
    
    def record_run(self, tier_source, prompt, result, elapsed_time):
        """Record a pipeline run for analytics"""
        run_data = {
            'timestamp': datetime.now().isoformat(),
            'tier': tier_source,
            'prompt': prompt[:100],  # First 100 chars
            'status': result.get('status', 'Unknown'),
            'passed': 'PASS' in result.get('status', ''),
            'elapsed_time': elapsed_time,
            'testbench_source': result.get('testbench_source', 'Unknown'),
        }
        
        self.runs.append(run_data)
        
        # Update tier stats
        if tier_source in self.tier_stats:
            stats = self.tier_stats[tier_source]
            stats['count'] += 1
            if run_data['passed']:
                stats['pass'] += 1
            # Update average time
            if stats['count'] == 1:
                stats['avg_time'] = elapsed_time
            else:
                stats['avg_time'] = (stats['avg_time'] * (stats['count'] - 1) + elapsed_time) / stats['count']
    
    def get_summary(self):
        """Generate performance summary"""
        total_runs = len(self.runs)
        total_passed = sum(1 for r in self.runs if r['passed'])
        
        summary = {
            'total_runs': total_runs,
            'total_passed': total_passed,
            'overall_pass_rate': (total_passed / total_runs * 100) if total_runs > 0 else 0,
            'tier_breakdown': self.tier_stats,
            'recent_runs': self.runs[-10:] if self.runs else []
        }
        
        return summary
    
    def print_report(self):
        """Print formatted performance report"""
        summary = self.get_summary()
        
        print("\n" + "="*70)
        print("📊 PIPELINE PERFORMANCE ANALYTICS")
        print("="*70)
        
        print(f"\n📈 Overall Statistics:")
        print(f"   Total Runs: {summary['total_runs']}")
        print(f"   Passed: {summary['total_passed']}/{summary['total_runs']}")
        print(f"   Success Rate: {summary['overall_pass_rate']:.1f}%")
        
        print(f"\n🎯 Tier Breakdown:")
        for tier, stats in summary['tier_breakdown'].items():
            if stats['count'] > 0:
                pass_rate = (stats['pass'] / stats['count'] * 100)
                print(f"\n   {tier}:")
                print(f"      Used: {stats['count']} times")
                print(f"      Passed: {stats['pass']}/{stats['count']} ({pass_rate:.1f}%)")
                print(f"      Avg Time: {stats['avg_time']:.2f}s")
        
        print(f"\n⏱️  Recent Runs:")
        for i, run in enumerate(summary['recent_runs'][-5:], 1):
            status_emoji = "✅" if run['passed'] else "❌"
            print(f"   {i}. {status_emoji} {run['tier']} - {run['testbench_source']}")
            print(f"      Time: {run['elapsed_time']:.2f}s | Prompt: {run['prompt'][:50]}...")
        
        print("\n" + "="*70 + "\n")
    
    def save_report(self, filepath="pipeline_analytics.json"):
        """Save analytics to file"""
        with open(filepath, 'w') as f:
            json.dump({
                'summary': self.get_summary(),
                'detailed_runs': self.runs
            }, f, indent=2)
        print(f"✓ Analytics saved to {filepath}")


# Global analytics instance
_analytics = PipelineAnalytics()

def get_analytics():
    """Get global analytics instance"""
    return _analytics


if __name__ == "__main__":
    print(__doc__)
    print("\n✓ Pipeline analytics system ready!")
    print("✓ Use get_analytics() to record pipeline runs")
