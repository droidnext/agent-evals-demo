"""Tool usage validation evaluation function."""


def evaluate_tool_usage_check(input: dict, output: dict, expected: dict) -> float:
    """Evaluate if correct tools were used.
    
    This function checks if the tools used by the agent match the expected tools.
    
    Args:
        input: Input dictionary containing test case information.
        output: Output dictionary containing agent execution results.
            Should contain 'tools_used' field with list of tools actually used.
        expected: Dictionary containing expected values.
            Should contain 'expected_tool_calls' field with expected tools (comma-separated string or list).
    
    Returns:
        float: Score between 0.0 and 1.0.
            - 1.0 if all expected tools were used (when expected_tool_calls is empty, returns 1.0 if no tools used)
            - 0.0 if no tools were used when tools were expected
            - Percentage of correct tools used (len(correct_tools) / len(expected_tools))
    """
    if output is None:
        return 0.0
    
    # Extract expected tools from expected dict
    expected_tools_str = expected.get('expected_tool_calls', '')
    if isinstance(expected_tools_str, list):
        expected_tools = {str(t).strip() for t in expected_tools_str if str(t).strip()}
    else:
        expected_tools = set(expected_tools_str.split(',')) if expected_tools_str else set()
        expected_tools = {t.strip() for t in expected_tools if t.strip()}
    
    # Extract actual tools from output
    actual_tools = output.get('tools_used', [])
    if isinstance(actual_tools, str):
        actual_tools = [t.strip() for t in actual_tools.split(',') if t.strip()]
    actual_tools = set(actual_tools)
    
    # If no tools expected, return 1.0 if no tools used, 0.0 otherwise
    if not expected_tools:
        return 1.0 if not actual_tools else 0.0
    
    # If tools expected but none used, return 0.0
    if not actual_tools:
        return 0.0
    
    # Calculate score based on intersection of expected and actual tools
    correct_tools = expected_tools & actual_tools
    return len(correct_tools) / len(expected_tools) if expected_tools else 0.0
