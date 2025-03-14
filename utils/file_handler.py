import pandas as pd
import numpy as np
import io
import os
import base64
import re
import json

def process_uploaded_file(file_obj):
    """
    Process uploaded file and convert to pandas DataFrame.
    
    Args:
        file_obj: File object from st.file_uploader
        
    Returns:
        tuple: (DataFrame, file_type)
    """
    # Get file extension
    file_name = file_obj.name
    file_extension = os.path.splitext(file_name)[1].lower()
    
    # Read file based on extension
    if file_extension == '.csv':
        df = pd.read_csv(file_obj)
        file_type = 'csv'
    elif file_extension == '.xlsx':
        df = pd.read_excel(file_obj)
        file_type = 'excel'
    elif file_extension == '.json':
        # Try to parse as JSON
        try:
            data = json.load(io.StringIO(file_obj.getvalue().decode('utf-8')))
            
            # Check if it's a list of records or a single object
            if isinstance(data, list):
                df = pd.DataFrame(data)
            else:
                # If it's a nested JSON, try to flatten it
                df = pd.json_normalize(data)
            
            file_type = 'json'
        except Exception as e:
            raise ValueError(f"Failed to parse JSON file: {str(e)}")
    else:
        raise ValueError(f"Unsupported file format: {file_extension}")
    
    # Clean column names
    df.columns = [clean_column_name(col) for col in df.columns]
    
    # Perform basic cleaning
    df = clean_dataframe(df)
    
    return df, file_type

def clean_column_name(col_name):
    """
    Clean column name to be more user-friendly and compatible.
    
    Args:
        col_name: Original column name
        
    Returns:
        str: Cleaned column name
    """
    # Convert to string if not already
    col_name = str(col_name)
    
    # Replace spaces and special characters with underscores
    col_name = re.sub(r'[^\w\s]', '_', col_name)
    col_name = re.sub(r'\s+', '_', col_name)
    
    # Remove multiple consecutive underscores
    col_name = re.sub(r'_+', '_', col_name)
    
    # Remove leading/trailing underscores
    col_name = col_name.strip('_')
    
    # Ensure it's not empty
    if not col_name:
        col_name = 'column'
    
    return col_name.lower()

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
    
    # Replace empty strings with NaN
    df_clean = df_clean.replace('', np.nan)
    
    # Attempt to convert string columns that look numeric to proper numeric types
    for col in df_clean.select_dtypes(include=['object']).columns:
        # Skip columns with high percentage of non-numeric values
        non_numeric_count = sum(pd.to_numeric(df_clean[col], errors='coerce').isna())
        if non_numeric_count / len(df_clean) < 0.3:  # Less than 30% non-numeric
            try:
                df_clean[col] = pd.to_numeric(df_clean[col], errors='coerce')
            except:
                pass
    
    # Attempt to convert columns that look like dates to datetime
    for col in df_clean.select_dtypes(include=['object']).columns:
        try:
            # Check if it's a date column by trying to convert a sample
            sample = df_clean[col].dropna().iloc[0] if not df_clean[col].dropna().empty else ""
            if isinstance(sample, str) and re.search(r'\d{1,4}[-/]\d{1,2}[-/]\d{1,4}', sample):
                df_clean[col] = pd.to_datetime(df_clean[col], errors='coerce')
        except:
            pass
    
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
    # Create a copy for the head preview to avoid modifying the original
    preview_df = df.head(max_rows).copy()
    
    # Convert datetime columns to string for the head preview
    for col in preview_df.columns:
        if pd.api.types.is_datetime64_any_dtype(preview_df[col]):
            preview_df[col] = preview_df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
    
    preview = {
        "head": preview_df.to_dict(orient='records'),
        "shape": df.shape,
        "columns": list(df.columns),
        "dtypes": {col: str(dtype) for col, dtype in zip(df.columns, df.dtypes)},
        "missing_values": df.isna().sum().to_dict(),
        "summary": {}
    }
    
    # Generate summary statistics for numeric columns
    numeric_cols = df.select_dtypes(include=['number']).columns
    if not numeric_cols.empty:
        preview["summary"]["numeric"] = df[numeric_cols].describe().to_dict()
    
    # Generate summary for categorical columns
    categorical_cols = df.select_dtypes(include=['object', 'category']).columns
    if not categorical_cols.empty:
        preview["summary"]["categorical"] = {}
        for col in categorical_cols:
            value_counts = df[col].value_counts().head(5).to_dict()
            if value_counts:
                preview["summary"]["categorical"][col] = value_counts
    
    # Generate summary for datetime columns
    datetime_cols = df.select_dtypes(include=['datetime']).columns
    if not datetime_cols.empty:
        preview["summary"]["datetime"] = {}
        for col in datetime_cols:
            preview["summary"]["datetime"][col] = {
                "min": df[col].min().isoformat() if not pd.isna(df[col].min()) else None,
                "max": df[col].max().isoformat() if not pd.isna(df[col].max()) else None
            }
    
    return preview

def dataframe_to_csv(df):
    """
    Convert a dataframe to a downloadable CSV.
    
    Args:
        df (DataFrame): Input dataframe
        
    Returns:
        str: Base64 encoded CSV data
    """
    csv = df.to_csv(index=False)
    b64 = base64.b64encode(csv.encode()).decode()
    return b64

def dataframe_to_excel(df):
    """
    Convert a dataframe to a downloadable Excel file.
    
    Args:
        df (DataFrame): Input dataframe
        
    Returns:
        str: Base64 encoded Excel data
    """
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, sheet_name='Sheet1', index=False)
    
    excel_data = output.getvalue()
    b64 = base64.b64encode(excel_data).decode()
    return b64

def extract_text_from_pdf(file_obj):
    """
    Extract text from PDF file.
    
    Args:
        file_obj: File object from st.file_uploader
        
    Returns:
        str: Extracted text
    """
    try:
        import PyPDF2
        
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_obj.getvalue()))
        text = ""
        
        for page_num in range(len(pdf_reader.pages)):
            page = pdf_reader.pages[page_num]
            text += page.extract_text() + "\n\n"
        
        return text
    except ImportError:
        return "PyPDF2 is not installed. Unable to extract text from PDF."
    except Exception as e:
        return f"Error extracting text from PDF: {str(e)}"