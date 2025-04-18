# Assignment 5: Reasoning with LLMs

This repository contains a project that demonstrates reasoning with Large Language Models (LLMs) using mathematical tools and integration with external services like Gmail and Microsoft Paint. The project is built using Python and leverages the MCP (Model Context Protocol) framework for tool-based reasoning.

## Features

- **Mathematical Tools**: Perform operations like addition, subtraction, multiplication, division, factorial, logarithms, and more.
- **String Manipulation**: Convert strings to ASCII values and validate them.
- **Exponential Calculations**: Compute the sum of exponentials of a list of integers and validate the results.
- **Fibonacci Sequence**: Generate Fibonacci numbers.
- **Integration with Paint**: Draw shapes and add text in Microsoft Paint programmatically.
- **Gmail Integration**: Send emails with results using a local Gmail API.
- **Dynamic Prompts**: Use prompts to guide reasoning and tool usage.

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/your-repo/assignment-5-reasoning-llm.git
   cd assignment-5-reasoning-llm
   ```

2. Install dependencies:
   ```bash

  pip install uv
  uv --install
   ```

3. Set up environment variables:
   - Create a `.env` file in the root directory.
   - Add your Gemini API key:
     ```env
     GEMINI_API_KEY=your_api_key_here
     ```

## Usage

### Running the MCP Server

To start the MCP server:
```bash
python example2.py
```

### Running the Main Script

To execute the main script:
```bash
python main.py
```

### Sending Gmail

Ensure the local Gmail API is running at `http://localhost:5007/send-email`. The `call_send_gmail` tool will use this endpoint to send emails.

### Drawing in Paint

The project includes tools to interact with Microsoft Paint. Ensure Paint is installed and accessible on your system.

## Project Structure

- `example2.py`: Contains the MCP server implementation and tool definitions.
- `main.py`: Main script to interact with the MCP server and perform reasoning tasks.
- `prompts.md`: Contains prompt templates for guiding the reasoning process.
- `prompt_of_prompts.md`: Evaluation criteria for prompt design.
- `talk2mcp-gmail.py`: Script for integrating with Gmail API.
- `pyproject.toml`: Project metadata and dependencies.

## Tools

### Mathematical Tools
- `add`, `subtract`, `multiply`, `divide`
- `power`, `sqrt`, `cbrt`
- `factorial`, `log`, `remainder`
- `sin`, `cos`, `tan`

### String Tools
- `strings_to_chars_to_int`
- `validate_strings_to_chars_to_int`

### Exponential Tools
- `int_list_to_exponential_sum`
- `validate_int_list_to_exponential_sum`

### Paint Tools
- `open_paint`
- `draw_rectangle`
- `add_text_in_paint`

### Gmail Tool
- `call_send_gmail`

## Contributing

Contributions are welcome! Please fork the repository and submit a pull request.

## License

This project is licensed under the MIT License. See the `LICENSE` file for details.

## Acknowledgments

- [MCP Framework](https://github.com/mcp-framework)
- [Google GenAI](https://genai.google.com)
- Python community for the amazing libraries used in this project.
