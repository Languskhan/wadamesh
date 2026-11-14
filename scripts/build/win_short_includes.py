# Windows-only build fix: keep the compiler command line under Windows' 32,767-char limit.
#
# On Windows, xtensa g++ fails with "CreateProcess: No such file or directory" when the
# command it builds for cc1plus is longer than Windows allows. This env passes hundreds of
# Arduino-ESP32 framework include folders, each spelled out in full. Right before each
# compiler call, this script rewrites those -I entries as one -iprefix plus short
# -iwithprefixbefore entries, in the same positions, so the header search order is
# unchanged. Only long xtensa gcc/g++ calls are touched; other platforms: no-op.
#
# A short log of rewritten/failed commands goes to .pio/win_short_includes.log.
Import("env")  # noqa: F821  (SCons)
import ntpath
import os
import shlex
import tempfile

LIMIT = 24000


def _log(msg):
    try:
        path = os.path.join(env.subst("$PROJECT_DIR"), ".pio", "win_short_includes.log")
        os.makedirs(os.path.dirname(path), exist_ok=True)
        with open(path, "a") as f:
            f.write(msg + "\n")
    except Exception:
        pass


def _unquote(t):
    return t[1:-1] if len(t) >= 2 and t[0] == t[-1] == '"' else t


def _plain(raw):
    # gcc response-file token -> plain text: drop surrounding quotes, undo \\ escapes
    t = _unquote(raw)
    return t.replace("\\\\", "\\").replace('\\"', '"')


def _rspq(plain):
    # plain text -> gcc response-file token
    t = plain.replace("\\", "\\\\").replace('"', '\\"')
    return '"%s"' % t if (" " in t or "\t" in t) else t


def _expand(args):
    """[(raw response-file token, plain text)] for the whole command, @files inlined."""
    out = []
    for a in args[1:]:
        p = _unquote(a)
        if p.startswith("@") and os.path.isfile(_unquote(p[1:])):
            with open(_unquote(p[1:])) as f:
                out += [(t, _plain(t)) for t in shlex.split(f.read(), posix=False)]
        else:
            out.append((_rspq(p), p))
    return out


def _shorten(toks):
    fw = [i for i, (_, p) in enumerate(toks)
          if p.startswith("-I") and "framework-arduinoespressif32" in p]
    if len(fw) < 10:
        return None
    fws = set(fw)
    prefix = ntpath.commonpath([ntpath.normpath(toks[i][1][2:]) for i in fw])
    out = []
    for i, (raw, p) in enumerate(toks):
        if i == fw[0]:
            out += ["-iprefix", _rspq(prefix.replace("\\", "/") + "/")]
        if i in fws:
            rel = ntpath.relpath(ntpath.normpath(p[2:]), prefix).replace("\\", "/")
            out += ["-iwithprefixbefore", _rspq(rel)]
        else:
            out.append(raw)
    return out


def _wrap(spawn):
    if getattr(spawn, "_win_short", False):
        return spawn

    def wrapped(sh, escape, cmd, args, spawnenv):
        exe = os.path.basename(_unquote(args[0])).lower() if args else ""
        if "xtensa" in exe and ("gcc" in exe or "g++" in exe):
            toks = _expand(args)
            n = len(args[0]) + sum(len(p) + 1 for _, p in toks)
            if n > LIMIT:
                short = _shorten(toks)
                if short:
                    fd, rsp = tempfile.mkstemp(suffix=".rsp", text=True)
                    with os.fdopen(fd, "w") as f:
                        f.write(" ".join(short))
                    n2 = len(args[0]) + sum(len(t) + 1 for t in short)
                    rc = spawn(sh, escape, cmd, [args[0], "@" + rsp.replace("\\", "/")], spawnenv)
                    try:
                        os.remove(rsp)
                    except OSError:
                        pass
                    _log("%s len %d -> %d: %s" % ("FAILED rc=%s" % rc if rc else "ok", n, n2, toks[-1][1]))
                    return rc
                _log("long command not shortened (%d chars): %s" % (n, toks[-1][1]))
            rc = spawn(sh, escape, cmd, args, spawnenv)
            if rc:
                _log("FAILED rc=%s len %d (not rewritten): %s" % (rc, n, toks[-1][1]))
            return rc
        return spawn(sh, escape, cmd, args, spawnenv)

    wrapped._win_short = True
    return wrapped


if os.name == "nt":
    env["SPAWN"] = _wrap(env["SPAWN"])
    _log("installed (%s)" % env.subst("$PIOENV"))
