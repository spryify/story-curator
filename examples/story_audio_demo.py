#!/usr/bin/env python3
"""
Demonstration script for generating children's story audio files for testing.

This script shows how the integration tests generate audio files using the macOS 'say' command
with various children's story content, similar to the fixtures in media_analyzer.
"""

import sys
import subprocess
from pathlib import Path
import tempfile


def create_story_audio_demo():
    """Create sample story audio files to demonstrate the integration test approach."""
    
    # Check if 'say' command is available (macOS only)
    try:
        subprocess.run(['say', '-v', '?'], capture_output=True, check=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ The 'say' command is not available. This demo requires macOS.")
        return False
    
    # Sample stories from our integration tests
    stories = {
        "magic_garden": {
            "text": """
                The Magic Garden Adventure. In a colorful garden lived a curious butterfly named Flutter. 
                Flutter loved to explore and learn about all the flowers. One sunny morning, Flutter met 
                a wise old owl named Professor Hoot. Would you like to learn about the special magic of 
                the garden, asked Professor Hoot. Oh yes, please, Flutter replied excitedly.
            """,
            "voice": "Samantha",
            "rate": 150
        },
        
        "counting_lesson": {
            "text": """
                Let's Count Together! One butterfly dancing in the garden, two happy bees buzzing 
                around the flowers, three little frogs sitting by the pond, four colorful birds 
                singing in the trees, and five busy ants marching in a line.
            """,
            "voice": "Victoria", 
            "rate": 140
        },
        
        "animal_friends": {
            "text": """
                The Tale of Animal Friends. Once upon a time, in a peaceful forest, lived many animal 
                friends. There was a playful rabbit named Hop, a wise old owl called Hoot, a friendly 
                bear named Cuddles, and a colorful bird named Melody.
            """,
            "voice": "Alex",
            "rate": 160
        }
    }
    
    print("🎙️  Generating children's story audio files...")
    print("=" * 60)
    
    # Create temporary directory for demo files
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        for story_name, story_config in stories.items():
            print(f"\n📖 Creating '{story_name}' story...")
            
            # Generate audio file
            audio_path = temp_path / f"{story_name}.aiff"
            
            try:
                # Use macOS 'say' command to generate speech
                cmd = [
                    "say", 
                    "-r", str(story_config["rate"]),  # Speaking rate
                    "-v", story_config["voice"],       # Voice
                    "-o", str(audio_path),             # Output file
                    story_config["text"].strip()       # Text to speak
                ]
                
                print(f"   Voice: {story_config['voice']}")
                print(f"   Rate: {story_config['rate']} words/minute") 
                print(f"   Generating audio...")
                
                # Execute the command
                result = subprocess.run(cmd, capture_output=True, text=True)
                
                if result.returncode == 0 and audio_path.exists():
                    file_size = audio_path.stat().st_size
                    print(f"   ✅ Created: {audio_path.name} ({file_size:,} bytes)")
                    
                    # Get audio file duration using 'afinfo' (macOS tool)
                    try:
                        duration_result = subprocess.run(
                            ['afinfo', str(audio_path)], 
                            capture_output=True, text=True
                        )
                        if 'estimated duration:' in duration_result.stdout:
                            duration_line = [line for line in duration_result.stdout.split('\n') 
                                           if 'estimated duration:' in line][0]
                            duration = duration_line.split(':')[1].strip().split()[0]
                            print(f"   Duration: {duration} seconds")
                    except:
                        pass
                        
                    # Show first few words of transcription
                    words = story_config["text"].strip().split()[:8]
                    preview = " ".join(words) + "..."
                    print(f"   Preview: \"{preview}\"")
                    
                else:
                    print(f"   ❌ Failed to create audio file")
                    if result.stderr:
                        print(f"   Error: {result.stderr.strip()}")
                        
            except Exception as e:
                print(f"   ❌ Exception: {e}")
        
        print(f"\n🎯 Integration Test Usage:")
        print("=" * 60)
        print("These audio files are generated dynamically in our integration tests using:")
        print()
        print("@pytest.fixture")
        print("def story_audio_files(self, tmp_path, children_story_texts):")
        print("    audio_files = {}")
        print("    for story_name, story_text in children_story_texts.items():")
        print("        audio_path = tmp_path / f'{story_name}.wav'")
        print("        create_story_audio_file(audio_path, story_text, voice='Samantha', rate=150)")
        print("        audio_files[story_name] = audio_path")
        print("    return audio_files")
        print()
        print("✨ Benefits of Real Audio Integration Tests:")
        print("• Tests actual speech recognition (Whisper)")
        print("• Validates subject extraction from real transcriptions") 
        print("• Ensures icon matching works with realistic content")
        print("• No mocks - tests real component integration")
        print("• Demonstrates different story types and themes")
        
        input("\nPress Enter to continue and clean up demo files...")
    
    print("🧹 Demo files cleaned up.")
    return True


def main():
    """Main function for the demo script."""
    print("Children's Story Audio Generator Demo")
    print("====================================")
    print()
    print("This demo shows how our integration tests generate real audio files")
    print("from children's stories using the macOS 'say' command, similar to")
    print("the fixtures used in the media_analyzer module.")
    print()
    
    if not create_story_audio_demo():
        print("Demo could not run. Please ensure you're on macOS with the 'say' command available.")
        sys.exit(1)
        
    print()
    print("✅ Demo completed successfully!")
    print()
    print("To run the real integration tests:")
    print("pytest src/audio_icon_matcher/tests_integration/ -v")


if __name__ == "__main__":
    main()
