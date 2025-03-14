import pandas as pd
import json
from typing import Dict, Any, List, Optional, Union
import numpy as np
from data_visualization import detect_dataset_type, generate_visualizations

def generate_enhanced_dataset_analysis(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate comprehensive analysis of a dataset with well-formatted results
    
    Args:
        df: DataFrame to analyze
        
    Returns:
        Dictionary containing analysis results
    """
    try:
        # Detect dataset type
        dataset_type = detect_dataset_type(df)
        
        # Basic dataset information
        dataset_info = {
            "shape": {
                "rows": df.shape[0],
                "columns": df.shape[1]
            },
            "columns": list(df.columns),
            "dtypes": {col: str(df[col].dtype) for col in df.columns},
            "detected_type": dataset_type
        }
        
        # Identify numeric columns for statistical analysis
        numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
        
        # Calculate statistics for numeric columns
        stats = {}
        percentiles = {}
        top_values = {}
        bottom_values = {}
        
        for col in numeric_columns:
            stats[col] = {
                "min": float(df[col].min()),
                "max": float(df[col].max()),
                "mean": float(df[col].mean()),
                "median": float(df[col].median()),
                "std": float(df[col].std())
            }
            
            percentiles[col] = {
                "25%": float(df[col].quantile(0.25)),
                "50%": float(df[col].quantile(0.50)),
                "75%": float(df[col].quantile(0.75)),
                "90%": float(df[col].quantile(0.90)),
                "95%": float(df[col].quantile(0.95))
            }
            
            # Get top 5 and bottom 5 values
            top_values[col] = df[col].nlargest(5).tolist()
            bottom_values[col] = df[col].nsmallest(5).tolist()
        
        # Date analysis if there are datetime columns
        date_columns = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
        date_analysis = {}
        
        for col in date_columns:
            date_analysis[col] = {
                "min_date": df[col].min().strftime('%Y-%m-%d'),
                "max_date": df[col].max().strftime('%Y-%m-%d'),
                "range_days": (df[col].max() - df[col].min()).days
            }
        
        # Categorical columns analysis
        categorical_columns = df.select_dtypes(include=['object', 'category']).columns.tolist()
        categorical_analysis = {}
        
        for col in categorical_columns:
            value_counts = df[col].value_counts().head(10).to_dict()  # Top 10 most common values
            categorical_analysis[col] = {
                "unique_values": df[col].nunique(),
                "most_common": value_counts
            }
        
        # Create analysis result
        analysis_result = {
            "dataset_info": dataset_info,
            "statistics": stats,
            "percentiles": percentiles,
            "top_values": top_values,
            "bottom_values": bottom_values,
            "date_analysis": date_analysis,
            "categorical_analysis": categorical_analysis
        }
        
        # Add dataset-type specific metrics
        if dataset_type == "financial":
            financial_metrics = calculate_financial_metrics(df)
            analysis_result["financial_metrics"] = financial_metrics
        elif dataset_type == "sales":
            sales_metrics = calculate_sales_metrics(df)
            analysis_result["sales_metrics"] = sales_metrics
        elif dataset_type == "time_series":
            time_series_metrics = calculate_time_series_metrics(df)
            analysis_result["time_series_metrics"] = time_series_metrics
        
        return analysis_result
    
    except Exception as e:
        return {"error": str(e)}

def calculate_financial_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate metrics specific to financial data
    
    Args:
        df: DataFrame with financial data columns
        
    Returns:
        Dictionary of financial metrics
    """
    # Ensure dataframe has proper date ordering
    if 'date' in df.columns:
        df = df.sort_values('date')
    
    # Calculate daily returns
    if 'close' in df.columns:
        df['daily_return'] = df['close'].pct_change() * 100
    
    # Calculate moving averages
    df['ma_5'] = df['close'].rolling(window=5).mean()
    df['ma_20'] = df['close'].rolling(window=20).mean()
    
    # Calculate volatility (standard deviation of returns)
    volatility = df['daily_return'].std()
    
    # Calculate Average True Range (ATR) - a measure of volatility
    df['high_low'] = df['high'] - df['low']
    df['high_close'] = abs(df['high'] - df['close'].shift())
    df['low_close'] = abs(df['low'] - df['close'].shift())
    df['true_range'] = df[['high_low', 'high_close', 'low_close']].max(axis=1)
    atr = df['true_range'].rolling(window=14).mean().iloc[-1]
    
    # Calculate average volume
    avg_volume = df['volume'].mean()
    
    # Calculate highest and lowest prices and their dates
    highest_price = df['high'].max()
    highest_price_date = df.loc[df['high'].idxmax(), 'date'] if 'date' in df.columns else None
    if highest_price_date is not None and isinstance(highest_price_date, pd.Timestamp):
        highest_price_date = highest_price_date.strftime('%Y-%m-%d')
    
    lowest_price = df['low'].min()
    lowest_price_date = df.loc[df['low'].idxmin(), 'date'] if 'date' in df.columns else None
    if lowest_price_date is not None and isinstance(lowest_price_date, pd.Timestamp):
        lowest_price_date = lowest_price_date.strftime('%Y-%m-%d')
    
    # Get last price and calculate price change from first available price
    last_price = df['close'].iloc[-1]
    first_price = df['close'].iloc[0]
    price_change = ((last_price - first_price) / first_price) * 100
    
    # Find days with highest and lowest trading volumes
    highest_volume = df['volume'].max()
    highest_volume_date = df.loc[df['volume'].idxmax(), 'date'] if 'date' in df.columns else None
    if highest_volume_date is not None and isinstance(highest_volume_date, pd.Timestamp):
        highest_volume_date = highest_volume_date.strftime('%Y-%m-%d')
    
    # Return compiled metrics
    return {
        "price_metrics": {
            "highest_price": highest_price,
            "highest_price_date": highest_price_date,
            "lowest_price": lowest_price,
            "lowest_price_date": lowest_price_date,
            "last_price": last_price,
            "price_change_percent": price_change,
            "avg_true_range": atr
        },
        "trading_metrics": {
            "volatility": volatility,
            "avg_daily_return": df['daily_return'].mean(),
            "positive_days": int((df['daily_return'] > 0).sum()),
            "negative_days": int((df['daily_return'] < 0).sum()),
            "highest_volume": highest_volume,
            "highest_volume_date": highest_volume_date,
            "avg_volume": avg_volume
        }
    }

def calculate_sales_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate metrics specific to sales data
    
    Args:
        df: DataFrame with sales data columns
        
    Returns:
        Dictionary of sales metrics
    """
    metrics = {}
    
    # Identify available metrics
    has_revenue = 'revenue' in df.columns
    has_profit = 'profit' in df.columns
    has_quantity = 'quantity' in df.columns
    has_product = 'product' in df.columns
    has_date = 'date' in df.columns or any(pd.api.types.is_datetime64_any_dtype(df[col]) for col in df.columns)
    
    # Find the date column if present
    date_col = None
    if has_date:
        for col in df.columns:
            if pd.api.types.is_datetime64_any_dtype(df[col]):
                date_col = col
                break
        if date_col is None and 'date' in df.columns:
            date_col = 'date'
            df[date_col] = pd.to_datetime(df[date_col])
    
    # Overall metrics
    overall = {}
    
    if has_revenue:
        overall["total_revenue"] = float(df['revenue'].sum())
        overall["avg_revenue"] = float(df['revenue'].mean())
    
    if has_profit:
        overall["total_profit"] = float(df['profit'].sum())
        overall["avg_profit"] = float(df['profit'].mean())
        
        if has_revenue:
            overall["profit_margin"] = float((df['profit'].sum() / df['revenue'].sum()) * 100)
    
    if has_quantity:
        overall["total_quantity"] = int(df['quantity'].sum())
        overall["avg_quantity"] = float(df['quantity'].mean())
    
    metrics["overall"] = overall
    
    # Product metrics if product column exists
    if has_product:
        product_metrics = {}
        
        # Top products
        if has_revenue:
            top_revenue_products = df.groupby('product')['revenue'].sum().nlargest(5).to_dict()
            product_metrics["top_revenue_products"] = top_revenue_products
        
        if has_profit:
            top_profit_products = df.groupby('product')['profit'].sum().nlargest(5).to_dict()
            product_metrics["top_profit_products"] = top_profit_products
            
            if has_revenue:
                # Calculate profit margin by product
                product_margins = df.groupby('product').apply(
                    lambda x: (x['profit'].sum() / x['revenue'].sum()) * 100
                ).nlargest(5).to_dict()
                product_metrics["top_margin_products"] = product_margins
        
        if has_quantity:
            top_quantity_products = df.groupby('product')['quantity'].sum().nlargest(5).to_dict()
            product_metrics["top_quantity_products"] = top_quantity_products
        
        metrics["product_metrics"] = product_metrics
    
    # Time-based metrics if date column exists
    if has_date:
        time_metrics = {}
        
        # Group by day
        df['day'] = df[date_col].dt.date
        
        # Best days
        if has_revenue:
            best_revenue_days = df.groupby('day')['revenue'].sum().nlargest(5).to_dict()
            time_metrics["best_revenue_days"] = {str(k): v for k, v in best_revenue_days.items()}
        
        if has_profit:
            best_profit_days = df.groupby('day')['profit'].sum().nlargest(5).to_dict()
            time_metrics["best_profit_days"] = {str(k): v for k, v in best_profit_days.items()}
        
        if has_quantity:
            best_quantity_days = df.groupby('day')['quantity'].sum().nlargest(5).to_dict()
            time_metrics["best_quantity_days"] = {str(k): v for k, v in best_quantity_days.items()}
        
        metrics["time_metrics"] = time_metrics
    
    return metrics

def calculate_time_series_metrics(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Calculate metrics specific to time series data
    
    Args:
        df: DataFrame with time series data
        
    Returns:
        Dictionary of time series metrics
    """
    metrics = {}
    
    # Find date column
    date_cols = [col for col in df.columns if pd.api.types.is_datetime64_any_dtype(df[col])]
    if not date_cols:
        return metrics
    
    date_col = date_cols[0]
    
    # Ensure data is sorted by date
    df = df.sort_values(date_col)
    
    # Find numeric columns
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    if not numeric_cols:
        return metrics
    
    # Calculate trend metrics for each numeric column
    trend_metrics = {}
    
    for col in numeric_cols:
        # Skip columns we don't need to analyze
        if col in ['id', 'index']:
            continue
        
        # Calculate growth metrics
        first_value = df[col].iloc[0]
        last_value = df[col].iloc[-1]
        
        if first_value != 0:
            growth_percent = ((last_value - first_value) / first_value) * 100
        else:
            growth_percent = np.nan
        
        # Calculate volatility (standard deviation)
        volatility = df[col].std()
        
        # Calculate percent change between consecutive values
        df[f'{col}_pct_change'] = df[col].pct_change() * 100
        
        # Identify significant changes
        df[f'{col}_significant_change'] = abs(df[f'{col}_pct_change']) > 10  # 10% threshold
        
        significant_changes = df[df[f'{col}_significant_change'] == True]
        
        significant_points = []
        if not significant_changes.empty:
            for idx, row in significant_changes.iterrows():
                significant_points.append({
                    'date': row[date_col].strftime('%Y-%m-%d'),
                    'value': row[col],
                    'percent_change': row[f'{col}_pct_change']
                })
        
        # Store metrics for this column
        trend_metrics[col] = {
            'start_value': first_value,
            'end_value': last_value,
            'absolute_change': last_value - first_value,
            'percent_change': growth_percent,
            'volatility': volatility,
            'max_value': df[col].max(),
            'min_value': df[col].min(),
            'significant_changes': significant_points[:5]  # Top 5 significant changes
        }
    
    metrics['trend_metrics'] = trend_metrics
    
    # Calculate seasonality metrics if enough data points
    if len(df) >= 30:
        seasonality_metrics = {}
        
        # Add day, month, year extractors
        df['day'] = df[date_col].dt.day
        df['month'] = df[date_col].dt.month
        df['year'] = df[date_col].dt.year
        
        # Check if we have multiple years of data
        if df['year'].nunique() > 1:
            for col in numeric_cols[:3]:  # Limit to first 3 numeric columns
                # Skip columns we don't need to analyze
                if col in ['id', 'index']:
                    continue
                
                # Monthly patterns
                monthly_avg = df.groupby('month')[col].mean().to_dict()
                
                # Find month with highest and lowest values
                max_month = max(monthly_avg, key=monthly_avg.get)
                min_month = min(monthly_avg, key=monthly_avg.get)
                
                seasonality_metrics[col] = {
                    'monthly_average': monthly_avg,
                    'best_month': max_month,
                    'worst_month': min_month
                }
        
        metrics['seasonality_metrics'] = seasonality_metrics
    
    return metrics

def generate_enhanced_visualizations(df: pd.DataFrame) -> Dict[str, Any]:
    """
    Generate enhanced visualizations for the dataset
    
    Args:
        df: DataFrame to visualize
        
    Returns:
        Dictionary containing visualization specifications
    """
    return generate_visualizations(df)

def format_analysis_to_markdown(analysis_result: Dict[str, Any]) -> str:
    """
    Format the analysis result dictionary into a well-structured markdown string
    
    Args:
        analysis_result: Dictionary containing analysis results
        
    Returns:
        Markdown formatted string
    """
    md = []
    
    # Dataset information
    dataset_info = analysis_result.get("dataset_info", {})
    dataset_type = dataset_info.get("detected_type", "generic")
    
    md.append("# Dataset Analysis Report\n")
    
    md.append("## Dataset Overview")
    md.append(f"- **Records**: {dataset_info.get('shape', {}).get('rows')} rows")
    md.append(f"- **Features**: {dataset_info.get('shape', {}).get('columns')} columns")
    md.append(f"- **Detected dataset type**: {dataset_type}")
    md.append(f"- **Columns**: {', '.join(dataset_info.get('columns', []))}\n")
    
    # Statistics
    stats = analysis_result.get("statistics", {})
    if stats:
        md.append("## Statistical Summary\n")
        
        # Create a table for numeric columns (limit to 5 columns to avoid huge tables)
        numeric_cols = list(stats.keys())[:5]
        
        if numeric_cols:
            md.append("### Key Metrics")
            
            # Headers for the table
            md.append("\n| Metric | " + " | ".join(col for col in numeric_cols) + " |")
            md.append("|" + "-" * 8 + "|" + "".join("-" * 12 + "|" for _ in numeric_cols))
            
            # Rows for each statistic
            metrics = ["min", "max", "mean", "median", "std"]
            metric_names = {"min": "Minimum", "max": "Maximum", "mean": "Mean", "median": "Median", "std": "Std Dev"}
            
            for metric in metrics:
                row = f"| {metric_names[metric]} | "
                for col in numeric_cols:
                    val = stats[col][metric]
                    if abs(val) < 0.01 or abs(val) > 10000:
                        formatted_val = f"{val:.2e}"
                    else:
                        formatted_val = f"{val:.2f}"
                    row += formatted_val + " | "
                md.append(row)
            md.append("")
    
    # Dataset-type specific sections
    if dataset_type == "financial":
        financial_metrics = analysis_result.get("financial_metrics", {})
        if financial_metrics:
            md.append("## Financial Analysis\n")
            
            price_metrics = financial_metrics.get("price_metrics", {})
            if price_metrics:
                md.append("### Price Performance")
                md.append(f"- **Highest Price**: ${price_metrics.get('highest_price', 0):.2f} on {price_metrics.get('highest_price_date', 'N/A')}")
                md.append(f"- **Lowest Price**: ${price_metrics.get('lowest_price', 0):.2f} on {price_metrics.get('lowest_price_date', 'N/A')}")
                md.append(f"- **Last Price**: ${price_metrics.get('last_price', 0):.2f}")
                md.append(f"- **Price Change**: {price_metrics.get('price_change_percent', 0):.2f}%")
                md.append(f"- **Average True Range (ATR)**: ${price_metrics.get('avg_true_range', 0):.2f}\n")
            
            trading_metrics = financial_metrics.get("trading_metrics", {})
            if trading_metrics:
                md.append("### Trading Performance")
                md.append(f"- **Volatility**: {trading_metrics.get('volatility', 0):.2f}%")
                md.append(f"- **Average Daily Return**: {trading_metrics.get('avg_daily_return', 0):.2f}%")
                md.append(f"- **Positive Days**: {trading_metrics.get('positive_days', 0)}")
                md.append(f"- **Negative Days**: {trading_metrics.get('negative_days', 0)}")
                md.append(f"- **Highest Volume**: {trading_metrics.get('highest_volume', 0):,.0f} on {trading_metrics.get('highest_volume_date', 'N/A')}")
                md.append(f"- **Average Volume**: {trading_metrics.get('avg_volume', 0):,.0f}\n")
    
    elif dataset_type == "sales":
        sales_metrics = analysis_result.get("sales_metrics", {})
        if sales_metrics:
            md.append("## Sales Analysis\n")
            
            overall = sales_metrics.get("overall", {})
            if overall:
                md.append("### Overall Performance")
                if "total_revenue" in overall:
                    md.append(f"- **Total Revenue**: ${overall.get('total_revenue', 0):,.2f}")
                if "total_profit" in overall:
                    md.append(f"- **Total Profit**: ${overall.get('total_profit', 0):,.2f}")
                if "profit_margin" in overall:
                    md.append(f"- **Overall Profit Margin**: {overall.get('profit_margin', 0):.2f}%")
                if "total_quantity" in overall:
                    md.append(f"- **Total Units Sold**: {overall.get('total_quantity', 0):,}")
                md.append("")
            
            product_metrics = sales_metrics.get("product_metrics", {})
            if product_metrics:
                md.append("### Product Performance")
                
                if "top_revenue_products" in product_metrics:
                    md.append("\n#### Top Products by Revenue")
                    md.append("| Product | Revenue |")
                    md.append("|---------|---------|")
                    for product, revenue in product_metrics["top_revenue_products"].items():
                        md.append(f"| {product} | ${revenue:,.2f} |")
                    md.append("")
                
                if "top_profit_products" in product_metrics:
                    md.append("#### Top Products by Profit")
                    md.append("| Product | Profit |")
                    md.append("|---------|--------|")
                    for product, profit in product_metrics["top_profit_products"].items():
                        md.append(f"| {product} | ${profit:,.2f} |")
                    md.append("")
                
                if "top_margin_products" in product_metrics:
                    md.append("#### Top Products by Profit Margin")
                    md.append("| Product | Margin |")
                    md.append("|---------|--------|")
                    for product, margin in product_metrics["top_margin_products"].items():
                        md.append(f"| {product} | {margin:.2f}% |")
                    md.append("")
            
            time_metrics = sales_metrics.get("time_metrics", {})
            if time_metrics:
                md.append("### Time-Based Analysis")
                
                if "best_revenue_days" in time_metrics:
                    md.append("\n#### Best Days by Revenue")
                    md.append("| Date | Revenue |")
                    md.append("|------|---------|")
                    for date, revenue in time_metrics["best_revenue_days"].items():
                        md.append(f"| {date} | ${revenue:,.2f} |")
                    md.append("")
    
    elif dataset_type == "time_series":
        time_series_metrics = analysis_result.get("time_series_metrics", {})
        if time_series_metrics:
            md.append("## Time Series Analysis\n")
            
            trend_metrics = time_series_metrics.get("trend_metrics", {})
            if trend_metrics:
                md.append("### Trend Analysis")
                
                for col, metrics in trend_metrics.items():
                    md.append(f"\n#### {col} Trend")
                    md.append(f"- **Starting Value**: {metrics.get('start_value', 0):.2f}")
                    md.append(f"- **Ending Value**: {metrics.get('end_value', 0):.2f}")
                    md.append(f"- **Absolute Change**: {metrics.get('absolute_change', 0):.2f}")
                    md.append(f"- **Percent Change**: {metrics.get('percent_change', 0):.2f}%")
                    md.append(f"- **Volatility**: {metrics.get('volatility', 0):.2f}")
                    
                    significant_changes = metrics.get('significant_changes', [])
                    if significant_changes:
                        md.append("\n**Significant Changes:**")
                        for change in significant_changes:
                            direction = "increase" if change.get('percent_change', 0) > 0 else "decrease"
                            md.append(f"- {change.get('date')}: {change.get('value', 0):.2f} ({abs(change.get('percent_change', 0)):.2f}% {direction})")
                    md.append("")
            
            seasonality_metrics = time_series_metrics.get("seasonality_metrics", {})
            if seasonality_metrics:
                md.append("### Seasonality Analysis")
                
                for col, metrics in seasonality_metrics.items():
                    md.append(f"\n#### {col} Seasonality")
                    md.append(f"- **Best Month**: {metrics.get('best_month')} (Average: {metrics.get('monthly_average', {}).get(metrics.get('best_month'), 0):.2f})")
                    md.append(f"- **Worst Month**: {metrics.get('worst_month')} (Average: {metrics.get('monthly_average', {}).get(metrics.get('worst_month'), 0):.2f})")
                    md.append("")
                    
                    monthly_data = metrics.get('monthly_average', {})
                    if monthly_data:
                        md.append("**Monthly Patterns:**")
                        md.append("| Month | Average Value |")
                        md.append("|-------|---------------|")
                        for month in range(1, 13):
                            if month in monthly_data:
                                md.append(f"| {month} | {monthly_data.get(month, 0):.2f} |")
                    md.append("")
    
    # Generic and common sections for all dataset types
    
    # Categorical analysis if available
    categorical_analysis = analysis_result.get("categorical_analysis", {})
    if categorical_analysis:
        md.append("## Categorical Analysis\n")
        
        for col, analysis in categorical_analysis.items():
            md.append(f"### {col}")
            md.append(f"- **Unique Values**: {analysis.get('unique_values', 0)}")
            
            most_common = analysis.get('most_common', {})
            if most_common:
                md.append("\n**Most Common Values:**")
                md.append("| Value | Count |")
                md.append("|-------|-------|")
                for value, count in most_common.items():
                    md.append(f"| {value} | {count} |")
            md.append("")
    
    # Date analysis if available
    date_analysis = analysis_result.get("date_analysis", {})
    if date_analysis:
        md.append("## Date Analysis\n")
        
        for col, analysis in date_analysis.items():
            md.append(f"### {col}")
            md.append(f"- **Start Date**: {analysis.get('min_date', 'N/A')}")
            md.append(f"- **End Date**: {analysis.get('max_date', 'N/A')}")
            md.append(f"- **Date Range**: {analysis.get('range_days', 0)} days")
            md.append("")
    
    md.append("## Visualization")
    md.append("Interactive visualizations are available in the application dashboard.")
    
    return "\n".join(md)

# Example usage
if __name__ == "__main__":
    # Example: Load sample data using the data_visualization module
    from data_visualization import load_sample_data
    
    # Test with different dataset types
    dataset_types = ["financial", "sales", "geographic", "generic"]
    
    for dtype in dataset_types:
        print(f"\nTesting with {dtype} dataset")
        
        # Load sample data
        df = load_sample_data(dtype)
        
        # Generate enhanced analysis
        analysis_result = generate_enhanced_dataset_analysis(df)
        
        # Generate visualizations
        visualizations = generate_enhanced_visualizations(df)
        
        # Format as markdown
        markdown_report = format_analysis_to_markdown(analysis_result)
        
        # Save markdown report to a file
        with open(f"analysis_{dtype}_dataset.md", "w") as f:
            f.write(markdown_report)
        
        print(f"Analysis and visualizations generated for {dtype} dataset")
        print(f"- Analysis metrics: {len(analysis_result)} sections")
        print(f"- Visualizations: {len(visualizations)} charts")
        print(f"- Report saved to: analysis_{dtype}_dataset.md")
    
    print("\nAll dataset types analyzed successfully!") 