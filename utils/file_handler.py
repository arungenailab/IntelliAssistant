import pandas as pd
import numpy as np
import base64
import io
from io import BytesIO

def process_uploaded_file(file_obj):
    """
    Process uploaded file and convert to pandas DataFrame.
    
    Args:
        file_obj: File object from st.file_uploader
        
    Returns:
        tuple: (DataFrame, file_type)
    """
    # Determine file type from extension
    file_type = file_obj.name.split('.')[-1].lower()
    
    # Process different file types
    if file_type == 'csv':
        df = pd.read_csv(file_obj)
    elif file_type in ['xls', 'xlsx']:
        df = pd.read_excel(file_obj)
    elif file_type == 'json':
        df = pd.read_json(file_obj)
    else:
        raise ValueError(f"Unsupported file type: {file_type}")
    
    # Clean the dataframe
    return clean_dataframe(df), file_type

def clean_column_name(col_name):
    """
    Clean column name to be more user-friendly and compatible.
    
    Args:
        col_name: Original column name
        
    Returns:
        str: Cleaned column name
    """
    # Replace spaces with underscores
    cleaned = str(col_name).strip().replace(' ', '_').lower()
    
    # Remove special characters
    cleaned = ''.join(c if c.isalnum() or c == '_' else '_' for c in cleaned)
    
    # Make sure it doesn't start with a number
    if cleaned and cleaned[0].isdigit():
        cleaned = 'col_' + cleaned
    
    return cleaned

def clean_dataframe(df):
    """
    Perform basic data cleaning on a dataframe.
    
    Args:
        df (DataFrame): Input dataframe
        
    Returns:
        DataFrame: Cleaned dataframe
    """
    # Make a copy of the dataframe to avoid modifying the original
    cleaned_df = df.copy()
    
    # Clean column names
    cleaned_df.columns = [clean_column_name(col) for col in cleaned_df.columns]
    
    # Handle missing values for numeric columns
    numeric_cols = cleaned_df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        # Fill missing numeric values with median
        for col in numeric_cols:
            if cleaned_df[col].isna().any():
                cleaned_df[col] = cleaned_df[col].fillna(cleaned_df[col].median())
    
    # Handle missing values for string columns
    string_cols = cleaned_df.select_dtypes(include=['object']).columns
    if len(string_cols) > 0:
        # Fill missing string values with empty string
        for col in string_cols:
            if cleaned_df[col].isna().any():
                cleaned_df[col] = cleaned_df[col].fillna('')
    
    return cleaned_df

def generate_preview(df, max_rows=5):
    """
    Generate a preview of a dataframe with additional info.
    
    Args:
        df (DataFrame): Input dataframe
        max_rows (int, optional): Maximum number of rows to include
        
    Returns:
        dict: Dataframe preview information
    """
    # Create a preview with basic info
    preview = {
        'data': df.head(max_rows).to_dict(orient='records'),
        'columns': df.columns.tolist(),
        'dtypes': {col: str(df[col].dtype) for col in df.columns},
        'shape': df.shape,
        'missing_values': df.isna().sum().to_dict()
    }
    
    # Add numeric column statistics
    numeric_cols = df.select_dtypes(include=[np.number]).columns
    if len(numeric_cols) > 0:
        preview['numeric_stats'] = {
            col: {
                'min': float(df[col].min()),
                'max': float(df[col].max()),
                'mean': float(df[col].mean()),
                'median': float(df[col].median()),
                'std': float(df[col].std())
            } for col in numeric_cols
        }
    
    # Add categorical column information
    cat_cols = df.select_dtypes(include=['object']).columns
    if len(cat_cols) > 0:
        preview['categorical_stats'] = {
            col: {
                'unique_values': df[col].nunique(),
                'most_common': df[col].value_counts().head(3).to_dict()
            } for col in cat_cols
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
    output = BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        df.to_excel(writer, index=False, sheet_name='Sheet1')
    
    excel_data = output.getvalue()
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
    # This is a placeholder function
    # In a real implementation, you would use a library like PyPDF2 or pdfplumber
    return "PDF text extraction not implemented"