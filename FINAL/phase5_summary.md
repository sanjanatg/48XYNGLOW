# Phase 5: Local LLM – Setup & Prompting (RAG)

## Overview

In Phase 5, we've implemented a Retrieval-Augmented Generation (RAG) system powered by a local Mistral-7B LLM. This system enhances the mutual fund search engine by providing AI-generated insights, explanations, and recommendations based on the retrieved fund data.

The implementation uses the Mistral-7B-Instruct model with Q4_K_M quantization, which offers an excellent balance between performance and resource requirements, needing approximately 6-8GB of VRAM.

## Key Components

### LLM Interface

The core of this phase is the `LLMInterface` class that:

1. **Loads and manages the local LLM**: Handles model loading, parameter configuration, and error handling.
2. **Implements context preparation**: Formats mutual fund data into appropriate context for the LLM.
3. **Provides specialized analysis functions**: 
   - Fund analysis
   - Fund comparison
   - Investment recommendations
   - Financial concept explanations

### RAG Implementation

The RAG system follows this workflow:

1. **Retrieval**: Uses the search engine to find relevant mutual funds based on the user's query.
2. **Context Building**: Transforms the retrieved fund data into a structured context.
3. **Generation**: Passes the context and query to the LLM to generate a comprehensive response.
4. **Presentation**: Formats and displays the response with attribution to the source funds.

### System Prompting

We've carefully designed the system prompt to ensure the LLM:
- Focuses on factual information from the provided context
- Provides balanced analysis mentioning both benefits and risks
- Uses objective metrics when comparing funds
- Never fabricates fund details not present in the context

### Demo Interface

The `run_llm_demo.py` script provides multiple modes for interacting with the system:

1. **Guided Demo**: Demonstrates the system with predefined queries.
2. **Conversation Mode**: Allows interactive Q&A about mutual funds.
3. **Fund-Specific Analysis**: Provides in-depth analysis of specific funds.
4. **Fund Comparison**: Compares multiple funds across different aspects.

## Technical Implementation

### Model Configuration

- **Model**: Mistral-7B-Instruct-v0.2
- **Quantization**: Q4_K_M (4-bit quantization with medium precision)
- **Context Window**: 8192 tokens
- **Integration**: Uses llama-cpp-python for efficient inference

### Integration with Search Engine

The LLM system integrates with our existing search engine:
1. User submits a query
2. Search engine retrieves relevant funds
3. LLM generates insights using the fund data as context
4. The response is presented to the user with attribution

### Context Optimization

To optimize context usage, we:
- Prioritize the most relevant fund information
- Format data in a consistent structure
- Include key metrics and unique features of each fund
- Limit the number of funds used as context to ensure depth of analysis

## Use Cases

### Fund Analysis

Generates comprehensive analysis of mutual funds, including:
- Performance evaluation
- Risk assessment
- Portfolio composition analysis
- Suitability for different investor profiles

### Comparative Analysis

Compares multiple funds across various dimensions:
- Returns and performance metrics
- Risk levels and volatility
- Expense ratios and costs
- Asset allocation and sector exposure
- Management style and strategy

### Investment Recommendations

Provides personalized recommendations based on:
- Investment goals (growth, income, preservation)
- Risk tolerance
- Investment horizon
- Tax considerations

### Financial Education

Explains financial concepts in the context of mutual funds:
- Fund categories and types
- Investment strategies
- Performance metrics
- Risk measures
- Tax implications

## Future Enhancements

1. **Model Upgrades**: Support for more powerful models as hardware capabilities increase
2. **Fine-tuning**: Domain-specific fine-tuning for mutual fund analysis
3. **Multi-modal Support**: Integration of charts and visualizations
4. **Memory**: Adding conversational memory for follow-up questions
5. **Evaluation**: Implementing factuality and relevance scoring

## Running the System

To use the system:
1. Download the Mistral-7B model (Q4_K_M quantization, ~4.2GB)
2. Place it in the models directory
3. Run the `run_llm_demo.py` script to start the interactive demo

System requirements:
- At least 8GB RAM
- 6-8GB VRAM (for optimal performance)
- ~4.5GB disk space for the model file

This phase transforms the search engine into a comprehensive mutual fund analysis platform that can understand complex queries, provide nuanced insights, and help users make informed investment decisions.

## Bug Fixes and Improvements

During code review, we identified and fixed several issues in the LLM integration phase:

1. **LLM Response Format Validation**:
   - **Issue**: No handling for unexpected response formats from the LLM
   - **Fix**: Added validation of the LLM response format:
     ```python
     # Extract generated text with proper error handling
     if 'choices' in response and len(response['choices']) > 0 and 'text' in response['choices'][0]:
         generated_text = response['choices'][0]['text'].strip()
     else:
         logger.warning(f"Unexpected response format from LLM: {response}")
         generated_text = "Sorry, I couldn't generate a proper response. The model returned an unexpected format."
     ```

2. **Context Preparation Issues**:
   - **Issue**: The context preparation for the LLM could fail with missing or invalid fund data
   - **Fix**: Added robust handling of fund data with proper defaults:
     ```python
     def _prepare_context(self, fund_data_list: List[Dict[str, Any]]) -> str:
         """Prepare context from fund data for the LLM"""
         context_parts = []
         
         for i, fund_data in enumerate(fund_data_list, 1):
             try:
                 # Get basic fund info with defaults
                 fund_name = fund_data.get('fund_name', 'Unknown Fund')
                 fund_context = f"Fund {i}: {fund_name}\n"
                 
                 # Add other fund details safely
                 # ...
                 
                 context_parts.append(fund_context)
             except Exception as e:
                 logger.error(f"Error preparing context for fund {i}: {str(e)}")
                 context_parts.append(f"Fund {i}: Error retrieving fund data.")
         
         return "\n\n".join(context_parts)
     ```

3. **LLM Model Loading Issues**:
   - **Issue**: Insufficient error handling when the LLM model failed to load
   - **Fix**: Added better error handling and user guidance:
     ```python
     def is_model_loaded(self) -> bool:
         """Check if the model is loaded."""
         return self.model is not None
         
     # In the generate_response method:
     if not self.is_model_loaded():
         return "Model not loaded. Please download the model file.", 0.0
     ```

4. **System Prompt Generation**:
   - **Issue**: The system prompt wasn't providing sufficient guidance to the LLM
   - **Fix**: Enhanced the system prompt to better instruct the LLM:
     ```python
     def generate_system_prompt(self) -> str:
         """Generate the system prompt for the LLM."""
         return """You are MutualFundGPT, an AI assistant specialized in analyzing and explaining mutual funds.
     You provide clear, concise, factual information about mutual funds and help investors make informed decisions.
     Always base your responses on the provided context information about mutual funds.
     Never make up fund details, returns, or holdings that are not mentioned in the context.
     Your analysis should be balanced, mentioning both potential benefits and risks.
     When comparing funds, use objective metrics like returns, risk level, and expense ratio."""
     ```

5. **Demo Script Robustness**:
   - **Issue**: The demo script (`run_llm_demo.py`) didn't handle errors gracefully
   - **Fix**: Added comprehensive error handling to provide a better user experience:
     ```python
     try:
         # Generate LLM response
         with Progress() as progress:
             task = progress.add_task("[green]Generating LLM response...", total=1)
             response, time_taken = llm.generate_response(query, context_funds)
             progress.update(task, completed=1)
         
         # Display response
         display_llm_response(query, response, context_funds, time_taken)
         
     except Exception as e:
         console.print(f"[bold red]Error:[/bold red] {str(e)}")
     ```

These improvements make the LLM integration more robust and user-friendly, ensuring that the LLM component can handle real-world data variations and provide meaningful responses even when faced with unexpected inputs or model behavior. The changes improve both the reliability of the LLM integration and the quality of the AI-generated responses. 