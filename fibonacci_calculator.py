#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
fibonacci_calculator.py

A production-grade script for calculating Fibonacci numbers and sequences.

This utility provides a robust, performant, and secure command-line interface
for Fibonacci sequence generation. It employs an iterative, memory-efficient
generator and includes comprehensive input validation to prevent common errors
and resource exhaustion.
"""

import argparse
import logging
import sys
from typing import Generator, List

# --- Constants ---

# A sensible upper limit to prevent excessive CPU/memory usage for a single run.
# The 93rd Fibonacci number exceeds the capacity of a 64-bit unsigned integer.
# We set a higher limit but caution that numbers will become extremely large.
MAX_FIBONACCI_INDEX: int = 100_000

# --- Logging Configuration ---

logging.basicConfig(
    level=logging.WARNING,
    format="[%(asctime)s] [%(levelname)-8s] - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
log = logging.getLogger(__name__)

# --- Core Logic ---

def generate_fibonacci(n: int) -> Generator[int, None, None]:
    """
    Generates Fibonacci numbers up to the n-th index using an iterative method.

    This generator is highly memory-efficient, yielding one number at a time
    instead of storing the entire sequence in memory.

    Args:
        n (int): The non-negative index of the last Fibonacci number to generate.
                 (e.g., n=0 yields [0], n=1 yields [0, 1], n=5 yields [0, 1, 1, 2, 3, 5])

    Yields:
        int: The next Fibonacci number in the sequence.

    Raises:
        ValueError: If n is negative or exceeds the defined MAX_FIBONACCI_INDEX.
    """
    if not isinstance(n, int) or n < 0:
        raise ValueError("The Fibonacci index must be a non-negative integer.")
    if n > MAX_FIBONACCI_INDEX:
        raise ValueError(
            f"Index {n} is too large. "
            f"Maximum allowed index is {MAX_FIBONACCI_INDEX}."
        )

    current, next_val = 0, 1
    for _ in range(n + 1):
        yield current
        current, next_val = next_val, current + next_val

# --- Command-Line Interface and Execution ---

def setup_arg_parser() -> argparse.ArgumentParser:
    """Configures and returns the argument parser for the script."""
    parser = argparse.ArgumentParser(
        description="Calculate Fibonacci numbers or sequences.",
        epilog="Example: python fibonacci_calculator.py 10 --sequence"
    )
    parser.add_argument(
        "index",
        type=int,
        help="The index (n) of the Fibonacci number to calculate."
    )
    parser.add_argument(
        "-s", "--sequence",
        action="store_true",
        help="Print the entire Fibonacci sequence up to the given index."
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_const",
        dest="loglevel",
        const=logging.INFO,
        default=logging.WARNING,
        help="Enable informational logging output."
    )
    parser.add_argument(
        "--debug",
        action="store_const",
        dest="loglevel",
        const=logging.DEBUG,
        help="Enable debug logging output (most verbose)."
    )
    return parser

def main() -> int:
    """
    Main execution function.

    Parses command-line arguments, invokes the Fibonacci generator,
    handles errors, and prints the result.

    Returns:
        int: Exit code (0 for success, 1 for failure).
    """
    parser = setup_arg_parser()
    args = parser.parse_args()

    log.setLevel(args.loglevel)
    log.info("Script execution started.")
    log.debug("Arguments received: %s", args)

    try:
        fib_generator = generate_fibonacci(args.index)
        if args.sequence:
            # Consume generator and print the whole sequence
            sequence: List[int] = list(fib_generator)
            log.info("Printing Fibonacci sequence up to index %d.", args.index)
            print(" ".join(map(str, sequence)))
        else:
            # Efficiently consume generator to get the last element
            log.info("Calculating Fibonacci number at index %d.", args.index)
            result = 0
            for result in fib_generator:
                pass
            print(result)

    except ValueError as e:
        log.error("Input validation failed: %s", e)
        print(f"Error: {e}", file=sys.stderr)
        return 1
    except Exception as e:
        log.critical("An unexpected error occurred: %s", e, exc_info=True)
        print("An unexpected error occurred. See logs for details.", file=sys.stderr)
        return 1

    log.info("Script execution finished successfully.")
    return 0

if __name__ == "__main__":
    sys.exit(main())
