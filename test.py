print("Test script running")
import sys
print(f"Python版本: {sys.version}", file=sys.stderr)
print(f"脚本路径: {__file__}", file=sys.stderr)
sys.exit(0)