"""Connectivity-aware editing helpers for KiCad 7 schematic files."""
import math
import uuid as uuidlib
from kicad_sexp import (Sym, Num, parse, dump, loads, saves, children, child,
                        prop, propval, set_propval)


def P(v):
    return round(float(v), 3)


class Schematic:
    def __init__(self, path):
        self.path = path
        self.tree = loads(path)
        self._lib = {}
        libs = child(self.tree, 'lib_symbols')
        if libs:
            for s in children(libs, 'symbol'):
                self._lib[s[1]] = s

    def save(self, path=None):
        saves(path or self.path, self.tree)

    # ---------- queries ----------
    def symbols(self):
        return children(self.tree, 'symbol')

    def by_ref(self, ref):
        for s in self.symbols():
            if propval(s, 'Reference') == ref:
                return s
        return self.by_inst_ref(ref)

    def by_inst_ref(self, ref):
        """Find a symbol by any of its per-instance references."""
        for s in self.symbols():
            inst = child(s, 'instances')
            if not inst:
                continue
            for proj in children(inst, 'project'):
                for pathnode in children(proj, 'path'):
                    r = child(pathnode, 'reference')
                    if r and r[1] == ref:
                        return s
        return None

    def lib_pins(self, lib_id):
        """pin number -> (x, y) in symbol coords (unit-merged)."""
        node = self._lib[lib_id]
        # resolve "extends"
        ext = child(node, 'extends')
        pins = {}

        def collect(n):
            for sub in children(n, 'symbol'):
                for p in children(sub, 'pin'):
                    at = child(p, 'at')
                    numnode = child(p, 'number')
                    pins[numnode[1]] = (float(at[1]), float(at[2]),
                                        p[1], p[2], sub[1])
        collect(node)
        if ext:
            base = self._lib[lib_id.split(':')[0] + ':' + ext[1]]
            collect(base)
        return pins

    def pin_pos(self, symnode, pinnum):
        lib_id = child(symnode, 'lib_id')[1]
        at = child(symnode, 'at')
        sx, sy = float(at[1]), float(at[2])
        rot = float(at[3]) if len(at) > 3 else 0.0
        mirror = child(symnode, 'mirror')
        unit = child(symnode, 'unit')
        unitno = int(unit[1]) if unit else 1
        info = self.lib_pins(lib_id).get(str(pinnum))
        if info is None:
            return None
        px, py, _t, _s, subname = info
        # check pin belongs to this unit (subname like NAME_0_1 / NAME_1_1)
        try:
            u = int(subname.rsplit('_', 2)[1])
            if u not in (0, unitno):
                return None
        except Exception:
            pass
        x, y = px, -py
        # rotate first (clockwise matrix in sheet coords), mirror after
        r = math.radians(rot)
        c, s = round(math.cos(r)), round(math.sin(r))
        x, y = x * c + y * s, -x * s + y * c
        if mirror is not None:
            m = str(mirror[1])
            if m == 'y':
                x = -x
            elif m == 'x':
                y = -y
        return (P(sx + x), P(sy + y))

    def all_pin_points(self, exclude_refs=()):
        pts = {}
        for s in self.symbols():
            ref = propval(s, 'Reference')
            if ref in exclude_refs:
                continue
            lib_id = child(s, 'lib_id')[1]
            for num in self.lib_pins(lib_id):
                pp = self.pin_pos(s, num)
                if pp:
                    pts.setdefault(pp, []).append((ref, num))
        return pts

    # ---------- graphics indexes ----------
    def wires(self):
        return children(self.tree, 'wire')

    @staticmethod
    def wire_ends(w):
        ptsnode = child(w, 'pts')
        xs = children(ptsnode, 'xy')
        return [(P(p[1]), P(p[2])) for p in xs]

    def labels(self, tag):
        return children(self.tree, tag)

    # ---------- edits ----------
    def remove_top(self, node):
        self.tree.remove(node)

    def delete_symbols(self, refs, prune=True, stop_points=()):
        """Delete symbols by ref; prune attached wires/labels/nc/junctions.

        Traversal seeds at deleted-symbol pin positions, walks wires by
        shared endpoints, stops at pins of kept symbols and at stop_points.
        """
        refs = set(refs)
        doomed = [s for s in self.symbols() if propval(s, 'Reference') in refs]
        seeds = set()
        for s in doomed:
            lib_id = child(s, 'lib_id')[1]
            for num in self.lib_pins(lib_id):
                pp = self.pin_pos(s, num)
                if pp:
                    seeds.add(pp)
        for s in doomed:
            self.tree.remove(s)
        if not prune:
            return
        keep_pins = set(self.all_pin_points())
        junctions = set()
        for j in self.labels('junction'):
            at = child(j, 'at')
            junctions.add((P(at[1]), P(at[2])))
        stop = keep_pins | set(stop_points) | junctions
        # walk
        wire_list = self.wires()
        visited = set(seeds) - stop
        dead_wires = set()
        changed = True
        while changed:
            changed = False
            for i, w in enumerate(wire_list):
                if i in dead_wires:
                    continue
                ends = self.wire_ends(w)
                if any(e in visited for e in ends):
                    dead_wires.add(i)
                    changed = True
                    for e in ends:
                        if e not in stop and e not in visited:
                            visited.add(e)
        for i in sorted(dead_wires, reverse=True):
            self.tree.remove(wire_list[i])
        for tag in ('label', 'global_label', 'hierarchical_label',
                    'no_connect', 'junction'):
            for node in list(self.labels(tag)):
                at = child(node, 'at')
                pt = (P(at[1]), P(at[2]))
                if pt in visited:
                    self.tree.remove(node)

    def add_wire(self, p1, p2):
        self.tree.append(parse(
            '(wire (pts (xy %s %s) (xy %s %s)) (stroke (width 0) '
            '(type default)) (uuid %s))' % (p1[0], p1[1], p2[0], p2[1],
                                            uuidlib.uuid4())))

    def add_label(self, text, pt, rot=0, kind='label', shape='passive'):
        if kind == 'label':
            self.tree.append(parse(
                '(label "%s" (at %s %s %s) (effects (font (size 1.27 1.27))'
                ' (justify left bottom)) (uuid %s))'
                % (text, pt[0], pt[1], rot, uuidlib.uuid4())))
        else:
            self.tree.append(parse(
                '(%s "%s" (shape %s) (at %s %s %s) (effects (font '
                '(size 1.27 1.27)) (justify left)) (uuid %s))'
                % (kind, text, shape, pt[0], pt[1], rot, uuidlib.uuid4())))

    def add_nc(self, pt):
        self.tree.append(parse('(no_connect (at %s %s) (uuid %s))'
                               % (pt[0], pt[1], uuidlib.uuid4())))

    def add_junction(self, pt):
        self.tree.append(parse(
            '(junction (at %s %s) (diameter 0) (color 0 0 0 0) (uuid %s))'
            % (pt[0], pt[1], uuidlib.uuid4())))

    def add_text(self, text, pt, size=1.27):
        self.tree.append(parse(
            '(text "%s" (at %s %s 0) (effects (font (size %s %s)) '
            '(justify left bottom)) (uuid %s))'
            % (text, pt[0], pt[1], size, size, uuidlib.uuid4())))

    # ---------- symbol attribute edits ----------
    @staticmethod
    def set_dnp(symnode, dnp=True):
        for attr in ('dnp',):
            existing = child(symnode, attr)
            if existing:
                symnode.remove(existing)
        # insert after on_board/in_bom flags
        idx = None
        for i, x in enumerate(symnode):
            if isinstance(x, list) and x and x[0] in ('on_board', 'in_bom',
                                                      'fields_autoplaced'):
                idx = i
        node = parse('(dnp %s)' % ('yes' if dnp else 'no'))
        if idx is not None:
            symnode.insert(idx + 1, node)
        else:
            symnode.append(node)

    @staticmethod
    def add_property(symnode, name, value, hide=True):
        existing = prop(symnode, name)
        if existing:
            existing[2] = value
            return
        ref = prop(symnode, 'Reference')
        at = child(ref, 'at') if ref else None
        x, y = (at[1], at[2]) if at else (Num('0'), Num('0'))
        node = parse('(property "%s" "%s" (at %s %s 0) (effects (font '
                     '(size 1.27 1.27)) hide))' % (name, value, x, y))
        # insert after last property
        last = None
        for i, c in enumerate(symnode):
            if isinstance(c, list) and c and c[0] == 'property':
                last = i
        symnode.insert((last or 0) + 1, node)

    def remove_label_at(self, text, pt, tags=('label', 'global_label',
                                              'hierarchical_label')):
        for tag in tags:
            for n in list(self.labels(tag)):
                if n[1] != text:
                    continue
                at = child(n, 'at')
                if (P(at[1]), P(at[2])) == (P(pt[0]), P(pt[1])):
                    self.tree.remove(n)
                    return True
        return False

    def remove_nc_at(self, pt):
        for n in list(self.labels('no_connect')):
            at = child(n, 'at')
            if (P(at[1]), P(at[2])) == (P(pt[0]), P(pt[1])):
                self.tree.remove(n)
                return True
        return False

    def remove_wire(self, p1, p2):
        p1 = (P(p1[0]), P(p1[1]))
        p2 = (P(p2[0]), P(p2[1]))
        for w in list(self.wires()):
            ends = self.wire_ends(w)
            if set(ends) == {p1, p2}:
                self.tree.remove(w)
                return True
        return False

    def convert_hier_to_local(self, text):
        """Replace all hierarchical labels named `text` with local labels."""
        n_conv = 0
        for n in list(self.labels('hierarchical_label')):
            if n[1] != text:
                continue
            at = child(n, 'at')
            self.tree.remove(n)
            self.add_label(text, (at[1], at[2]),
                           at[3] if len(at) > 3 else 0)
            n_conv += 1
        return n_conv

    def convert_local_to_hier(self, text, shape):
        n_conv = 0
        for n in list(self.labels('label')):
            if n[1] != text:
                continue
            at = child(n, 'at')
            self.tree.remove(n)
            self.add_label(text, (at[1], at[2]),
                           at[3] if len(at) > 3 else 0,
                           kind='hierarchical_label', shape=shape)
            n_conv += 1
        return n_conv

    _pwr_seq = [9000]

    def add_power(self, lib_id, pt, rot=0, project=None, sheetpath=None):
        """Clone an existing power symbol of lib_id at pt."""
        ref = '#PWR%05d' % self._pwr_seq[0]
        self._pwr_seq[0] += 1
        donor = None
        for s in self.symbols():
            if child(s, 'lib_id')[1] == lib_id:
                donor = s
                break
        assert donor is not None, 'no donor instance of %s' % lib_id
        node = parse(dump(donor))
        at = child(node, 'at')
        dx = P(pt[0]) - float(at[1])
        dy = P(pt[1]) - float(at[2])
        at[1], at[2] = Num(str(P(pt[0]))), Num(str(P(pt[1])))
        if len(at) > 3:
            at[3] = Num(str(rot))
        else:
            at.append(Num(str(rot)))
        uu = child(node, 'uuid')
        uu[1] = Sym(str(uuidlib.uuid4()))
        for pnode in children(node, 'pin'):
            pu = child(pnode, 'uuid')
            if pu:
                pu[1] = Sym(str(uuidlib.uuid4()))
        set_propval(node, 'Reference', ref)
        # shift property anchor positions along
        for p in children(node, 'property'):
            pat = child(p, 'at')
            if pat:
                pat[1] = Num(str(P(float(pat[1]) + dx)))
                pat[2] = Num(str(P(float(pat[2]) + dy)))
        inst = child(node, 'instances')
        if inst:
            node.remove(inst)
        if project and sheetpath:
            node.append(parse(
                '(instances (project "%s" (path "%s" (reference "%s") '
                '(unit 1))))' % (project, sheetpath, ref)))
        self.tree.append(node)
        return ref

    def gc_power(self):
        """Remove power symbols whose pin touches nothing."""
        segs = [tuple(self.wire_ends(w)) for w in self.wires()]
        pts = set()
        for a, b in segs:
            pts.update((a, b))
        pinpts = self.all_pin_points()
        removed = []
        for s in list(self.symbols()):
            lib_id = child(s, 'lib_id')[1]
            libdef = self._lib.get(lib_id)
            is_power = lib_id.startswith('power:') or (
                libdef is not None and child(libdef, 'power') is not None)
            if not is_power:
                continue
            pp = self.pin_pos(s, '1')
            others = [x for x in pinpts.get(pp, [])
                      if x[0] != propval(s, 'Reference')]
            if pp not in pts and not others:
                self.tree.remove(s)
                removed.append(propval(s, 'Reference'))
        return removed

    def ensure_instances(self, symnode, project, path_refs):
        """path_refs: list of (path, reference) tuples."""
        inst = child(symnode, 'instances')
        if inst:
            symnode.remove(inst)
        body = ' '.join('(path "%s" (reference "%s") (unit 1))' % (p, r)
                        for p, r in path_refs)
        symnode.append(parse('(instances (project "%s" %s))'
                             % (project, body)))
