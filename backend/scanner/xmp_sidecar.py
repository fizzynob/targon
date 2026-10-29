import os
import xml.etree.ElementTree as ET
from xml.sax.saxutils import escape as xml_escape
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple


def get_xmp_path(image_path: str, prefer_suffix: bool = True) -> Path:
    """
    Returns the path to the XMP sidecar file for an image.
    Checks for `image.xmp` or `image.jpg.xmp`.
    Default written format is `image.xmp` (or `image.jpg.xmp` if prefer_suffix is True).
    """
    p = Path(image_path)
    # Check if an existing sidecar is on disk
    cand1 = p.with_name(f"{p.name}.xmp")
    cand2 = p.with_suffix(".xmp")
    if cand1.exists():
        return cand1
    if cand2.exists():
        return cand2
    return cand1 if prefer_suffix else cand2


def build_xmp_xml(
    filename: str,
    description: Optional[str],
    tags: List[Dict[str, Any]],
    root_systems: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generates standard Adobe XMP metadata XML conforming to Dublin Core and Adobe Lightroom
    hierarchical subject specifications.
    """
    # Extract flat tags
    flat_tags = [t.get("name", "").strip() for t in tags if t.get("name")]
    # Dedup while preserving order
    seen = set()
    unique_tags = []
    for ft in flat_tags:
        if ft.lower() not in seen:
            seen.add(ft.lower())
            unique_tags.append(ft)

    # Build hierarchical subject tags (e.g., Animal|Cat|Blu, Scene|Indoor, Drive|C:|...)
    hierarchical_tags = []
    if root_systems:
        tr = root_systems.get("type_root", {})
        if tr:
            st = tr.get("super_type")
            cat = tr.get("category")
            spec = tr.get("specific")
            if st and cat and spec:
                hierarchical_tags.append(f"{st}|{cat}|{spec}")
                hierarchical_tags.append(f"{st}|{cat}")

        dr = root_systems.get("drive_root", {})
        if dr:
            drv = dr.get("drive", "C:")
            fld = dr.get("folder", "Root")
            sub = dr.get("subfolder", "Root")
            hierarchical_tags.append(f"Drive|{drv}|{fld}|{sub}")

        dvr = root_systems.get("device_root", {})
        if dvr:
            dev = dvr.get("device", "Unknown")
            fmt = dvr.get("image_type", "JPEG")
            hierarchical_tags.append(f"Device|{dev}|{fmt}")

    # XML Construction (properly XML-escaped so '&', '<', '>' in tags/descriptions never corrupt XML)
    bag_items = "\n     ".join(f"<rdf:li>{xml_escape(str(t))}</rdf:li>" for t in unique_tags)
    hier_items = "\n     ".join(f"<rdf:li>{xml_escape(str(h))}</rdf:li>" for h in hierarchical_tags)
    desc_val = xml_escape(str(description or ""))
    safe_filename = xml_escape(str(filename))

    type_meta = ""
    if root_systems:
        tr = root_systems.get("type_root", {})
        dr = root_systems.get("drive_root", {})
        dvr = root_systems.get("device_root", {})
        type_meta = f"""
   <targon:identity>{xml_escape(str(tr.get("specific", "")))}</targon:identity>
   <targon:category>{xml_escape(str(tr.get("category", "")))}</targon:category>
   <targon:superType>{xml_escape(str(tr.get("super_type", "")))}</targon:superType>
   <targon:driveRoot>{xml_escape(str(dr.get("drive", "")))}</targon:driveRoot>
   <targon:folder>{xml_escape(str(dr.get("folder", "")))}</targon:folder>
   <targon:subfolder>{xml_escape(str(dr.get("subfolder", "")))}</targon:subfolder>
   <targon:device>{xml_escape(str(dvr.get("device", "")))}</targon:device>
   <targon:captureDate>{xml_escape(str(dvr.get("capture_date", "")))}</targon:captureDate>
   <targon:imageFormat>{xml_escape(str(dvr.get("image_type", "")))}</targon:imageFormat>"""

    xmp_content = f"""<?xml version="1.0" encoding="UTF-8"?>
<x:xmpmeta xmlns:x="adobe:ns:meta/" x:xmptk="Targon AI 1.0">
 <rdf:RDF xmlns:rdf="http://www.w3.org/1999/02/22-rdf-syntax-ns#">
  <rdf:Description rdf:about=""
    xmlns:dc="http://purl.org/dc/elements/1.1/"
    xmlns:lr="http://ns.adobe.com/lightroom/1.0/"
    xmlns:xmp="http://ns.adobe.com/xap/1.0/"
    xmlns:targon="http://targon.ai/1.0/">
   <dc:title>
    <rdf:Alt>
     <rdf:li xml:lang="x-default">{safe_filename}</rdf:li>
    </rdf:Alt>
   </dc:title>
   <dc:description>
    <rdf:Alt>
     <rdf:li xml:lang="x-default">{desc_val}</rdf:li>
    </rdf:Alt>
   </dc:description>
   <dc:subject>
    <rdf:Bag>
     {bag_items}
    </rdf:Bag>
   </dc:subject>
   <lr:hierarchicalSubject>
    <rdf:Bag>
     {hier_items}
    </rdf:Bag>
   </lr:hierarchicalSubject>{type_meta}
  </rdf:Description>
 </rdf:RDF>
</x:xmpmeta>
"""
    return xmp_content


def write_xmp_sidecar(
    image_path: str,
    description: Optional[str],
    tags: List[Dict[str, Any]],
    root_systems: Optional[Dict[str, Any]] = None,
) -> Path:
    """
    Writes or updates the .xmp sidecar file on disk alongside the image.
    """
    xmp_path = get_xmp_path(image_path)
    xmp_path.parent.mkdir(parents=True, exist_ok=True)
    xml_data = build_xmp_xml(
        filename=Path(image_path).name,
        description=description,
        tags=tags,
        root_systems=root_systems,
    )
    with open(xmp_path, "w", encoding="utf-8") as f:
        f.write(xml_data)
    return xmp_path


def read_xmp_sidecar(image_path: str) -> Optional[Dict[str, Any]]:
    """
    Reads an existing .xmp sidecar file and extracts tags, description, and custom root metadata.
    """
    xmp_path = get_xmp_path(image_path)
    if not xmp_path.exists():
        return None

    try:
        tree = ET.parse(xmp_path)
        root = tree.getroot()

        # Namespaces
        ns = {
            "rdf": "http://www.w3.org/1999/02/22-rdf-syntax-ns#",
            "dc": "http://purl.org/dc/elements/1.1/",
            "lr": "http://ns.adobe.com/lightroom/1.0/",
            "targon": "http://targon.ai/1.0/",
        }

        tags: List[str] = []
        # Find dc:subject tags
        for li in root.findall(".//dc:subject//rdf:Bag/rdf:li", ns):
            if li.text and li.text.strip():
                tags.append(li.text.strip())

        # Find lr:hierarchicalSubject
        hierarchical: List[str] = []
        for li in root.findall(".//lr:hierarchicalSubject//rdf:Bag/rdf:li", ns):
            if li.text and li.text.strip():
                hierarchical.append(li.text.strip())

        # Description
        desc_node = root.find(".//dc:description//rdf:Alt/rdf:li", ns)
        description = desc_node.text.strip() if desc_node is not None and desc_node.text else None

        # Targon custom elements
        identity_node = root.find(".//targon:identity", ns)
        identity = identity_node.text.strip() if identity_node is not None and identity_node.text else None

        cat_node = root.find(".//targon:category", ns)
        category = cat_node.text.strip() if cat_node is not None and cat_node.text else None

        return {
            "xmp_path": str(xmp_path),
            "tags": tags,
            "hierarchical_tags": hierarchical,
            "description": description,
            "identity": identity,
            "category": category,
        }
    except Exception:
        return None
