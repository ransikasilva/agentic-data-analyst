import re
from pathlib import Path

files_to_fix = [
    'agent/nodes/coder.py',
    'agent/nodes/critic.py',
    'agent/nodes/summarizer.py',
    'agent/graph.py'
]

replacements = {
    'from ..state import': 'from agent.state import',
    'from ...models.openai_client import': 'from models.openai_client import',
    'from ...utils.file_parser import': 'from utils.file_parser import',
    'from .state import': 'from agent.state import',
    'from .nodes.planner import': 'from agent.nodes.planner import',
    'from .nodes.coder import': 'from agent.nodes.coder import',
    'from .nodes.critic import': 'from agent.nodes.critic import',
    'from .nodes.summarizer import': 'from agent.nodes.summarizer import',
    'from .tools.executor import': 'from agent.tools.executor import',
}

for file_path in files_to_fix:
    p = Path(file_path)
    if p.exists():
        content = p.read_text()
        for old, new in replacements.items():
            content = content.replace(old, new)
        p.write_text(content)
        print(f"Fixed: {file_path}")

print("Done!")
