import os
import sys

# Garante que a raiz do projeto está no sys.path para `import config` e `import src.*`
RAIZ = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if RAIZ not in sys.path:
    sys.path.insert(0, RAIZ)
