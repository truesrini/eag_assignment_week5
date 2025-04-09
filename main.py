import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters, types
from mcp.client.stdio import stdio_client
import asyncio
from google import genai
from concurrent.futures import TimeoutError
from functools import partial

# Load environment variables from .env file
load_dotenv()

# Access your API key and initialize Gemini client correctly
api_key = os.getenv("GEMINI_API_KEY")
client = genai.Client(api_key=api_key)

max_iterations = 6
last_response = None
iteration = 0
iteration_response = []

async def generate_with_timeout(client, prompt, timeout=10):
    """Generate content with a timeout"""
    print("Starting LLM generation...")
    try:
        # Convert the synchronous generate_content call to run in a thread
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None, 
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash",
                    contents=prompt
                )
            ),
            timeout=timeout
        )
        print("LLM generation completed")
        return response
    except TimeoutError:
        print("LLM generation timed out!")
        raise
    except Exception as e:
        print(f"Error in LLM generation: {e}")
        raise

def reset_state():
    """Reset all global variables to their initial state"""
    global last_response, iteration, iteration_response
    last_response = None
    iteration = 0
    iteration_response = []

async def main():
    reset_state()  # Reset at the start of main
    print("Starting main execution...")
    try:
        # Create a single MCP server connection
        print("Establishing connection to MCP server...")
        server_params = StdioServerParameters(
            command="python",
            args=["example2.py"]
        )

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                
                # Get available tools
                print("Requesting tool list...")
                tools_result = await session.list_tools()
                tools = tools_result.tools
                print(f"Successfully retrieved {len(tools)} tools")

                # Create system prompt with available tools
                print("Creating system prompt...")
                print(f"Number of tools: {len(tools)}")
                
                try:
                    tools_description = []
                    for i, tool in enumerate(tools):
                        try:
                            # Get tool properties
                            params = tool.inputSchema
                            desc = getattr(tool, 'description', 'No description available')
                            name = getattr(tool, 'name', f'tool_{i}')
                            
                            # Format the input schema in a more readable way
                            if 'properties' in params:
                                param_details = []
                                for param_name, param_info in params['properties'].items():
                                    param_type = param_info.get('type', 'unknown')
                                    param_details.append(f"{param_name}: {param_type}")
                                params_str = ', '.join(param_details)
                            else:
                                params_str = 'no parameters'

                            tool_desc = f"{i+1}. {name}({params_str}) - {desc}"
                            tools_description.append(tool_desc)
                            print(f"Added description for tool: {tool_desc}")
                        except Exception as e:
                            print(f"Error processing tool {i}: {e}")
                            tools_description.append(f"{i+1}. Error processing tool")
                    
                    tools_description = "\n".join(tools_description)
                    print("Successfully created tools description")
                except Exception as e:
                    print(f"Error creating tools description: {e}")
                    tools_description = "Error loading tools"
                
                print("Created system prompt...")
                
                system_prompt = f"""
You are a math agent solving problems in iterations and print the end result in paint. You have access to various mathematical tools & paint tools to display the final result.

Available tools:
{tools_description}

You will get the current context as JSON input. For any errors, use one of the error-handling messages to respond. Always perform self_check and output the answer.
{{
  "context": ["iteration1", "iteration2"],
  "error_handling": {{
      "on_tool_failure": "If a tool fails (e.g., due to invalid parameters, unavailable tool, or failure to return a result), the model should attempt to retry the operation up to 3 times. If the failure persists, it should log an error message and proceed with the next step.",
      "on_uncertainty": "If the model is unsure about the correctness of the reasoning or the final answer, it should ask for clarification or provide an explicit note stating that the result is uncertain.",
      "on_invalid_format": "If the response does not match the required format (e.g., JSON), the model should notify the user and attempt to correct the format."
    }},
    "self_check": "For each function call and final answer, verify the correctness and consistency of the output.Think Step by Step. If the output does not seem correct, raise an error or ask for clarification. Always ensure the format is as specified in the instructions.Alos include whether self check was successfull -Yes or No",
}}

You must respond with the correct JSON format like below:
1. For function calls:
{{
  "function_call": {{
    "name": "function_name",
    "args": {{
      "parameters": ["param1,param2"]
    }}
  }},
  "reasoning": "Arithmetic/Logical/Entity Lookup",
  "self_check": "Is this the correct method to call and the right paarmeters?-Yes/No",
  "errors": "None/Error description if any occur"
}}
   
2. For final answers:
{{
  "final_answer": "number",
  "reasoning": "Arithmetic/Logical/Entity Lookup",
  "self_check": "does this answer seem correct?Yes/No",
  "errors": "None/Error description if any occur"
}}

Important:
- When a function returns multiple values, you need to process all of them.
- Make sure that after a function call, you call a function to validate the function call.
- Only give FINAL_ANSWER when you have completed all necessary calculations.
- Do not repeat function calls with the same parameters.
- Only respond with valid json ,it should start with {{ and end with }}.Do not add string '''json to it.
- After you get the FINAL_ANSWER, you should make function calls to send Gmail with the final answer in the body of the email.
Example1
{{
  "function_call": {{
    "name": "strings_to_chars_to_int",
    "args": {{
       "parameters": ["India"]
    }}
  }},
  "reasoning": "logical",
  "self_check": "Is this the correct method to call?-Yes",
  "errors" : "None"
}}
Example1 -Validate
{{
  "function_call": {{
    "name": "validate_strings_to_chars_to_int",
    "args": {{
       "parameters": ["India","[73, 78, 68, 73, 65]"]
    }}
  }},
  "reasoning": "logical",
  "self_check": "Is this the correct method to call?-Yes",
  "errors" : "None"
}}

Example2
{{
  "final_answer":"50",
  "reasoning": "logical",
  "self_check": "Does this answer seem correct?-Yes",
  "errors" : "None"
}}

Example3
{{
  "function_call": {{
    "name": "call_send_gmail",
    "args": {{
       "parameters":["example@gmail.com","Final Answer","Final answer is 50"]
    }}
  }},
  "reasoning": "logical",
  "self_check": "Is this the correct method to call?-Yes",
  "errors" : "None"
}}

Answer either with a json format output for function call or final answer
"""

                query = """Find the ASCII values of characters in INDIA and then return sum of exponentials of those values. send a gmail with the final answer. """
                print("Starting iteration loop...")
                
                # Use global iteration variables
                global iteration, last_response
                
                while iteration < max_iterations:
                    print(f"\n--- Iteration {iteration + 1} ---")
                    if last_response is None:
                        current_query = query
                    else:
                        current_query = current_query + "\n\n" + " ".join(iteration_response)
                        current_query = current_query + "  What should I do next?"

                    # Get model's response with timeout
                    print("Preparing to generate LLM response...")
                    prompt = f"{system_prompt}\n\nQuery: {current_query}"
                    try:
                        response = await generate_with_timeout(client, prompt)
                        response_text = response.text.strip()
                        # Remove ```json and ``` if present
                        if response_text.startswith("```json"):
                            response_text = response_text[7:].strip()  # Remove ```json
                        if response_text.endswith("```"):
                            response_text = response_text[:-3].strip()  # Remove ```
                        print(f"LLM Response: {response_text}")
                        
                        # Find the FUNCTION_CALL line in the response
                        #for line in response_text.split('\n'):
                            #line = line.strip()
                            #if line.startswith("FUNCTION_CALL:"):
                                #response_text = line
                                #break
                        
                    except Exception as e:
                        print(f"Failed to get LLM response: {e}")
                        break

                    if "function_call" in response_text:
                        try:
                            # Parse the JSON response
                            import json
                            response_json = json.loads(response_text)
                            function_call = response_json.get("function_call", {})
                            func_name = function_call.get("name")
                            params = function_call.get("args", {}).get("parameters", [])
                            
                            print(f"\nDEBUG: Parsed function name: {func_name}")
                            print(f"DEBUG: Parsed parameters: {params}")
                            
                            # Find the matching tool to get its input schema
                            tool = next((t for t in tools if t.name == func_name), None)
                            if not tool:
                                print(f"DEBUG: Available tools: {[t.name for t in tools]}")
                                raise ValueError(f"Unknown tool: {func_name}")

                            print(f"DEBUG: Found tool: {tool.name}")
                            print(f"DEBUG: Tool schema: {tool.inputSchema}")

                            # Prepare arguments according to the tool's input schema
                            arguments = {}
                            schema_properties = tool.inputSchema.get('properties', {})
                            print(f"DEBUG: Schema properties: {schema_properties}")

                            for param_name, param_info in schema_properties.items():
                                if not params:  # Check if we have enough parameters
                                    raise ValueError(f"Not enough parameters provided for {func_name}")
                                    
                                value = params.pop(0)  # Get and remove the first parameter
                                param_type = param_info.get('type', 'string')
                                
                                print(f"DEBUG: Converting parameter {param_name} with value {value} to type {param_type}")
                                
                                # Convert the value to the correct type based on the schema
                                if param_type == 'integer':
                                    arguments[param_name] = int(value)
                                elif param_type == 'number':
                                    arguments[param_name] = float(value)
                                elif param_type == 'array':
                                    # Handle array input
                                    if isinstance(value, str):
                                        value = value.strip('[]').split(',')
                                    arguments[param_name] = [int(x.strip()) for x in value]
                                else:
                                    arguments[param_name] = str(value)

                            print(f"DEBUG: Final arguments: {arguments}")
                            print(f"DEBUG: Calling tool {func_name}")
                            
                            result = await session.call_tool(func_name, arguments=arguments)
                            print(f"DEBUG: Raw result: {result}")
                            
                            # Get the full result content
                            if hasattr(result, 'content'):
                                print(f"DEBUG: Result has content attribute")
                                # Handle multiple content items
                                if isinstance(result.content, list):
                                    iteration_result = [
                                        item.text if hasattr(item, 'text') else str(item)
                                        for item in result.content
                                    ]
                                else:
                                    iteration_result = str(result.content)
                            else:
                                print(f"DEBUG: Result has no content attribute")
                                iteration_result = str(result)
                                
                            print(f"DEBUG: Final iteration result: {iteration_result}")
                            
                            # Format the response based on result type
                            if isinstance(iteration_result, list):
                                result_str = f"[{', '.join(iteration_result)}]"
                            else:
                                result_str = str(iteration_result)
                            
                            iteration_response.append(
                                f"In the {iteration + 1} iteration you called {func_name} and got answer {result_str}."
                            )
                            last_response = iteration_result
                            print(f"DEBUG: iteration_response: {iteration_response}")

                        except Exception as e:
                            print(f"DEBUG: Error details: {str(e)}")
                            print(f"DEBUG: Error type: {type(e)}")
                            import traceback
                            traceback.print_exc()
                            iteration_response.append(f"Error in iteration {iteration + 1}: {str(e)}")
                            break
                    else:
                        iteration_response.append(
                                f"In the {iteration + 1} iteration you got {response_text} "
                            )
                        last_response = response_text
                        print(f"DEBUG: iteration_response: {iteration_response}")

                    iteration += 1

    except Exception as e:
        print(f"Error in main execution: {e}")
        import traceback
        traceback.print_exc()
    finally:
        reset_state()  # Reset at the end of main

if __name__ == "__main__":
    asyncio.run(main())


