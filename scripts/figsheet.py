"""List figure and table captions with their source page numbers.
usage: python figsheet.py book.json"""
import json, sys
b = json.load(open(sys.argv[1]))
for x in b['blocks']:
    if x['t'] == 'cap' and not x['x'].startswith('Image description') and x.get('pno'): print(x['pno'], '|', x['x'][:110])
