from __future__ import annotations

import json
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterable

import vk_targets as T

RG = shutil.which("rg") or "rg"

METHOD_RE = re.compile(r"^\.method\s+(.+?)\s+([\w<>$]+)(\(.*)$", re.S)
FIELD_RE = re.compile(r"^\.field\s+(.+?)\s+([\w$]+):(\S+)(?:\s*=\s*(.*))?$")
INVOKE_RE = re.compile(r"\binvoke-\w+(?:/range)?\s+\{[^}]*\},\s+(L[^;]+;)->([^\(]+)(\([^)]*\)\S+)")
IGET_RE = re.compile(r"\biget(?:-wide|-boolean|-object|-short|-byte|-char)?\s+(\w+),\s*(\w+),\s+(L[^;]+;)->([\w$]+):(\S+)")
IPUT_RE = re.compile(r"\biput(?:-wide|-boolean|-object|-short|-byte|-char)?\s+(\w+),\s*(\w+),\s+(L[^;]+;)->([\w$]+):(\S+)")
SGET_RE = re.compile(r"\bsget(?:-wide|-boolean|-object|-short|-byte|-char)?\s+(\w+),\s+(L[^;]+;)->([\w$]+):(\S+)")
CONST_RE = re.compile(r"\bconst/(?:4|16|high16)\s+(\w+),\s*(-?0x[0-9a-fA-F]+|-?\d+)")
CONST_WIDE_RE = re.compile(r"\bconst-wide/(?:16|32|high16)?\s*(\w+),\s*(-?0x[0-9a-fA-F]+|-?\d+L?)")
STRING_RE = re.compile(r'\bconst-string(?:/jumbo)?\s+(\w+),\s*"((?:[^"\\]|\\.)*)"')


class AutoPatchError(RuntimeError):
    pass


def parse_int(value: str) -> int:
    return int(value.rstrip("Ll"), 0)


def parse_descriptor(descriptor: str) -> tuple[list[str], str]:
    if not descriptor.startswith("("):
        raise ValueError(descriptor)
    end = descriptor.index(")")
    params_str = descriptor[1:end]
    ret = descriptor[end + 1 :]
    params = []
    i = 0
    while i < len(params_str):
        start = i
        while params_str[i] == "[":
            i += 1
        if params_str[i] == "L":
            i = params_str.index(";", i) + 1
        else:
            i += 1
        params.append(params_str[start:i])
    return params, ret


def opnames(body: str) -> list[str]:
    out = []
    for raw in body.splitlines():
        line = raw.strip()
        if not line or line.startswith((".", ":", "#")):
            continue
        out.append(line.split()[0])
    return out


@dataclass
class Method:
    cls: "SmaliClass"
    access: str
    name: str
    descriptor: str
    body: str

    @property
    def signature(self) -> str:
        return self.name + self.descriptor

    @property
    def header(self) -> str:
        return f".method {self.access} {self.name}{self.descriptor}"

    @property
    def is_static(self) -> bool:
        return "static" in self.access.split()

    @property
    def is_abstract(self) -> bool:
        return "abstract" in self.access.split()

    @property
    def params(self) -> list[str]:
        return parse_descriptor(self.descriptor)[0]

    @property
    def return_type(self) -> str:
        return parse_descriptor(self.descriptor)[1]

    def instructions(self) -> list[str]:
        return opnames(self.body)

    def invokes(self) -> list[tuple[str, str, str]]:
        return INVOKE_RE.findall(self.body)

    def iget(self) -> list[tuple[str, str, str, str, str]]:
        return IGET_RE.findall(self.body)

    def iput(self) -> list[tuple[str, str, str, str, str]]:
        return IPUT_RE.findall(self.body)

    def sget(self) -> list[tuple[str, str, str, str]]:
        return SGET_RE.findall(self.body)

    def consts(self) -> dict[str, int]:
        return {reg: parse_int(value) for reg, value in CONST_RE.findall(self.body)}

    def const_wides(self) -> dict[str, int]:
        return {reg: parse_int(value) for reg, value in CONST_WIDE_RE.findall(self.body)}

    def strings(self) -> list[str]:
        return [value for _, value in STRING_RE.findall(self.body)]


@dataclass
class SmaliClass:
    path: Path
    descriptor: str
    access: str
    source: str
    fields: list[tuple[str, str, str, str]]
    methods: list[Method]
    text: str = field(repr=False, default="")

    def method(self, signature: str) -> Method | None:
        for method in self.methods:
            if method.signature == signature:
                return method
        return None


def parse_class(path: Path) -> SmaliClass | None:
    text = path.read_text(encoding="utf-8", errors="ignore")
    descriptor = ""
    access = ""
    source = ""
    fields: list[tuple[str, str, str, str]] = []
    methods: list[Method] = []
    lines = text.splitlines()
    i = 0
    while i < len(lines):
        line = lines[i]
        if line.startswith(".class "):
            parts = line.split()
            descriptor = parts[-1]
            access = " ".join(parts[1:-1])
        elif line.startswith(".source "):
            match = re.search(r'\.source\s+"(.*)"', line)
            if match:
                source = match.group(1)
        elif line.startswith(".field "):
            match = FIELD_RE.match(line)
            if match:
                fields.append((match.group(1), match.group(2), match.group(3), match.group(4) or ""))
        elif line.startswith(".method "):
            match = METHOD_RE.match(line)
            if not match:
                i += 1
                continue
            method_access, name, descriptor_part = match.group(1), match.group(2), match.group(3)
            body: list[str] = []
            i += 1
            while i < len(lines) and not lines[i].startswith(".end method"):
                body.append(lines[i])
                i += 1
            methods.append(Method(None, method_access, name, descriptor_part, "\n".join(body)))
        i += 1
    if not descriptor:
        return None
    cls = SmaliClass(path, descriptor, access, source, fields, methods, text)
    for method in methods:
        method.cls = cls
    return cls


class SmaliRepo:
    def __init__(self, work: Path):
        self.work = work
        self._classes: dict[Path, SmaliClass | None] = {}

    def _rg(self, pattern: str, fixed: bool = True) -> list[Path]:
        args = [RG, "-l", "--no-messages", "-g", "*.smali"]
        if fixed:
            args.append("-F")
        args += [pattern, str(self.work)]
        proc = subprocess.run(args, capture_output=True, text=True)
        if proc.returncode not in (0, 1):
            raise AutoPatchError(f"rg failed: {proc.stderr.strip()}")
        return [Path(line) for line in proc.stdout.splitlines() if line]

    def _rg_regex(self, pattern: str) -> list[Path]:
        args = [RG, "-l", "--no-messages", "-g", "*.smali", "-e", pattern, str(self.work)]
        proc = subprocess.run(args, capture_output=True, text=True)
        if proc.returncode not in (0, 1):
            raise AutoPatchError(f"rg failed: {proc.stderr.strip()}")
        return [Path(line) for line in proc.stdout.splitlines() if line]

    def class_at(self, path: Path) -> SmaliClass | None:
        if path not in self._classes:
            self._classes[path] = parse_class(path)
        return self._classes[path]

    def by_source(self, source: str) -> list[SmaliClass]:
        return [c for c in (self.class_at(p) for p in self._rg(f'.source "{source}"')) if c]

    def by_descriptor(self, descriptor: str) -> list[SmaliClass]:
        pattern = rf"^\.class .*{re.escape(descriptor)}"
        return [c for c in (self.class_at(p) for p in self._rg_regex(pattern)) if c]

    def by_text(self, needle: str) -> list[SmaliClass]:
        return [c for c in (self.class_at(p) for p in self._rg(needle)) if c]


@dataclass
class SmaliPatch:
    name: str
    cls: SmaliClass
    method: Method
    body: str
    required: list[str] = field(default_factory=list)
    forbidden: list[str] = field(default_factory=list)
    constants: list[str] = field(default_factory=list)

    def manifest(self) -> dict:
        return {
            "name": self.name,
            "class": self.cls.descriptor,
            "method": self.method.signature,
            "opcodes": opnames(self.body),
            "constants": self.constants,
            "required": self.required,
            "forbidden": self.forbidden,
        }


def patch_file(path: Path, method_line: str, body: str) -> str:
    raw = path.read_bytes()
    text = raw.decode("utf-8")
    newline = "\r\n" if "\r\n" in text else "\n"
    lines = text.replace("\r\n", "\n").split("\n")
    start = [i for i, line in enumerate(lines) if line.strip() == method_line]
    if len(start) != 1:
        raise AutoPatchError(f"{path}: method {method_line!r} found {len(start)} times")
    begin = start[0]
    stop = next((i for i in range(begin + 1, len(lines)) if lines[i].strip() == ".end method"), None)
    if stop is None:
        raise AutoPatchError(f"{path}: no .end method for {method_line!r}")
    current = "\n".join(lines[begin + 1 : stop])
    if current.strip() == body.strip():
        return "unchanged"
    lines[begin + 1 : stop] = body.split("\n")
    path.write_bytes(newline.join(lines).encode("utf-8"))
    return "patched"


def one(items: Iterable, what: str):
    items = list(items)
    if len(items) != 1:
        names = ", ".join(getattr(item, "descriptor", str(item)) for item in items[:6])
        raise AutoPatchError(f"{what}: expected 1, got {len(items)} ({names})")
    return items[0]


def constant_patch(name: str, method: Method, value: int) -> SmaliPatch:
    if method.return_type == "J":
        body = T.long_body()
        constants = ["v0, 4102444672"]
    elif method.return_type in ("Z", "I"):
        body = T.bool_body(value)
        constants = [f"v0, {value}"]
    else:
        raise AutoPatchError(f"{name}: unsupported return type {method.return_type}")
    return SmaliPatch(name, method.cls, method, body, constants=constants)


def rule_subscription(repo: SmaliRepo) -> list[SmaliPatch]:
    providers = repo.by_source("MusicSubscriptionProvider.kt")
    ifaces = [c for c in providers if any(m.is_abstract for m in c.methods)]
    iface = one(ifaces, "MusicSubscriptionProvider interface")
    bool_method = one(
        [m for m in iface.methods if m.is_abstract and m.descriptor == "()Z"],
        "subscription boolean getter",
    )
    long_method = one(
        [m for m in iface.methods if m.is_abstract and m.descriptor == "()J"],
        "subscription long getter",
    )
    signatures = {bool_method.signature, long_method.signature}
    candidates: list[SmaliClass] = []
    for cls in repo.by_text(f"implements {iface.descriptor}"):
        if any(m.is_abstract for m in cls.methods):
            continue
        if all(cls.method(sig) is not None for sig in signatures):
            candidates.append(cls)
    for source in ("MusicSubscriptionProviderImpl.kt", "MusicSubscriptionProvider.kt"):
        for cls in repo.by_source(source):
            if any(m.is_abstract for m in cls.methods):
                continue
            if cls in candidates:
                continue
            if all(cls.method(sig) is not None for sig in signatures):
                candidates.append(cls)
    if not candidates:
        raise AutoPatchError("MusicSubscriptionProvider: no concrete implementation")
    patches = []
    for cls in candidates:
        for sig, value in ((bool_method.signature, 1), (long_method.signature, 0)):
            method = cls.method(sig)
            if method is None:
                continue
            patches.append(constant_patch(f"subscription {cls.descriptor} {sig}", method, value))
    return patches


def rule_account(repo: SmaliRepo) -> list[SmaliPatch]:
    patches = []
    for cls in repo.by_source("CurrentAccountInformation.kt"):
        ctors = [m for m in cls.methods if m.name == "<init>"]
        bool_fields: set[str] = set()
        long_fields: set[str] = set()
        for ctor in ctors:
            for value_reg, _, _, field_name, field_type in ctor.iput():
                if field_type == "Z" and value_reg == "p1":
                    bool_fields.add(field_name)
                if field_type == "J" and value_reg == "p2":
                    long_fields.add(field_name)
        if not bool_fields or not long_fields:
            continue
        if len(bool_fields) != 1 or len(long_fields) != 1:
            raise AutoPatchError(
                f"{cls.descriptor}: account fields are ambiguous: {sorted(bool_fields)} {sorted(long_fields)}"
            )
        bool_field = next(iter(bool_fields))
        long_field = next(iter(long_fields))
        ctor = cls.method("<init>(ZJ)V")
        if ctor is None:
            ctor = one(
                [m for m in ctors if len(m.params) >= 2 and m.params[0] == "Z" and m.params[1] == "J"],
                f"{cls.descriptor} account constructor",
            )
        internal = cls.descriptor[1:-1]
        body = T.ctor_account_body(internal)
        body = body.replace(f"L{internal};->a:Z", f"L{internal};->{bool_field}:Z")
        body = body.replace(f"L{internal};->b:J", f"L{internal};->{long_field}:J")
        patches.append(
            SmaliPatch(
                "account information constructor",
                cls,
                ctor,
                body,
                required=[f"->{bool_field} ", f"->{long_field} "],
                constants=["v2, 4102444672"],
            )
        )
    return [one(patches, "CurrentAccountInformation constructor")]


def mask_of(method: Method) -> int | None:
    consts = method.consts()
    match = re.search(r"and-int/lit8\s+(\w+),\s*(\w+),\s*(0x[0-9a-fA-F]+|\d+)", method.body)
    if match:
        return int(match.group(3), 0)
    for match in re.finditer(r"and-int/2addr\s+(\w+),\s+(\w+)", method.body):
        value = consts.get(match.group(2))
        if value is not None:
            return value
    for match in re.finditer(r"and-int\s+(\w+),\s*(\w+),\s*(\w+)", method.body):
        value = consts.get(match.group(3))
        if value is not None:
            return value
    return None


def rule_context_flags(repo: SmaliRepo) -> list[SmaliPatch]:
    patches = []
    for cls in repo.by_source("ContextFlags.kt"):
        by_mask = {}
        for method in cls.methods:
            if method.is_static and method.descriptor == "(I)Z":
                mask = mask_of(method)
                if mask is not None:
                    by_mask.setdefault(mask, []).append(method)
        expected = {0x2: 1, 0x1: 0, 0x8: 0, 0x4: 0}
        found = {}
        for mask, value in expected.items():
            method = one(by_mask.get(mask, []), f"{cls.descriptor} mask {mask:#x}")
            found[mask] = method
            patches.append(constant_patch(f"context flag {mask:#x}", method, value))
        if len(found) != len(expected):
            raise AutoPatchError(f"{cls.descriptor}: incomplete context flags")
    if len(patches) != 4:
        raise AutoPatchError(f"ContextFlags patches: expected 4, got {len(patches)}")
    return patches


def rule_music_track(repo: SmaliRepo) -> list[SmaliPatch]:
    classes = repo.by_descriptor("Lcom/vk/dto/music/MusicTrack;")
    cls = one(classes, "MusicTrack")
    groups: dict[str, dict[str, list[Method]]] = {}
    for method in cls.methods:
        if method.is_static or method.params or method.return_type not in ("I", "Z"):
            continue
        igets = method.iget()
        fields = {(entry[3], entry[4]) for entry in igets}
        if len(fields) != 1:
            continue
        field_name, field_type = next(iter(fields))
        if field_type != "I":
            continue
        if method.return_type == "I":
            if len(method.instructions()) > 4 or "if-" in method.body:
                continue
            groups.setdefault(field_name, {}).setdefault("I", []).append(method)
        else:
            if "if-eqz" not in method.body and "if-nez" not in method.body:
                continue
            groups.setdefault(field_name, {}).setdefault("Z", []).append(method)
    matches = [
        (field, data["I"][0], data["Z"][0])
        for field, data in groups.items()
        if len(data.get("I", [])) == 1 and len(data.get("Z", [])) == 1
    ]
    if len(matches) != 1:
        raise AutoPatchError(f"MusicTrack field accessor pair: expected 1, got {len(matches)}")
    field, int_method, bool_method = matches[0]
    return [
        constant_patch(f"MusicTrack {field} int", int_method, 0),
        constant_patch(f"MusicTrack {field} bool", bool_method, 0),
    ]


def rule_player_model(repo: SmaliRepo) -> list[SmaliPatch]:
    patches = []
    for cls in repo.by_source("PlayerModelImpl.kt"):
        methods = [
            m
            for m in cls.methods
            if m.is_static and len(m.params) == 2 and m.params[1] == "Ljava/util/List;" and m.return_type == "Z"
        ]
        method = one(methods, f"{cls.descriptor} player restriction")
        patches.append(constant_patch("player restriction", method, 0))
    return [one(patches, "PlayerModelImpl restriction")]


def rule_features(repo: SmaliRepo) -> list[SmaliPatch]:
    classes = repo.by_descriptor("Lcom/vk/toggle/d;") or repo.by_source("FeaturesHelper.kt")
    methods = [
        m
        for cls in classes
        for m in cls.methods
        if m.is_static and m.descriptor == "(Z)Z" and "VIDEO_MUSIC_PLAYER" in m.body
    ]
    method = one(methods, "FeaturesHelper video music player")
    return [constant_patch("video music player", method, 1)]


def rule_track_ext(repo: SmaliRepo) -> list[SmaliPatch]:
    methods = [
        m
        for cls in repo.by_source("MusicTrackExt.kt")
        for m in cls.methods
        if m.is_static and m.params == ["Lcom/vk/dto/music/MusicTrack;"] and m.return_type == "Z"
    ]
    method = one(methods, "MusicTrackExt restriction")
    if "MusicTrack;" not in method.body:
        raise AutoPatchError(f"{method.cls.descriptor}: track restriction lost its anchor")
    return [constant_patch("track restriction", method, 0)]


def rule_configure(repo: SmaliRepo) -> list[SmaliPatch]:
    methods = [
        m
        for cls in repo.by_source("MusicConfigureInformationProvider.kt")
        for m in cls.methods
        if not m.is_static and m.descriptor == "()Z" and ("isAudioAdAvailable" in m.body or "AudioAdConfig" in m.body)
    ]
    method = one(methods, "MusicConfigureInformationProvider availability")
    return [constant_patch("audio ad availability", method, 0)]


def rule_callback(repo: SmaliRepo) -> list[SmaliPatch]:
    methods = [
        m
        for cls in repo.by_source("VkMusicApiCallback.kt")
        for m in cls.methods
        if m.return_type == "V"
        and "account.unregisterDevice" in m.body
        and "account.managePushDeviceMulti" in m.body
    ]
    method = one(methods, "VkMusicApiCallback credentials callback")
    return [
        SmaliPatch(
            "credentials callback",
            method.cls,
            method,
            T.void_body(),
            forbidden=["account.unregisterDevice", "account.managePushDeviceMulti"],
        )
    ]


def _preference_getter(cls: SmaliClass) -> Method:
    methods = []
    for method in cls.methods:
        if not method.is_static or len(method.params) != 4:
            continue
        if method.params[0] != "Ljava/lang/String;" or method.params[1] != "Ljava/lang/String;":
            continue
        if method.return_type == "V":
            continue
        if "ReentrantReadWriteLock" not in method.body:
            continue
        if not any(inv[2].startswith("(Landroid/content/SharedPreferences;") for inv in method.invokes()):
            continue
        methods.append(method)
    return one(methods, f"{cls.descriptor} preference getter")


def _preference_remover(cls: SmaliClass) -> Method:
    methods = [
        m
        for m in cls.methods
        if m.is_static
        and m.descriptor == "(Ljava/lang/String;Ljava/lang/String;)V"
        and "SharedPreferences;->contains" in m.body
        and "SharedPreferences$Editor;->remove" in m.body
    ]
    return one(methods, f"{cls.descriptor} preference remover")


def _prefs_getter(cls: SmaliClass, method: Method) -> tuple[str, str]:
    for _, name, descriptor in method.invokes():
        if descriptor == "(Ljava/lang/String;)Landroid/content/SharedPreferences;":
            return name, descriptor
    raise AutoPatchError(f"{method.cls.descriptor}->{method.signature}: SharedPreferences getter not found")


def _raw_prefs_getter(cls: SmaliClass, normal: Method) -> Method:
    candidates = [
        m
        for m in cls.methods
        if m.is_static
        and m.descriptor == "(Ljava/lang/String;)Landroid/content/SharedPreferences;"
        and m.signature != normal.signature
    ]
    if len(candidates) == 1:
        return candidates[0]
    for candidate in candidates:
        if "Context" in candidate.body or "gtl" in candidate.body:
            return candidate
    if candidates:
        return candidates[0]
    return normal


def _low_level(cls: SmaliClass, method: Method) -> tuple[str, str]:
    for _, name, descriptor in method.invokes():
        if descriptor.startswith("(Landroid/content/SharedPreferences;") and len(parse_descriptor(descriptor)[0]) == 5:
            return name, descriptor
    raise AutoPatchError(f"{cls.descriptor}->{method.signature}: preference constructor not found")


def _preference_body(cls: str, lock: str, raw_name: str, raw_desc: str, normal_name: str, normal_desc: str, low_name: str, low_desc: str) -> str:
    return (
        "    .locals 2\n\n"
        f"    sget-object v0, L{cls};->{lock}:Ljava/util/concurrent/locks/ReentrantReadWriteLock;\n\n"
        "    invoke-virtual {v0}, Ljava/util/concurrent/locks/ReentrantReadWriteLock;->readLock()Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;\n\n"
        "    move-result-object v0\n\n"
        "    invoke-virtual {v0}, Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;->lock()V\n\n"
        "    :try_start\n"
        '    const-string v1, "EncryptedPreferenceMeta"\n\n'
        "    invoke-virtual {v1, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n\n"
        "    move-result v1\n\n"
        "    if-eqz v1, :scoped\n\n"
        '    const-string v1, "encrypted_key.authorized"\n\n'
        "    invoke-virtual {v1, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n\n"
        "    move-result v1\n\n"
        "    if-eqz v1, :scoped\n\n"
        '    const-string v1, "plain_session_management"\n\n'
        f"    invoke-static {{v1}}, L{cls};->{raw_name}{raw_desc}\n\n"
        "    move-result-object v1\n\n"
        "    goto :resolved\n\n"
        "    :scoped\n"
        f"    invoke-static {{p0}}, L{cls};->{normal_name}{normal_desc}\n\n"
        "    move-result-object v1\n\n"
        "    :resolved\n"
        f"    invoke-static {{v1, p2, p0, p1, p3}}, L{cls};->{low_name}{low_desc}\n\n"
        "    move-result-object p0\n"
        "    :try_end\n"
        "    .catchall {:try_start .. :try_end} :catchall\n\n"
        "    invoke-virtual {v0}, Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;->unlock()V\n\n"
        "    return-object p0\n\n"
        "    :catchall\n"
        "    move-exception p0\n\n"
        "    invoke-virtual {v0}, Ljava/util/concurrent/locks/ReentrantReadWriteLock$ReadLock;->unlock()V\n\n"
        "    throw p0\n"
    )


def _preference_remove_body(cls: str, raw_name: str, raw_desc: str, normal_name: str, normal_desc: str) -> str:
    return (
        "    .locals 1\n\n"
        '    const-string v0, "EncryptedPreferenceMeta"\n\n'
        "    invoke-virtual {v0, p0}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n\n"
        "    move-result v0\n\n"
        "    if-eqz v0, :scoped\n\n"
        '    const-string v0, "encrypted_key.authorized"\n\n'
        "    invoke-virtual {v0, p1}, Ljava/lang/String;->equals(Ljava/lang/Object;)Z\n\n"
        "    move-result v0\n\n"
        "    if-eqz v0, :scoped\n\n"
        '    const-string v0, "plain_session_management"\n\n'
        f"    invoke-static {{v0}}, L{cls};->{raw_name}{raw_desc}\n\n"
        "    move-result-object p0\n\n"
        "    goto :resolved\n\n"
        "    :scoped\n"
        f"    invoke-static {{p0}}, L{cls};->{normal_name}{normal_desc}\n\n"
        "    move-result-object p0\n\n"
        "    :resolved\n"
        "    invoke-interface {p0, p1}, Landroid/content/SharedPreferences;->contains(Ljava/lang/String;)Z\n\n"
        "    move-result v0\n\n"
        "    if-eqz v0, :done\n\n"
        "    invoke-interface {p0}, Landroid/content/SharedPreferences;->edit()Landroid/content/SharedPreferences$Editor;\n\n"
        "    move-result-object p0\n\n"
        "    invoke-interface {p0, p1}, Landroid/content/SharedPreferences$Editor;->remove(Ljava/lang/String;)Landroid/content/SharedPreferences$Editor;\n\n"
        "    move-result-object p0\n\n"
        "    invoke-interface {p0}, Landroid/content/SharedPreferences$Editor;->apply()V\n\n"
        "    :done\n"
        "    return-void\n"
    )


def rule_preference(repo: SmaliRepo) -> list[SmaliPatch]:
    classes = repo.by_descriptor("Lcom/vk/core/preference/Preference;")
    if not classes:
        return []
    cls = one(classes, "Preference class")
    if not repo.by_text('"plain_session_management"'):
        return []
    getter = _preference_getter(cls)
    remover = _preference_remover(cls)
    normal_name, normal_desc = _prefs_getter(cls, getter)
    normal_method = cls.method(normal_name + normal_desc)
    if normal_method is None:
        raise AutoPatchError(f"{cls.descriptor}: preference getter {normal_name}{normal_desc} missing")
    raw = _raw_prefs_getter(cls, normal_method)
    low_name, low_desc = _low_level(cls, getter)
    lock = ""
    for _, _, name, field_type in getter.sget():
        if field_type == "Ljava/util/concurrent/locks/ReentrantReadWriteLock;":
            lock = name
            break
    if not lock:
        raise AutoPatchError(f"{cls.descriptor}: preference lock field not found")
    get_body = _preference_body(
        cls.descriptor[1:-1], lock, raw.name, raw.descriptor, normal_name, normal_desc, low_name, low_desc
    )
    remove_normal_name, remove_normal_desc = _prefs_getter(cls, remover)
    remove_normal = cls.method(remove_normal_name + remove_normal_desc)
    if remove_normal is None:
        raise AutoPatchError(f"{cls.descriptor}: remover getter {remove_normal_name}{remove_normal_desc} missing")
    remove_raw = _raw_prefs_getter(cls, remove_normal)
    remove_body = _preference_remove_body(
        cls.descriptor[1:-1], remove_raw.name, remove_raw.descriptor, remove_normal_name, remove_normal_desc
    )
    return [
        SmaliPatch(
            "preference session getter",
            cls,
            getter,
            get_body,
            required=["EncryptedPreferenceMeta", "encrypted_key.authorized", "plain_session_management"],
        ),
        SmaliPatch(
            "preference session remover",
            cls,
            remover,
            remove_body,
            required=["EncryptedPreferenceMeta", "encrypted_key.authorized", "plain_session_management"],
        ),
    ]


def rule_scope(repo: SmaliRepo) -> list[SmaliPatch]:
    classes = repo.by_text("session_management_unencrypted")
    patches = []
    for cls in classes:
        if (
            '"encrypted_session_management"' not in cls.text
            or '"plain_session_management"' not in cls.text
        ):
            continue
        for method in cls.methods:
            if "session_management_unencrypted" not in method.body:
                continue
            body = method.body.replace('"session_management_unencrypted"', '"session_management"')
            patches.append(
                SmaliPatch(
                    "session preference scope",
                    cls,
                    method,
                    body,
                    required=['"session_management"', '"encrypted_session_management"', '"plain_session_management"'],
                    forbidden=['"session_management_unencrypted"'],
                )
            )
    if not patches and repo.by_text("encrypted_session_management"):
        raise AutoPatchError("session preference scope: encrypted session preferences found, scope class not resolved")
    return [one(patches, "session preference scope")] if patches else []


def rule_migration(repo: SmaliRepo) -> list[SmaliPatch]:
    classes = repo.by_source("FromStandalone2UpdateTask.kt")
    if not classes:
        return []
    start = T.MIGRATION["start"]
    end = T.MIGRATION["end"]
    replacement = T.MIGRATION["replacement"]
    patches = []
    for cls in classes:
        for method in cls.methods:
            body = method.body
            if start not in body:
                continue
            lines = body.split("\n")
            begin = next(i for i, line in enumerate(lines) if line == start)
            stop = next((i for i in range(begin + 1, len(lines)) if lines[i] == end), None)
            if stop is None:
                raise AutoPatchError(f"{cls.descriptor}->{method.signature}: migration end not found")
            new_body = "\n".join(lines[:begin] + [replacement] + lines[stop + 1 :])
            patches.append(
                SmaliPatch(
                    "migration force result",
                    cls,
                    method,
                    new_body,
                )
            )
    if not patches:
        raise AutoPatchError("FromStandalone2UpdateTask migration pattern not found")
    return [one(patches, "migration patch")]


RULES = (
    rule_subscription,
    rule_account,
    rule_context_flags,
    rule_music_track,
    rule_player_model,
    rule_features,
    rule_track_ext,
    rule_configure,
    rule_callback,
    rule_preference,
    rule_scope,
    rule_migration,
)


@dataclass
class AutoPatchResult:
    patches: list[SmaliPatch]
    warnings: list[str] = field(default_factory=list)

    def manifest(self) -> dict:
        return {"smali": [patch.manifest() for patch in self.patches]}


def resolve(work: Path) -> AutoPatchResult:
    repo = SmaliRepo(work)
    patches: list[SmaliPatch] = []
    warnings: list[str] = []
    for rule in RULES:
        result = rule(repo)
        if not result and rule in (rule_preference, rule_scope, rule_migration):
            warnings.append(f"{rule.__name__}: not applicable")
            continue
        if not result:
            raise AutoPatchError(f"{rule.__name__}: no patches")
        patches.extend(result)
    return AutoPatchResult(patches, warnings)


def write_manifest(path: Path, manifest: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
