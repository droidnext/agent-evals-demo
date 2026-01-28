"""SQL syntax validation evaluation function."""

try:
    import sqlparse
except ImportError:
    sqlparse = None


def evaluate_sql_syntax(input: dict, output: dict) -> float:
    """Evaluate if SQL syntax is correct.
    
    This function checks if SQL queries in the output have valid syntax.
    It validates SQL syntax using sqlparse parser.
    
    Args:
        input: Input dictionary containing test case information.
            May contain 'sql_queries' field with expected SQL queries (optional).
        output: Output dictionary containing agent execution results.
            Should contain 'sql_queries' field with list of SQL queries executed,
            or 'sql_query' for a single query.
    
    Returns:
        float: Score between 0.0 and 1.0.
            - 1.0 if all SQL queries have valid syntax
            - 0.0 if any SQL query has invalid syntax or if no SQL queries found
            - 0.0 if sqlparse is not available
    """
    if output is None:
        return 0.0
    
    if sqlparse is None:
        return 0.0
    
    # Extract SQL queries from output
    sql_queries = []
    
    # Check for 'sql_queries' (list) or 'sql_query' (single query)
    if 'sql_queries' in output:
        queries = output['sql_queries']
        if isinstance(queries, str):
            sql_queries = [q.strip() for q in queries.split(',') if q.strip()]
        elif isinstance(queries, list):
            sql_queries = [str(q).strip() for q in queries if q]
    elif 'sql_query' in output:
        query = output['sql_query']
        if query:
            sql_queries = [str(query).strip()]
    
    # If no SQL queries found, return 0.0
    if not sql_queries:
        return 0.0
    
    # Validate each SQL query
    for sql_query in sql_queries:
        if not sql_query:
            continue
        
        # Try to parse the SQL query
        # sqlparse.parse() will return an empty list or raise an exception for invalid syntax
        try:
            parsed = sqlparse.parse(sql_query)
            # If parsing returns empty list, the query is likely invalid
            if not parsed:
                return 0.0
            # Check if the parsed statement has any tokens (basic validation)
            if parsed and len(parsed) > 0:
                statement = parsed[0]
                # If statement has no tokens, it's likely invalid
                if not statement.tokens:
                    return 0.0
        except Exception:
            # If parsing raises an exception, the syntax is invalid
            return 0.0
    
    return 1.0
