"""
boot.py - Auto-start virtual pet game on power-up
This file runs automatically when the ESP32-C6 boots
"""

import sys
import time

# Add virtual_pet directory to Python path
sys.path.append('/virtual_pet')

# Small delay to ensure everything is initialized
time.sleep_ms(100)

print("\n" + "="*40)
print("  Virtual Pet - Auto Starting...")
print("="*40 + "\n")

# Execute the game using exec()
try:
    exec(open('/virtual_pet/main.py').read())
except Exception as e:
    print("Error starting game:", e)
    import sys
    sys.print_exception(e)
    print("\nTo manually start:")
    print(">>> import sys")
    print(">>> sys.path.append('/virtual_pet')")
    print(">>> exec(open('/virtual_pet/main.py').read())")