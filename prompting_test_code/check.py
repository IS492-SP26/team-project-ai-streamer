import sys

print("="*50)
print("Verifying Package Installation")
print("="*50)

packages = [
    'requests',
    'dotenv',
    'tqdm',
]

success_count = 0

for pkg in packages:
    try:
        if pkg == 'dotenv':
            __import__('dotenv')
            pkg_name = 'python-dotenv'
        else:
            __import__(pkg)
            pkg_name = pkg
        print(f"✅ {pkg_name:20s} INSTALLED")
        success_count += 1
    except ImportError:
        display_name = 'python-dotenv' if pkg == 'dotenv' else pkg
        print(f"❌ {display_name:20s} MISSING")

print("="*50)
print(f"Result: {success_count}/{len(packages)} packages installed")
print("="*50)

if success_count == len(packages):
    print("\n🎉 SUCCESS! All packages ready!")
    print("\nNext: Check API keys")
    print("Run: python check_api_keys.py")
else:
    print("\n⚠️ Some packages missing!")
    print("Please install missing packages")

sys.exit(0 if success_count == len(packages) else 1)