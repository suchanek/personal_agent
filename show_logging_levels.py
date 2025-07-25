#!/usr/bin/env python3
"""
Display Python logging levels and their numeric values.
"""

import logging

def display_logging_levels():
    """Display all standard Python logging levels and their numeric values."""
    
    print("Python Logging Levels and Values:")
    print("=" * 40)
    
    # Standard logging levels
    levels = [
        ('NOTSET', logging.NOTSET),
        ('DEBUG', logging.DEBUG),
        ('INFO', logging.INFO),
        ('WARNING', logging.WARNING),
        ('ERROR', logging.ERROR),
        ('CRITICAL', logging.CRITICAL),
    ]
    
    # Display in a formatted table
    print(f"{'Level Name':<12} {'Numeric Value':<15} {'logger.LEVEL'}")
    print("-" * 50)
    
    for level_name, level_value in levels:
        print(f"{level_name:<12} {level_value:<15} logger.{level_name}")
    
    print("\nSpecific values you asked about:")
    print("-" * 30)
    print(f"logger.INFO     = {logging.INFO}")
    print(f"logger.WARNING  = {logging.WARNING}")
    print(f"logger.ERROR    = {logging.ERROR}")
    
    print("\nUsage examples:")
    print("-" * 15)
    print("logger.setLevel(logging.INFO)     # Sets level to 20")
    print("logger.setLevel(logging.WARNING)  # Sets level to 30") 
    print("logger.setLevel(logging.ERROR)    # Sets level to 40")

if __name__ == "__main__":
    display_logging_levels()