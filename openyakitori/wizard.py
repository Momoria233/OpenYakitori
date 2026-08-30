import json
import os
import sys
from typing import Dict, List, Any

# Ensure we can import from the openyakitori package or local directory
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

try:
    from openyakitori.scanner import scan_plugins
except ImportError:
    try:
        from scanner import scan_plugins
    except ImportError:
        # Fallback if running directly in the directory without package structure
        sys.path.append(current_dir)
        from scanner import scan_plugins

def call_llm(prompt: str) -> str:
    """
    Calls the LLM with the given prompt.
    
    Args:
        prompt: The prompt string to send to the LLM.
        
    Returns:
        The LLM's response string.
        
    Raises:
        NotImplementedError: This function is not yet implemented.
    """
    raise NotImplementedError("LLM interface not implemented yet.")

def construct_prompt(plugin_name: str, plugin_code: str) -> str:
    """
    Constructs the prompt for the LLM to analyze the plugin code.
    
    Args:
        plugin_name: The name of the plugin.
        plugin_code: The source code of the plugin.
        
    Returns:
        The constructed prompt string.
    """
    prompt = f"""You are an expert developer analyzing NoneBot plugin code.
Your task is to extract command information from the provided Python code for the plugin "{plugin_name}".

You need to identify the following patterns:
- `on_command`
- `on_regex`
- `on_keyword`
- `Command`
- `@xxx.handle()` handlers

For each command found, extract a description from the associated docstrings or comments.

Return the result STRICTLY as a valid JSON object. Do not include any markdown formatting (like ```json ... ```) or extra text.
The JSON object must have a "commands" key containing a list of command objects.

Example JSON structure:
{{
  "commands": [
    {{
      "type": "command",
      "trigger": "start",
      "description": "Start the bot"
    }},
    {{
      "type": "regex",
      "trigger": "^hello",
      "description": "Reply to hello"
    }}
  ]
}}

Plugin Code:
```python
{plugin_code}
```
"""
    return prompt

def main():
    plugins = scan_plugins()
    print("扫描插件完成")
    
    print("调用 LLM 分析插件")
    all_commands: List[Dict[str, Any]] = []
    
    for plugin_name, plugin_code in plugins.items():
        prompt = construct_prompt(plugin_name, plugin_code)
        
        try:
            response = call_llm(prompt)
            data = json.loads(response)
        except NotImplementedError:
            # Mock JSON response to allow process to continue
            data = {"commands": []}
        except json.JSONDecodeError:
            # Handle JSON decode error if LLM returns invalid JSON
            data = {"commands": []}
        except Exception as e:
            # Handle other exceptions
            print(f"Error processing plugin {plugin_name}: {e}")
            data = {"commands": []}
            
        if "commands" in data and isinstance(data["commands"], list):
            all_commands.extend(data["commands"])

    print("生成 commands.json")
    output_dir = ".openyakitori"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
        
    output_file = os.path.join(output_dir, "commands.json")
    try:
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(all_commands, f, indent=2, ensure_ascii=False)
    except IOError as e:
        print(f"Error writing to file {output_file}: {e}")

if __name__ == "__main__":
    main()
