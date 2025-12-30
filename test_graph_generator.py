#!/usr/bin/env python3
"""Test script for the graph generator."""
import os
import sys
from dotenv import load_dotenv
from src.graphics.graph_generator import get_graph_generator

def main():
    # Load environment variables
    load_dotenv()
    
    # Get the graph generator
    generator = get_graph_generator()
    
    print("Generating precious metals graphs...")
    try:
        # Update all graphs
        graphs = generator.update_all_graphs()
        
        if not graphs:
            print("No graphs generated. Check your API key and internet connection.")
            return
        
        print(f"\nGenerated {len(graphs)} graphs:")
        for name, path in graphs.items():
            print(f"  {name}: {path}")
            if os.path.exists(path):
                size = os.path.getsize(path)
                print(f"    Size: {size} bytes")
        
        print("\nGraphs saved to assets/images/ directory")
        print("You can view these files to see the generated visualizations.")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
