#!/usr/bin/env python3

import sys
import os

# --- Configuration ---
# Add 'src' to the path, just as main.py does.
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
SRC_PATH = os.path.join(PROJECT_ROOT, 'src')
if SRC_PATH not in sys.path:
    sys.path.insert(0, SRC_PATH)

PERSONAS_FILE_PATH = os.path.join(SRC_PATH, 'miso_engine', 'personas.py')
SEARCH_STRING = "PlannerAgent"
# --- End Configuration ---

print("--- STARTING IMPORT DIAGNOSTIC ---")
print(f"Project Root: {PROJECT_ROOT}")
print(f"Source Path (added to sys.path): {SRC_PATH}")
print(f"Target File (for grep comparison): {PERSONAS_FILE_PATH}")
print(f"Current sys.path: {sys.path}\n")

# --- 1. Filesystem Check (Replicating your 'grep' check) ---
print("--- Test 1: Reading file from disk (Python's 'grep') ---")
try:
    with open(PERSONAS_FILE_PATH, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if SEARCH_STRING in content:
        print(f"SUCCESS: Found '{SEARCH_STRING}' in {PERSONAS_FILE_PATH}\n")
    else:
        print(f"ERROR: Did NOT find '{SEARCH_STRING}' in {PERSONAS_FILE_PATH}\n")
        # This would be very strange if 'grep' works.
        # Check for case sensitivity or encoding issues.
        
except FileNotFoundError:
    print(f"ERROR: File not found at {PERSONAS_FILE_PATH}\n")
except Exception as e:
    print(f"ERROR: Could not read file: {e}\n")


# --- 2. Import System Check (This is the critical test) ---
print("--- Test 2: Attempting module import ---")
try:
    # We are inside ~/MISO-Phoenix, so we import 'miso_engine.personas'
    # This mimics the 'from .personas' inside the 'miso_engine' package
    from miso_engine import personas
    
    print("SUCCESS: Module 'miso_engine.personas' imported.")
    
    # Get the *exact* file Python loaded
    loaded_file_path = personas.__file__
    print(f"  > Python loaded module from: {loaded_file_path}\n")
    
    if loaded_file_path != os.path.abspath(PERSONAS_FILE_PATH):
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
        print("  > CRITICAL MISMATCH: This is the wrong file!")
        print(f"  > Expected: {os.path.abspath(PERSONAS_FILE_PATH)}")
        print(f"  > This indicates a 'shadowed' file, likely from 'site-packages'.")
        print(f"  > Check your venv at: {sys.prefix}")
        print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!\n")
    
    # --- 3. Module Content Check (Post-Import) ---
    print("--- Test 3: Checking content of the *loaded* module ---")
    
    # Check the file content of the *actual* loaded file
    print(f"  > Reading content from {loaded_file_path}...")
    with open(loaded_file_path, 'r', encoding='utf-8') as f:
        loaded_content = f.read()
    if SEARCH_STRING in loaded_content:
        print(f"  > SUCCESS: Found '{SEARCH_STRING}' in file Python loaded.\n")
    else:
        print(f"  > ERROR: Did NOT find '{SEARCH_STRING}' in file Python loaded.\n")
        
    # Check the *parsed dictionary*
    print("--- Test 4: Checking the 'MISO_PERSONAS' dictionary ---")
    if hasattr(personas, 'MISO_PERSONAS'):
        print("  > SUCCESS: 'MISO_PERSONAS' attribute exists.")
        
        if SEARCH_STRING in personas.MISO_PERSONAS:
            print(f"  > SUCCESS: Key '{SEARCH_STRING}' is in the MISO_PERSONAS dictionary.")
        else:
            print(f"  > ERROR: Key '{SEARCH_STRING}' is NOT in the MISO_PERSONAS dictionary.")
            print(f"  > This means the file was found, but parsing failed.")
            print(f"  > Check for a SYNTAX ERROR (e.g., missing comma) in personas.py")
            print(f"  >  ... *before* the 'PlannerAgent' entry.")
            print(f"\n  > Available keys: {list(personas.MISO_PERSONAS.keys())}")
            
    else:
        print("  > ERROR: 'MISO_PERSONAS' attribute does NOT exist in the loaded module.")
        
except ImportError as e:
    print(f"IMPORT FAILED: {e}")
    print("  > This could mean 'src' is not on sys.path,")
    print("  > or 'src/miso_engine/__init__.py' is missing.")
except Exception as e:
    print(f"An unexpected error occurred: {e}")

print("\n--- DIAGNOSTIC COMPLETE ---")
