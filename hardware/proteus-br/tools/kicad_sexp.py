"""Minimal s-expression round-trip toolkit for KiCad 7 schematic files.

Parses .kicad_sch into nested lists of (Sym, str, int, float), serializes
back in a KiCad-compatible pretty format. Numbers keep original text via
Num wrapper to avoid float noise.
"""


class Sym(str):
    """Unquoted atom."""
    __slots__ = ()


class Num(str):
    """Numeric atom kept as original text."""
    __slots__ = ()

    @property
    def f(self):
        return float(self)


def tokenize(text):
    i, n = 0, len(text)
    while i < n:
        c = text[i]
        if c in ' \t\r\n':
            i += 1
        elif c in '()':
            yield c
            i += 1
        elif c == '"':
            j = i + 1
            buf = []
            while j < n:
                ch = text[j]
                if ch == '\\':
                    buf.append(text[j:j + 2])
                    j += 2
                elif ch == '"':
                    break
                else:
                    buf.append(ch)
                    j += 1
            yield ('STR', ''.join(buf))
            i = j + 1
        else:
            j = i
            while j < n and text[j] not in ' \t\r\n()"':
                j += 1
            yield ('ATOM', text[i:j])
            i = j


def parse(text):
    stack = [[]]
    for tok in tokenize(text):
        if tok == '(':
            stack.append([])
        elif tok == ')':
            done = stack.pop()
            stack[-1].append(done)
        else:
            kind, val = tok
            if kind == 'STR':
                stack[-1].append(val)
            else:
                try:
                    float(val)
                    stack[-1].append(Num(val))
                except ValueError:
                    stack[-1].append(Sym(val))
    assert len(stack) == 1 and len(stack[0]) == 1, 'unbalanced sexp'
    return stack[0][0]


def _escape(s):
    out = []
    for ch in s:
        if ch == '"':
            out.append('\\"')
        elif ch == '\\':
            out.append('\\\\')
        elif ch == '\n':
            out.append('\\n')
        else:
            out.append(ch)
    return ''.join(out)


def dump(node, indent=0):
    if isinstance(node, (Sym, Num)):
        return str(node)
    if isinstance(node, str):
        return '"%s"' % _escape(node)
    # list
    parts = [dump(x, indent + 1) for x in node]
    flat = '(' + ' '.join(parts) + ')'
    if len(flat) <= 100 and '\n' not in flat:
        return flat
    pad = '  ' * (indent + 1)
    head = []
    rest = []
    # keep leading atoms on the opening line
    for k, x in enumerate(node):
        if rest or isinstance(x, list):
            rest.append(x)
        else:
            head.append(x)
    lines = ['(' + ' '.join(dump(x) for x in head)]
    for x in rest:
        lines.append(pad + dump(x, indent + 1))
    lines.append('  ' * indent + ')')
    return '\n'.join(lines)


def loads(path):
    with open(path) as f:
        return parse(f.read())


def saves(path, tree):
    with open(path, 'w') as f:
        f.write(dump(tree) + '\n')


# ---- helpers on parsed trees ----

def children(node, tag):
    return [x for x in node if isinstance(x, list) and x and x[0] == tag]


def child(node, tag):
    cs = children(node, tag)
    return cs[0] if cs else None


def prop(symnode, name):
    for p in children(symnode, 'property'):
        if p[1] == name:
            return p
    return None


def propval(symnode, name):
    p = prop(symnode, name)
    return p[2] if p else None


def set_propval(symnode, name, value):
    p = prop(symnode, name)
    if p:
        p[2] = value
    else:
        raise KeyError(name)
