import os
import pandas as pd
import numpy as np
import json
import random
from pathlib import Path
from datetime import datetime, timedelta, date
from typing import List, Dict, Any
import zipfile
import io
import os, zipfile



# ============================================
# 1. DOWNLOAD REAL DATASETS
# ===========================================
# Setup

import sys

# Base directory of this script
exe_dir = Path(__file__).resolve().parent
print(exe_dir)

# Create folders inside that directory
for folder in ["training_data", "training_jsonl", "real_datasets"]:
    target = exe_dir/folder
    target.mkdir(exist_ok=True)
    print(f"📂 Created folder: {target}")


def download_real_datasets():


    # UCI dataset (unchanged)
    try:
        url = "https://archive.ics.uci.edu/ml/machine-learning-databases/adult/adult.data"
        cols = ['age','workclass','fnlwgt','education','education-num','marital-status','occupation',
                'relationship','race','sex','capital-gain','capital-loss','hours-per-week','native-country','income']
        df = pd.read_csv(url, header=None, names=cols)
        Path("real_datasets").mkdir(exist_ok=True)
        df.to_csv(exe_dir/"real_datasets/adult_income.csv", index=False)
        print("  ✅ Downloaded: UCI Adult Income")
    except Exception as e:
        print(f"  ⚠️  Failed to download UCI data: {e}")

    print("✅ All datasets processed!\n")


# ============================================
# 2. LOAD REAL DATASETS
# ============================================

def load_real_datasets():
    """Load all downloaded real datasets"""
    datasets = {}
    
    try:
        superstore_path = list(Path(exe_dir/'real_datasets').glob('*superstore*.csv*'))[0]
        datasets['superstore'] = pd.read_csv(superstore_path, encoding='latin1')
        print(f"✅ Loaded Superstore: {len(datasets['superstore'])} rows")
    except Exception as e:
        print(f"⚠️  Superstore not found: {e}")
    
    try:
        hr_path = list(Path(exe_dir/'real_datasets').glob('*hr_d*.csv'))[0]
        datasets['hr'] = pd.read_csv(hr_path)
        print(f"✅ Loaded HR Analytics: {len(datasets['hr'])} rows")
    except Exception as e:
        print(f"⚠️  HR Analytics not found: {e}")
    
    try:
        netflix_path = list(Path(exe_dir/'real_datasets').glob('*netflix_*.csv'))[0]
        datasets['netflix'] = pd.read_csv(netflix_path)
        print(f"✅ Loaded Netflix: {len(datasets['netflix'])} rows")
    except Exception as e:
        print(f"⚠️  Netflix not found: {e}")
    
    try:
        ecommerce_path = list(Path(exe_dir/'real_datasets').glob('*data.csv'))[0]
        datasets['ecommerce'] = pd.read_csv(ecommerce_path, encoding='latin1')
        print(f"✅ Loaded E-commerce: {len(datasets['ecommerce'])} rows")
    except Exception as e:
        print(f"⚠️  E-commerce not found: {e}")
    
    try:
        datasets['adult'] = pd.read_csv(exe_dir/'real_datasets/adult_income.csv')
        print(f"✅ Loaded Adult Income: {len(datasets['adult'])} rows")
    except Exception as e:
        print(f"⚠️  Adult Income not found: {e}")
    
    return datasets

# ============================================
# 3. CONTEXT BUILDER
# ============================================

def build_context(sheets: Dict[str, pd.DataFrame], focus_sheet: str = None, rows_limit: int = 50):
    """Build standardized workbook context"""
    summary = f"WORKBOOK: {len(sheets)} sheets\n"
    summary += "SUMMARY: " + "; ".join([f"{name} (rows={len(df)}, cols={len(df.columns)})" for name, df in sheets.items()]) + "\n\n"
    
    for sheet_name, df in sheets.items():
        if focus_sheet and sheet_name.lower() != focus_sheet.lower():
            continue
        
        summary += f"SHEET: {sheet_name}\n"
        summary += f"COLUMNS: {', '.join(df.columns)}\n"
        
        sample = df.head(min(rows_limit, len(df)))
        summary += f"ROWS (showing {len(sample)} of {len(df)}):\n"
        for _, row in sample.iterrows():
            summary += " | ".join([str(v) for v in row.values]) + "\n"
        summary += "\n"
    
    return summary.strip()

def _to_json_safe(obj: Any) -> Any:
    """Recursively convert pandas/numpy/datetime objects and non-JSON-safe keys to JSON-safe types."""
    try:
        import pandas as _pd  # local import to avoid issues if pandas not loaded yet
        import numpy as _np
    except Exception:
        _pd = None
        _np = None

    # Mappings: ensure keys are JSON-safe (str/int/float/bool/None) and values processed
    if isinstance(obj, dict):
        safe_dict = {}
        for k, v in obj.items():
            # Normalize key
            if isinstance(k, (str, int, float, bool)) or k is None:
                safe_key = k
            else:
                # Special handling for datetimes
                if (_pd is not None and isinstance(k, (_pd.Timestamp,))) or isinstance(k, (datetime,)):
                    try:
                        safe_key = (k if isinstance(k, datetime) else _pd.Timestamp(k)).isoformat()
                    except Exception:
                        safe_key = str(k)
                elif _np is not None and isinstance(k, (_np.generic,)):
                    # numpy scalar key -> convert to native Python, then keep if allowed else str()
                    native_k = k.item()
                    if isinstance(native_k, (str, int, float, bool)) or native_k is None:
                        safe_key = native_k
                    else:
                        safe_key = str(native_k)
                else:
                    safe_key = str(k)

            safe_dict[safe_key] = _to_json_safe(v)
        return safe_dict

    # Sequences
    if isinstance(obj, list):
        return [_to_json_safe(x) for x in obj]
    if isinstance(obj, tuple):
        return [_to_json_safe(x) for x in obj]

    # pandas/NumPy containers
    if _pd is not None and isinstance(obj, (_pd.Series, _pd.Index)):
        return _to_json_safe(obj.tolist())
    if _np is not None and isinstance(obj, _np.ndarray):
        return _to_json_safe(obj.tolist())

    # Date/time-like
    if (_pd is not None and isinstance(obj, (_pd.Timestamp,))) or isinstance(obj, (datetime, date)):
        try:
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            return _pd.Timestamp(obj).isoformat()
        except Exception:
            return str(obj)
    if _np is not None and isinstance(obj, _np.datetime64):
        try:
            return _pd.Timestamp(obj).isoformat() if _pd is not None else str(obj)
        except Exception:
            return str(obj)

    # Timedelta-like
    if _pd is not None and isinstance(obj, _pd.Timedelta):
        return str(obj)
    if _np is not None and isinstance(obj, _np.timedelta64):
        return str(obj)

    # NumPy scalars
    if _np is not None and isinstance(obj, _np.bool_):
        return bool(obj)
    if _np is not None and isinstance(obj, (_np.integer,)):
        return int(obj)
    if _np is not None and isinstance(obj, (_np.floating,)):
        # Handle nan/inf gracefully
        if _np.isnan(obj):
            return None
        return float(obj)

    # pandas NA
    if _pd is not None:
        try:
            # pd.isna works on many scalars
            if _pd.isna(obj):
                return None
        except Exception:
            pass

    return obj


def build_training_example(context: str, question: str, answer: Dict[str, Any]):
    """Create a single training example"""
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are a spreadsheet analyst. Use ONLY the provided context. For structured tasks, return JSON only as specified. If 'SheetName' is quoted, use that exact sheet (case-insensitive) and ignore others. Full Name = First_Name + ' ' + Last_Name (case-insensitive, trimmed). City = exact equality (case-insensitive, trimmed). Return 'insufficient' when context is incomplete."
            },
            {
                "role": "user",
                "content": context + f"\n\nQuestion: {question}"
            },
            {
                "role": "assistant",
                "content": json.dumps(_to_json_safe(answer), indent=2, ensure_ascii=False)
            }
        ]
    }

def create_example(df, sheet_name, question, answer):
    """Helper to create training example"""
    context = build_context({sheet_name: df}, focus_sheet=sheet_name)
    return build_training_example(context, f"On sheet '{sheet_name}' {question}", answer)

# ============================================
# 4. UNIVERSAL 100+ TASK TYPE GENERATOR
# ============================================

def generate_diverse_tasks(df: pd.DataFrame, sheet_name: str, n_samples: int = 10000):
    """
    Generate 100+ diverse task types from any dataset
    """
    examples = []
    
    # Get column info
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns.tolist()
    date_cols = [col for col in df.columns if 'date' in col.lower() or 'year' in col.lower()]
    
    task_types = 100
    per_task = max(1, n_samples // task_types)
    
    print(f"    Generating {task_types} task types for {sheet_name}...")
    
    # ==========================================
    # CATEGORY 1: BASIC COUNTS (10 types)
    # ==========================================
    
    # Type 1: Simple count
    if categorical_cols:
        for _ in range(per_task):
            col = random.choice(categorical_cols)
            val = random.choice(df[col].dropna().unique())
            count = len(df[df[col] == val])
            examples.append(create_example(df, sheet_name, 
                f"How many records have {col} equal to '{val}'?",
                {"count": count, "criteria": {col: val}, "insufficient": False}))
    
    # Type 2: Count with NOT
    if categorical_cols:
        for _ in range(per_task):
            col = random.choice(categorical_cols)
            val = random.choice(df[col].dropna().unique())
            count = len(df[df[col] != val])
            examples.append(create_example(df, sheet_name,
                f"How many records have {col} NOT equal to '{val}'?",
                {"count": count, "criteria": {col: f"NOT {val}"}, "insufficient": False}))
    
    # Type 3: Count with IN
    if categorical_cols:
        for _ in range(per_task):
            col = random.choice(categorical_cols)
            vals = random.sample(list(df[col].dropna().unique()), min(3, len(df[col].unique())))
            count = len(df[df[col].isin(vals)])
            examples.append(create_example(df, sheet_name,
                f"How many records have {col} in {vals}?",
                {"count": count, "criteria": {col: f"IN {vals}"}, "insufficient": False}))
    
    # Type 4: Text contains
    if categorical_cols:
        for _ in range(per_task):
            col = random.choice(categorical_cols)
            val = str(random.choice(df[col].dropna().unique()))
            if len(val) > 3:
                substring = val[:len(val)//2]
                count = len(df[df[col].astype(str).str.contains(substring, na=False, case=False)])
                examples.append(create_example(df, sheet_name,
                    f"How many records have {col} containing '{substring}'?",
                    {"count": count, "criteria": {col: f"CONTAINS {substring}"}, "insufficient": False}))
    
    # Type 5-10: Multi-criteria AND
    if len(categorical_cols) >= 2:
        for _ in range(per_task * 6):
            col1, col2 = random.sample(categorical_cols, 2)
            val1 = random.choice(df[col1].dropna().unique())
            val2 = random.choice(df[col2].dropna().unique())
            count = len(df[(df[col1] == val1) & (df[col2] == val2)])
            examples.append(create_example(df, sheet_name,
                f"How many records have {col1}='{val1}' AND {col2}='{val2}'?",
                {"count": count, "criteria": {col1: val1, col2: val2}, "insufficient": False}))
    
    # ==========================================
    # CATEGORY 2: AGGREGATIONS (30 types)
    # ==========================================
    
    if numeric_cols:
        operations = [
            ('sum', lambda x: x.sum()),
            ('avg', lambda x: x.mean()),
            ('min', lambda x: x.min()),
            ('max', lambda x: x.max()),
            ('median', lambda x: x.median()),
            ('std', lambda x: x.std())
        ]
        
        for op_name, op_func in operations:
            # Simple aggregation
            for _ in range(per_task):
                col = random.choice(numeric_cols)
                result = round(float(op_func(df[col].dropna())), 2) if len(df[col].dropna()) > 0 else 0
                examples.append(create_example(df, sheet_name,
                    f"What is the {op_name} of {col}?",
                    {"operation": op_name, "column": col, "result": result, "insufficient": False}))
            
            # Aggregation with filter
            if categorical_cols:
                for _ in range(per_task):
                    num_col = random.choice(numeric_cols)
                    cat_col = random.choice(categorical_cols)
                    val = random.choice(df[cat_col].dropna().unique())
                    filtered = df[df[cat_col] == val]
                    result = round(float(op_func(filtered[num_col].dropna())), 2) if len(filtered) > 0 else 0
                    examples.append(create_example(df, sheet_name,
                        f"What is the {op_name} of {num_col} where {cat_col}='{val}'?",
                        {"operation": op_name, "column": num_col, "filters": {cat_col: val}, "result": result, "insufficient": len(filtered)==0}))
            
            # Aggregation with group by
            if categorical_cols:
                for _ in range(per_task):
                    num_col = random.choice(numeric_cols)
                    cat_col = random.choice(categorical_cols)
                    result = df.groupby(cat_col)[num_col].apply(op_func).round(2).to_dict()
                    examples.append(create_example(df, sheet_name,
                        f"What is the {op_name} of {num_col} grouped by {cat_col}?",
                        {"operation": op_name, "column": num_col, "group_by": cat_col, "result": result, "insufficient": False}))
            
            # Aggregation with range
            if len(numeric_cols) >= 2:
                for _ in range(per_task):
                    num_col = random.choice(numeric_cols)
                    filter_col = random.choice(numeric_cols)
                    min_val = round(float(df[filter_col].quantile(0.25)), 2)
                    max_val = round(float(df[filter_col].quantile(0.75)), 2)
                    filtered = df[(df[filter_col] >= min_val) & (df[filter_col] <= max_val)]
                    result = round(float(op_func(filtered[num_col].dropna())), 2) if len(filtered) > 0 else 0
                    examples.append(create_example(df, sheet_name,
                        f"What is the {op_name} of {num_col} where {filter_col} is between {min_val} and {max_val}?",
                        {"operation": op_name, "column": num_col, "filters": {filter_col: f"{min_val}-{max_val}"}, "result": result, "insufficient": False}))
    
    # ==========================================
    # CATEGORY 3: PERCENTILES (10 types)
    # ==========================================
    
    if numeric_cols:
        for percentile in [10, 25, 50, 75, 90, 95, 99]:
            for _ in range(per_task):
                col = random.choice(numeric_cols)
                result = round(float(df[col].quantile(percentile/100)), 2)
                examples.append(create_example(df, sheet_name,
                    f"What is the {percentile}th percentile of {col}?",
                    {"operation": f"percentile_{percentile}", "column": col, "result": result, "insufficient": False}))
    
    # ==========================================
    # CATEGORY 4: DISTINCT COUNTS (5 types)
    # ==========================================
    
    for _ in range(per_task * 5):
        col = random.choice(df.columns)
        count = int(df[col].nunique())
        examples.append(create_example(df, sheet_name,
            f"How many distinct values are in column {col}?",
            {"operation": "count_distinct", "column": col, "result": count, "insufficient": False}))
    
    # ==========================================
    # CATEGORY 5: NULL ANALYSIS (5 types)
    # ==========================================
    
    for _ in range(per_task * 5):
        col = random.choice(df.columns)
        null_count = int(df[col].isna().sum())
        examples.append(create_example(df, sheet_name,
            f"How many null/missing values are in column {col}?",
            {"operation": "count_nulls", "column": col, "result": null_count, "insufficient": False}))
    
    # ==========================================
    # CATEGORY 6: DATE/TIME (10 types)
    # ==========================================
    
    if date_cols:
        date_col = date_cols[0]
        df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
        
        # By year
        for _ in range(per_task * 3):
            years = df[date_col].dt.year.dropna().unique()
            if len(years) > 0:
                year = random.choice(years)
                count = len(df[df[date_col].dt.year == year])
                examples.append(create_example(df, sheet_name,
                    f"How many records are from year {int(year)}?",
                    {"count": count, "criteria": {"year": int(year)}, "insufficient": False}))
        
        # Date range
        for _ in range(per_task * 7):
            valid_dates = df[date_col].dropna()
            if len(valid_dates) > 0:
                start = valid_dates.min()
                end = start + pd.DateOffset(months=random.randint(1, 12))
                count = len(df[(df[date_col] >= start) & (df[date_col] <= end)])
                examples.append(create_example(df, sheet_name,
                    f"How many records are between {start.date()} and {end.date()}?",
                    {"count": count, "criteria": {"date_range": f"{start.date()} to {end.date()}"}, "insufficient": False}))

    # After potentially converting columns to datetime above, refresh numeric_cols
    try:
        from pandas.api import types as pdt
        numeric_cols = [
            c for c in numeric_cols
            if pdt.is_numeric_dtype(df[c]) and not pdt.is_datetime64_any_dtype(df[c]) and not pdt.is_timedelta64_dtype(df[c])
        ]
    except Exception:
        # Fallback: keep only columns that are still numpy-number dtypes
        numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # ==========================================
    # CATEGORY 7: RATIOS (5 types)
    # ==========================================
    
    if len(numeric_cols) >= 2:
        for _ in range(per_task * 5):
            col1, col2 = random.sample(numeric_cols, 2)
            df['temp_ratio'] = df[col1] / (df[col2].replace(0, np.nan))
            avg_ratio = round(float(df['temp_ratio'].mean()), 2) if df['temp_ratio'].notna().any() else 0
            examples.append(create_example(df, sheet_name,
                f"What is the average ratio of {col1} to {col2}?",
                {"operation": "avg_ratio", "columns": [col1, col2], "result": avg_ratio, "insufficient": False}))
            df.drop('temp_ratio', axis=1, inplace=True)
    
    # ==========================================
    # CATEGORY 8: TOP/BOTTOM N (10 types)
    # ==========================================
    
    if numeric_cols and categorical_cols:
        for _ in range(per_task * 5):
            num_col = random.choice(numeric_cols)
            cat_col = random.choice(categorical_cols)
            top_n = df.groupby(cat_col)[num_col].sum().nlargest(3).to_dict()
            examples.append(create_example(df, sheet_name,
                f"What are the top 3 {cat_col} by total {num_col}?",
                {"operation": "top_n", "n": 3, "group_by": cat_col, "column": num_col, "result": top_n, "insufficient": False}))
        
        for _ in range(per_task * 5):
            num_col = random.choice(numeric_cols)
            cat_col = random.choice(categorical_cols)
            bottom_n = df.groupby(cat_col)[num_col].sum().nsmallest(3).to_dict()
            examples.append(create_example(df, sheet_name,
                f"What are the bottom 3 {cat_col} by total {num_col}?",
                {"operation": "bottom_n", "n": 3, "group_by": cat_col, "column": num_col, "result": bottom_n, "insufficient": False}))
    
    # ==========================================
    # CATEGORY 9: MULTI-COLUMN GROUPING (5 types)
    # ==========================================
    
    if len(categorical_cols) >= 2 and numeric_cols:
        for _ in range(per_task * 5):
            cat1, cat2 = random.sample(categorical_cols, 2)
            num_col = random.choice(numeric_cols)
            result = df.groupby([cat1, cat2])[num_col].sum().head(10).to_dict()
            examples.append(create_example(df, sheet_name,
                f"What is the total {num_col} grouped by {cat1} and {cat2}?",
                {"operation": "sum", "group_by": [cat1, cat2], "column": num_col, "result": str(result), "insufficient": False}))
    
    # ==========================================
    # CATEGORY 10: EDGE CASES (10 types)
    # ==========================================
    
    # Missing column
    for _ in range(per_task * 5):
        fake_col = f"NonExistent_{random.randint(1,1000)}"
        examples.append(create_example(df, sheet_name,
            f"What is the average of column {fake_col}?",
            {"operation": "avg", "column": fake_col, "result": None, "insufficient": True, "reason": f"Column '{fake_col}' does not exist."}))
    
    # Empty result
    if categorical_cols:
        for _ in range(per_task * 5):
            col = random.choice(categorical_cols)
            fake_val = f"NonExistent_{random.randint(1,1000)}"
            examples.append(create_example(df, sheet_name,
                f"How many records have {col}='{fake_val}'?",
                {"count": 0, "criteria": {col: fake_val}, "insufficient": True, "reason": "No matching records."}))
    
    print(f"    ✅ Generated {len(examples)} examples for {sheet_name}")
    return examples

# ============================================
# 5. MAIN EXECUTION
# ============================================

def main():
    # Inference mode (optional)
    try:
        import argparse
        parser = argparse.ArgumentParser(description="Train or query finetuned Ollama model with file context.")
        parser.add_argument('--ask', type=str, help='Question to ask the model (enables inference mode).')
        parser.add_argument('--files', nargs='*', help='CSV file paths to include as sheets in context.')
        parser.add_argument('--model', type=str, default='my-finetuned-model', help='Ollama model name to use.')
        parser.add_argument('--rows-limit', type=int, default=50, help='Rows per sheet to include in context.')
        parser.add_argument('--focus-sheet', type=str, default=None, help='Optional specific sheet name to focus on.')
        args, _unknown = parser.parse_known_args()
        if args.ask:
            if not args.files:
                print("--files required with --ask")
                return
            from training_model.inference_wrapper import read_csvs_to_sheets, call_ollama_chat
            sheets = read_csvs_to_sheets(args.files)
            if not sheets:
                print("No readable CSV files provided.")
                return
            context = build_context(sheets, focus_sheet=args.focus_sheet, rows_limit=args.rows_limit)
            system_prompt = (
                "You are a spreadsheet analyst. Use ONLY the provided context. For structured tasks, return JSON only as specified. "
                "If 'SheetName' is quoted, use that exact sheet (case-insensitive) and ignore others. "
                "Full Name = First_Name + ' ' + Last_Name (case-insensitive, trimmed). City = exact equality (case-insensitive, trimmed). "
                "Return 'insufficient' when context is incomplete."
            )
            user_content = context + f"\n\nQuestion: {args.ask}"
            try:
                answer = call_ollama_chat(args.model, system_prompt, user_content)
                print("\n--- Model Answer ---\n")
                print(answer)
            except Exception as rexc:
                print(f"Ollama request failed: {rexc}")
            return
    except Exception:
        # If argparse not available or error, continue with training mode
        pass

    # Step 1: Download datasets
    download_real_datasets()
    
    # Step 2: Load datasets
    print("\n📂 Loading real datasets...")
    datasets = load_real_datasets()
    
    if not datasets:
        print("❌ No datasets loaded. Please check downloads.")
        return
    
    # Step 3: Generate training examples
    print("\n📊 Generating 50,000+ training examples with 100+ task types per dataset...")
    all_examples = []
    
    if 'superstore' in datasets :
        print("  ⏳ Superstore Orders (10,000 examples)...")
        all_examples.extend(generate_diverse_tasks(datasets['superstore'], 'superstore', 10000))
    
    if 'hr' in datasets:
        print("  ⏳ HR Analytics (15,000 examples)...")
        all_examples.extend(generate_diverse_tasks(datasets['hr'], 'HR_Analytics', 15000))
    
    if 'netflix' in datasets:
        print("  ⏳ Netflix (10,000 examples)...")
        all_examples.extend(generate_diverse_tasks(datasets['netflix'], 'Netflix', 10000))
    
    if 'ecommerce' in datasets:
        print("  ⏳ E-commerce (10,000 examples)...")
        all_examples.extend(generate_diverse_tasks(datasets['ecommerce'], 'Ecommerce', 10000))
    
    if 'adult' in datasets:
        print("  ⏳ Adult Income (5,000 examples)...")
        all_examples.extend(generate_diverse_tasks(datasets['adult'], 'Adult_Income', 5000))
    
    # Shuffle
    random.shuffle(all_examples)
    
    # Save JSONL
    output_path = Path(exe_dir/"training_jsonl/real_data_50k_diverse_train.jsonl")
    with open(output_path, "w", encoding="utf-8") as f:
        for ex in all_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")
    
    print(f"\n✅ Successfully generated {len(all_examples)} training examples!")
    print(f"📁 Saved to: {output_path}")
    print(f"\n📈 Each dataset has 100+ diverse task types covering:")
    print(f"   - Basic counts (10 types)")
    print(f"   - Aggregations (30 types)")
    print(f"   - Percentiles (10 types)")
    print(f"   - Distinct/Null analysis (10 types)")
    print(f"   - Date/Time operations (10 types)")
    print(f"   - Ratios & calculations (5 types)")
    print(f"   - Top/Bottom rankings (10 types)")
    print(f"   - Multi-column grouping (5 types)")
    print(f"   - Edge cases (10 types)")
    print(f"   TOTAL: 100+ task types per dataset")

if __name__ == "__main__":
    main()
