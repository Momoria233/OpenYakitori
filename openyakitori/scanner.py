import os
from typing import Dict

def scan_plugins(plugin_dir: str = "plugins") -> Dict[str, str]:
    """
    Recursively scans the plugin directory for Python files and merges them by plugin folder.

    Args:
        plugin_dir: The directory to scan for plugins. Defaults to "plugins".

    Returns:
        A dictionary where keys are plugin names (folder names) and values are the merged
        source code of all Python files within that plugin folder.
    """
    plugins_code: Dict[str, str] = {}
    
    # Ensure plugin_dir exists
    if not os.path.exists(plugin_dir):
        return {}

    # Iterate over items in the plugin directory
    for item in os.listdir(plugin_dir):
        item_path = os.path.join(plugin_dir, item)
        
        # We only care about directories (plugin folders)
        # If the plugin is a single file in plugins/ dir, it's not explicitly covered by "plugin folder name" rule
        # but typically plugins are folders. The example says `plugins/bilibili/xxx.py` -> `bilibili`.
        # If there is `plugins/myplugin.py`, should it be `myplugin`?
        # The spec says "plugin_name is plugin folder name". So I will assume plugins are folders.
        if not os.path.isdir(item_path):
            continue
            
        # Ignore __pycache__ and hidden directories
        if item == "__pycache__" or item.startswith("."):
            continue

        plugin_name = item
        plugin_content = []
        total_chars = 0
        max_chars = 200000

        # Recursively walk through the plugin directory
        for root, dirs, files in os.walk(item_path):
            # Modify dirs in-place to skip __pycache__
            if "__pycache__" in dirs:
                dirs.remove("__pycache__")
                
            for file in files:
                if not file.endswith(".py"):
                    continue
                
                file_path = os.path.join(root, file)
                try:
                    with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                        content = f.read()
                        
                        # Check if adding this file exceeds the limit
                        if total_chars + len(content) > max_chars:
                            remaining_chars = max_chars - total_chars
                            if remaining_chars > 0:
                                plugin_content.append(content[:remaining_chars])
                                total_chars += remaining_chars
                            # Stop reading files for this plugin if limit reached
                            # We can break the inner loop, but need to break the outer loop too
                            # A flag or check at start of loop can handle this
                            break 
                        
                        plugin_content.append(content)
                        total_chars += len(content)
                        
                        # Add a newline separator between files
                        if total_chars < max_chars:
                            plugin_content.append("\n")
                            total_chars += 1
                        
                except Exception as e:
                    print(f"Error reading file {file_path}: {e}")
            
            if total_chars >= max_chars:
                break
        
        if plugin_content:
            plugins_code[plugin_name] = "".join(plugin_content)

    return plugins_code
