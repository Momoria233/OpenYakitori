import os
import shutil
import sys
import json
import subprocess
from openyakitori.scanner import scan_plugins

def setup_dummy_files(base_dir="dummy_plugins"):
    if os.path.exists(base_dir):
        shutil.rmtree(base_dir)
    os.makedirs(base_dir)

    # Plugin 1: Normal multiple files
    p1 = os.path.join(base_dir, "plugin1")
    os.makedirs(p1)
    with open(os.path.join(p1, "part1.py"), "w", encoding="utf-8") as f:
        f.write("def func1():\n    pass")
    with open(os.path.join(p1, "part2.py"), "w", encoding="utf-8") as f:
        f.write("def func2():\n    pass")
    # Non-py file
    with open(os.path.join(p1, "README.md"), "w", encoding="utf-8") as f:
        f.write("Documentation")

    # Plugin 2: Nested directories
    p2 = os.path.join(base_dir, "plugin2")
    os.makedirs(os.path.join(p2, "sub"))
    with open(os.path.join(p2, "sub", "deep.py"), "w", encoding="utf-8") as f:
        f.write("deep_content")

    # Plugin 3: __pycache__ test
    p3 = os.path.join(base_dir, "plugin3")
    os.makedirs(os.path.join(p3, "__pycache__"))
    with open(os.path.join(p3, "__pycache__", "cache.py"), "w", encoding="utf-8") as f:
        f.write("SHOULD_NOT_BE_INCLUDED")
    with open(os.path.join(p3, "real.py"), "w", encoding="utf-8") as f:
        f.write("real_content")

    # Plugin 4: Large content
    p4 = os.path.join(base_dir, "plugin4")
    os.makedirs(p4)
    with open(os.path.join(p4, "large.py"), "w", encoding="utf-8") as f:
        f.write("a" * 200010)

    # Top level __pycache__ (should be ignored entirely)
    os.makedirs(os.path.join(base_dir, "__pycache__"))
    with open(os.path.join(base_dir, "__pycache__", "garbage.py"), "w", encoding="utf-8") as f:
        f.write("garbage")

    return base_dir

def test_scan_plugins(dummy_dir):
    print("Testing scan_plugins...")
    results = scan_plugins(dummy_dir)

    # 1. Check keys
    assert "plugin1" in results, "plugin1 missing"
    assert "plugin2" in results, "plugin2 missing"
    assert "plugin3" in results, "plugin3 missing"
    assert "plugin4" in results, "plugin4 missing"
    assert "__pycache__" not in results, "__pycache__ should not be a key"

    # 2. Check content merging
    p1_content = results["plugin1"]
    assert "def func1():" in p1_content, "part1.py content missing"
    assert "def func2():" in p1_content, "part2.py content missing"
    # Note: scanner adds \n between files
    
    # 3. Check ignore non-py
    assert "Documentation" not in p1_content, "README.md content included"

    # 4. Check nested
    assert "deep_content" in results["plugin2"], "Nested file content missing"

    # 5. Check __pycache__ ignore
    assert "SHOULD_NOT_BE_INCLUDED" not in results["plugin3"], "__pycache__ content included"
    assert "real_content" in results["plugin3"], "real content missing in plugin3"

    # 6. Check truncation
    assert len(results["plugin4"]) <= 200000, f"Content not truncated: {len(results['plugin4'])}"
    assert len(results["plugin4"]) == 200000, "Content should be exactly 200000"

    print("scan_plugins verified successfully.")

def test_wizard():
    print("Testing wizard.py...")
    # wizard.py looks for "plugins" in CWD.
    # We'll use a temporary directory for this test to avoid messing with root
    
    test_cwd = "test_wizard_env"
    if os.path.exists(test_cwd):
        shutil.rmtree(test_cwd)
    os.makedirs(test_cwd)
    
    # Copy dummy plugins to test_cwd/plugins
    shutil.copytree("dummy_plugins", os.path.join(test_cwd, "plugins"))
    
    # Path to wizard.py
    wizard_script = os.path.abspath(os.path.join("openyakitori", "wizard.py"))
    
    # Run wizard.py
    try:
        result = subprocess.run(
            [sys.executable, wizard_script],
            cwd=test_cwd,
            capture_output=True,
            text=True
        )
        
        # 1. Check exit code
        if result.returncode != 0:
            print("wizard.py failed with stderr:", result.stderr)
        assert result.returncode == 0, "wizard.py exited with error"
        
        # 2. Check CLI output
        assert "扫描插件完成" in result.stdout, "Missing '扫描插件完成' in output"
        assert "生成 commands.json" in result.stdout, "Missing '生成 commands.json' in output"
        
        # 3. Check .openyakitori directory and file
        output_file = os.path.join(test_cwd, ".openyakitori", "commands.json")
        assert os.path.exists(output_file), "commands.json not created"
        
        with open(output_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            assert isinstance(data, list), "commands.json content is not a list"
            # Since we mock LLM in wizard.py (NotImplementedError -> empty list), list might be empty or combined empty lists
            # The current wizard implementation catches NotImplementedError and uses {"commands": []}
            # So all_commands should be empty list if all fail, or list of commands if some succeed.
            # But wait, wizard.py:
            # except NotImplementedError: data = {"commands": []}
            # ... all_commands.extend(data["commands"])
            # So it should be []
            assert data == [], "commands.json should be empty list (mock LLM)"

        print("wizard.py verified successfully.")
        
    finally:
        # cleanup test env
        if os.path.exists(test_cwd):
            shutil.rmtree(test_cwd)

def cleanup():
    if os.path.exists("dummy_plugins"):
        shutil.rmtree("dummy_plugins")

def main():
    try:
        dummy_dir = setup_dummy_files()
        test_scan_plugins(dummy_dir)
        test_wizard()
        print("\nAll verifications PASSED!")
    except AssertionError as e:
        print(f"\nVerification FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\nAn error occurred: {e}")
        sys.exit(1)
    finally:
        cleanup()

if __name__ == "__main__":
    main()
