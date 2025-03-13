import pandas as pd
import json

def process_uploaded_file(file_path):
    """
    Process an uploaded file and return a pandas DataFrame and file type
    
    Args:
        file_path (str): Path to the uploaded file
        
    Returns:
        tuple: (DataFrame, file_type)
    """
    file_type = file_path.split('.')[-1].lower()
    
    try:
        if file_type == 'csv':
            df = pd.read_csv(file_path)
        elif file_type == 'xlsx' or file_type == 'xls':
            df = pd.read_excel(file_path)
        elif file_type == 'json':
            df = pd.read_json(file_path)
        else:
            raise ValueError(f"Unsupported file type: {file_type}")
        
        # Clean column names
        df.columns = df.columns.str.strip()
        
        # Convert date columns
        for col in df.columns:
            if df[col].dtype == 'object':
                try:
                    df[col] = pd.to_datetime(df[col])
                except:
                    pass
        
        return df, file_type
        
    except Exception as e:
        raise Exception(f"Error processing file: {str(e)}")

def generate_preview(df, max_rows=5):
    """
    Generate a preview of the DataFrame
    
    Args:
        df (DataFrame): The DataFrame to preview
        max_rows (int): Maximum number of rows to include
        
    Returns:
        list: List of dictionaries representing the preview rows
    """
    try:
        preview_df = df.head(max_rows)
        
        # Convert datetime columns to string
        for col in preview_df.columns:
            if pd.api.types.is_datetime64_any_dtype(preview_df[col]):
                preview_df[col] = preview_df[col].dt.strftime('%Y-%m-%d %H:%M:%S')
        
        return preview_df.to_dict(orient='records')
        
    except Exception as e:
        raise Exception(f"Error generating preview: {str(e)}")

def get_dataset_info(df):
    """
    Get information about a dataset
    
    Args:
        df (DataFrame): The DataFrame to analyze
        
    Returns:
        dict: Dataset information including shape, columns, and preview
    """
    try:
        return {
            'shape': {
                'rows': df.shape[0],
                'columns': df.shape[1]
            },
            'columns': df.columns.tolist(),
            'preview': generate_preview(df)
        }
    except Exception as e:
        raise Exception(f"Error getting dataset info: {str(e)}")
