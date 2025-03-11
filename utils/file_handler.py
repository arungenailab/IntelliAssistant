import pandas as pd
import numpy as np
import re
import io
import base64
from datetime import datetime

def process_uploaded_file(file_obj):
    """
    Process uploaded file and convert to pandas DataFrame.
    
    Args:
        file_obj: File object from st.file_uploader
        
    Returns:
        tuple: (DataFrame, file_type)
    """
    file_type = None
    try:
        # Determine file type from name
        filename = file_obj.name.lower()
        
        if filename.endswith('.csv'):
            file_type = 'csv'
            df = pd.read_csv(file_obj)
        
        elif filename.endswith('.xlsx') or filename.endswith('.xls'):
            file_type = 'excel'
            df = pd.read_excel(file_obj)
        
        elif filename.endswith('.json'):
            file_type = 'json'
            df = pd.read_json(file_obj)
        
        elif filename.endswith('.pdf'):
            file_type = 'pdf'
            # For PDFs, we assume tabular data that can be extracted
            # In a real implementation, would use tools like tabula-py or PyPDF2
            # This is a simplified placeholder
            raise NotImplementedError("PDF extraction requires additional libraries")
        
        else:
            # Try to infer file type
            content = file_obj.getvalue()
            
            # Check if it's a CSV by looking for commas and newlines
            if content.count(b',') > 0 and content.count(b'\n') > 0:
                file_type = 'csv'
                file_obj.seek(0)  # Reset file pointer
                df = pd.read_csv(file_obj)
            else:
                # Try as Excel
                try:
                    file_type = 'excel'
                    file_obj.seek(0)
                    df = pd.read_excel(file_obj)
                except:
                    raise ValueError("Unsupported file format")
        
        # Clean up column names
        df.columns = [clean_column_name(col) for col in df.columns]
        
        # Handle common data cleaning tasks
        df = clean_dataframe(df)
        
        return df, file_type
    
    except Exception as e:
        raise Exception(f"Error processing file: {str(e)}")

def clean_column_name(col_name):
    """
    Clean column name to be more user-friendly and compatible.
    
    Args:
        col_name: Original column name
        
    Returns:
        str: Cleaned column name
    """
    if not isinstance(col_name, str):
        col_name = str(col_name)
    
    # Replace spaces with underscores
    col_name = col_name.replace(' ', '_')
    
    # Remove special characters
    col_name = re.sub(r'[^\w\s]', '', col_name)
    
    # Convert to lowercase
    col_name = col_name.lower()
    
    return col_name

def clean_dataframe(df):
    """
    Perform basic data cleaning on a dataframe.
    
    Args:
        df (DataFrame): Input dataframe
        
    Returns:
        DataFrame: Cleaned dataframe
    """
    # Make a copy to avoid modifying the original
    df_clean = df.copy()
    
    # Try to convert string columns that look like dates to datetime
    for col in df_clean.columns:
        # Skip columns that are already numeric
        if pd.api.types.is_numeric_dtype(df_clean[col]):
            continue
        
        # Check if column contains dates
        try:
            if df_clean[col].dtype == 'object':
                # Check a sample for date-like strings
                sample = df_clean[col].dropna().head(100)
                date_patterns = [
                    r'\d{4}-\d{2}-\d{2}',  # YYYY-MM-DD
                    r'\d{2}/\d{2}/\d{4}',  # MM/DD/YYYY
                    r'\d{2}-\d{2}-\d{4}',  # MM-DD-YYYY
                    r'\d{2}\.\d{2}\.\d{4}'  # MM.DD.YYYY
                ]
                
                is_date = False
                for pattern in date_patterns:
                    if sample.astype(str).str.match(pattern).any():
                        is_date = True
                        break
                
                if is_date:
                    df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
        except:
            pass
    
    # Try to convert string columns that look like numbers to numeric
    for col in df_clean.columns:
        if df_clean[col].dtype == 'object':
            try:
                # Check if column contains numbers as strings
                numeric_values = pd.to_numeric(df_clean[col], errors='coerce')
                # If at least 80% of the values can be converted, keep the conversion
                if numeric_values.notna().sum() >= 0.8 * len(df_clean):
                    df_clean[col] = numeric_values
            except:
                pass
    
    # Handle missing values for numeric columns (replace with NaN)
    for col in df_clean.select_dtypes(include=[np.number]).columns:
        df_clean[col] = df_clean[col].replace([np.inf, -np.inf], np.nan)
    
    return df_clean

def generate_preview(df, max_rows=5):
    """
    Generate a preview of a dataframe with additional info.
    
    Args:
        df (DataFrame): Input dataframe
        max_rows (int, optional): Maximum number of rows to include
        
    Returns:
        dict: Dataframe preview information
    """
    if df is None or df.empty:
        return {
            "empty": True,
            "message": "The dataframe is empty"
        }
    
    # Get basic dataframe info
    info = {
        "empty": False,
        "rows": len(df),
        "columns": len(df.columns),
        "column_names": list(df.columns),
        "dtypes": {col: str(df[col].dtype) for col in df.columns},
        "preview_data": df.head(max_rows).to_dict(orient='records'),
        "missing_values": df.isna().sum().to_dict(),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    
    # Add numeric column statistics if applicable
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        info["numeric_stats"] = {
            col: {
                "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                "median": float(df[col].median()) if not pd.isna(df[col].median()) else None
            } for col in numeric_cols
        }
    
    return info

def dataframe_to_csv(df):
    """
    Convert a dataframe to a downloadable CSV.
    
    Args:
        df (DataFrame): Input dataframe
        
    Returns:
        str: Base64 encoded CSV data
    """
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)
    csv_str = csv_buffer.getvalue()
    b64 = base64.b64encode(csv_str.encode()).decode()
    return b64

def dataframe_to_excel(df):
    """
    Convert a dataframe to a downloadable Excel file.
    
    Args:
        df (DataFrame): Input dataframe
        
    Returns:
        str: Base64 encoded Excel data
    """
    excel_buffer = io.BytesIO()
    df.to_excel(excel_buffer, index=False)
    excel_data = excel_buffer.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    return b64

def extract_text_from_pdf(file_obj):
    """
    Extract text from PDF file (placeholder).
    
    Args:
        file_obj: File object from st.file_uploader
        
    Returns:
        str: Extracted text
    """
    # In a real implementation, would use tools like PyPDF2 or pdfplumber
    # This is a simplified placeholder
    raise NotImplementedError("PDF text extraction requires additional libraries")
