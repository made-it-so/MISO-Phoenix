# run_swarm.py
import autogen
from autogen import UserProxyAgent, GroupChatManager, AssistantAgent, Agent
import sys
import os
import logging
from typing import List, Dict, Any, Optional

# --- Correct sys.path modification ---
# Get the directory containing run_swarm.py (project root)
project_root = os.path.dirname(os.path.abspath(__file__))
# Get the path to the src directory
src_dir = os.path.join(project_root, "src")
# Add src directory to the Python path if it's not already there
if src_dir not in sys.path:
    sys.path.insert(0, src_dir) # Use insert(0, ...) to prioritize this path
    print(f"DEBUG: Added '{src_dir}' to sys.path")
# -------------------------------------


# Import the specific creation functions AFTER modifying sys.path
try:
    # Use correct function names based on the clean agents.py
    from miso_swarm.agents import create_user_proxy_agent, create_coding_manager
    # Import worker functions NEEDED by run_swarm (the ones passed to manager)
    from miso_swarm.worker_agents import (
        create_code_writer_agent,
        create_code_reviewer_agent,
        create_code_tester_agent,
        create_code_execution_agent
    )
    # Ensure utils is importable if needed
    import miso_swarm.utils
except ImportError as e:
    # More detailed error logging
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
    logger = logging.getLogger(__name__)
    logger.error(f"Error: Could not import necessary functions: {e}", exc_info=True)
    logger.error("Please ensure __init__.py files exist in src/ and src/miso_swarm/ and all agent files are correct.")
    logger.error(f"Current sys.path: {sys.path}") # Debugging import path
    sys.exit(1)
except Exception as e: # Catch other potential init errors
     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
     logger = logging.getLogger(__name__)
     logger.error(f"An unexpected error occurred during initial imports: {e}", exc_info=True)
     sys.exit(1)


# --- Configuration ---
# Configure logging (if not already configured above)
if not logging.getLogger().hasHandlers():
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__) # Define logger for the main script
logging.getLogger("autogen").setLevel(logging.DEBUG) # Enable DEBUG for autogen


def get_llm_config() -> Optional[Dict[str, Any]]:
    """Loads LLM config from environment variable."""
    try:
        oai_config_list_str = os.getenv("OAI_CONFIG_LIST")
        if not oai_config_list_str:
            raise ValueError("Environment variable OAI_CONFIG_LIST is not set.")

        config_list = autogen.config_list_from_json(
            env_or_file="OAI_CONFIG_LIST", filter_dict={"model": ["gpt-4o"]},
        )
        if not config_list:
            logger.warning(f"OAI_CONFIG_LIST was set but did not contain a valid config for 'gpt-4o'. Value: {oai_config_list_str}")
            raise ValueError("Config list loaded is empty or missing 'gpt-4o'.")

        llm_config = {
            "config_list": config_list, "cache_seed": None, "temperature": 0.0, "timeout": 120,
        }
        logger.info("LLM Config loaded successfully.")
        return llm_config
    except ValueError as e:
        logger.error(f"Error loading OAI_CONFIG_LIST: {e}.")
        logger.error("Example: export OAI_CONFIG_LIST='[{\"model\": \"gpt-4o\", \"api_key\": \"YOUR_API_KEY\"}]'")
        return None
    except Exception as e:
        logger.error(f"An unexpected error occurred loading LLM config: {e}", exc_info=True)
        return None

# --- Main Swarm Execution ---
def main():
    print("\nWelcome to the Miso Swarm!")
    print("Attempting to generate correct worker_agents.py code from file...")

    # 1. Load LLM Config ONCE
    llm_config = get_llm_config()
    if not llm_config:
        sys.exit(1)

    # --- Read Task from File --- ### THIS IS THE CORRECTED PART ###
    prompt_file = "generation_prompt.txt"
    try:
        # Construct full path relative to the script's location (project root)
        prompt_file_path = os.path.join(project_root, prompt_file)
        with open(prompt_file_path, 'r', encoding='utf-8') as f: # Added encoding
            task = f.read().strip()
        if not task:
            raise ValueError(f"{prompt_file} is empty.")
        logger.info(f"Read task from {prompt_file_path}")
    except FileNotFoundError:
        logger.error(f"Error: Prompt file '{prompt_file_path}' not found.")
        logger.error("Please ensure 'generation_prompt.txt' exists in the same directory as run_swarm.py.")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Error reading prompt file '{prompt_file_path}': {e}", exc_info=True)
        sys.exit(1)
    # --- End Read Task from File ---

    try:
        # 2. Instantiate ALL agents, passing the llm_config
        logger.info("Instantiating agents...")
        # Use correct function names
        user_proxy = create_user_proxy_agent(llm_config)
        code_writer = create_code_writer_agent(llm_config)
        code_reviewer = create_code_reviewer_agent(llm_config)
        code_tester = create_code_tester_agent(llm_config)
        exec_llm_config = llm_config.copy()
        code_executor = create_code_execution_agent(exec_llm_config)
        logger.info("All required agents instantiated successfully.")

        # 3. Create the agent list for the group chat
        group_chat_agents: List[Agent] = [
            user_proxy, code_writer, code_reviewer, code_tester, code_executor
        ]

        # 4. Instantiate the manager
        manager_llm_config = llm_config.copy()
        coding_manager = create_coding_manager(
            agents=group_chat_agents, llm_config=manager_llm_config
        )
        logger.info("GroupChatManager created.")

        # 5. Task is already loaded from file

        # 6. Initiate the chat
        logger.info("--- Initiating Chat with Coding Manager ---")
        print("\n--- Starting Group Chat ---")
        print(f"Task:\n{task}\n--------------------") # Print the task being used

        chat_result = user_proxy.initiate_chat(
            coding_manager, message=task, clear_history=True,
        )
        print("--- Group Chat Finished ---")
        print("DEBUG: Raw chat result object:", chat_result)

        # 7. Print results
        print("\n--- Chat Result Summary ---")
        print("Summary:", chat_result.summary if chat_result else "N/A")
        print("Cost:", chat_result.cost if chat_result else "N/A")

        print("\n--- Full Group Chat History ---")
        history = chat_result.chat_history if chat_result else []
        if history:
             for msg in history:
                 name = msg.get('name', 'Unknown')
                 role = msg.get('role', 'Unknown')
                 content = msg.get('content')
                 print(f"[{name}/{role}]")
                 if content is None: print("<No content or function call>")
                 elif isinstance(content, str): print(content)
                 else: print(f"<Content type: {type(content)}>\n{str(content)}")
                 print("-" * 20)
        else:
             print("No chat history recorded.")

        logger.info("--- Chat Concluded ---")
        print("\n********************************************************")
        print("IMPORTANT: The generated 'worker_agents.py' file (if successful)")
        print("is located in the 'workspace/' directory.")
        print("You MUST manually move it to 'src/miso_swarm/' to fix the swarm.")
        print("Run: mv ~/MISO-Phoenix/workspace/worker_agents.py ~/MISO-Phoenix/src/miso_swarm/worker_agents.py")
        print("********************************************************")

    except Exception as e:
        logger.error(f"An error occurred during swarm execution: {e}", exc_info=True)
    except KeyboardInterrupt:
        print("\nSwarm execution interrupted by user. Exiting.")

if __name__ == "__main__":
    main()

