# src/miso_swarm/worker_agents.py

from pathlib import Path
import traceback # For detailed error logging
import os # Needed if using LLM integration
import html # For escaping text content
import re # For CSS Applier
import subprocess # For LinterAgent
import json # For LinterAgent
import tempfile # For LinterAgent
import shlex # For robust command splitting

# Placeholder for LLM setup (replace with your actual LLM client, e.g., LangChain)
# Make sure OPENAI_API_KEY is set in your environment if using OpenAI
# from langchain_openai import ChatOpenAI # Example
# llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.0) # Example


def create_file_agent(task_details: dict) -> dict:
    """
    Worker Agent: Creates a new file at the specified path.

    Args:
        task_details: A dictionary containing 'file_path' (str).

    Returns:
        A dictionary with 'success' (bool) and 'message' (str).
    """
    file_path_str = task_details.get("file_path")
    if not file_path_str:
        return {"success": False, "message": "Error: 'file_path' not provided in task details."}

    try:
        # Assume relative path from project root
        project_root = Path(".") # Or determine dynamically if needed
        file_path = (project_root / file_path_str).resolve()

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create the file (idempotent)
        file_path.touch(exist_ok=True)

        relative_path = file_path.relative_to(project_root.resolve())
        return {"success": True, "message": f"File created: {relative_path}"}

    except Exception as e:
        error_details = traceback.format_exc()
        return {"success": False, "message": f"Error creating file {file_path_str}: {e}\nDetails:\n{error_details}"}


def write_component_signature_agent(task_details: dict) -> dict:
    """
    Worker Agent: Writes a React component function signature.

    Args:
        task_details: Dict containing 'component_name' (str), 'props' (list of str).

    Returns:
        Dict with 'success' (bool) and 'code_snippet' (str) or 'message' (str).
    """
    component_name = task_details.get("component_name")
    props = task_details.get("props", []) # Default to empty list

    if not component_name:
        return {"success": False, "message": "Error: 'component_name' not provided."}

    # Format props string for the signature (e.g., "{ label, onClick }")
    props_str = ""
    if props:
        # Note: Need double braces {{}} for literal braces in f-string if using LLM below
        props_str = f"{{ {', '.join(props)} }}"

    # Construct the basic function signature
    # (Using simple string formatting here; LLM integration is optional)
    code_snippet = f"function {component_name}({props_str}) {{\n  // TODO: Implement component\n}}"

    # --- LLM Integration (Optional - uncomment and adapt if needed) ---
    # prompt = f"""Generate only the function signature for a React functional component named '{component_name}'.
    # It should accept the following props: {', '.join(props) if props else 'None'}.
    # Example: function MyComponent({{ prop1, prop2 }}) {{ ... }}
    # Respond ONLY with the code snippet."""
    # try:
    #     # Assuming your LLM client has a .invoke() method
    #     # Ensure OPENAI_API_KEY is set in environment if using OpenAI
    #     # code_snippet = llm.invoke(prompt).strip()
    #     pass # Replace pass with actual LLM call
    # except Exception as e:
    #     return {"success": False, "message": f"LLM error generating signature: {e}"}
    # --- End LLM Integration ---


    if code_snippet:
         return {"success": True, "code_snippet": code_snippet}
    else:
         # Should only happen if LLM integration is used and fails without exception
         return {"success": False, "message": "Error: Failed to generate code snippet."}


def render_jsx_element_agent(task_details: dict) -> dict:
    """
    Worker Agent: Renders a single, basic JSX element.

    Args:
        task_details: Dict containing 'element_type' (str, e.g., 'div', 'button'),
                      optional 'text_content' (str),
                      optional 'add_children_placeholder' (bool, default False).

    Returns:
        Dict with 'success' (bool) and 'code_snippet' (str) or 'message' (str).
    """
    element_type = task_details.get("element_type")
    text_content = task_details.get("text_content")
    add_children_placeholder = task_details.get("add_children_placeholder", False)

    if not element_type:
        return {"success": False, "message": "Error: 'element_type' not provided."}

    # Basic validation for common HTML tags (can be expanded)
    # Allows for PascalCase component names too
    if not re.match(r"^[a-zA-Z][a-zA-Z0-9]*$", element_type):
         return {"success": False, "message": f"Error: Invalid 'element_type': {element_type}"}

    # Escape text content to prevent basic injection issues if used directly
    escaped_content = html.escape(text_content) if text_content else ""

    children_placeholder = "{/* children */}" if add_children_placeholder else ""

    # Determine content: text or placeholder (priority to placeholder if both specified)
    inner_content = children_placeholder if add_children_placeholder else escaped_content

    # Handle self-closing tags if no content (simple heuristic, can be improved)
    self_closing_tags = {"img", "input", "br", "hr", "meta"} # Example set
    if not inner_content and element_type.lower() in self_closing_tags:
        code_snippet = f"<{element_type} />"
    else:
        code_snippet = f"<{element_type}>{inner_content}</{element_type}>"

    return {"success": True, "code_snippet": code_snippet}


def apply_css_classes_agent(task_details: dict) -> dict:
    """
    Worker Agent: Adds Tailwind CSS classes to a JSX element snippet.

    Args:
        task_details: Dict containing 'jsx_snippet' (str) and
                      'css_classes' (list of str).

    Returns:
        Dict with 'success' (bool) and 'code_snippet' (str) or 'message' (str).
    """
    jsx_snippet = task_details.get("jsx_snippet")
    css_classes = task_details.get("css_classes", [])

    if not jsx_snippet:
        return {"success": False, "message": "Error: 'jsx_snippet' not provided."}
    if not css_classes:
        # Nothing to do, return original snippet
        return {"success": True, "code_snippet": jsx_snippet}

    # Combine new classes into a string
    classes_str = " ".join(css_classes)

    # Regex to find the first opening tag (e.g., <div or <button type="button")
    # Captures: 1=tag name, 2=existing attributes (optional), 3=self-closing slash (optional)
    match = re.match(r"<([a-zA-Z0-9]+)(\s*[^>/]*)?(\s*/?)>", jsx_snippet, re.IGNORECASE)

    if not match:
        # Fallback for snippets that might ONLY be content, though less likely for this agent
        if not jsx_snippet.strip().startswith('<'):
             print(f"Warning: apply_css_classes_agent received snippet without a clear opening tag: {jsx_snippet}")
             return {"success": True, "code_snippet": jsx_snippet} # Return original if no tag found
        return {"success": False, "message": "Error: Could not find opening tag in jsx_snippet."}

    tag_name = match.group(1)
    existing_attrs = match.group(2) if match.group(2) else ""
    is_self_closing = bool(match.group(3) and '/' in match.group(3))

    # Check if className already exists
    class_match = re.search(r'className=(["\'])(.*?)\1', existing_attrs) # Handles " or '

    if class_match:
        quote_char = class_match.group(1)
        existing_classes = class_match.group(2)
        # Append new classes, ensuring no leading/trailing spaces in final string
        # Basic duplicate prevention (split, unique set, rejoin) could be added here
        new_classes = f"{existing_classes} {classes_str}".strip()
        # Replace the old className attribute
        updated_attrs = existing_attrs.replace(class_match.group(0), f'className={quote_char}{new_classes}{quote_char}')
    else:
        # Add new className attribute (ensure space before if other attrs exist)
        updated_attrs = f'{existing_attrs} className="{classes_str}"'.strip()


    # Reconstruct the tag, ensuring space before attributes
    # Add space only if updated_attrs is not empty
    attrs_with_space = f" {updated_attrs}" if updated_attrs else ""
    if is_self_closing:
        new_tag = f"<{tag_name}{attrs_with_space} />"
        updated_jsx = new_tag # Replace the whole snippet for self-closing
    else:
        # Find where the original tag ends (>)
        original_tag_end_index = jsx_snippet.find('>')
        if original_tag_end_index == -1:
             return {"success": False, "message": "Error: Malformed opening tag in jsx_snippet (missing '>')."}
        new_opening_tag_part = f"<{tag_name}{attrs_with_space}>"
        # Replace only up to the original closing >
        updated_jsx = new_opening_tag_part + jsx_snippet[original_tag_end_index+1:]


    return {"success": True, "code_snippet": updated_jsx}


def lint_code_agent(task_details: dict) -> dict:
    """
    Worker Agent (QA): Lints a code snippet using an external linter (e.g., ESLint).

    Requires Node.js and ESLint configured (e.g., `npm install eslint` and setup config).

    Args:
        task_details: Dict containing 'code_snippet' (str) and
                      optional 'language' (str, determines file extension, default 'jsx').

    Returns:
        Dict with 'success' (bool, indicates agent ran), 'passed' (bool, linting result),
        and 'errors' (list, if linting failed) or 'message' (str, if agent failed).
    """
    code_snippet = task_details.get("code_snippet")
    language = task_details.get("language", "jsx") # Default to jsx for React

    if not code_snippet:
        return {"success": False, "message": "Error: 'code_snippet' not provided."}

    # Determine file extension based on language
    ext_map = {"javascript": "js", "jsx": "jsx", "typescript": "ts", "tsx": "tsx", "python": "py"}
    extension = ext_map.get(language, "tmp")

    # Use tempfile context manager for automatic cleanup
    temp_filename = None # Define outside try block for access in finally
    try:
        # Create temp file *relative* to project root if possible, might help eslint find config
        project_root = Path(".").resolve()
        # Create a temporary directory within the project if needed (optional)
        # temp_dir = project_root / ".miso_temp_lint"
        # temp_dir.mkdir(exist_ok=True)
        # with tempfile.NamedTemporaryFile(mode='w+', suffix=f'.{extension}', delete=False, encoding='utf-8', dir=temp_dir) as temp_file:

        # Simpler: just create in default temp location
        with tempfile.NamedTemporaryFile(mode='w+', suffix=f'.{extension}', delete=False, encoding='utf-8') as temp_file:
            temp_filename = temp_file.name
            temp_file.write(code_snippet)
            temp_file.flush() # Ensure content is written before linting

            # --- Execute Linter (Example using ESLint for JS/JSX) ---
            eslint_config_path = project_root / "eslint.config.js"
            if not eslint_config_path.exists():
                 return {"success": False, "message": f"Error: ESLint config not found at {eslint_config_path}"}

            if language in ("javascript", "jsx", "typescript", "tsx"):
                # Explicitly point to the config file
                lint_command = f"npx eslint --config {shlex.quote(str(eslint_config_path))} {shlex.quote(temp_filename)} --format json"
            elif language == "python":
                # Example using flake8 (doesn't typically use project config file in same way)
                lint_command = f"flake8 --format='%(row)d:%(col)d:%(code)s:%(text)s' {shlex.quote(temp_filename)}"
            else:
                return {"success": False, "message": f"Error: Unsupported language for linting: {language}"}

            print(f"   🧹 Running lint command: {lint_command}")
            # Run from project root to help eslint find plugins/configs if needed
            process = subprocess.run(shlex.split(lint_command), capture_output=True, text=True, timeout=30, cwd=project_root)

            # --- Parse Linter Output ---
            # ESLint typically exits with 0 if no errors, 1 if errors, 2 if config/fatal error
            # Check stderr first for fatal errors
            if process.returncode == 2 or "Oops! Something went wrong" in process.stderr:
                 stderr_output = process.stderr.strip()
                 # Try to parse stdout even on error, might contain partial JSON
                 parsed_stdout = None
                 try:
                     parsed_stdout = json.loads(process.stdout) if process.stdout else None
                 except json.JSONDecodeError:
                     pass # Ignore if stdout isn't valid JSON

                 if parsed_stdout and isinstance(parsed_stdout, list) and parsed_stdout[0].get("messages"):
                      # Sometimes fatal errors still produce useful messages in stdout JSON
                      errors = parsed_stdout[0].get("messages", [])
                      formatted_errors = [
                          {"line": e.get("line"), "column": e.get("column"), "rule": e.get("ruleId"), "message": e.get("message")}
                          for e in errors if e.get("severity") == 2
                      ]
                      if formatted_errors:
                           print(f"   ⚠️ ESLint fatal error, but parsed errors from stdout.")
                           return {"success": True, "passed": False, "errors": formatted_errors}

                 # If stdout didn't help, report stderr
                 return {"success": False, "message": f"ESLint execution error (Code {process.returncode}). Stderr: {stderr_output or 'None'}. Stdout: {process.stdout or 'None'}"}


            if language in ("javascript", "jsx", "typescript", "tsx"):
                try:
                    # ESLint JSON output is a list containing one object
                    lint_results = json.loads(process.stdout)
                    if not lint_results:
                         # No output means no errors found (usually)
                         if process.returncode == 0:
                              return {"success": True, "passed": True, "message": "Linting passed (no issues found)."}
                         else:
                              # Non-zero exit code but no JSON output is strange
                              return {"success": False, "message": f"Linter exited with code {process.returncode} but no JSON output. Stderr: {process.stderr}"}

                    file_result = lint_results[0] # Get results for the single temp file
                    error_count = file_result.get("errorCount", 0)
                    warning_count = file_result.get("warningCount", 0) # Optionally track warnings

                    if error_count == 0:
                        # Success if exit code is 0 (no errors)
                        return {"success": True, "passed": process.returncode == 0, "message": f"Linting passed ({warning_count} warnings)."}
                    else:
                        errors = file_result.get("messages", [])
                        # Format errors
                        formatted_errors = [
                            {"line": e.get("line"), "column": e.get("column"), "rule": e.get("ruleId"), "message": e.get("message")}
                            for e in errors if e.get("severity") == 2 # Severity 2 is error
                        ]
                        return {"success": True, "passed": False, "errors": formatted_errors}

                except json.JSONDecodeError:
                    # JSON parsing failed, likely means a syntax error the parser couldn't handle
                    # ESLint might output human-readable errors to stdout or stderr
                    error_output = process.stdout.strip() or process.stderr.strip()
                    # Try to extract a line number if possible
                    line_match = re.search(r"Parsing error.* (\d+):", error_output)
                    line_num = int(line_match.group(1)) if line_match else None
                    formatted_error = [{"line": line_num, "message": f"Syntax/Parsing Error: {error_output}"}]
                    print(f"   ⚠️ ESLint JSON parse failed, likely syntax error. Reporting raw output.")
                    return {"success": True, "passed": False, "errors": formatted_error}
                except IndexError:
                     return {"success": False, "message": f"Error parsing ESLint JSON output structure. Raw: {process.stdout} Stderr: {process.stderr}"}

            elif language == "python":
                 # Parse flake8 output (line:col:code:message)
                 if process.returncode == 0 and not process.stdout.strip():
                      return {"success": True, "passed": True, "message": "Linting passed."}
                 else:
                      errors = []
                      for line in process.stdout.strip().splitlines():
                           parts = line.split(':', 3)
                           if len(parts) == 4:
                                try:
                                    errors.append({
                                         "line": int(parts[0]), "column": int(parts[1]),
                                         "rule": parts[2].strip(), "message": parts[3].strip()
                                    })
                                except ValueError: # Handle if line/col aren't ints
                                     errors.append({"message": line})
                           else: errors.append({"message": line}) # Fallback for unexpected format
                      return {"success": True, "passed": False, "errors": errors}

            else: # Should not happen due to earlier check
                 return {"success": False, "message": "Internal error: Linter parsing logic missing."}


    except FileNotFoundError:
        return {"success": False, "message": f"Error: Linter command not found. Is Node/ESLint/Flake8 installed and in PATH?"}
    except subprocess.TimeoutExpired:
        return {"success": False, "message": "Error: Linter command timed out."}
    except Exception as e:
        error_details = traceback.format_exc()
        return {"success": False, "message": f"Error running linter: {e}\nDetails:\n{error_details}"}
    finally:
        # Ensure temporary file is deleted even if errors occur
        try:
            if temp_filename and Path(temp_filename).exists():
                os.unlink(temp_filename)
        except Exception as e_clean:
            print(f"Warning: Failed to delete temp lint file {temp_filename}: {e_clean}")



# --- Example Usage (for testing all agents) ---
if __name__ == "__main__":
    print("--- File Creator ---")
    test_task_1 = {"file_path": "src/components/NewButton.jsx"}
    result_1 = create_file_agent(test_task_1)
    print(f"Test 1 Result: {result_1}")
    try: Path("src/components/NewButton.jsx").unlink(missing_ok=True)
    except Exception as e_inner: print(f"Cleanup warning: {e_inner}")
    try: Path("src/components").rmdir()
    except OSError: pass
    try: Path("src").rmdir()
    except OSError: pass

    test_task_2 = {"file_path": "nonexistent_dir/another_dir/test.txt"}
    result_2 = create_file_agent(test_task_2)
    print(f"Test 2 Result: {result_2}")
    try: Path("nonexistent_dir/another_dir/test.txt").unlink(missing_ok=True)
    except Exception as e_inner: print(f"Cleanup warning: {e_inner}")
    try: Path("nonexistent_dir/another_dir").rmdir()
    except OSError: pass
    try: Path("nonexistent_dir").rmdir()
    except OSError: pass

    test_task_3 = {} # Missing file_path
    result_3 = create_file_agent(test_task_3)
    print(f"Test 3 Result: {result_3}")


    print("\n--- Component Signature Writer ---")
    sig_task_1 = {"component_name": "Button", "props": ["label", "onClick"]}
    sig_result_1 = write_component_signature_agent(sig_task_1)
    print(f"Sig Test 1: {sig_result_1}")
    sig_task_2 = {"component_name": "UserProfile"} # No props
    sig_result_2 = write_component_signature_agent(sig_task_2)
    print(f"Sig Test 2: {sig_result_2}")
    sig_task_3 = {} # Missing name
    sig_result_3 = write_component_signature_agent(sig_task_3)
    print(f"Sig Test 3: {sig_result_3}")


    print("\n--- JSX Element Renderer ---")
    jsx_task_1 = {"element_type": "button", "text_content": "Click Me"}
    jsx_result_1 = render_jsx_element_agent(jsx_task_1)
    print(f"JSX Test 1: {jsx_result_1}")
    jsx_task_2 = {"element_type": "div", "add_children_placeholder": True}
    jsx_result_2 = render_jsx_element_agent(jsx_task_2)
    print(f"JSX Test 2: {jsx_result_2}")
    jsx_task_3 = {"element_type": "img"} # Self-closing
    jsx_result_3 = render_jsx_element_agent(jsx_task_3)
    print(f"JSX Test 3: {jsx_result_3}")
    jsx_task_4 = {"element_type": "MyComponent", "text_content": "<script>alert('xss')</script>"} # Custom component + escaping test
    jsx_result_4 = render_jsx_element_agent(jsx_task_4)
    print(f"JSX Test 4: {jsx_result_4}")
    jsx_task_5 = {} # Missing element type
    jsx_result_5 = render_jsx_element_agent(jsx_task_5)
    print(f"JSX Test 5: {jsx_result_5}")


    print("\n--- CSS Class Applier ---")
    css_task_1 = {"jsx_snippet": "<button>Click Me</button>", "css_classes": ["bg-blue-500", "text-white", "rounded"]}
    css_result_1 = apply_css_classes_agent(css_task_1)
    print(f"CSS Test 1: {css_result_1}")
    css_task_2 = {'jsx_snippet': '<div className="existing classes">Content</div>', "css_classes": ["p-4", "m-2"]}
    css_result_2 = apply_css_classes_agent(css_task_2)
    print(f"CSS Test 2: {css_result_2}")
    css_task_3 = {"jsx_snippet": "<img src='...' />", "css_classes": ["w-full", "h-auto"]}
    css_result_3 = apply_css_classes_agent(css_task_3)
    print(f"CSS Test 3: {css_result_3}")
    css_task_4 = {"jsx_snippet": "<span>Text</span>", "css_classes": []}
    css_result_4 = apply_css_classes_agent(css_task_4)
    print(f"CSS Test 4: {css_result_4}")
    css_task_5 = {} # Missing snippet
    css_result_5 = apply_css_classes_agent(css_task_5)
    print(f"CSS Test 5: {css_result_5}")


    print("\n--- Linter Agent ---")
    # Test Linter Agent (Requires eslint setup for JS/JSX)
    good_jsx = """
import React from 'react';

function GoodComponent({ name }) {
  // const _unused = 1; // Add this line to test unused var warning
  if (!name) { // Example of logic
     return <div>Loading...</div>;
  }
  return (
    <div className="p-4">
      Hello, {name}!
    </div>
  );
}

export default GoodComponent;
"""
    lint_task_1 = {"code_snippet": good_jsx, "language": "jsx"}
    lint_result_1 = lint_code_agent(lint_task_1)
    print(f"Lint Test 1 (Good JSX): {json.dumps(lint_result_1, indent=2)}")

    # Intentionally broken JSX/JS for testing error capture
    bad_jsx = """
import React from 'react';

function BadComponent({ name }) // Missing curly braces and prop usage validation
  const unusedVar = 1; // Syntax error: Unexpected identifier, also unused
  return (
    <div className="p-4 // Missing closing quote
      Hello, {name}!
    </div> // Closing tag might be flagged depending on parser state
  );
}
// Missing export default
"""
    lint_task_2 = {"code_snippet": bad_jsx, "language": "jsx"}
    lint_result_2 = lint_code_agent(lint_task_2)
    print(f"Lint Test 2 (Bad JSX): {json.dumps(lint_result_2, indent=2)}")

    good_py = """
import os # Example import

def hello(name: str) -> str:
    \"\"\"Greets the user.\"\"\"
    # unused_var = 1 # Add to test flake8 unused warning
    print(f"Hello, {name}!")
    return f"Hello, {name}!"

if __name__ == "__main__":
    GREETING = hello("World")
    print(GREETING)
"""
    lint_task_3 = {"code_snippet": good_py, "language": "python"}
    lint_result_3 = lint_code_agent(lint_task_3)
    print(f"Lint Test 3 (Good Python): {json.dumps(lint_result_3, indent=2)}")

    bad_py = """
import os, sys # F401 os imported but unused, E401 multiple imports

def bad_func ( name ): # E225 missing whitespace, E231 missing whitespace, E251 unexpected spaces, potentially missing types
    unused = 1 # F841 local variable 'unused' is assigned to but never used
    print("Hello, " + name) # Consider f-string
    return name; # E703 statement ends with a semicolon
"""
    lint_task_4 = {"code_snippet": bad_py, "language": "python"}
    lint_result_4 = lint_code_agent(lint_task_4)
    print(f"Lint Test 4 (Bad Python): {json.dumps(lint_result_4, indent=2)}")

    lint_task_5 = {} # Missing snippet
    lint_result_5 = lint_code_agent(lint_task_5)
    print(f"Lint Test 5 (Missing Snippet): {json.dumps(lint_result_5, indent=2)}")

