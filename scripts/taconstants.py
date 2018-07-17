from typing import NewType, Iterable, Set, Dict, Optional

TAConstants = NewType('TAConstants', Dict[int, Set[str]])

def read_taconstants(fname: str) -> TAConstants:
    constants = TAConstants(dict())
    with open(fname, 'r') as f:
        for line in f.readlines():
            constStr = line.strip().split()[0].strip()
            valStr = line.strip().split()[-1].strip()
            try:
                # Handles both hex and decimal
                val = int(valStr)
                if val not in constants:
                    constants[val] = set()
                constants[val].add(constStr)
            except ValueError:
                pass
            
    return constants
