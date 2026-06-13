"""Quick test for URL validity in resource finder"""
import sys
sys.path.insert(0, '.')
from backend.plugins.resource_finder import find_resources

r = find_resources('AZ-204', 'Azure Functions')
print("Keys:", list(r.keys()))

for category, items in r.items():
    print(f"\n--- {category} ---")
    for item in items:
        url = item.get("url", "")
        # Check for double-domain bug
        has_bug = "learn.microsoft.comhttps://" in url or "learn.microsoft.comhttp://" in url
        print(f"  URL: {url}")
        print(f"  Double-domain bug: {'YES!' if has_bug else 'NO'}")
        if has_bug:
            print("  *** FIX NEEDED ***")

print("\nNo AzureOpenAI import:", "AzureOpenAI" not in open("backend/plugins/resource_finder.py").read())
print("Done")