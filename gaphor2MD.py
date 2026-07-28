#!/usr/bin/env python3
"""
gaphor2md - Estrae uno strato semantico Markdown dai modelli Gaphor (.gaphor).

Compatibile con il formato file v4 (Gaphor 3.x) e con il vecchio formato 2.x.

Il file .gaphor e' XML: ogni elemento del modello e' un tag il cui nome coincide
con la metaclasse UML. Le proprieta' seguono tre soli schemi:

    <name><val>Utente</val></name>                 -> valore scalare
    <owningPackage><ref refid="abc"/></owningPackage>  -> riferimento singolo
    <ownedAttribute><reflist><ref .../></reflist>  -> collezione di riferimenti

Differenze del formato v4 gestite qui:
  * gli elementi stanno dentro un wrapper <model>, non sotto la radice;
  * namespace per linguaggio di modellazione (UML:, Core:, ...);
  * le molteplicita' sono riferimenti a LiteralInteger / LiteralUnlimitedNatural;
  * i diagrammi sono metaclassi distinte (ClassDiagram, UseCaseDiagram, ...);
  * le descrizioni stanno nel campo `note` degli elementi.

Esempi:
    python gaphor2md.py modello.gaphor -o docs/model
    python gaphor2md.py -r src/ -o docs/model --singleFile
    python gaphor2md.py -r src/ -o docs/model --check   # per la CI
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
    "LiteralUnlimitedNatural",
    "LiteralBoolean",
    "ValueSpecification",
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

# Relazioni: tipo -> (chiavi origine, chiavi destinazione).
# Viene usata la prima chiave presente sull'elemento, cosi' lo stesso mapping
# copre nomi diversi tra le versioni di Gaphor.
RELATION_ENDS = {
    "Generalization": (("specific",), ("general",)),
    "Dependency": (("client",), ("supplier",)),
    "Usage": (("client",), ("supplier",)),
    "Realization": (("realizingClassifier", "client"), ("abstraction", "supplier")),
    "Abstraction": (("client",), ("supplier",)),
    "Substitution": (("substitutingClassifier", "client"), ("contract", "supplier")),
    "InterfaceRealization": (
        ("implementingClassifier", "implementatingClassifier", "client"),
        ("contract", "supplier"),
    ),
    "Include": (("includingCase",), ("addition",)),
    "Extend": (("extension",), ("extendedCase",)),
    "Transition": (("source",), ("target",)),
    "ControlFlow": (("source",), ("target",)),
    "ObjectFlow": (("source",), ("target",)),
    "PackageImport": (("importingNamespace",), ("importedPackage",)),
    "Message": (("sendEvent",), ("receiveEvent",)),
    "Connector": (("end",), ()),
    "Extension": (("ownedEnd",), ()),
    "CommunicationPath": ((), ()),
}

RELATION_TYPES = set(RELATION_ENDS) | {"Association"}

# Etichette per i diagrammi: chiavi sia per metaclasse (v4) sia per
# l'attributo diagramType (v2.x).
DIAGRAM_LABELS = {
    "Diagram": "generico",
    "ClassDiagram": "classi",
    "PackageDiagram": "package",
    "ComponentDiagram": "componenti",
    "DeploymentDiagram": "deployment",
    "ActivityDiagram": "attivita'",
    "SequenceDiagram": "sequenza",
    "CommunicationDiagram": "comunicazione",
    "StateMachineDiagram": "macchina a stati",
    "UseCaseDiagram": "casi d'uso",
    "ProfileDiagram": "profilo",
    "ObjectDiagram": "oggetti",
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

# Attributi che identificano il contenitore, in ordine di preferenza.
# v4 usa owningPackage / structuredClassifier; v2.x usava package / class_.
OWNER_KEYS = (
    "owningPackage",
    "package",
    "nestingPackage",
    "structuredClassifier",
    "class",
    "interface",
    "enumeration",
    "datatype",
    "owningClassifier",
    "ownerFormalParam",
    "namespace",
    "owner",
    "element",
)


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
        for key in keys:
            if key in self.refs:
                return self.refs[key]
            values = self.refLists.get(key)
            if values:
                return values[0]
        return None


def stripNamespace(tag: str) -> str:
    return tag.split("}", 1)[-1]


def normalizeName(tag: str) -> str:
    """`class_` -> `class`: Gaphor accoda un underscore alle keyword Python."""
    return stripNamespace(tag).rstrip("_")


def textOf(node: ET.Element) -> str:
    return "".join(node.itertext()).strip()


def iterModelNodes(root: ET.Element):
    """
    Restituisce i nodi degli elementi del modello.

    Nel formato v4 sono figli di un wrapper <model>; nel formato 2.x sono
    figli diretti della radice <gaphor>. Gestiamo entrambi senza dipendere
    dall'URI del namespace, cambiato tra le versioni.
    """
    wrappers = [child for child in root if stripNamespace(child.tag) == "model"]
    if wrappers:
        for wrapper in wrappers:
            yield from wrapper
    else:
        yield from root


def parseGaphorFile(path: Path) -> dict[str, ModelElement]:
    """Legge un file .gaphor e restituisce la mappa id -> ModelElement."""
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        raise ValueError(f"XML non valido in {path}: {exc}") from exc

    elements: dict[str, ModelElement] = {}
    for node in iterModelNodes(root):
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
    if "matrix" in element.values:
        return True
    if element.elemType.endswith(("Item", "Line", "Box", "Ellipse")):
        return True
    return "diagram" in element.refs and "subject" in element.refs


def isDiagram(element: ModelElement) -> bool:
    return element.elemType == "Diagram" or element.elemType.endswith("Diagram")


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
            eid: el for eid, el in self.semantic.items() if isDiagram(el)
        }
        self.associationEnds = self._indexAssociationEnds()
        self.commentsByTarget = self._indexComments()
        self.diagramMembership = self._indexDiagramMembership()

    def _indexAssociationEnds(self) -> set[str]:
        """Property che fanno da estremo di un'associazione: non sono attributi."""
        ends: set[str] = set()
        for element in self.semantic.values():
            if element.elemType != "Association":
                continue
            ends.update(element.refLists.get("memberEnd", []))
            ends.update(element.refLists.get("ownedEnd", []))
        for element in self.semantic.values():
            if element.elemType == "Property" and (
                "association" in element.refs or "owningAssociation" in element.refs
            ):
                ends.add(element.elemId)
        return ends

    def _indexComments(self) -> dict[str, list[str]]:
        out: dict[str, list[str]] = {}
        for element in self.semantic.values():
            if element.elemType != "Comment":
                continue
            body = (element.values.get("body") or "").strip()
            if not body:
                continue
            for targetId in element.refLists.get("annotatedElement", []):
                out.setdefault(targetId, []).append(body)
        return out

    def _indexDiagramMembership(self) -> dict[str, list[str]]:
        """diagramId -> id degli elementi semantici presenti sul diagramma."""
        out: dict[str, list[str]] = {did: [] for did in self.diagrams}
        for presentation in self.presentations.values():
            subjectId = presentation.refs.get("subject")
            if not subjectId:
                continue
            diagramId = presentation.refs.get("diagram")
            if diagramId not in out:
                # Formati piu' vecchi: e' il diagramma a elencare le presentazioni.
                for did, diagram in self.diagrams.items():
                    if presentation.elemId in diagram.refLists.get(
                        "ownedPresentation", []
                    ):
                        diagramId = did
                        break
            if diagramId in out and subjectId not in out[diagramId]:
                out[diagramId].append(subjectId)
        return out

    def get(self, elemId: str | None) -> ModelElement | None:
        return self.elements.get(elemId) if elemId else None

    def nameOf(self, elemId: str | None, fallback: str = "?", depth: int = 0) -> str:
        element = self.get(elemId)
        if element is None:
            return fallback
        if element.name:
            return element.name
        # Una relazione senza nome (es. una dipendenza che punta a un'altra
        # dipendenza) viene descritta tramite i suoi estremi.
        if depth < 2 and element.elemType in RELATION_TYPES:
            return f"{element.elemType}[{relationLabel(self, element, depth + 1)}]"
        return f"({element.elemType.lower()} anonimo)"

    def literalValue(self, elemId: str | None) -> str:
        """Valore di un LiteralInteger / LiteralUnlimitedNatural (formato v4)."""
        element = self.get(elemId)
        if element is None:
            return ""
        return (element.values.get("value") or element.values.get("name") or "").strip()

    def boundOf(self, element: ModelElement, key: str) -> str | None:
        """
        Estremo di molteplicita'. In v4 e' un riferimento a un Literal*,
        in 2.x era un valore inline.
        """
        if key in element.refs:
            value = self.literalValue(element.refs[key])
            return value or None
        return element.values.get(key)

    def typeNameOf(self, element: ModelElement) -> str:
        """Tipo di una Property/Parameter: per riferimento o come stringa libera."""
        typed = self.get(element.refs.get("type"))
        if typed is not None and typed.name:
            return typed.name
        return (element.values.get("typeValue") or "").strip()

    def ownerOf(self, element: ModelElement) -> ModelElement | None:
        """Risale la catena di contenimento fino al primo Package."""
        seen: set[str] = set()
        current: ModelElement | None = element
        while current is not None and current.elemId not in seen:
            seen.add(current.elemId)
            ownerId = current.firstRef(*OWNER_KEYS)
            owner = self.get(ownerId)
            if owner is None:
                return None
            if owner.elemType in PACKAGE_TYPES:
                return owner
            current = owner
        return None

    def packagePath(self, package: ModelElement | None) -> str:
        """Nome qualificato del package: `App PT / Domain Model / Exercises`."""
        if package is None:
            return "(root)"
        parts: list[str] = []
        seen: set[str] = set()
        current: ModelElement | None = package
        while current is not None and current.elemId not in seen:
            seen.add(current.elemId)
            parts.append(current.name or "(anonimo)")
            parent = self.get(current.firstRef("owningPackage", "nestingPackage", "package"))
            current = parent if parent is not None and parent.elemType in PACKAGE_TYPES else None
        return " / ".join(reversed(parts))

    def descriptionsFor(self, element: ModelElement) -> list[str]:
        """Note dell'elemento (v4) piu' eventuali Comment collegati."""
        out: list[str] = []
        note = (element.values.get("note") or "").strip()
        if note:
            out.append(note)
        out.extend(self.commentsByTarget.get(element.elemId, []))
        return out


# --------------------------------------------------------------------------- #
# Rendering
# --------------------------------------------------------------------------- #


def multiplicityOf(index: ModelIndex, element: ModelElement) -> str:
    lower = index.boundOf(element, "lowerValue")
    upper = index.boundOf(element, "upperValue")
    if lower is None and upper is None:
        return ""
    if lower is not None and lower == upper:
        return lower
    return f"{lower or '0'}..{upper or '*'}"


def visibilityOf(element: ModelElement) -> str:
    return VISIBILITY_SYMBOLS.get(element.values.get("visibility", "public"), "+")


def escapePipes(text: str) -> str:
    return text.replace("|", "\\|")


def flattenText(text: str, limit: int = 300) -> str:
    """Testo su una riga: le tabelle Markdown non tollerano gli a capo."""
    collapsed = re.sub(r"\s+", " ", text).strip()
    if len(collapsed) > limit:
        collapsed = collapsed[: limit - 1].rstrip() + "…"
    return escapePipes(collapsed)


def renderAttributes(index: ModelIndex, owner: ModelElement) -> list[str]:
    rows: list[str] = []
    for propId in owner.refLists.get("ownedAttribute", []):
        prop = index.get(propId)
        if prop is None or prop.elemType != "Property":
            continue
        if propId in index.associationEnds:
            continue  # compare nella tabella delle relazioni
        typeName = index.typeNameOf(prop) or "—"
        mult = multiplicityOf(index, prop)
        flags = [
            label
            for key, label in (
                ("isStatic", "static"),
                ("isDerived", "derived"),
                ("isReadOnly", "readonly"),
            )
            if prop.values.get(key) == "1"
        ]
        rows.append(
            "| {vis} | {name} | {type} | {mult} | {default} | {flags} |".format(
                vis=visibilityOf(prop),
                name=escapePipes(prop.name or "—"),
                type=escapePipes(typeName),
                mult=mult or "—",
                default=escapePipes(prop.values.get("defaultValue", "")) or "—",
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
        flags = [
            label
            for key, label in (("isAbstract", "abstract"), ("isStatic", "static"))
            if operation.values.get(key) == "1"
        ]
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
    for description in index.descriptionsFor(element):
        lines += ["", description.strip()]

    lines += renderAttributes(index, element)
    lines += renderOperations(index, element)
    lines += renderLiterals(index, element)

    if lines[-1] != "":
        lines.append("")
    return lines


def relationLabel(index: ModelIndex, element: ModelElement, depth: int = 0) -> str:
    """Etichetta leggibile per una relazione, che tipicamente non ha nome."""
    if element.elemType == "Association":
        ends = [index.get(pid) for pid in element.refLists.get("memberEnd", [])]
        names = [index.typeNameOf(e) or "?" for e in ends if e is not None]
        label = " — ".join(names[:2]) if len(names) >= 2 else "?"
    else:
        sourceKeys, targetKeys = RELATION_ENDS.get(element.elemType, ((), ()))
        source = (
            index.nameOf(element.firstRef(*sourceKeys), "?", depth) if sourceKeys else "?"
        )
        target = (
            index.nameOf(element.firstRef(*targetKeys), "?", depth) if targetKeys else "?"
        )
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
        mult = multiplicityOf(index, end)
        label = classifier
        if mult:
            label += f" [{mult}]"
        if end.name:
            label += f" ({end.name})"
        descriptions.append(label)

    details = []
    if association.name:
        details.append(f"nome: {association.name}")
    for end in ends[:2]:
        aggregation = AGGREGATION_SYMBOLS.get(end.values.get("aggregation", ""))
        if aggregation:
            details.append(f"{aggregation} lato {index.typeNameOf(end) or '?'}")

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
        note = (element.values.get("note") or "").strip()
        if note:
            details.append(flattenText(note, 120))
        rows.append(
            "| {kind} | {a} | {b} | {details} |".format(
                kind=element.elemType,
                a=escapePipes(index.nameOf(sourceId, "—", 1)),
                b=escapePipes(index.nameOf(targetId, "—", 1)),
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
        label = DIAGRAM_LABELS.get(diagram.elemType) or DIAGRAM_LABELS.get(
            rawType, rawType or "generico"
        )
        lines.append(f"### {diagram.name or '(diagramma senza nome)'} — *{label}*")
        for description in index.descriptionsFor(diagram):
            lines += ["", description.strip()]
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
        if element.elemType in NESTED_TYPES | RELATION_TYPES | PACKAGE_TYPES:
            continue
        if element.elemType == "Comment" or isDiagram(element):
            continue
        key = index.packagePath(index.ownerOf(element))
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
        "generator: gaphor2md",
        "---",
        "",
        f"# Modello: {sourcePath.stem}",
        "",
        "Strato semantico generato automaticamente dal file Gaphor. "
        "Non modificare a mano: rigenerare con `gaphor2md.py`.",
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
    parser.add_argument(
        "--stats", action="store_true",
        help="stampa un riepilogo diagnostico del parsing",
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
        if not args.singleFile and not args.force and not args.check and not args.stats:
            if readStoredHash(target) == sourceHash:
                log(f"= {target} (invariato)")
                continue
        try:
            elements = parseGaphorFile(source)
        except ValueError as exc:
            print(f"errore: {exc}", file=sys.stderr)
            return 2

        if not elements:
            print(
                f"attenzione: nessun elemento trovato in {source} — "
                "formato non riconosciuto?",
                file=sys.stderr,
            )

        index = ModelIndex(elements)
        markdown = renderModelMarkdown(index, source, sourceHash)
        documents.append((source, markdown))

        if args.stats:
            print(f"--- {source} ---")
            print(f"  elementi totali    : {len(elements)}")
            print(f"  di presentazione   : {len(index.presentations)}")
            print(f"  semantici          : {len(index.semantic)}")
            print(f"  diagrammi          : {len(index.diagrams)}")
            print(f"  end di associazione: {len(index.associationEnds)}")

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
