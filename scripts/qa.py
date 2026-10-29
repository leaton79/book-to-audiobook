import json, sys, random
b = json.load(open(sys.argv[1])); bl = b['blocks']; random.seed(1)
for i, x in enumerate(bl):
    if x['t'] == 'h1': print('##', x['x'], '=>', [y['x'][:160] for y in bl[i + 1:i + 3]])
print('--- samples')
for x in random.sample([y for y in bl if y['t'] == 'p'], min(6, len(bl))): print('*', x['x'][:500]); print()
print('--- short paras (possible junk)')
for x in bl:
    if x['t'] in ('p', 'quote') and len(x['x']) < 40: print('  ', repr(x['x']))
