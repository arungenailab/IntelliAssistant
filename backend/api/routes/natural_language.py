from fastapi import APIRouter
from utils.langgraph_sql.api_integration import convert_text_to_sql
import traceback

router = APIRouter()

@router.post('/sql')
async def natural_language_to_sql(request: dict):
    try:
        # Extract request parameters
        query = request.get('query', '')
        db_info = request.get('dbInfo', {})
        schema_info = request.get('schemaInfo', {})
        conversation_history = request.get('conversationHistory', [])
        execute = request.get('execute', False) 
        limit = request.get('limit', 50)
        
        # Extract feature flags if present (defaulting to configured values if absent)
        feature_flags = request.get('featureFlags', {})
        use_langgraph = feature_flags.get('enableLangGraphSql', None)  
        enable_reflection = feature_flags.get('enableSqlReflection', None)
        enable_execution = feature_flags.get('enableSqlExecution', None)
        
        # Convert natural language to SQL
        result = await convert_text_to_sql(
            query=query,
            connection_params=db_info,
            schema_info=schema_info,
            conversation_history=conversation_history,
            execute_query=execute,
            limit=limit,
            use_langgraph=use_langgraph,
            enable_reflection=enable_reflection,
            enable_execution=enable_execution
        )
        
        return result
        
    except Exception as e:
        logger.error(f"Error in natural language to SQL conversion: {str(e)}")
        logger.error(traceback.format_exc())
        return {
            "error": f"Error converting natural language to SQL: {str(e)}"
        } 