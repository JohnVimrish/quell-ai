import pandas as pd
import numpy as np
import json
import random
from pathlib import Path
from datetime import datetime, date
from typing import List, Dict, Any
import re
import argparse

import sys

# Base directory of this script
exe_dir = Path(__file__).resolve().parent
print(exe_dir)





# ============================================
# 2. LOAD LARGE DATASETS
# ============================================

def load_large_datasets():
    """Load large datasets with proper handling"""
    datasets = {}
    
    # Brazilian E-commerce (100+ MB, multi-file)
    try:

        orders = pd.read_csv(exe_dir/'real_datasets/olist_orders_dataset.csv')
        order_items = pd.read_csv(exe_dir/'real_datasets/olist_order_items_dataset.csv')
        products = pd.read_csv(exe_dir/'real_datasets/olist_products_dataset.csv')
        customers = pd.read_csv(exe_dir/'real_datasets/olist_customers_dataset.csv')
        datasets['brazilian_ecommerce'] = {
            'orders': orders,
            'order_items': order_items,
            'products': products,
            'customers': customers
        }
        print(f"Loaded Brazilian E-commerce: {len(orders)} orders")
    except Exception as e:
        print(f"Brazilian E-commerce not found: {e}")
    
    # NYC Parking Tickets (multiple yearly files)
    try:
        base = Path(exe_dir/'real_datasets')
        patterns = [
            'Parking_Violations_Issued*.csv'  ]
        files = []
        for pat in patterns:
            files.extend(sorted(base.glob(pat)))
        # Deduplicate preserving order
        seen = set()
        files = [f for f in files if not (f in seen or seen.add(f))]
        # Fallback to single default file if present
        default_csv = base / 'Parking_Violations_Issued.csv'
        if not files and default_csv.exists():
            files = [default_csv]

        if files:
            target_total = 200_000
            per_file = max(20_000, target_total // max(1, len(files)))
            samples = []
            total_loaded = 0
            for fpath in files:
                if total_loaded >= target_total:
                    break
                nrows = min(per_file, target_total - total_loaded)
                try:
                    df_part = pd.read_csv(fpath, nrows=nrows)
                    # Add a simple year/tag from filename if available
                    m = re.search(r'(20\d{2})', fpath.name)
                    if m and 'SourceYear' not in df_part.columns:
                        df_part['SourceYear'] = int(m.group(1))
                    samples.append(df_part)
                    total_loaded += len(df_part)
                except Exception as e_inner:
                    print(f"  Skipped {fpath.name}: {e_inner}")
            if samples:
                parking = pd.concat(samples, ignore_index=True, sort=False)
                datasets['nyc_parking'] = parking
                print(f"Loaded NYC Parking: {len(parking)} rows from {len(samples)} file(s)")
        else:
            print("NYC Parking files not found.")
    except Exception as e:
        print(f"NYC Parking not found: {e}")
    
    

    
    # COVID-19 (100+ MB)
    try:
        covid_files = list(Path(exe_dir/'real_datasets').glob('*covid*.csv'))
        if covid_files:
            covid = pd.read_csv(covid_files[0], nrows=50000)
            datasets['covid'] = covid
            print(f"Loaded COVID-19: {len(covid)} records")
    except Exception as e:
        print(f"COVID-19 not found: {e}")
    
    return datasets

# ============================================
# 3. CONTEXT BUILDER (Same as before)
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
        import pandas as _pd
        import numpy as _np
    except Exception:
        _pd = None
        _np = None

    if isinstance(obj, dict):
        safe = {}
        for k, v in obj.items():
            if isinstance(k, (str, int, float, bool)) or k is None:
                key = k
            else:
                if (_pd is not None and isinstance(k, (_pd.Timestamp,))) or isinstance(k, (datetime,)):
                    try:
                        key = (k if isinstance(k, datetime) else _pd.Timestamp(k)).isoformat()
                    except Exception:
                        key = str(k)
                elif _np is not None and isinstance(k, (_np.generic,)):
                    native = k.item()
                    key = native if isinstance(native, (str, int, float, bool)) or native is None else str(native)
                else:
                    key = str(k)
            safe[key] = _to_json_safe(v)
        return safe

    if isinstance(obj, list):
        return [_to_json_safe(x) for x in obj]
    if isinstance(obj, tuple):
        return [_to_json_safe(x) for x in obj]

    if _pd is not None and isinstance(obj, (_pd.Series, _pd.Index)):
        return _to_json_safe(obj.tolist())
    if _np is not None and isinstance(obj, _np.ndarray):
        return _to_json_safe(obj.tolist())

    if (_pd is not None and isinstance(obj, (_pd.Timestamp,))) or isinstance(obj, (datetime, date)):
        try:
            return obj.isoformat() if isinstance(obj, (datetime, date)) else _pd.Timestamp(obj).isoformat()
        except Exception:
            return str(obj)
    if _np is not None and isinstance(obj, _np.datetime64):
        try:
            return _pd.Timestamp(obj).isoformat() if _pd is not None else str(obj)
        except Exception:
            return str(obj)

    if _pd is not None and isinstance(obj, _pd.Timedelta):
        return str(obj)
    if _np is not None and isinstance(obj, _np.timedelta64):
        return str(obj)

    if _np is not None and isinstance(obj, _np.bool_):
        return bool(obj)
    if _np is not None and isinstance(obj, (_np.integer,)):
        return int(obj)
    if _np is not None and isinstance(obj, (_np.floating,)):
        try:
            return None if _np.isnan(obj) else float(obj)
        except Exception:
            return float(obj)

    if _pd is not None:
        try:
            if _pd.isna(obj):
                return None
        except Exception:
            pass

    return obj


def safe_mean(x):
    """Return mean of numeric values, 0.0 if empty/all-NaN. Accepts Series, arrays, lists, or scalars."""
    try:
        s = x if isinstance(x, pd.Series) else pd.Series(x)
    except Exception:
        try:
            s = pd.Series(list(x))
        except Exception:
            s = pd.Series([x])
    s = pd.to_numeric(s, errors='coerce').dropna()
    return float(s.mean()) if len(s) else 0.0


def build_training_example(context: str, question: str, answer: Dict[str, Any]):
    """Create a single training example"""
    return {
        "messages": [
            {
                "role": "system",
                "content": "You are a spreadsheet analyst. Use ONLY the provided context. For structured tasks, return JSON only as specified. If 'SheetName' is quoted, use that exact sheet (case-insensitive) and ignore others. Return 'insufficient' when context is incomplete."
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
# 4. DOMAIN-SPECIFIC TASK GENERATORS
# ============================================

def generate_ecommerce_tasks(ecom_sheets: Dict[str, pd.DataFrame], n_samples: int = 5000):
    """E-commerce specific analytical questions"""
    examples = []
    per_task = n_samples // 20
    
    if 'orders' in ecom_sheets and 'order_items' in ecom_sheets:
        orders = ecom_sheets['orders']
        items = ecom_sheets['order_items']
        
        # Revenue analysis
        for _ in range(per_task):
            merged = orders.merge(items, on='order_id')
            merged['revenue'] = merged['price'] + merged['freight_value']
            total_revenue = round(merged['revenue'].sum(), 2)
            
            examples.append(create_example(
                orders, 'Orders',
                "What is the total revenue (price + freight) from all orders?",
                {"operation": "revenue_sum", "result": total_revenue, "insufficient": False}
            ))
        
        # Average order value
        for _ in range(per_task):
            avg_order = round(safe_mean(items.groupby('order_id')['price'].sum()), 2)
            examples.append(create_example(
                items, 'OrderItems',
                "What is the average order value?",
                {"operation": "avg", "result": avg_order, "insufficient": False}
            ))
        
        # Orders by status
        for _ in range(per_task):
            status = random.choice(orders['order_status'].unique())
            count = len(orders[orders['order_status'] == status])
            examples.append(create_example(
                orders, 'Orders',
                f"How many orders have status '{status}'?",
                {"count": count, "criteria": {"order_status": status}, "insufficient": False}
            ))
        
        # Top selling products
        for _ in range(per_task):
            top_products = items.groupby('product_id')['price'].sum().nlargest(5).to_dict()
            examples.append(create_example(
                items, 'OrderItems',
                "What are the top 5 products by total sales?",
                {"operation": "top_n", "n": 5, "result": top_products, "insufficient": False}
            ))
    
    return examples

def generate_bank_marketing_tasks(bank: pd.DataFrame, n_samples: int = 5000):
    """Bank marketing campaign analysis"""
    examples = []
    per_task = n_samples // 20
    
    # Conversion rate by job
    for _ in range(per_task):
        job = random.choice(bank['job'].unique())
        total = len(bank[bank['job'] == job])
        converted = len(bank[(bank['job'] == job) & (bank['y'] == 'yes')])
        rate = round((converted / total * 100), 2) if total > 0 else 0
        examples.append(create_example(
            bank, 'Campaigns',
            f"What is the conversion rate for job category '{job}'?",
            {"operation": "conversion_rate", "filters": {"job": job}, "result": rate, "insufficient": False}
        ))
    
    # Average campaign contacts
    for _ in range(per_task):
        avg_contacts = round(safe_mean(bank['campaign']), 2)
        examples.append(create_example(
            bank, 'Campaigns',
            "What is the average number of contacts per campaign?",
            {"operation": "avg", "column": "campaign", "result": avg_contacts, "insufficient": False}
        ))
    
    # Success by education
    for _ in range(per_task):
        education = random.choice(bank['education'].unique())
        success_count = len(bank[(bank['education'] == education) & (bank['y'] == 'yes')])
        examples.append(create_example(
            bank, 'Campaigns',
            f"How many successful conversions for education level '{education}'?",
            {"count": success_count, "criteria": {"education": education, "success": "yes"}, "insufficient": False}
        ))
    
    return examples

def _find_first(df: pd.DataFrame, patterns: List[str]) -> str:
    cols = [c for c in df.columns]
    for p in patterns:
        for c in cols:
            if re.search(p, str(c), flags=re.IGNORECASE):
                return c
    return None

def generate_parking_tasks(parking: pd.DataFrame, n_samples: int = 10000):
    """NYC parking violations tasks across multiple yearly files using inferred metadata."""
    examples = []
    per_task = max(1, n_samples // 20)

    # Infer columns
    date_col = _find_first(parking, [r'^issue\s*date$', r'date'])
    desc_col = _find_first(parking, [r'violation\s*description', r'violation\s*code'])
    state_col = _find_first(parking, [r'registration\s*state', r'state$'])
    plate_type_col = _find_first(parking, [r'plate\s*type'])
    borough_col = _find_first(parking, [r'borough', r'county'])
    year_col = 'SourceYear' if 'SourceYear' in parking.columns else _find_first(parking, [r'year'])

    # Numeric amount column preference
    numeric_cols = parking.select_dtypes(include=[np.number]).columns.tolist()
    amount_col = None
    for pref in [r'fine', r'penalty', r'payment', r'amount', r'total']:
        amount_col = _find_first(parking[numeric_cols] if numeric_cols else parking, [pref])
        if amount_col:
            break
    if not amount_col and numeric_cols:
        amount_col = numeric_cols[0]

    # 1) Counts by description
    if desc_col is not None and desc_col in parking.columns:
        vals = parking[desc_col].dropna().astype(str).unique().tolist()
        if vals:
            for _ in range(per_task):
                v = random.choice(vals)
                cnt = int((parking[desc_col].astype(str) == str(v)).sum())
                examples.append(create_example(
                    parking, 'ParkingViolations',
                    f"How many violations are for description '{v}'?",
                    {"count": cnt, "criteria": {desc_col: v}, "insufficient": False}
                ))

    # 2) Top 5 violation descriptions
    if desc_col is not None and desc_col in parking.columns:
        top5 = parking[desc_col].astype(str).value_counts().head(5).to_dict()
        examples.append(create_example(
            parking, 'ParkingViolations',
            "What are the top 5 violation descriptions by count?",
            {"operation": "top_n", "n": 5, "group_by": desc_col, "result": top5, "insufficient": False}
        ))

    # 3) Average fine/amount overall and by year
    if amount_col is not None and amount_col in parking.columns:
        overall_avg = round(safe_mean(parking[amount_col]), 2)
        examples.append(create_example(
            parking, 'ParkingViolations',
            f"What is the average {amount_col} across all violations?",
            {"operation": "avg", "column": amount_col, "result": overall_avg, "insufficient": False}
        ))
        if year_col and year_col in parking.columns:
            by_year = parking.groupby(year_col)[amount_col].mean().round(2).dropna().to_dict()
            examples.append(create_example(
                parking, 'ParkingViolations',
                f"What is the average {amount_col} by {year_col}?",
                {"operation": "avg", "group_by": year_col, "column": amount_col, "result": by_year, "insufficient": False}
            ))

    # 4) Counts by state/borough/plate type
    for col, label in [(state_col, 'registration state'), (borough_col, 'borough'), (plate_type_col, 'plate type')]:
        if col and col in parking.columns:
            vals = parking[col].dropna().astype(str).unique().tolist()
            if vals:
                v = random.choice(vals)
                cnt = int((parking[col].astype(str) == str(v)).sum())
                examples.append(create_example(
                    parking, 'ParkingViolations',
                    f"How many violations have {label} '{v}'?",
                    {"count": cnt, "criteria": {col: v}, "insufficient": False}
                ))

    # 5) Peak month by counts
    if date_col and date_col in parking.columns:
        dt = pd.to_datetime(parking[date_col], errors='coerce')
        months = dt.dt.to_period('M').astype(str)
        peak_month = months.value_counts().idxmax() if months.notna().any() else None
        if peak_month:
            cnt = int((months == peak_month).sum())
            examples.append(create_example(
                parking, 'ParkingViolations',
                f"Which month has the highest number of violations?",
                {"operation": "peak_month", "result": peak_month, "count": cnt, "insufficient": False}
            ))

    return examples

def generate_covid_tasks(covid: pd.DataFrame, n_samples: int = 10000):
    """COVID-19 dataset tasks using inferred metadata (date, region, metrics)."""
    examples = []
    per_task = max(1, n_samples // 20)

    # Infer columns
    date_col = _find_first(covid, [r'^date$', r'date'])
    region_col = _find_first(covid, [r'country', r'state', r'province', r'county', r'region'])
    # Prefer case-like columns
    metric_prefs = [r'new[_\s]?cases', r'cases', r'confirmed', r'deaths', r'hospital']
    numeric_cols = covid.select_dtypes(include=[np.number]).columns.tolist()
    metric_col = None
    for p in metric_prefs:
        mc = _find_first(covid[numeric_cols] if numeric_cols else covid, [p])
        if mc:
            metric_col = mc
            break
    if not metric_col and numeric_cols:
        metric_col = numeric_cols[0]

    # 1) Total metric sum
    if metric_col and metric_col in covid.columns:
        total_val = float(pd.to_numeric(covid[metric_col], errors='coerce').fillna(0).sum())
        examples.append(create_example(
            covid, 'COVID',
            f"What is the total {metric_col} across the dataset?",
            {"operation": "sum", "column": metric_col, "result": round(total_val, 2), "insufficient": False}
        ))

    # 2) Peak day for metric
    if metric_col and date_col and (metric_col in covid.columns) and (date_col in covid.columns):
        dt = pd.to_datetime(covid[date_col], errors='coerce')
        df = covid.copy()
        df['_dt'] = dt
        daily = df.groupby('_dt')[metric_col].sum().dropna()
        if not daily.empty:
            peak_day = daily.idxmax()
            peak_val = float(daily.max())
            examples.append(create_example(
                covid, 'COVID',
                f"Which date has the highest total {metric_col}?",
                {"operation": "peak_day", "column": metric_col, "result": str(peak_day.date()) if hasattr(peak_day, 'date') else str(peak_day), "value": round(peak_val, 2), "insufficient": False}
            ))

    # 3) Average metric
    if metric_col and metric_col in covid.columns:
        avg_val = round(safe_mean(covid[metric_col]), 2)
        examples.append(create_example(
            covid, 'COVID',
            f"What is the average of {metric_col}?",
            {"operation": "avg", "column": metric_col, "result": avg_val, "insufficient": False}
        ))

    # 4) Region-specific totals
    if region_col and region_col in covid.columns and metric_col and metric_col in covid.columns:
        vals = covid[region_col].dropna().astype(str).unique().tolist()
        if vals:
            for _ in range(per_task):
                v = random.choice(vals)
                total = float(pd.to_numeric(covid.loc[covid[region_col].astype(str) == v, metric_col], errors='coerce').fillna(0).sum())
                examples.append(create_example(
                    covid, 'COVID',
                    f"What is the total {metric_col} for {region_col} '{v}'?",
                    {"operation": "sum", "column": metric_col, "filters": {region_col: v}, "result": round(total, 2), "insufficient": False}
                ))

    # 5) Top 5 regions by total metric
    if region_col and region_col in covid.columns and metric_col and metric_col in covid.columns:
        grouped = covid.groupby(region_col)[metric_col].sum().sort_values(ascending=False).head(5)
        examples.append(create_example(
            covid, 'COVID',
            f"What are the top 5 {region_col}s by total {metric_col}?",
            {"operation": "top_n", "n": 5, "group_by": region_col, "column": metric_col, "result": grouped.round(2).to_dict(), "insufficient": False}
        ))

    return examples

# ============================================
# 5. MAIN EXECUTION
# ============================================

def main():
    parser = argparse.ArgumentParser(description="Train or query finetuned Ollama model with file context.")
    parser.add_argument('--ask', type=str, help='Question to ask the model (enables inference mode).')
    parser.add_argument('--files', nargs='*', help='CSV file paths to include as sheets in context.')
    parser.add_argument('--model', type=str, default='my-finetuned-model', help='Ollama model name to use.')
    parser.add_argument('--rows-limit', type=int, default=50, help='Rows per sheet to include in context.')
    parser.add_argument('--focus-sheet', type=str, default=None, help='Optional specific sheet name to focus on.')
    parser.add_argument('--train', action='store_true', help='Generate training JSONL from local datasets.')
    args = parser.parse_args()

    if args.ask:
        # Inference mode: build context from provided CSVs and query Ollama
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
            "You are a spreadsheet analyst. Use ONLY the provided context. "
            "For structured tasks, return JSON only as specified. If 'SheetName' is quoted, "
            "use that exact sheet (case-insensitive) and ignore others. Return 'insufficient' when context is incomplete."
        )
        user_content = context + f"\n\nQuestion: {args.ask}"
        try:
            answer = call_ollama_chat(args.model, system_prompt, user_content)
            print("\n--- Model Answer ---\n")
            print(answer)
        except Exception as rexc:
            print(f"Ollama request failed: {rexc}")
        return

    # Default: training mode (or --train)
    print("\nLoading large datasets...")
    datasets = load_large_datasets()
    if not datasets:
        print("No datasets loaded.")
        return

    print("\nGenerating 50,000+ domain-specific training examples...")
    all_examples = []
    if 'brazilian_ecommerce' in datasets:
        print("  E-commerce tasks (10,000 examples)...")
        all_examples.extend(generate_ecommerce_tasks(datasets['brazilian_ecommerce'], 10000))
    if 'covid' in datasets:
        print("  COVID-19 tasks (10,000 examples)...")
        all_examples.extend(generate_covid_tasks(datasets['covid'], 10000))
    if 'nyc_parking' in datasets:
        print("  NYC Parking tasks (10,000 examples)...")
        all_examples.extend(generate_parking_tasks(datasets['nyc_parking'], 10000))

    random.shuffle(all_examples)
    output_path = Path(exe_dir / 'training_jsonl/large_datasets_50k_train.jsonl')
    with open(output_path, "w", encoding="utf-8") as f:
        for ex in all_examples:
            f.write(json.dumps(ex, ensure_ascii=False) + "\n")

    print(f"\nGenerated {len(all_examples)} training examples!")
    print(f"Saved to: {output_path}")
    print("\nDomain-specific coverage:")
    print("   - E-commerce: Revenue, AOV, product rankings")
    print("   - Banking: Conversion rates, campaign metrics")
    print("   - COVID-19: Totals, peaks, regional summaries")
    print("   - Parking: Multi-year counts, averages, top violations")

if __name__ == "__main__":
    main()
