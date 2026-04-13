import sys
import os

# Make 'app/' importable during pytest so 'from main import app' resolves
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
