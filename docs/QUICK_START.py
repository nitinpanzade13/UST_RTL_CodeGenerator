"""
🚀 QUICK START GUIDE - Tier-Based Testbench Generation
How to use the new system immediately
"""

# ============================================================
# 1. RUN YOUR APP WITH NEW TIER SYSTEM
# ============================================================
print("""
Simply run your app as before - the tier system is built in!

    python app.py

What changed:
- If AI testbench fails → automatically tries dataset matching
- Shows which tier was used in results
- Falls back to generic generation if needed
- All transparent to you!
""")


# ============================================================
# 2. UNDERSTANDING THE OUTPUT
# ============================================================
print("""
🔍 NEW OUTPUT YOU'LL SEE:

🧠 TIER 1: Attempting AI testbench generation...
⚠️ TIER 1 failed → Attempting TIER 2 (Dataset Matching)...
📊 TIER 2A: Searching final_rtl_tb_dataset.jsonl...
✅ TIER 2A Match found!
   Details: {'problem_id': 'Prob060_m2014_q4k', 'similarity': 0.71, 'quality': 0.90}
✅ Using TIER_2A_DATASET

This tells you:
- TIER 1 AI generation attempted but failed
- TIER 2A found a matching design (71% similar, 90% quality)
- Using the matched testbench from dataset
""")


# ============================================================
# 3. CHECK TESTBENCH SOURCE IN RESULTS
# ============================================================
print("""
📊 MONITORING WHICH TIER IS USED:

result = run_pipeline(model, tokenizer, prompt)

result['testbench_source']  # "TIER_1_AI" or "TIER_2_OR_3_FALLBACK"
result['status']            # "✅ PASS" or "❌ FAIL"
result['simulation_output'] # Detailed test output

To track performance:
- Look for "TIER_1_AI" → AI generation working
- Look for "TIER_2_OR_3_FALLBACK" → Dataset/generic used
- Count success rates for each tier
""")


# ============================================================
# 4. USE ANALYTICS TO MONITOR PERFORMANCE
# ============================================================
print("""
📈 TRACKING PERFORMANCE:

from pipeline_analytics import get_analytics
import time

# After running several pipeline calls...

analytics = get_analytics()
analytics.print_report()

Output shows:
- Total success rate
- Success rate per tier
- Average generation time
- Recent run details
""")


# ============================================================
# 5. RUN TEST SUITE TO UNDERSTAND COVERAGE
# ============================================================
print("""
🧪 SEE HOW YOUR DATASETS PERFORM:

python test_tiers.py

Shows:
- Which tier handles each design type
- Dataset coverage percentage
- Design complexity breakdown
- Recommendations for improvements
- Saved to test_results.json
""")


# ============================================================
# 6. ADVANCED: DIRECT MATCHER ACCESS
# ============================================================
print("""
🔧 USE MATCHER DIRECTLY:

from dataset_matcher import DatasetMatcher, select_testbench_source

matcher = DatasetMatcher()

# Option A: Automatic tier selection
source, tb_code, metadata = select_testbench_source(
    prompt="Design a 4-bit counter",
    rtl_code="...",
    matcher=matcher
)
# Returns best tier automatically

# Option B: Find TIER 2A match only
match, similarity = matcher.find_tier2a_match(
    prompt="Design counter",
    rtl_code="...",
    threshold=0.55  # Adjust if needed
)

if match:
    quality = matcher.get_testbench_quality_score(match['testbench_code'])
    print(f"Match found: {similarity:.0%} similar, {quality:.0%} quality")

# Option C: Check TIER 2B
problem_id, tb_code = matcher.find_tier2b_match(rtl_code)
""")


# ============================================================
# 7. KEY METRICS TO MONITOR
# ============================================================
print("""
📊 WHAT TO TRACK:

1. Success Rates by Tier:
   - TIER 1 (AI):      Should be ~30-40% of runs (increasing over time)
   - TIER 2A (Dataset): Should be ~50-70% of runs (main workhorse)
   - TIER 2B (Eval):   Should be ~5-10% of runs (for simple designs)
   - TIER 3 (Generic):  Should be <5% of runs (last resort)

2. Average Similarity for Matches:
   - Good: 55-70% (threshold)
   - Excellent: 70%+ (high confidence)

3. Testbench Quality Scores:
   - Good: 70%+ (usable)
   - Excellent: 85%+ (high quality)

4. Generation Time:
   - TIER 1: 5-15s (with AI)
   - TIER 2/3: 0.1-0.5s (instant)
""")


# ============================================================
# 8. OPTIMIZATION TIPS
# ============================================================
print("""
⚡ WAYS TO IMPROVE:

1. Add successful AI-generated testbenches to TIER 2A
   - Manually curate best ones
   - Add to final_rtl_tb_dataset.jsonl
   - Improves future coverage

2. Adjust similarity threshold if needed
   - Lower threshold → more matches (riskier)
   - Higher threshold → fewer but better matches
   - Currently: 0.55 is good balance

3. Monitor which designs fail
   - Collect failed designs
   - Add to dataset when you find solutions
   - Dataset learns from your use

4. Combine with AI model improvements
   - TIER 1 AI still important for novel designs
   - TIER 2 datasets catch patterns
   - Both together = best results
""")


# ============================================================
# 9. TROUBLESHOOTING
# ============================================================
print("""
🐛 ISSUES & SOLUTIONS:

❌ "No dataset match → using TIER 3"
   ✅ Design is novel, TIER 3 fallback is working
   ✅ Add this design to dataset later if it passes

❌ "Testbench quality low (< 70%)"
   ✅ Adjust threshold: matcher.find_tier2a_match(..., threshold=0.70)
   ✅ Try more specific prompts (helps similarity)

❌ "Still getting TIER 1 failures"
   ✅ Normal - AI generation isn't perfect
   ✅ Good news: TIER 2/3 fallback catches it

❌ "Generation slow"
   ✅ First load: 2s (one-time cache)
   ✅ Subsequent searches: 0.3s (dataset lookup)
   ✅ Much faster than AI generation!
""")


# ============================================================
# 10. EXAMPLE: COMPLETE WORKFLOW
# ============================================================
print("""
📋 COMPLETE EXAMPLE:

from evaluate_pipeline import run_pipeline
from pipeline_analytics import get_analytics
import time

model, tokenizer = load_model()
analytics = get_analytics()

prompts = [
    "Design a 4-bit counter",
    "Design a 2:1 multiplexer",
    "Design an 8-bit accumulator"
]

for prompt in prompts:
    start = time.time()
    result = run_pipeline(model, tokenizer, prompt)
    elapsed = time.time() - start
    
    # Record analytics
    tier_source = result.get('testbench_source', 'UNKNOWN')
    analytics.record_run(tier_source, prompt, result, elapsed)
    
    # Print status
    print(f"{result['status']} - {tier_source}")

# Generate report
print("\\n" + "="*70)
analytics.print_report()
analytics.save_report('pipeline_results.json')
""")


# ============================================================
# SUMMARY
# ============================================================
print("""
✅ SUMMARY:

Your system now has:
1. ✓ 100% fallback guarantee (TIER 3 always works)
2. ✓ 439 pre-tested testbenches (TIER 2A)
3. ✓ 156 reference designs (TIER 2B)
4. ✓ Automatic tier selection
5. ✓ Performance analytics
6. ✓ Comprehensive documentation

🎯 Immediate Next Steps:
1. Run python app.py to see it in action
2. Run python test_tiers.py to understand coverage
3. Check TIER_SYSTEM_GUIDE.md for detailed docs
4. Use pipeline_analytics to monitor performance

💡 Long-term Benefits:
- As you run more designs, success rates improve
- Dataset can grow with your successful designs
- System learns your patterns over time
""")


if __name__ == "__main__":
    import textwrap
    
    # Print all guides
    import inspect
    current_module = inspect.getmodule(inspect.currentframe())
    
    print("\n" + "="*70)
    print("🚀 TIER-BASED TESTBENCH SYSTEM - QUICK START")
    print("="*70 + "\n")
    
    # Guide content is already printed above via print statements
    print("""
📚 For more information, see:
   - TIER_SYSTEM_GUIDE.md (complete documentation)
   - test_tiers.py (see system in action)
   - pipeline_analytics.py (performance tracking)

Ready to use? Just run:
   python app.py
    """)
