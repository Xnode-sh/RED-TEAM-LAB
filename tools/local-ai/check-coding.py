#!/usr/bin/env python3
"""Run only in a filesystem/network sandbox: checks synthetic generated functions."""
import copy
import json
from pathlib import Path
import re
import resource
import sys
resource.setrlimit(resource.RLIMIT_CPU, (5, 5))
resource.setrlimit(resource.RLIMIT_AS, (256*1024*1024, 256*1024*1024))
root = Path(__file__).resolve().parent
path = Path(sys.argv[1]) if len(sys.argv) > 1 else root/'runtime/coding-benchmark.json'
report = json.loads(path.read_text())
failures = []
checks = 0
for result in report['results']:
    answer = result['answer']
    blocks = re.findall(r'```(?:python)?\s*\n(.*?)```', answer, re.S)
    source = blocks[0] if blocks else answer
    scope = {}
    try:
        exec(compile(source, '<generated>', 'exec'), scope)
        if result['case'] == 'deduplicate':
            cases = [([], []), ([1, 2, 1, 3, 2], [1, 2, 3]),
                     ([{'x':1}, {'x':1}, {'x':2}], [{'x':1}, {'x':2}]),
                     ([[1], [1], [2], [1]], [[1], [2]]),
                     ([{'x':[1]}, [1], {'x':[1]}, [1]], [{'x':[1]}, [1]]),
                     ([{'a':1,'b':2}, {'b':2,'a':1}], [{'a':1,'b':2}]),
                     ([1, True, 1.0, 2], [1, 2])]
            function = scope['unique_equal']
        else:
            cases = [([], []), ([[5,7],[1,3],[3,5]], [[1,7]]),
                     ([[8,9],[1,2],[4,6]], [[1,2],[4,6],[8,9]]),
                     ([[1,10],[2,3],[4,8]], [[1,10]]),
                     ([[2,2],[2,2]], [[2,2]])]
            function = scope['merge_intervals']
        for index, (argument, expected) in enumerate(cases):
            saved = copy.deepcopy(argument)
            actual = function(argument)
            checks += 1
            if actual != expected or argument != saved:
                failures.append(f"{result['case']} case {index}: result={actual!r}, expected={expected!r}, mutated={argument != saved}")
    except Exception as error:
        failures.append(f"{result['case']}: {type(error).__name__}: {error}")
print('Model:', report['model'])
print('Checks:', checks, 'Failures:', len(failures))
for failure in failures:
    print(failure)
(root/'runtime'/('coding-check-'+report['model']+'.json')).write_text(json.dumps({'model':report['model'], 'checks':checks, 'failures':failures}, indent=2)+'\n')
sys.exit(bool(failures))
