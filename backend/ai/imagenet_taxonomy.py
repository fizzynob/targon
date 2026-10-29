import json
from pathlib import Path
from typing import Dict, List, Tuple

# Load full 1000 ImageNet simple labels if available locally
_LABELS_PATH = Path(__file__).resolve().parent / "imagenet_labels.json"
_ALL_IMAGENET_LABELS: List[str] = []
try:
    if _LABELS_PATH.exists():
        with open(_LABELS_PATH, "r", encoding="utf-8") as _f:
            _ALL_IMAGENET_LABELS = json.load(_f)
except Exception:
    _ALL_IMAGENET_LABELS = []

# Specific ImageNet index mappings for accurate hierarchical categorization
CAT_CLASS_MAP: Dict[int, str] = {
    281: "tabby cat",
    282: "tiger cat",
    283: "persian cat",
    284: "siamese cat",
    285: "egyptian cat",
    286: "cougar",
    287: "lynx",
}

DOG_BREED_HIGHLIGHTS: Dict[int, str] = {
    151: "chihuahua",
    152: "japanese spaniel",
    153: "maltese",
    154: "pekinese",
    155: "shih-tzu",
    158: "toy terrier",
    162: "beagle",
    172: "whippet",
    207: "golden retriever",
    208: "labrador retriever",
    230: "shetland sheepdog",
    231: "collie",
    232: "border collie",
    234: "rottweiler",
    235: "german shepherd",
    248: "eskimo dog",
    249: "malamute",
    250: "siberian husky",
    254: "pug",
    258: "samoyed",
    259: "pomeranian",
    263: "pembroke corgi",
    264: "cardigan corgi",
}

LANDSCAPE_CLASS_MAP: Dict[int, Tuple[str, List[str]]] = {
    970: ("mountain", ["nature", "landscape", "outdoor", "alps"]),
    971: ("macro", ["macro", "abstract", "bubble"]),
    972: ("cliff", ["nature", "landscape", "outdoor", "rock"]),
    973: ("ocean", ["nature", "ocean", "underwater", "coral reef"]),
    974: ("landscape", ["nature", "landscape", "outdoor", "geyser"]),
    975: ("lakeside", ["nature", "landscape", "water", "outdoor", "lake"]),
    976: ("landscape", ["nature", "landscape", "coast", "outdoor", "promontory"]),
    977: ("beach", ["nature", "beach", "coast", "outdoor", "sandbar"]),
    978: ("seashore", ["nature", "beach", "ocean", "coast", "outdoor"]),
    979: ("valley", ["nature", "landscape", "outdoor", "scenic"]),
    980: ("mountain", ["nature", "landscape", "mountain", "outdoor", "volcano"]),
}


def _get_raw_label(idx: int) -> str:
    if 0 <= idx < len(_ALL_IMAGENET_LABELS):
        return _ALL_IMAGENET_LABELS[idx].lower().strip()
    return ""


def classify_imagenet_idx(idx: int) -> Tuple[str, List[Tuple[str, str]]]:
    """
    Given an ImageNet class index (0..999), returns:
      (primary_subject_category, list of (tag_name, tag_type))
    where tag_type is 'category' | 'scene' | 'attribute'.
    Fully maps ALL 1000 ImageNet categories into fine-grained semantic categories,
    never falling back to vague 'object' tags.
    """
    tags: List[Tuple[str, str]] = []
    raw_label = _get_raw_label(idx)

    # 1. Domestic & wild cats (281..293)
    if 281 <= idx <= 285:
        primary_cat = "cat"
        tags.append(("cat", "category"))
        tags.append(("pet", "category"))
        tags.append(("feline", "category"))
        tags.append(("animal", "category"))
        subtype = CAT_CLASS_MAP.get(idx)
        if subtype and subtype != "egyptian cat":
            tags.append((subtype, "attribute"))
        elif raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    if 286 <= idx <= 293:
        primary_cat = "cat"
        tags.append(("cat", "category"))
        tags.append(("feline", "category"))
        tags.append(("wildlife", "category"))
        tags.append(("animal", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 2. Dogs (151..268) and wolves/foxes (269..280)
    if 151 <= idx <= 268:
        primary_cat = "dog"
        tags.append(("dog", "category"))
        tags.append(("pet", "category"))
        tags.append(("canine", "category"))
        tags.append(("animal", "category"))
        if idx in DOG_BREED_HIGHLIGHTS:
            tags.append((DOG_BREED_HIGHLIGHTS[idx], "attribute"))
        elif raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    if 269 <= idx <= 280:
        primary_cat = "dog"
        tags.append(("canine", "category"))
        tags.append(("wildlife", "category"))
        tags.append(("animal", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 3. Birds (7..24, 80..100, 127..146)
    if (7 <= idx <= 24) or (80 <= idx <= 100) or (127 <= idx <= 146):
        primary_cat = "bird"
        tags.append(("bird", "category"))
        tags.append(("animal", "category"))
        tags.append(("nature", "scene"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 4. Fish, Sharks & Aquatic (0..6, 147..150, 389..397)
    if (0 <= idx <= 6) or (147 <= idx <= 150) or (389 <= idx <= 397):
        primary_cat = "animal"
        tags.append(("marine life", "category"))
        tags.append(("aquatic", "category"))
        tags.append(("animal", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 5. Amphibians & Reptiles (25..68)
    if 25 <= idx <= 68:
        primary_cat = "animal"
        tags.append(("reptile" if idx >= 33 else "amphibian", "category"))
        tags.append(("wildlife", "category"))
        tags.append(("animal", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 6. Insects, Arachnids & Invertebrates (69..79, 101..126, 300..326)
    if (69 <= idx <= 79) or (101 <= idx <= 126) or (300 <= idx <= 326):
        primary_cat = "animal"
        tags.append(("insect", "category"))
        tags.append(("nature", "category"))
        tags.append(("macro", "scene"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 7. Other Wildlife Mammals (294..299, 327..388)
    if (294 <= idx <= 299) or (327 <= idx <= 388):
        primary_cat = "animal"
        tags.append(("animal", "category"))
        tags.append(("wildlife", "category"))
        tags.append(("mammal", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 8. Landscapes & Geology (970..980)
    if idx in LANDSCAPE_CLASS_MAP:
        primary_cat, scene_list = LANDSCAPE_CLASS_MAP[idx]
        for s in scene_list:
            t_type = "category" if s in ("nature", "landscape", "beach", "mountain", "ocean") else "scene"
            tags.append((s, t_type))
        return primary_cat, tags

    # 9. Flowers, Trees & Botanical (981..999)
    if 981 <= idx <= 999:
        primary_cat = "nature"
        tags.append(("nature", "category"))
        tags.append(("botanical", "category"))
        tags.append(("outdoor", "scene"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 10. Food, Produce & Dining (923..969)
    if 923 <= idx <= 969:
        primary_cat = "food"
        tags.append(("food", "category"))
        tags.append(("culinary", "scene"))
        tags.append(("dining", "scene"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 11. Vehicles & Transport
    vehicle_indices = {
        403, 404, 405, 407, 408, 428, 436, 444, 468, 475, 479, 510, 511, 555, 561, 569,
        573, 575, 581, 586, 595, 603, 609, 612, 627, 654, 656, 660, 661, 665, 670, 671,
        675, 690, 705, 717, 724, 734, 751, 757, 779, 780, 785, 802, 803, 812, 814, 817,
        820, 829, 833, 847, 864, 866, 867, 870, 874, 880, 895, 914
    }
    if idx in vehicle_indices or any(
        kw in raw_label for kw in ("car", "truck", "bus", "train", "bike", "bicycle", "ship", "boat", "plane", "airliner", "wagon", "cart", "scooter", "tractor")
    ):
        primary_cat = "vehicle"
        tags.append(("vehicle", "category"))
        tags.append(("transport", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 12. Musical Instruments
    instrument_indices = {
        401, 402, 420, 441, 486, 494, 513, 541, 546, 558, 563, 578, 579, 593, 594, 642,
        645, 683, 699, 701, 702, 776, 777, 822, 875, 881, 889
    }
    if idx in instrument_indices or any(
        kw in raw_label for kw in ("guitar", "piano", "violin", "cello", "flute", "drum", "sax", "trumpet", "harp", "organ", "accordion", "banjo", "harmonica")
    ):
        primary_cat = "instrument"
        tags.append(("instrument", "category"))
        tags.append(("music", "scene"))
        tags.append(("audio", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 13. Architecture, Historic Structures & Landmarks
    arch_indices = {
        425, 438, 449, 460, 483, 497, 498, 500, 523, 525, 536, 538, 576, 580, 598, 600,
        624, 629, 649, 650, 663, 668, 679, 698, 706, 708, 716, 727, 743, 762, 788, 819,
        821, 832, 839, 853, 858, 862, 873, 897, 900, 912, 915
    }
    if idx in arch_indices or any(
        kw in raw_label for kw in ("castle", "palace", "monastery", "church", "mosque", "dome", "bridge", "arch", "tower", "lighthouse", "barn", "prison", "fountain", "roof", "fence", "wall", "shop", "bakery", "restaurant", "library", "cinema", "theater")
    ):
        primary_cat = "architecture"
        tags.append(("architecture", "category"))
        tags.append(("structure", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 14. Electronics, Cameras & Computing
    tech_indices = {
        487, 491, 508, 527, 528, 530, 531, 548, 590, 605, 620, 651, 664, 673, 681, 688,
        707, 720, 732, 745, 759, 760, 782, 844, 845, 851, 878, 879, 892
    }
    if idx in tech_indices or any(
        kw in raw_label for kw in ("computer", "laptop", "notebook", "monitor", "screen", "television", "keyboard", "mouse", "phone", "camera", "projector", "radio", "speaker", "microphone", "printer", "clock", "watch", "binoculars", "telescope")
    ):
        primary_cat = "electronics"
        tags.append(("electronics", "category"))
        tags.append(("technology", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 15. Armor, Historical & Military
    if any(
        kw in raw_label for kw in ("cuirass", "breastplate", "shield", "buckler", "pickelhaube", "chain mail", "scabbard", "sword", "cannon", "projectile", "missile", "rifle", "revolver", "holster", "bow", "torch")
    ):
        primary_cat = "historical art"
        tags.append(("historical art", "category"))
        tags.append(("artwork", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 16. Clothing, Apparel & Fashion
    if any(
        kw in raw_label for kw in ("suit", "tie", "gown", "vestment", "abaya", "kimono", "coat", "shirt", "sweatshirt", "jersey", "cardigan", "jeans", "skirt", "bikini", "trunks", "pajama", "sock", "hat", "cap", "helmet", "bonnet", "wig", "mask", "sunglass", "shoe", "sandal", "clog", "boot", "purse", "backpack", "bag", "wallet", "umbrella", "apron")
    ):
        primary_cat = "apparel"
        tags.append(("apparel", "category"))
        tags.append(("fashion", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 17. Furniture, Home Decor & Interior
    indoor_indices = {423, 526, 532, 554, 559, 765, 831, 846, 857}
    if idx in indoor_indices or any(
        kw in raw_label for kw in ("chair", "throne", "couch", "sofa", "bed", "crib", "desk", "table", "bookcase", "cabinet", "wardrobe", "bench", "lamp", "chandelier", "curtain", "shade", "pillow", "quilt", "rug", "vase", "pitcher", "goblet", "bottle", "glass", "cup", "mug", "tub", "shower", "toilet", "stove", "fireplace")
    ):
        primary_cat = "interior"
        tags.append(("interior", "category"))
        tags.append(("indoor", "scene"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 18. Sports & Recreation
    if any(
        kw in raw_label for kw in ("ball", "ski", "snowboard", "sled", "surfboard", "racket", "barbell", "dumbbell", "gym", "parachute", "tent")
    ):
        primary_cat = "sports & recreation"
        tags.append(("sports & recreation", "category"))
        tags.append(("athletics", "scene"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 19. Books, Print & Media
    if any(
        kw in raw_label for kw in ("book", "jacket", "menu", "sign", "envelope", "binder", "pen", "pencil", "puzzle")
    ):
        primary_cat = "document"
        tags.append(("document", "category"))
        tags.append(("media & print", "category"))
        if raw_label:
            tags.append((raw_label, "attribute"))
        return primary_cat, tags

    # 20. Remaining Everyday Items, Tools & Equipment (never emit 'object'!)
    primary_cat = "equipment"
    if raw_label:
        tags.append((raw_label, "attribute"))
    tags.append(("equipment", "category"))
    tags.append(("everyday item", "attribute"))
    return primary_cat, tags
