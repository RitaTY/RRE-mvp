"""
RRE Blind Test Set - All-Aspects Accuracy Audit
Customized for Rita's and Gemini's actual data formats

Rita format: Multiple aspects in one cell, comma-separated
Gemini format: One aspect per row
"""

import csv
from collections import defaultdict
import re

# Normalize aspect names to handle spacing variations
def normalize_aspect_name(aspect):
    """Normalize aspect names to standard format"""
    aspect = aspect.strip()
    
    # Mapping to standardize Rita's and Gemini's variations
    mapping = {
        'material/ quality': 'Material/Quality',
        'material/quality': 'Material/Quality',
        'sizing/fit': 'Sizing/Fit',
        'fit/sizing': 'Sizing/Fit',
        'comfort': 'Comfort',
        'style': 'Color/Aesthetics',
        'color/aesthetics': 'Color/Aesthetics',
        'durability': 'Durability',
        'shipping/packaging': 'Shipping/Packaging',
        'instruction/ ux': 'Instructions/UX',
        'instructions/ux': 'Instructions/UX',
        'value/price': 'Value/Price',
    }
    
    aspect_lower = aspect.lower()
    if aspect_lower in mapping:
        return mapping[aspect_lower]
    
    return aspect  # Return original if no mapping found

def load_rita_aspects(csv_path):
    """
    Load Rita's aspects where multiple aspects are comma-separated in one cell.
    
    Returns: {review_id: [aspect1, aspect2, ...]}
    """
    reviews = defaultdict(list)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        
        for row in reader:
            review_id = row['Review_ID']
            aspects_str = row['Rita_Aspect']
            
            # Split by comma and normalize each aspect
            aspects = [normalize_aspect_name(a) for a in aspects_str.split(',')]
            aspects = [a for a in aspects if a]  # Remove empty strings
            
            reviews[review_id] = aspects
    
    return reviews

def load_gemini_aspects(csv_path):
    """
    Load Gemini's aspects where each aspect is on its own row.
    The file has a malformed format with extra quotes.
    
    Returns: {review_id: [aspect1, aspect2, ...]}
    """
    reviews = defaultdict(list)
    
    with open(csv_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
        # Skip the header (first line)
        for line in lines[1:]:
            # Remove the outer quotes and split by comma
            # The line is like: "RRE_001,Fit/Sizing,negative,""evidence"""
            line = line.strip().strip('"')
            
            # Split by comma (being careful about commas in quotes)
            parts = line.split(',')
            
            if len(parts) < 2:
                continue
            
            review_id = parts[0].strip()
            aspect = parts[1].strip()
            
            # Normalize the aspect name
            aspect_normalized = normalize_aspect_name(aspect)
            
            if aspect_normalized:
                reviews[review_id].append(aspect_normalized)
    
    return reviews

def calculate_metrics(rita_aspects, gemini_aspects):
    """
    Calculate Recall, Precision, and F1-Score.
    
    Returns: (recall, precision, f1, tp, fn, fp, details)
    """
    
    if not rita_aspects and not gemini_aspects:
        return 1.0, 1.0, 1.0, 0, 0, 0, "Both empty"
    
    if not rita_aspects:
        return 0.0, 0.0, 0.0, 0, 0, len(gemini_aspects), "Rita has no aspects"
    
    if not gemini_aspects:
        return 0.0, 0.0, 0.0, 0, len(rita_aspects), 0, "Gemini found no aspects"
    
    # Convert to sets (case-insensitive)
    rita_set = set(a.lower() for a in rita_aspects)
    gemini_set = set(a.lower() for a in gemini_aspects)
    
    # Calculate overlaps
    matches = rita_set & gemini_set
    
    tp = len(matches)
    fn = len(rita_set - gemini_set)
    fp = len(gemini_set - rita_set)
    
    # Calculate metrics
    recall = tp / len(rita_set) if len(rita_set) > 0 else 0
    precision = tp / len(gemini_set) if len(gemini_set) > 0 else 0
    
    if recall + precision > 0:
        f1 = 2 * (recall * precision) / (recall + precision)
    else:
        f1 = 0.0
    
    # Generate details
    details = []
    if matches:
        details.append(f"Matched: {', '.join(sorted(matches))}")
    if fn > 0:
        missed = rita_set - gemini_set
        details.append(f"Missed: {', '.join(sorted(missed))}")
    if fp > 0:
        extra = gemini_set - rita_set
        details.append(f"Extra: {', '.join(sorted(extra))}")
    
    details_str = " | ".join(details) if details else "Perfect match"
    
    return recall, precision, f1, tp, fn, fp, details_str

def run_audit(rita_csv, gemini_csv, output_csv):
    """Main audit function"""
    
    print("="*80)
    print("RRE BLIND TEST SET - ALL-ASPECTS ACCURACY AUDIT")
    print("="*80)
    
    # Load data
    print("\n1. Loading Rita's labels...")
    rita_data = load_rita_aspects(rita_csv)
    print(f"   Loaded {len(rita_data)} reviews from Rita")
    total_rita = sum(len(aspects) for aspects in rita_data.values())
    print(f"   Total aspects: {total_rita}")
    
    print("\n2. Loading Gemini's labels...")
    gemini_data = load_gemini_aspects(gemini_csv)
    print(f"   Loaded {len(gemini_data)} reviews from Gemini")
    total_gemini = sum(len(aspects) for aspects in gemini_data.values())
    print(f"   Total aspects: {total_gemini}")
    
    # Calculate metrics
    print("\n3. Calculating metrics...")
    
    results = []
    total_recall = 0
    total_precision = 0
    total_f1 = 0
    total_tp = 0
    total_fn = 0
    total_fp = 0
    
    all_reviews = sorted(set(rita_data.keys()) | set(gemini_data.keys()))
    
    for review_id in all_reviews:
        rita = rita_data.get(review_id, [])
        gemini = gemini_data.get(review_id, [])
        
        recall, precision, f1, tp, fn, fp, details = calculate_metrics(rita, gemini)
        
        results.append({
            'Review_ID': review_id,
            'Rita_Aspects': ', '.join(rita) if rita else 'NONE',
            'Rita_Count': len(rita),
            'Gemini_Aspects': ', '.join(gemini) if gemini else 'NONE',
            'Gemini_Count': len(gemini),
            'True_Positives': tp,
            'False_Negatives': fn,
            'False_Positives': fp,
            'Recall': f"{recall:.3f}",
            'Precision': f"{precision:.3f}",
            'F1_Score': f"{f1:.3f}",
            'Details': details
        })
        
        total_recall += recall
        total_precision += precision
        total_f1 += f1
        total_tp += tp
        total_fn += fn
        total_fp += fp
    
    # Write results
    print(f"\n4. Writing results to {output_csv}...")
    with open(output_csv, 'w', newline='', encoding='utf-8') as f:
        if results:
            writer = csv.DictWriter(f, fieldnames=results[0].keys())
            writer.writeheader()
            writer.writerows(results)
    
    # Calculate averages
    num_reviews = len(results)
    
    # Macro-averaged (average per review)
    macro_recall = (total_recall / num_reviews * 100) if num_reviews > 0 else 0
    macro_precision = (total_precision / num_reviews * 100) if num_reviews > 0 else 0
    macro_f1 = (total_f1 / num_reviews * 100) if num_reviews > 0 else 0
    
    # Micro-averaged (aggregate then calculate)
    micro_recall = (total_tp / (total_tp + total_fn) * 100) if (total_tp + total_fn) > 0 else 0
    micro_precision = (total_tp / (total_tp + total_fp) * 100) if (total_tp + total_fp) > 0 else 0
    
    if micro_recall + micro_precision > 0:
        micro_f1 = 2 * (micro_recall * micro_precision) / (micro_recall + micro_precision)
    else:
        micro_f1 = 0
    
    # Print results
    print("\n" + "="*80)
    print("RESULTS SUMMARY")
    print("="*80)
    
    print(f"\nReviews Evaluated: {num_reviews}")
    print(f"Total Rita Aspects: {total_rita}")
    print(f"Total Gemini Aspects: {total_gemini}")
    
    print(f"\nAspect Detection Performance:")
    print(f"  True Positives (TP):  {total_tp:3d} - Aspects Gemini correctly identified")
    print(f"  False Negatives (FN): {total_fn:3d} - Rita's aspects Gemini missed")
    print(f"  False Positives (FP): {total_fp:3d} - Gemini's aspects Rita didn't label")
    
    print(f"\n{'─'*80}")
    print("MACRO-AVERAGED METRICS (average per review):")
    print(f"{'─'*80}")
    print(f"  Recall:    {macro_recall:6.2f}% - Did Gemini catch Rita's aspects?")
    print(f"  Precision: {macro_precision:6.2f}% - Were Gemini's aspects correct?")
    print(f"  F1-Score:  {macro_f1:6.2f}% - Overall performance")
    
    print(f"\n{'─'*80}")
    print("MICRO-AVERAGED METRICS (aggregate all aspects):")
    print(f"{'─'*80}")
    print(f"  Recall:    {micro_recall:6.2f}%")
    print(f"  Precision: {micro_precision:6.2f}%")
    print(f"  F1-Score:  {micro_f1:6.2f}%")
    
    # Decision
    print("\n" + "="*80)
    
    decision_metric = micro_f1
    
    if decision_metric >= 80:
        print("✅ DECISION: GREEN LIGHT - USE GEMINI FLASH LITE")
        print("="*80)
        print(f"\nMicro F1-Score: {decision_metric:.2f}% (Threshold: ≥80%)")
        print("\nInterpretation:")
        print(f"  - Gemini catches {micro_recall:.1f}% of all aspects Rita labeled")
        print(f"  - {micro_precision:.1f}% of Gemini's aspects are accurate")
        print("\nNext Steps:")
        print("  1. ✅ Proceed with Gemini Flash Lite for production")
        print("  2. 📊 Document these metrics in Blueprint")
        print("  3. 📈 Monitor production for drift (re-audit quarterly)")
    else:
        print("🚨 DECISION: RED FLAG - DO NOT USE GEMINI FLASH LITE")
        print("="*80)
        print(f"\nMicro F1-Score: {decision_metric:.2f}% (Threshold: ≥80%)")
        print("\nInterpretation:")
        print(f"  - Gemini only catches {micro_recall:.1f}% of Rita's aspects")
        print(f"  - Only {micro_precision:.1f}% of Gemini's aspects are accurate")
        print("\nAction Required:")
        print("  1. 🚨 FLAG TO SAHAL IMMEDIATELY")
        print(f"  2. 📁 Review {output_csv} for failure patterns")
        print("  3. 🔧 Options:")
        print("     a) Refine prompts and re-test")
        print("     b) Upgrade to Gemini Flash Standard")
        print("     c) Use Claude Sonnet instead")
        print("  4. ⛔ DO NOT use Flash Lite for production")
        
        # Show worst cases
        print("\nWorst Performing Reviews (F1 < 0.50):")
        sorted_results = sorted(results, key=lambda x: float(x['F1_Score']))
        count = 0
        for r in sorted_results:
            if float(r['F1_Score']) < 0.50 and count < 10:
                print(f"  {r['Review_ID']}: F1={r['F1_Score']} - {r['Details']}")
                count += 1
    
    print("\n" + "="*80)
    print(f"\n📁 Full results saved to: {output_csv}")
    print("="*80 + "\n")
    
    return {
        'macro_f1': macro_f1,
        'micro_f1': micro_f1,
        'micro_recall': micro_recall,
        'micro_precision': micro_precision,
        'total_tp': total_tp,
        'total_fn': total_fn,
        'total_fp': total_fp
    }

if __name__ == '__main__':
    RITA_CSV = '/mnt/user-data/uploads/RRE_Blind_Test_Set_csv_-_RRE_Blind_Test_Set_Rita.csv'
    GEMINI_CSV = '/mnt/user-data/uploads/RRE_Blind_Test_Set_csv_-_RRE_Blind_Test_Set_Geimini_2.csv'
    OUTPUT_CSV = '/home/claude/RRE_Accuracy_Audit_Results.csv'
    
    metrics = run_audit(RITA_CSV, GEMINI_CSV, OUTPUT_CSV)
