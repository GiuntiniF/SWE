#!/usr/bin/env python3
"""
gaphor2MD - Estrae uno strato semantico Markdown dai modelli Gaphor (.gaphor).

Il formato .gaphor e' XML: ogni elemento del modello e' un tag di primo livello
il cui nome coincide con la metaclasse UML. Le proprieta' sono espresse come:

    <name><val>Utente</val></name>                 -> valore scalare
    <class_><ref refid="abc"/></class_>            -> riferimento singolo
    <ownedAttribute><reflist><ref .../></reflist>  -> collezione di riferimenti

Lo script ignora completamente gli elementi di presentazione (geometria,
matrici, stili) e produce un Markdown compatto pensato per essere letto da un
LLM: indice dei diagrammi, elementi raggruppati per package, tabella unica
delle relazioni.

Esempi:
    python gaphor2MD.py modello.gaphor -o docs/model
    python gaphor2MD.py -r src/ -o docs/model --single-file
    python gaphor2MD.py -r src/ -o docs/model --check   # per la CI
"""

from __future__ import annotations

import argparse
import hashlib
import re
import sys
from dataclasses import dataclass, field
from pathlib import Path
from xml.etree import ElementTree as ET

# --------------------------------------------------------------------------- #
# Tassonomia
# --------------------------------------------------------------------------- #

VISIBILITY_SYMBOLS = {
    "public": "+",
    "private": "-",
    "protected": "#",
    "package": "~",
}

AGGREGATION_SYMBOLS = {
    "shared": "aggregazione",
    "composite": "composizione",
}

# Elementi renderizzati dentro al proprio contenitore, mai come voce autonoma.
NESTED_TYPES = {
    "Property",
    "Operation",
    "Parameter",
    "EnumerationLiteral",
    "Slot",
    "LiteralSpecification",
    "LiteralString",
    "LiteralInteger",
}

# Elementi puramente tecnici, privi di contenuto semantico.
IGNORED_TYPES = {
    "StyleSheet",
    "Picture",
    "Metadata",
    "PendingChange",
    "ElementChange",
    "ValueChange",
    "RefChange",
}

# Relazioni: (tipo -> (attributo sorgente, attributo destinazione)).
# Il primo nome trovato tra quelli elencati viene usato.
RELATION_ENDS = {
    "Generalization": (("specific",), ("general",)),
    "Dependency": (("client",), ("supplier",)),
    "Usage": (("client",), ("supplier",)),
    "Realization": (("client",), ("supplier",)),
    "Abstraction": (("client",), ("supplier",)),
    "Substitution": (("substitutingClassifier",), ("contract",)),
    "InterfaceRealization": (("implementatingClassifier", "client"), ("contract", "supplier")),
    "Include": (("includingCase",), ("addition",)),
    "Extend": (("extension",), ("extendedCase",)),
    "Transition": (("source",), ("target",)),
    "ControlFlow": (("source",), ("target",)),
    "ObjectFlow": (("source",), ("target",)),
    "Connector": (("end",), ()),
    "Extension": (("ownedEnd",), ()),
    "PackageImport": (("importingNamespace",), ("importedPackage",)),
    "Message": (("sendEvent",), ("receiveEvent",)),
    "CommunicationPath": ((), ()),
}

RELATION_TYPES = set(RELATION_ENDS) | {"Association"}

DIAGRAM_TYPE_LABELS = {
    "": "generico",
    "cls": "classi",
    "uc": "casi d'uso",
    "pkg": "package",
    "cmp": "componenti",
    "dep": "deployment",
    "act": "attivita'",
    "sd": "sequenza",
    "ste": "macchina a stati",
    "obj": "oggetti",
    "prf": "profilo",
    "c4": "C4",
}

PACKAGE_TYPES = {"Package", "Model", "Profile"}

# Attributi che identificano il contenitore di un elemento, in ordine di preferenza.
OWNER_KEYS = ("package", "owningPackage", "namespace", "owner", "nestingPackage")


# --------------------------------------------------------------------------- #
# Modello in memoria
# --------------------------------------------------------------------------- #


@dataclass
class ModelElement:
    """Un elemento del modello, indipendente dalla rappresentazione grafica."""

    elemId: str
    elemType: str
    values: dict[str, str] = field(default_factory=dict)
    refs: dict[str, str] = field(default_factory=dict)
    refLists: dict[str, list[str]] = field(default_factory=dict)

    @property
    def name(self) -> str:
        return (self.values.get("name") or "").strip()

    def firstRef(self, *keys: str) -> str | None:
        """Primo riferimento disponibile tra le chiavi indicate."""
        for key in keys:
            if key in self.refs:
                return self.refs[key]
            values = self.refLists.get(key)
            if values:
                return values[0]
        return None

    def allRefs(self, *keys: str) -> list[str]:
        out: list[str] = []
        for key in keys:
            if key in self.refs:
                out.append(self.refs[key])
            out.extend(self.refLists.get(key, []))
        return out


def stripNamespace(tag: str) -> str:
    return tag.split("}", 1)[-1]


def normalizeName(tag: str) -> str:
    """`class_` -> `class`: Gaphor aggiunge un underscore alle keyword Python."""
    return stripNamespace(tag).rstrip("_")


def textOf(node: ET.Element) -> str:
    return "".join(node.itertext()).strip()


def parseGaphorFile(path: Path) -> dict[str, ModelElement]:
    """Legge un file .gaphor e restituisce la mappa id -> ModelElement."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"XML non valido in {path}: {exc}") from exc

    elements: dict[str, ModelElement] = {}
    for node in root:
        elemId = node.get("id")
        if not elemId:
            continue
        element = ModelElement(elemId=elemId, elemType=stripNamespace(node.tag))
        for prop in node:
            propName = normalizeName(prop.tag)
            children = list(prop)
            if not children:
                value = textOf(prop)
                if value:
                    element.values[propName] = value
                continue
            for child in children:
                childTag = stripNamespace(child.tag)
                if childTag == "val":
                    element.values[propName] = textOf(child)
                elif childTag == "ref":
                    element.refs[propName] = child.get("refid", "")
                elif childTag == "reflist":
                    element.refLists.setdefault(propName, []).extend(
                        ref.get("refid", "")
                        for ref in child
                        if stripNamespace(ref.tag) == "ref"
                    )
        elements[elemId] = element
    return elements


def isPresentation(element: ModelElement) -> bool:
    """True per gli item grafici (geometria/stile), da scartare."""
    if "matrix" in element.values or "canvas" in element.refs:
        return True
    if element.elemType.endswith(("Item", "Line", "Box")):
        return True
    return "diagram" in element.refs and "subject" in element.refs


# --------------------------------------------------------------------------- #
# Query sul modello
# --------------------------------------------------------------------------- #


class ModelIndex:
    """Indice di lookup costruito una sola volta per file."""

    def __init__(self, elements: dict[str, ModelElement]) -> None:
        self.elements = elements
        self.presentations = {
            eid: el for eid, el in elements.items() if isPresentation(el)
        }
        self.semantic = {
            eid: el
            for eid, el in elements.items()
            if eid not in self.presentations and el.elemType not in IGNORED_TYPES
        }
        self.diagrams = {
            eid: el for eid, el in self.semantic.items() if el.elemType == "Diagram"
        }
        self.commentsByTarget = self._indexComments()
        self.diagramMembership = self._indexDiagramMembership()

    def _indexComments(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for element in self.semantic.values():
            if element.elemType != "Comment":
                continue
            body = (element.values.get("body") or "").strip()
            if not body:
                continue
            for targetId in element.allRefs("annotatedElement"):
                out.setdefault(targetId, []).append(body)
        return out

    def _indexDiagramMembership(self) -> dict[str, list[str]]:
        """diagramId -> lista di id di elementi semantici presenti sul diagramma."""
        out: dict[str, list[str]] = {did: [] for did in self.diagrams}
        for presentation in self.presentations.values():
            subjectId = presentation.refs.get("subject")
            if not subjectId:
                continue
            diagramId = presentation.refs.get("diagram")
            if diagramId is None:
                # Formati piu' vecchi: il diagramma elenca le presentazioni.
                for did, diagram in self.diagrams.items():
                    if presentation.elemId in diagram.refLists.get("ownedPresentation", []):
                        diagramId = did
                        break
            if diagramId in out and subjectId not in out[diagramId]:
                out[diagramId].append(subjectId)
        return out

    def get(self, elemId: str | None) -> ModelElement | None:
        return self.elements.get(elemId) if elemId else None

    def nameOf(self, elemId: str | None, fallback: str = "?") -> str:
        element = self.get(elemId)
        if element is None:
            return fallback
        if element.name:
            return element.name
        return f"({element.elemType.lower()} anonimo)"

    def typeNameOf(self, element: ModelElement) -> str:
        """Tipo di una Property/Parameter: per riferimento o come stringa libera."""
        typed = self.get(element.refs.get("type"))
        if typed is not None and typed.name:
            return typed.name
        return (element.values.get("typeValue") or "").strip()

    def ownerOf(self, element: ModelElement) -> ModelElement | None:
        ownerId = element.firstRef(*OWNER_KEYS)
        owner = self.get(ownerId)
        if owner is not None and owner.elemType in PACKAGE_TYPES:
            return owner
        # Risalita: se il proprietario non e' un package, cerca il suo.
        if owner is not None and owner is not element:
            return self.ownerOf(owner)
        return None

    def commentsFor(self, elemId: str) -> list[str]:
        return self.commentsByTarget.get(elemId, [])


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def multiplicityOf(element: ModelElement) -> str:
    lower = element.values.get("lowerValue")
    upper = element.values.get("upperValue")
    if lower is None and upper is None:
        return ""
    if lower is not None and lower == upper:
        return lower
    return f"{lower or '0'}..{upper or '*'}"


def visibilityOf(element: ModelElement) -> str:
    return VISIBILITY_SYMBOLS.get(element.values.get("visibility", "public"), "+")


def escapePipes(text: str) -> str:
    return text.replace("|", "\\|")


def flattenText(text: str, limit: int = 400) -> str:
    """Testo su una riga sola: le tabelle Markdown non tollerano gli a capo."""
    collapsed = re.sub(r"\s+", " ", text).strip()
    if len(collapsed) > limit:
        collapsed = collapsed[: limit - 1].rstrip() + "…"
    return escapePipes(collapsed)


def renderAttributes(index: ModelIndex, owner: ModelElement) -> list[str]:
    propertyIds = owner.refLists.get("ownedAttribute", [])
    rows: list[str] = []
    for propId in propertyIds:
        prop = index.get(propId)
        if prop is None or prop.elemType != "Property":
            continue
        if prop.refs.get("association") or prop.refs.get("owningAssociation"):
            continue  # e' un end di associazione, compare nella tabella relazioni
        typeName = index.typeNameOf(prop) or "—"
        mult = multiplicityOf(prop)
        default = prop.values.get("defaultValue", "")
        flags = []
        if prop.values.get("isStatic") == "1":
            flags.append("static")
        if prop.values.get("isDerived") == "1":
            flags.append("derived")
        if prop.values.get("isReadOnly") == "1":
            flags.append("readonly")
        rows.append(
            "| {vis} | {name} | {type} | {mult} | {default} | {flags} |".format(
                vis=visibilityOf(prop),
                name=escapePipes(prop.name or "—"),
                type=escapePipes(typeName),
                mult=mult or "—",
                default=escapePipes(default) or "—",
                flags=", ".join(flags) or "—",
            )
        )
    if not rows:
        return []
    return [
        "",
        "**Attributi**",
        "",
        "| Vis | Nome | Tipo | Molt. | Default | Note |",
        "| --- | --- | --- | --- | --- | --- |",
        *rows,
        "",
    ]


def renderOperations(index: ModelIndex, owner: ModelElement) -> list[str]:
    rows: list[str] = []
    for opId in owner.refLists.get("ownedOperation", []):
        operation = index.get(opId)
        if operation is None or operation.elemType != "Operation":
            continue
        params: list[str] = []
        returnType = ""
        for paramId in operation.refLists.get("ownedParameter", []):
            param = index.get(paramId)
            if param is None:
                continue
            typeName = index.typeNameOf(param)
            if param.values.get("direction") == "return":
                returnType = typeName
                continue
            direction = param.values.get("direction", "in")
            prefix = "" if direction == "in" else f"{direction} "
            label = f"{prefix}{param.name}" if param.name else prefix.strip() or "?"
            params.append(f"{label}: {typeName}" if typeName else label)
        flags = []
        if operation.values.get("isAbstract") == "1":
            flags.append("abstract")
        if operation.values.get("isStatic") == "1":
            flags.append("static")
        rows.append(
            "| {vis} | {sig} | {ret} | {flags} |".format(
                vis=visibilityOf(operation),
                sig=escapePipes(f"{operation.name}({', '.join(params)})"),
                ret=escapePipes(returnType) or "void",
                flags=", ".join(flags) or "—",
            )
        )
    if not rows:
        return []
    return [
        "",
        "**Operazioni**",
        "",
        "| Vis | Firma | Ritorno | Note |",
        "| --- | --- | --- | --- |",
        *rows,
        "",
    ]


def renderLiterals(index: ModelIndex, owner: ModelElement) -> list[str]:
    names = [
        index.nameOf(litId)
        for litId in owner.refLists.get("ownedLiteral", [])
        if index.get(litId) is not None
    ]
    if not names:
        return []
    return ["", "**Valori**: " + ", ".join(f"`{n}`" for n in names), ""]


def renderElement(
    index: ModelIndex, element: ModelElement, level: int = 4
) -> list[str]:
    stereotypes = []
    if element.values.get("isAbstract") == "1":
        stereotypes.append("abstract")
    header = f"{'#' * level} {element.elemType} `{element.name or '(anonimo)'}`"
    if stereotypes:
        header += f" *<<{', '.join(stereotypes)}>>*"

    lines = [header]
    for comment in index.commentsFor(element.elemId):
        lines += ["", comment.strip()]

    lines += renderAttributes(index, element)
    lines += renderOperations(index, element)
    lines += renderLiterals(index, element)

    if lines[-1] != "":
        lines.append("")
    return lines


def relationLabel(index: ModelIndex, element: ModelElement) -> str:
    """Etichetta leggibile per una relazione, che tipicamente non ha nome."""
    if element.elemType == "Association":
        ends = [index.get(pid) for pid in element.refLists.get("memberEnd", [])]
        names = [index.typeNameOf(e) or "?" for e in ends if e is not None]
        label = " — ".join(names[:2]) if len(names) >= 2 else "?"
    else:
        sourceKeys, targetKeys = RELATION_ENDS.get(element.elemType, ((), ()))
        source = index.nameOf(element.firstRef(*sourceKeys), "?") if sourceKeys else "?"
        target = index.nameOf(element.firstRef(*targetKeys), "?") if targetKeys else "?"
        label = f"{source} → {target}"
    return f"{element.name} ({label})" if element.name else label


def renderAssociation(index: ModelIndex, association: ModelElement) -> str | None:
    ends = [index.get(pid) for pid in association.refLists.get("memberEnd", [])]
    ends = [e for e in ends if e is not None]
    if len(ends) < 2:
        return None
    descriptions = []
    for end in ends[:2]:
        classifier = index.typeNameOf(end) or "?"
        mult = multiplicityOf(end)
        role = end.name
        label = classifier
        if mult:
            label += f" [{mult}]"
        if role:
            label += f" ({role})"
        descriptions.append(label)

    details = []
    for end in ends[:2]:
        aggregation = AGGREGATION_SYMBOLS.get(end.values.get("aggregation", ""))
        if aggregation:
            details.append(f"{aggregation} lato {index.typeNameOf(end) or '?'}")
    if association.name:
        details.insert(0, f"nome: {association.name}")

    return "| Association | {a} | {b} | {details} |".format(
        a=escapePipes(descriptions[0]),
        b=escapePipes(descriptions[1]),
        details=escapePipes("; ".join(details)) or "—",
    )


def renderRelations(index: ModelIndex) -> list[str]:
    rows: list[str] = []
    for element in index.semantic.values():
        if element.elemType == "Association":
            row = renderAssociation(index, element)
            if row:
                rows.append(row)
            continue
        if element.elemType not in RELATION_ENDS:
            continue
        sourceKeys, targetKeys = RELATION_ENDS[element.elemType]
        sourceId = element.firstRef(*sourceKeys) if sourceKeys else None
        targetId = element.firstRef(*targetKeys) if targetKeys else None
        if sourceId is None and targetId is None:
            continue
        details = []
        if element.name:
            details.append(f"nome: {element.name}")
        guard = element.values.get("guard") or element.refs.get("guard")
        if guard and isinstance(guard, str) and guard in index.elements:
            guardText = index.elements[guard].values.get("specification", "")
            if guardText:
                details.append(f"guardia: {guardText}")
        rows.append(
            "| {kind} | {a} | {b} | {details} |".format(
                kind=element.elemType,
                a=escapePipes(index.nameOf(sourceId, "—")),
                b=escapePipes(index.nameOf(targetId, "—")),
                details=escapePipes("; ".join(details)) or "—",
            )
        )
    if not rows:
        return []
    rows.sort()
    return [
        "## Relazioni",
        "",
        "| Tipo | Origine | Destinazione | Dettagli |",
        "| --- | --- | --- | --- |",
        *rows,
        "",
    ]


def renderDiagramIndex(index: ModelIndex) -> list[str]:
    if not index.diagrams:
        return []
    lines = ["## Diagrammi", ""]
    for diagramId, diagram in sorted(
        index.diagrams.items(), key=lambda kv: kv[1].name.lower()
    ):
        rawType = diagram.values.get("diagramType", "")
        label = DIAGRAM_TYPE_LABELS.get(rawType, rawType or "generico")
        lines.append(f"### {diagram.name or '(diagramma senza nome)'} — *{label}*")
        for comment in index.commentsFor(diagramId):
            lines += ["", comment.strip()]
        lines.append("")

        byType: dict[str, list[str]] = {}
        for memberId in index.diagramMembership.get(diagramId, []):
            member = index.get(memberId)
            if member is None or member.elemType in NESTED_TYPES:
                continue
            if member.elemType == "Comment":
                continue
            label = (
                relationLabel(index, member)
                if member.elemType in RELATION_TYPES
                else index.nameOf(memberId)
            )
            byType.setdefault(member.elemType, []).append(label)
        if not byType:
            lines += ["_Nessun elemento semantico._", ""]
            continue
        for elemType in sorted(byType):
            names = sorted(set(byType[elemType]), key=str.lower)
            lines.append(f"- **{elemType}**: {', '.join(names)}")
        lines.append("")
    return lines


def renderElementsByPackage(index: ModelIndex) -> list[str]:
    groups: dict[str, list[ModelElement]] = {}
    for element in index.semantic.values():
        if element.elemType in NESTED_TYPES | RELATION_TYPES:
            continue
        if element.elemType in {"Diagram", "Comment"} | PACKAGE_TYPES:
            continue
        owner = index.ownerOf(element)
        key = owner.name if owner is not None and owner.name else "(root)"
        groups.setdefault(key, []).append(element)

    if not groups:
        return []

    lines = ["## Elementi", ""]
    for packageName in sorted(groups, key=str.lower):
        lines += [f"### Package `{packageName}`", ""]
        members = sorted(groups[packageName], key=lambda e: (e.elemType, e.name.lower()))
        for element in members:
            lines += renderElement(index, element, level=4)
    return lines


def renderModelMarkdown(index: ModelIndex, sourcePath: Path, sourceHash: str) -> str:
    counts: dict[str, int] = {}
    for element in index.semantic.values():
        if element.elemType in NESTED_TYPES:
            continue
        counts[element.elemType] = counts.get(element.elemType, 0) + 1

    lines = [
        "---",
        f"source: {sourcePath.name}",
        f"sourceHash: {sourceHash}",
        "generator: gaphor2MD",
        "---",
        "",
        f"# Modello: {sourcePath.stem}",
        "",
        "Strato semantico generato automaticamente dal file Gaphor. "
        "Non modificare a mano: rigenerare con `gaphor2MD.py`.",
        "",
        "| Tipo | Conteggio |",
        "| --- | --- |",
    ]
    for elemType in sorted(counts):
        lines.append(f"| {elemType} | {counts[elemType]} |")
    lines.append("")

    lines += renderDiagramIndex(index)
    lines += renderElementsByPackage(index)
    lines += renderRelations(index)

    text = "\n".join(lines)
    return re.sub(r"\n{3,}", "\n\n", text).rstrip() + "\n"


# --------------------------------------------------------------------------- #
# I/O e CLI
# --------------------------------------------------------------------------- #


def hashFile(path: Path) -> str:
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return f"sha256:{digest[:16]}"


def readStoredHash(path: Path) -> str | None:
    if not path.exists():
        return None
    with path.open(encoding="utf-8") as handle:
        for lineNumber, line in enumerate(handle):
            if lineNumber > 10:
                break
            if line.startswith("sourceHash:"):
                return line.split(":", 1)[1].strip()
    return None


def collectInputs(paths: list[Path], recursive: bool) -> list[Path]:
    found: list[Path] = []
    for path in paths:
        if path.is_dir():
            pattern = "**/*.gaphor" if recursive else "*.gaphor"
            found.extend(sorted(path.glob(pattern)))
        elif path.is_file():
            found.append(path)
        else:
            print(f"attenzione: percorso inesistente {path}", file=sys.stderr)
    return found


def buildParser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Converte modelli Gaphor (.gaphor) in Markdown semantico.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("inputs", nargs="+", type=Path, help="file .gaphor o directory")
    parser.add_argument(
        "-o", "--outDir", type=Path, default=Path("docs/model"),
        help="directory di output (default: docs/model)",
    )
    parser.add_argument(
        "-r", "--recursive", action="store_true",
        help="cerca ricorsivamente nelle directory",
    )
    parser.add_argument(
        "--singleFile", action="store_true",
        help="concatena tutti i modelli in un unico MODEL.md",
    )
    parser.add_argument(
        "--force", action="store_true",
        help="rigenera anche se il sorgente non e' cambiato",
    )
    parser.add_argument(
        "--check", action="store_true",
        help="non scrive nulla; esce con 1 se il Markdown e' disallineato (uso in CI)",
    )
    parser.add_argument("-q", "--quiet", action="store_true", help="output minimale")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = buildParser().parse_args(argv)
    sources = collectInputs(args.inputs, args.recursive)
    if not sources:
        print("nessun file .gaphor trovato", file=sys.stderr)
        return 1

    def log(message: str) -> None:
        if not args.quiet:
            print(message)

    stale: list[Path] = []
    documents: list[tuple[Path, str]] = []

    for source in sources:
        sourceHash = hashFile(source)
        target = args.outDir / f"{source.stem}.md"
        if not args.singleFile and not args.force and not args.check:
            if readStoredHash(target) == sourceHash:
                log(f"= {target} (invariato)")
                continue
        try:
            elements = parseGaphorFile(source)
        except ValueError as exc:
            print(f"errore: {exc}", file=sys.stderr)
            return 2
        index = ModelIndex(elements)
        markdown = renderModelMarkdown(index, source, sourceHash)
        documents.append((source, markdown))

        if args.check:
            if not target.exists() or readStoredHash(target) != sourceHash:
                stale.append(target)
            continue
        if args.singleFile:
            continue
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(markdown, encoding="utf-8")
        log(f"+ {target} ({len(markdown.splitlines())} righe)")

    if args.check:
        if stale:
            for path in stale:
                print(f"disallineato: {path}", file=sys.stderr)
            return 1
        log("tutti i Markdown sono aggiornati")
        return 0

    if args.singleFile and documents:
        target = args.outDir / "MODEL.md"
        target.parent.mkdir(parents=True, exist_ok=True)
        merged = "\n\n---\n\n".join(text for _, text in documents)
        target.write_text(merged, encoding="utf-8")
        log(f"+ {target} ({len(merged.splitlines())} righe)")

    return 0


if __name__ == "__main__":
    sys.exit(main())
