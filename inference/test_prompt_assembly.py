import os, re, glob

PROMPT_DIRS = ['/a0/usr/agents/agent0/prompts', '/a0/usr/prompts', '/a0/prompts']
INCLUDE_RE = re.compile(r'\{\{\s*include\s+"([^"]+)"\s*\}\}')

def find_file(name):
    for d in PROMPT_DIRS:
        p = os.path.join(d, name)
        if os.path.isfile(p): return p
    return None

def read_and_expand(filename, depth=0):
    if depth > 10: return ''
    path = find_file(filename)
    if not path: return ''
    with open(path) as f:
        content = f.read()
    return INCLUDE_RE.sub(lambda m: read_and_expand(m.group(1), depth+1), content)

main_text = read_and_expand('agent.system.main.md')
print('Main prompt:', len(main_text), 'chars ~', len(main_text)//4, 'tokens')

seen, tools = set(), []
for d in PROMPT_DIRS:
    for path in sorted(glob.glob(os.path.join(d, 'agent.system.tool.*.md'))):
        name = os.path.basename(path)
        if name not in seen:
            seen.add(name)
            tools.append(read_and_expand(name))

tools_str = '\n\n'.join(tools)
total = len(main_text) + len(tools_str)
print('Tools text:', len(tools_str), 'chars ~', len(tools_str)//4, 'tokens,', len(tools), 'files')
print('Total static prompt est: ~', total//4, 'tokens')
