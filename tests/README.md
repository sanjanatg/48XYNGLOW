# Find My Fund - Test Runner

This directory contains tools for testing the Find My Fund RAG system with various queries and evaluating its performance.

## Prerequisites

Before running the tests, make sure you have:

1. Installed the required packages:
   ```bash
   pip install colorama requests
   ```

2. Started the Ollama service:
   ```bash
   # Using the provided script
   .\start_all.ps1
   
   # Or directly
   ollama serve
   ```

3. Started the API server:
   ```bash
   cd FINAL
   python api_server.py
   ```

## Test Files

- `test_queries.json`: Contains sample test queries with expected funds
- `test_runner.py`: Python script to run tests against the API

## Running Tests

### Using Default Test File

Simply run the test runner with no arguments:

```bash
cd tests
python test_runner.py
```

This will use the default `test_queries.json` file in the same directory.

### Using a Custom Test File

```bash
python test_runner.py path/to/custom_test_file.json
```

### Specifying Number of Results

You can specify how many top results to fetch for each query:

```bash
python test_runner.py path/to/test_file.json 10
```

### Interactive Mode

If no test file is found, or if you prefer manual testing, the test runner will offer an interactive mode where you can enter queries one by one.

## Test File Format

The test file should be a JSON array of objects with the following structure:

```json
[
  {
    "query": "low risk debt fund",
    "expected_fund": "ICICI Low Risk Bond Fund"
  },
  {
    "query": "tech fund with high returns",
    "expected_fund": "HDFC Technology Fund"
  }
]
```

Each object must have a `query` field and may optionally have an `expected_fund` field for validation.

## Evaluation Metrics

The test runner reports:

1. Success rate of API calls
2. Match rate of expected funds (if provided)
3. Response time for each query
4. Score breakdown (semantic, metadata, fuzzy, combined)
5. LLM reasoning/explanation

## Adapting for New Test Sets

If evaluators provide a different test set format, you can:

1. Convert it to the expected JSON format
2. Create a custom adapter in `test_runner.py` to handle the new format
3. Use the test runner in interactive mode to manually test queries

## Troubleshooting

If you encounter issues:

1. Check that Ollama is running and the model is available
2. Ensure the API server is running at http://localhost:5000
3. Verify that the test file is properly formatted
4. Check for any errors in the terminal output

For more details, refer to the main project documentation. 