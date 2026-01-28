# LLM-As-Judge Evaluation Prompts - Summary

**Created:** January 20, 2026  
**Location:** `/evals/eval_prompts/`

## What Was Created

This directory contains **6 YAML-based LLM-as-judge prompt templates** for evaluating AI agent performance across multiple dimensions.

### File Structure

```
evals/eval_prompts/
├── __init__.py                      # Package initialization with YAML loaders
├── response_relevance.yaml          # Criterion 1: Response Relevance (15%)
├── response_completeness.yaml       # Criterion 2: Response Completeness (15%)
├── response_coherence.yaml          # Criterion 3: Response Coherence (10%)
├── query_understanding.yaml         # Criterion 6: Query Understanding (15%)
├── instruction_following.yaml        # Criterion 9: Instruction Following (5%)
├── semantic_search_quality.yaml      # Criterion 11: Semantic Search Quality (5%)
├── README.md                        # Comprehensive documentation
├── example_usage.py                 # Usage examples and integration guide
└── SUMMARY.md                       # This file
```

## Coverage

### LLM-As-Judge Criteria (6 of 11 total criteria)

| ID | Criterion | Weight | File | Type |
|----|-----------|--------|------|------|
| 1 | Response Relevance | 15% | `response_relevance.yaml` | Universal |
| 2 | Response Completeness | 15% | `response_completeness.yaml` | Universal |
| 3 | Response Coherence | 10% | `response_coherence.yaml` | Universal |
| 6 | Query Understanding | 15% | `query_understanding.yaml` | Universal |
| 9 | Instruction Following | 5% | `instruction_following.yaml` | Universal |
| 11 | Semantic Search Quality | 5% | `semantic_search_quality.yaml` | Usecase-Specific |

**Total LLM-as-judge weight:** 65% of overall evaluation score

### Other Criteria (Not LLM-as-judge)

These criteria use code-based or agent-path evaluation methods:

| ID | Criterion | Weight | Type | Evaluation Method |
|----|-----------|--------|------|-------------------|
| 4 | Routing Correctness | 20% | Agent Path | F1 score calculation |
| 5 | Tool Usage Correctness | 10% | Code-Based | Percentage calculation |
| 7 | Agent Path Efficiency | 5% | Agent Path | Ratio calculation |
| 8 | Sub-Agent Invocation Order | 5% | Agent Path | Binary logic check |
| 10 | Tool Call Success Rate | 0% | Code-Based | Success rate monitoring |

## Key Features

### 1. YAML-Based Format
All prompts are stored in YAML format for:
- Easy editing without code changes
- Portable across different systems
- Version control friendly
- Metadata included (weights, score ranges, etc.)
- Consistent structure across all prompts

### 2. Detailed Scoring Guidelines
Each prompt includes:
- **Score 5:** Excellent performance
- **Score 4:** Good performance with minor issues
- **Score 3:** Adequate with notable gaps
- **Score 2:** Poor with significant issues
- **Score 1:** Failing to meet criteria

### 3. Context-Aware Variables
Prompts use template variables for:
- User queries and agent responses
- Expected outputs and requirements
- Agent instructions and guidelines
- Search actions and results

### 4. Domain Agnostic
While created for cruise booking agents, prompts can be adapted for:
- E-commerce agents
- Customer service bots
- Information retrieval systems
- Any multi-agent conversational system

## Usage Example

```python
from evals.eval_prompts import RESPONSE_RELEVANCE_TEMPLATE, load_prompt

# Method 1: Use pre-loaded template
prompt = RESPONSE_RELEVANCE_TEMPLATE.format(
    input="User's query here",
    output="Agent's response here",
    expected_response_type="Type of expected response"
)

# Method 2: Load YAML with metadata
config = load_prompt('response_relevance')
print(f"Weight: {config['weight']}, Required: {config['required_variables']}")
prompt = config['template'].format(
    input="User's query here",
    output="Agent's response here",
    expected_response_type="Type of expected response"
)

# Send to LLM for evaluation
evaluation = your_llm_api.generate(prompt)

# Expected output format:
# Score: 5
# Reasoning: Response perfectly addresses the user's query...
```

## Integration Points

### With Evaluation Framework
- Aligns with `datasets/evaluation_criteria.csv` definitions
- Follows scoring scales from `../datasets/evaluation_spec.md`
- Maps to criteria in `CRITERIA_QUICK_REFERENCE.md`

### With LLM APIs
Compatible with:
- OpenAI GPT-4 / GPT-3.5
- Anthropic Claude (3.5 Sonnet, 3 Opus)
- Other instruction-following LLMs

### With Observability Tools
Can integrate with:
- Phoenix (Arize AI)
- LangSmith
- Weights & Biases
- Custom evaluation pipelines

## Best Practices

### 1. Temperature Settings
```python
# Use temperature=0 for consistent scoring
response = llm.generate(prompt, temperature=0)
```

### 2. Multiple Evaluators
```python
# Run same prompt with different LLMs for reliability
scores = []
for model in ["gpt-4", "claude-3-5-sonnet"]:
    scores.append(evaluate(prompt, model))
average_score = sum(scores) / len(scores)
```

### 3. Batch Processing
```python
# Evaluate multiple test cases efficiently
results = []
for test_case in test_cases:
    prompt = format_prompt(test_case)
    result = evaluate(prompt)
    results.append(result)
```

### 4. Score Validation
```python
# Ensure scores are in valid range
def validate_score(score, min_score=1, max_score=5):
    if not (min_score <= score <= max_score):
        raise ValueError(f"Score {score} out of range")
    return score
```

## Score Aggregation

### Individual Criterion Score
```python
# Normalize 1-5 score to 0-1 range
normalized_score = (score - 1) / 4  # or just score / 5
```

### Weighted Overall Score
```python
weights = {
    'response_relevance': 0.15,
    'response_completeness': 0.15,
    'response_coherence': 0.10,
    'query_understanding': 0.15,
    'instruction_following': 0.05,
    'semantic_search_quality': 0.05  # if applicable
}

# Note: Remaining 35% comes from code-based criteria
llm_judge_score = sum(
    (scores[criterion] / 5) * weight
    for criterion, weight in weights.items()
)
```

## Comparison with Arize AI Framework

Our prompts follow best practices from [Arize AI tutorials](https://github.com/Arize-ai/tutorials/tree/main/python):

| Aspect | Arize AI Approach | Our Implementation |
|--------|-------------------|-------------------|
| **Structure** | Clear BEGIN DATA / END DATA sections | ✓ Implemented |
| **Scoring** | Numeric scales with guidelines | ✓ 1-5 scale with detailed guidelines |
| **Output Format** | Standardized parseable format | ✓ Score + Reasoning format |
| **Context** | Include relevant context in prompt | ✓ Template variables for all context |
| **Criteria** | Specific evaluation dimensions | ✓ 6 distinct criteria |

## Future Enhancements

Potential additions for future versions:

1. **Multi-language Support:** Prompts for evaluating non-English responses
2. **Explanation Quality:** Evaluate quality of agent's explanations
3. **Factual Accuracy:** Check correctness of facts in response
4. **Bias Detection:** Identify potential biases in agent responses
5. **Creativity Score:** For creative or generative use cases
6. **Code Quality:** For code-generating agents

## Version History

- **v1.0** (2026-01-20): Initial release with 6 LLM-as-judge prompts
  - Response Relevance
  - Response Completeness
  - Response Coherence
  - Query Understanding
  - Instruction Following
  - Semantic Search Quality

## References

1. [Arize AI Python Tutorials](https://github.com/Arize-ai/tutorials/tree/main/python)
2. Phoenix Evaluation Documentation
3. LangChain Evaluation Guide
4. OpenAI Evals Framework

## Support

For questions or issues:
1. Check `README.md` for detailed usage instructions
2. Review `example_usage.py` for code examples
3. Refer to `../CRITERIA_QUICK_REFERENCE.md` for criteria definitions
4. See `../datasets/evaluation_spec.md` for complete specifications

---

**Total Lines of Code:** ~600 lines across all files  
**Test Status:** ✓ All imports successful  
**Integration Ready:** Yes
