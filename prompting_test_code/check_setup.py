import sys
print("Python version:", sys.version)
print()

try:
    import requests
    print("✅ requests installed, version:", requests.__version__)
except Exception as e:
    print("❌ requests error:", e)

try:
    import dotenv
    print("✅ python-dotenv installed")
except Exception as e:
    print("❌ dotenv error:", e)

try:
    import tqdm
    print("✅ tqdm installed, version:", tqdm.__version__)
except Exception as e:
    print("❌ tqdm error:", e)

print("\n" + "="*50)

# Test .env file
print("Checking .env configuration...")
print("="*50)

from dotenv import load_dotenv
import os

load_dotenv()

claude_key = os.getenv('CLAUDE_API_KEY')
groq_key = os.getenv('GROQ_API_KEY')
gemini_key = os.getenv('GEMINI_API_KEY')

if claude_key:
    print(f"✅ CLAUDE_API_KEY: {claude_key[:15]}...")
else:
    print("❌ CLAUDE_API_KEY: Not found")

if groq_key:
    print(f"✅ GROQ_API_KEY: {groq_key[:10]}...")
else:
    print("❌ GROQ_API_KEY: Not found")

if gemini_key:
    print(f"✅ GEMINI_API_KEY: {gemini_key[:10]}...")
else:
    print("❌ GEMINI_API_KEY: Not found")

print("="*50)

if claude_key and groq_key and gemini_key:
    print("\n🎉 Everything is ready!")
    print("\nNext step: Run the test")
    print("  python src/test_runner.py --scenario 1")
else:
    print("\n⚠️ Please configure missing API keys in .env file")
