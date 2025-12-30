#!/usr/bin/env python3
"""Test script for the TTS engine."""
import os
import sys
from dotenv import load_dotenv
from src.tts.tts_engine import get_tts_engine

def main():
    # Load environment variables
    load_dotenv()
    
    # Get the TTS engine
    engine = get_tts_engine()
    
    print("Testing TTS engine...")
    try:
        # Test basic audio generation
        print("\n1. Testing basic audio generation...")
        test_text = "Hello, this is a test of the Silver Ronin text-to-speech system."
        audio_file = engine.generate_audio(test_text)
        
        if audio_file and os.path.exists(audio_file):
            print(f"✓ Generated test audio: {audio_file}")
            size = os.path.getsize(audio_file)
            print(f"  File size: {size} bytes")
        else:
            print("✗ Failed to generate test audio")
        
        # Update commentary
        print("\n2. Updating commentary queue...")
        status = engine.update_all()
        
        print(f"  New commentary items: {status['new_commentary_items']}")
        print(f"  Queue size: {status['queue_size']}")
        print(f"  Audio files generated: {status['audio_files_generated']}")
        
        if status['audio_files']:
            print("\n  Generated audio files:")
            for file in status['audio_files']:
                if os.path.exists(file):
                    size = os.path.getsize(file)
                    print(f"    - {file} ({size} bytes)")
        
        # Show queue items
        if engine.commentary_queue:
            print("\n3. Commentary queue preview:")
            for i, item in enumerate(engine.commentary_queue[:5], 1):
                print(f"  {i}. [{item.category.upper()}] {item.text[:60]}...")
                print(f"     Priority: {item.priority}, Time: {item.timestamp.strftime('%H:%M:%S')}")
        
        print(f"\nAudio files saved to: {engine.output_dir}")
        print("You can play these files to hear the generated speech.")
            
    except Exception as e:
        print(f"Error: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
