import urllib.request
from pathlib import Path
from typing import List, Tuple, Dict, Any, Optional
import numpy as np
import onnxruntime as ort
from PIL import Image
from tokenizers import Tokenizer

VISION_MODEL_URL = (
    "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main/onnx/vision_model_quantized.onnx"
)
TEXT_MODEL_URL = (
    "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main/onnx/text_model_quantized.onnx"
)
TOKENIZER_URL = (
    "https://huggingface.co/Xenova/clip-vit-base-patch32/resolve/main/tokenizer.json"
)

# Standard CLIP normalization constants
CLIP_MEAN = np.array([0.48145466, 0.4578275, 0.40821073], dtype=np.float32)
CLIP_STD = np.array([0.26862954, 0.26130258, 0.27577711], dtype=np.float32)

# Multi-Prompt Ensembled Hierarchical Concept Taxonomy
# Each entry:
#   (specific_label, category, super_type, is_illustration, prompts, extra_tags)
CLIP_CONCEPT_TAXONOMY: List[Tuple[str, str, str, bool, List[str], List[Tuple[str, str]]]] = [
    # --- 1. People, Portraits & Selfies ---
    (
        "Webcam Portrait",
        "person",
        "People",
        False,
        [
            "a dark indoor webcam photo of a person wearing glasses",
            "a low light selfie photo of a person in a dark room",
            "a close-up webcam capture of a person with hand near face",
        ],
        [("person", "category"), ("portrait", "scene"), ("webcam portrait", "attribute"), ("glasses", "attribute")],
    ),
    (
        "Beach Portrait",
        "person",
        "People",
        False,
        [
            "a photo of a person on a sandy beach taking a picture with a smartphone",
            "a person at the beach at sunset holding a phone and wearing a watch",
            "a back or side view photo of a person at the ocean beach",
        ],
        [("person", "category"), ("beach", "scene"), ("smartphone", "attribute"), ("beach portrait", "attribute")],
    ),
    (
        "Portrait",
        "person",
        "People",
        False,
        [
            "a portrait photograph of a person",
            "a close-up photo of a man, woman, boy, or girl",
            "a clear photograph of a human face",
        ],
        [("person", "category"), ("portrait", "scene"), ("human face", "attribute")],
    ),
    (
        "Selfie",
        "person",
        "People",
        False,
        [
            "a close-up selfie photo of a person",
            "a mirror selfie or front-camera smartphone photo of a person",
        ],
        [("person", "category"), ("selfie", "scene"), ("portrait", "scene")],
    ),
    (
        "Group Photo",
        "person",
        "People",
        False,
        [
            "a group photo of friends or family posing together",
            "several people smiling or standing together in a photograph",
        ],
        [("person", "category"), ("people", "category"), ("group photo", "scene")],
    ),
    (
        "Crowd & Event",
        "person",
        "People",
        False,
        [
            "a photo of a large crowd of people at a concert, festival, or event",
            "an audience or festival crowd gathering",
        ],
        [("people", "category"), ("crowd", "scene"), ("event", "scene")],
    ),

    # --- 2. Domestic Pets & Animals ---
    (
        "Russian Blue Cat",
        "cat",
        "Animal",
        False,
        [
            "a photo of a Russian Blue cat with slate-gray fur and green eyes",
            "a domestic short-haired gray Russian Blue cat sitting indoors or outdoors",
            "a close-up portrait of a gray Russian Blue cat",
        ],
        [("cat", "category"), ("pet", "category"), ("feline", "category"), ("animal", "category"), ("russian blue", "attribute"), ("slate-gray coat", "attribute")],
    ),
    (
        "Ginger Tabby Cat",
        "cat",
        "Animal",
        False,
        [
            "a photo of an orange ginger tabby cat",
            "a close-up photo of an orange striped domestic cat",
            "a marmalade orange cat sitting in a garden or indoors",
        ],
        [("cat", "category"), ("pet", "category"), ("feline", "category"), ("animal", "category"), ("ginger cat", "attribute"), ("tabby cat", "attribute"), ("orange ginger coat", "attribute")],
    ),
    (
        "Striped Tabby Cat",
        "cat",
        "Animal",
        False,
        [
            "a photo of a brown or gray striped tabby cat",
            "a domestic tabby cat with striped fur markings",
        ],
        [("cat", "category"), ("pet", "category"), ("feline", "category"), ("animal", "category"), ("tabby cat", "attribute")],
    ),
    (
        "Siamese Cat",
        "cat",
        "Animal",
        False,
        [
            "a photo of a Siamese cat with dark pointed ears and blue eyes",
            "a cream and dark brown Siamese domestic cat",
        ],
        [("cat", "category"), ("pet", "category"), ("feline", "category"), ("animal", "category"), ("siamese cat", "attribute")],
    ),
    (
        "Black Cat",
        "cat",
        "Animal",
        False,
        [
            "a photo of a sleek black domestic cat",
            "a close-up of a black cat with bright eyes",
        ],
        [("cat", "category"), ("pet", "category"), ("feline", "category"), ("animal", "category"), ("black cat", "attribute")],
    ),
    (
        "White Cat",
        "cat",
        "Animal",
        False,
        [
            "a photo of a fluffy white domestic cat",
            "a pure white cat indoors or outdoors",
        ],
        [("cat", "category"), ("pet", "category"), ("feline", "category"), ("animal", "category"), ("white cat", "attribute")],
    ),
    (
        "Domestic Cat",
        "cat",
        "Animal",
        False,
        [
            "a photo of a cute domestic pet cat or kitten",
            "a house cat relaxing on furniture or outdoors",
        ],
        [("cat", "category"), ("pet", "category"), ("feline", "category"), ("animal", "category")],
    ),
    (
        "Golden Retriever",
        "dog",
        "Animal",
        False,
        [
            "a photo of a golden retriever dog outdoors in a park",
            "a happy golden retriever pet dog with golden fur",
        ],
        [("dog", "category"), ("pet", "category"), ("canine", "category"), ("animal", "category"), ("golden retriever", "attribute")],
    ),
    (
        "German Shepherd",
        "dog",
        "Animal",
        False,
        [
            "a photo of a German Shepherd dog",
            "an alert German Shepherd canine outdoors",
        ],
        [("dog", "category"), ("pet", "category"), ("canine", "category"), ("animal", "category"), ("german shepherd", "attribute")],
    ),
    (
        "Siberian Husky",
        "dog",
        "Animal",
        False,
        [
            "a photo of a Siberian Husky or Malamute dog",
            "a husky dog with thick fur",
        ],
        [("dog", "category"), ("pet", "category"), ("canine", "category"), ("animal", "category"), ("siberian husky", "attribute")],
    ),
    (
        "Pembroke Corgi",
        "dog",
        "Animal",
        False,
        [
            "a photo of a cute Pembroke Welsh Corgi dog",
            "a short-legged corgi pet dog",
        ],
        [("dog", "category"), ("pet", "category"), ("canine", "category"), ("animal", "category"), ("corgi", "attribute")],
    ),
    (
        "Domestic Dog",
        "dog",
        "Animal",
        False,
        [
            "a photo of a domestic pet dog or puppy",
            "a pet dog playing or sitting",
        ],
        [("dog", "category"), ("pet", "category"), ("canine", "category"), ("animal", "category")],
    ),
    (
        "Wild Bird",
        "bird",
        "Animal",
        False,
        [
            "a wildlife photo of a bird perched on a branch or flying",
            "a colorful wild bird or eagle in nature",
        ],
        [("bird", "category"), ("animal", "category"), ("wildlife", "category"), ("wild bird", "attribute")],
    ),
    (
        "Wildlife Mammal",
        "wildlife",
        "Animal",
        False,
        [
            "a wildlife photograph of wild animals in nature",
            "a wild mammal such as a deer, bear, elephant, lion, or fox in its natural habitat",
        ],
        [("wildlife", "category"), ("animal", "category"), ("nature", "scene"), ("wild animal", "attribute")],
    ),
    (
        "Marine & Aquatic Life",
        "wildlife",
        "Animal",
        False,
        [
            "an underwater photo of fish, coral reef, shark, or marine life",
            "aquatic animals swimming in ocean water",
        ],
        [("marine life", "category"), ("animal", "category"), ("ocean", "scene"), ("underwater", "attribute")],
    ),

    # --- 3. Digital Artwork, Historical Illustrations & Game Assets ---
    (
        "Knight & Warrior",
        "character art",
        "Artwork",
        True,
        [
            "a digital painting illustration of a medieval knight or warrior in armor and red cloak",
            "a historical soldier, king, or military commander portrait illustration in plate armor",
            "fantasy video game character portrait of an armored warrior or nobleman",
        ],
        [("character art", "category"), ("artwork", "category"), ("knight & warrior", "attribute"), ("armor", "attribute"), ("medieval", "scene"), ("illustration", "attribute")],
    ),
    (
        "Historical Scholar & Noble",
        "character art",
        "Artwork",
        True,
        [
            "a digital painting portrait of a historical nobleman, scholar, priest, or merchant in robes",
            "an illustrated historical character portrait from a strategy video game",
        ],
        [("character art", "category"), ("artwork", "category"), ("historical figure", "attribute"), ("illustration", "attribute")],
    ),
    (
        "Historical Battle & Army",
        "historical art",
        "Artwork",
        True,
        [
            "a digital painting of a medieval army battle with cavalry horses and soldiers on a battlefield",
            "a historical war siege illustration with armored soldiers marching toward a castle",
            "medieval warfare painting with knights on horseback and smoke in the sky",
        ],
        [("historical art", "category"), ("artwork", "category"), ("historical battle", "attribute"), ("cavalry & soldiers", "attribute"), ("medieval", "scene"), ("illustration", "attribute")],
    ),
    (
        "Medieval Castle & Town",
        "architecture",
        "Architecture",
        True,
        [
            "a painting or illustration of a medieval castle, palace, or town by a river canal",
            "historic European castle, monastery, and town architecture illustration",
            "a fortified medieval citadel or fortress overlooking a landscape",
        ],
        [("architecture", "category"), ("castle & town", "attribute"), ("medieval architecture", "attribute"), ("historic building", "attribute")],
    ),
    (
        "Medieval Agriculture & Village",
        "historical art",
        "Artwork",
        True,
        [
            "a painting of medieval farming with ox cart, bullock cart, and agricultural fields",
            "an illustration of rural village peasants harvesting crops with oxen and wagons",
        ],
        [("historical art", "category"), ("artwork", "category"), ("agriculture & village", "attribute"), ("rural life", "scene"), ("illustration", "attribute")],
    ),
    (
        "Historical Ships & Harbor",
        "historical art",
        "Artwork",
        True,
        [
            "a painting of historical wooden sailing ships in a harbor or ocean port",
            "a maritime illustration of medieval galleons, docks, and coastal trade",
        ],
        [("historical art", "category"), ("artwork", "category"), ("sailing ship & harbor", "attribute"), ("maritime", "scene"), ("ocean", "scene")],
    ),
    (
        "Royal Court & Throne Room",
        "historical art",
        "Artwork",
        True,
        [
            "an illustration of a medieval royal throne room, cathedral altar, or palace interior",
            "a painting of a king's court, library, workshop, or historic indoor hall",
        ],
        [("historical art", "category"), ("artwork", "category"), ("royal court & hall", "attribute"), ("indoor", "scene"), ("illustration", "attribute")],
    ),
    (
        "Medieval Siege & Cannon",
        "historical art",
        "Artwork",
        True,
        [
            "a historical illustration of medieval siege engines, cannons, artillery, or trebuchets",
            "a painting of gunfire, cannons, and fortifications in battle",
        ],
        [("historical art", "category"), ("artwork", "category"), ("siege & artillery", "attribute"), ("illustration", "attribute")],
    ),
    (
        "Anime & Digital Illustration",
        "artwork",
        "Artwork",
        True,
        [
            "an anime, manga, cartoon, or stylized digital art illustration",
            "a vibrant digital painting or concept art",
        ],
        [("artwork", "category"), ("digital illustration", "attribute"), ("illustration", "attribute")],
    ),

    # --- 4. Nature, Scenery & Landscapes ---
    (
        "Alpine Mountain Lake",
        "mountain",
        "Nature",
        False,
        [
            "a scenic landscape photo of alpine mountains and a crystal clear lake",
            "majestic mountain peaks and valley with water and pine trees",
        ],
        [("nature", "category"), ("landscape", "category"), ("mountain", "category"), ("alpine lake", "attribute"), ("lakeside", "scene"), ("outdoor", "scene")],
    ),
    (
        "Ocean Beach & Coast",
        "beach",
        "Nature",
        False,
        [
            "a scenic landscape photo of a sandy ocean beach with turquoise waves",
            "a tropical or coastal seashore with ocean water, sand, and horizon",
        ],
        [("nature", "category"), ("landscape", "category"), ("beach", "category"), ("seashore", "attribute"), ("ocean", "scene"), ("coast", "scene"), ("outdoor", "scene")],
    ),
    (
        "Forest & Woodland",
        "landscape",
        "Nature",
        False,
        [
            "a scenic nature photo of a lush green forest with tall trees and foliage",
            "sunlight shining through woodland trees in nature",
        ],
        [("nature", "category"), ("landscape", "category"), ("forest & woodland", "attribute"), ("foliage", "attribute"), ("outdoor", "scene")],
    ),
    (
        "Sunset & Golden Horizon",
        "landscape",
        "Nature",
        False,
        [
            "a vibrant scenic sunset or sunrise with golden orange clouds over the horizon",
            "a dramatic twilight sky at dusk",
        ],
        [("nature", "category"), ("landscape", "category"), ("sunset", "scene"), ("golden hour", "scene"), ("sky", "attribute"), ("outdoor", "scene")],
    ),
    (
        "Winter Snow Landscape",
        "landscape",
        "Nature",
        False,
        [
            "a winter landscape photo covered in white snow and ice",
            "snowy mountains and trees in winter",
        ],
        [("nature", "category"), ("landscape", "category"), ("winter snow", "attribute"), ("snow", "scene"), ("outdoor", "scene")],
    ),
    (
        "Flowers & Botanical",
        "botanical",
        "Nature",
        False,
        [
            "a close-up macro photo of blooming flowers, petals, or garden plants",
            "colorful botanical blossoms in nature",
        ],
        [("nature", "category"), ("botanical", "category"), ("flowers & plants", "attribute"), ("macro", "scene"), ("outdoor", "scene")],
    ),

    # --- 5. Modern Architecture, Urban & Interiors ---
    (
        "City Skyline & Street",
        "architecture",
        "Architecture",
        False,
        [
            "a photograph of a modern city skyline, skyscrapers, or busy urban street",
            "urban buildings, streets, and architecture",
        ],
        [("architecture", "category"), ("city & street", "attribute"), ("urban", "scene"), ("outdoor", "scene")],
    ),
    (
        "Modern Building & Landmark",
        "architecture",
        "Architecture",
        False,
        [
            "an architectural photograph of a building exterior, bridge, or monument",
            "structural design of a modern house or landmark",
        ],
        [("architecture", "category"), ("building & structure", "attribute"), ("outdoor", "scene")],
    ),
    (
        "Cozy Living Space",
        "interior",
        "Interior",
        False,
        [
            "an indoor photograph of a living room, bedroom, or home interior with furniture",
            "an interior room with sofa, desk, table, and decor",
        ],
        [("interior", "category"), ("living space", "attribute"), ("indoor", "scene")],
    ),

    # --- 6. Food, Culinary & Lifestyle ---
    (
        "Pizza & Italian Dish",
        "food",
        "Lifestyle",
        False,
        [
            "a close-up food photo of a baked pizza with melted cheese and toppings",
            "delicious Italian pizza or pasta dish on a plate",
        ],
        [("food", "category"), ("pizza", "attribute"), ("culinary", "scene"), ("dining", "scene")],
    ),
    (
        "Gourmet Meal & Dining",
        "food",
        "Lifestyle",
        False,
        [
            "a delicious plate of food, restaurant meal, or home-cooked dish on a table",
            "culinary food photography of dinner or lunch",
        ],
        [("food", "category"), ("meal & dining", "attribute"), ("culinary", "scene")],
    ),
    (
        "Coffee, Dessert & Drinks",
        "food",
        "Lifestyle",
        False,
        [
            "a photo of a cup of coffee, latte art, sweet cake dessert, or cocktail beverage",
            "cafe pastry and drink on a table",
        ],
        [("food", "category"), ("coffee & dessert", "attribute"), ("cafe", "scene")],
    ),

    # --- 7. Vehicles & Transportation ---
    (
        "Automobile & Sports Car",
        "vehicle",
        "Transport",
        False,
        [
            "a photo of a modern car, sports car, sedan, or SUV parked or driving on a road",
            "automotive photography of a motor vehicle",
        ],
        [("vehicle", "category"), ("transport", "category"), ("automobile", "attribute"), ("car", "attribute"), ("outdoor", "scene")],
    ),
    (
        "Bicycle & Motorcycle",
        "vehicle",
        "Transport",
        False,
        [
            "a photo of a bicycle, mountain bike, or motorcycle",
            "a two-wheeled bike outdoors",
        ],
        [("vehicle", "category"), ("transport", "category"), ("bike & motorcycle", "attribute"), ("outdoor", "scene")],
    ),
    (
        "Aircraft & Aviation",
        "vehicle",
        "Transport",
        False,
        [
            "a photo of an airplane, airliner, jet, or helicopter flying in the sky or at an airport",
        ],
        [("vehicle", "category"), ("transport", "category"), ("aircraft", "attribute"), ("aviation", "scene")],
    ),

    # --- 8. Technology, Instruments & Documents ---
    (
        "Laptop & Workstation",
        "electronics",
        "Technology",
        False,
        [
            "a photo of a laptop computer, desktop monitor, keyboard, or workspace setup",
            "modern electronic devices and computer hardware on a desk",
        ],
        [("electronics", "category"), ("technology", "category"), ("computer & workstation", "attribute"), ("indoor", "scene")],
    ),
    (
        "Camera & Smartphone",
        "electronics",
        "Technology",
        False,
        [
            "a close-up photo of a digital camera, camera lens, or smartphone gadget",
        ],
        [("electronics", "category"), ("technology", "category"), ("camera & gadget", "attribute")],
    ),
    (
        "Musical Instrument",
        "instrument",
        "Technology",
        False,
        [
            "a photo of a musical instrument such as an acoustic guitar, electric guitar, piano, or violin",
        ],
        [("instrument", "category"), ("musical instrument", "attribute"), ("music", "scene")],
    ),
    (
        "Receipt & Invoice",
        "document",
        "Document",
        False,
        [
            "a photo of a printed store receipt, coffee shop receipt, bill, or invoice with prices",
            "a paper receipt showing item totals",
        ],
        [("document", "category"), ("receipt", "attribute"), ("text", "attribute")],
    ),
    (
        "Printed Document & Text",
        "document",
        "Document",
        False,
        [
            "a photo of a printed text document, book page, menu, sign, or form",
            "white paper with printed black text",
        ],
        [("document", "category"), ("printed text", "attribute"), ("text", "attribute")],
    ),
    (
        "Software Screenshot",
        "screenshot",
        "Document",
        False,
        [
            "a digital computer or phone screenshot of a software interface, webpage, or chat app",
        ],
        [("screenshot", "category"), ("digital interface", "attribute")],
    ),
]

ENVIRONMENT_PROMPTS = [
    ("outdoor", ["an outdoor photograph taken outside in nature, street, beach, or open sky", "an exterior outdoor scene"]),
    ("indoor", ["an indoor photograph taken inside a room, bedroom, or building interior", "an interior indoor room scene"]),
]


class CLIPEngine:
    """
    OpenAI CLIP (ViT-B/32) Vision-Language Neural Intelligence Engine.
    Provides:
      1. Multi-prompt ensembled hierarchical zero-shot classification across 50+ photography & art concepts.
      2. Dual-crop (full scene + salient subject) 512-dimensional multimodal visual embeddings.
      3. Natural language semantic search (e.g. searching 'cat on velvet couch' or 'person at beach').
    """

    def __init__(self, models_dir: Optional[str] = None):
        if models_dir is None:
            self.base_dir = (
                Path(__file__).resolve().parent.parent.parent / ".targon_cache" / "models"
            )
        else:
            self.base_dir = Path(models_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)

        self.vision_path = self.base_dir / "clip_vision_quantized.onnx"
        self.text_path = self.base_dir / "clip_text_quantized.onnx"
        self.tok_path = self.base_dir / "clip_tokenizer.json"

        self.v_sess: Optional[ort.InferenceSession] = None
        self.t_sess: Optional[ort.InferenceSession] = None
        self.tok: Optional[Tokenizer] = None

        self._taxonomy_embeds: Optional[np.ndarray] = None
        self._env_embeds: Optional[np.ndarray] = None

        self._init_models()

    @property
    def is_ready(self) -> bool:
        return self.v_sess is not None and self.t_sess is not None and self.tok is not None

    def _init_models(self):
        try:
            if not self.vision_path.exists():
                urllib.request.urlretrieve(VISION_MODEL_URL, str(self.vision_path))
            if not self.text_path.exists():
                urllib.request.urlretrieve(TEXT_MODEL_URL, str(self.text_path))
            if not self.tok_path.exists():
                urllib.request.urlretrieve(TOKENIZER_URL, str(self.tok_path))

            if self.vision_path.exists() and self.text_path.exists() and self.tok_path.exists():
                sess_opts = ort.SessionOptions()
                sess_opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
                sess_opts.intra_op_num_threads = 2
                self.v_sess = ort.InferenceSession(
                    str(self.vision_path),
                    sess_options=sess_opts,
                    providers=["CPUExecutionProvider"],
                )
                self.t_sess = ort.InferenceSession(
                    str(self.text_path),
                    sess_options=sess_opts,
                    providers=["CPUExecutionProvider"],
                )
                self.tok = Tokenizer.from_file(str(self.tok_path))
                self._precompute_default_taxonomy()
        except Exception:
            self.v_sess = None
            self.t_sess = None
            self.tok = None

    def _precompute_default_taxonomy(self):
        """Loads or precomputes ensembled text embeddings for all photography & art concepts."""
        if self.t_sess is None or self.tok is None:
            return

        cache_npy = self.base_dir / "clip_taxonomy_embeds_v3.npy"
        env_npy = self.base_dir / "clip_env_embeds_v3.npy"

        if cache_npy.exists() and env_npy.exists():
            try:
                loaded = np.load(str(cache_npy))
                loaded_env = np.load(str(env_npy))
                if loaded.shape == (len(CLIP_CONCEPT_TAXONOMY), 512) and loaded_env.shape == (2, 512):
                    self._taxonomy_embeds = loaded
                    self._env_embeds = loaded_env
                    return
            except Exception:
                pass

        # Precompute ensembled concept vectors
        concept_vecs = []
        for _, _, _, _, prompts, _ in CLIP_CONCEPT_TAXONOMY:
            p_embeds = self.embed_text(prompts)
            if p_embeds is not None and len(p_embeds) > 0:
                avg_vec = np.mean(p_embeds, axis=0)
                norm = float(np.linalg.norm(avg_vec))
                if norm > 1e-6:
                    avg_vec = avg_vec / norm
                concept_vecs.append(avg_vec.astype(np.float32))
            else:
                concept_vecs.append(np.zeros(512, dtype=np.float32))

        self._taxonomy_embeds = np.stack(concept_vecs, axis=0)

        env_vecs = []
        for _, e_prompts in ENVIRONMENT_PROMPTS:
            e_embeds = self.embed_text(e_prompts)
            avg_e = np.mean(e_embeds, axis=0)
            avg_e = avg_e / (float(np.linalg.norm(avg_e)) + 1e-6)
            env_vecs.append(avg_e.astype(np.float32))
        self._env_embeds = np.stack(env_vecs, axis=0)

        try:
            np.save(str(cache_npy), self._taxonomy_embeds)
            np.save(str(env_npy), self._env_embeds)
        except Exception:
            pass

    def embed_image(self, pil_img: Image.Image) -> Optional[np.ndarray]:
        """Extracts a 512-dimensional L2-normalized CLIP visual embedding vector."""
        if self.v_sess is None:
            return None
        try:
            img = pil_img.convert("RGB").resize((224, 224), Image.Resampling.BILINEAR)
            arr = (np.array(img, dtype=np.float32) / 255.0 - CLIP_MEAN) / CLIP_STD
            tensor = np.transpose(arr, (2, 0, 1))[np.newaxis, :, :, :]

            input_name = self.v_sess.get_inputs()[0].name
            out = self.v_sess.run(None, {input_name: tensor})[0]
            embed = out[0].astype(np.float32)
            norm = float(np.linalg.norm(embed))
            if norm > 1e-6:
                embed = embed / norm
            return embed
        except Exception:
            return None

    def embed_text(self, texts: List[str]) -> Optional[np.ndarray]:
        """Extracts 512-dimensional L2-normalized CLIP text embedding vectors for a list of strings."""
        if self.t_sess is None or self.tok is None or not texts:
            return None
        try:
            max_len = 77
            padded_ids = []
            for t in texts:
                ids = self.tok.encode(t.strip()).ids[:max_len]
                padded = ids + [0] * (max_len - len(ids))
                padded_ids.append(padded)

            input_ids = np.array(padded_ids, dtype=np.int64)
            input_name = self.t_sess.get_inputs()[0].name
            out = self.t_sess.run(None, {input_name: input_ids})[0]
            embeds = out.astype(np.float32)
            norms = np.linalg.norm(embeds, axis=1, keepdims=True) + 1e-6
            return embeds / norms
        except Exception:
            return None

    def classify_image_detailed(
        self,
        full_img: Image.Image,
        crop_img: Optional[Image.Image] = None,
        top_k: int = 5,
        single_pass: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """
        Performs ensembled zero-shot classification.
        When single_pass=True (default), runs ViT-B/32 once on full_img instead of twice,
        cutting transformer latency in half while returning full_embedding for reuse.
        """
        if self._taxonomy_embeds is None or not self.is_ready:
            return None

        emb_full = self.embed_image(full_img)
        if emb_full is None:
            return None

        if not single_pass and crop_img is not None and crop_img.size != full_img.size:
            emb_crop = self.embed_image(crop_img)
            if emb_crop is not None:
                combined = 0.65 * emb_full + 0.35 * emb_crop
                norm = float(np.linalg.norm(combined))
                img_embed = combined / norm if norm > 1e-6 else emb_full
            else:
                img_embed = emb_full
        else:
            img_embed = emb_full

        similarities = np.dot(self._taxonomy_embeds, img_embed)
        # CLIP native trained logit scale temperature (1 / 100 = 0.01)
        temp = 0.01
        scaled = (similarities - np.max(similarities)) / temp
        probs = np.exp(scaled) / np.sum(np.exp(scaled))

        top_indices = np.argsort(similarities)[::-1][:top_k]
        best_idx = int(top_indices[0])
        best_sim = float(similarities[best_idx])
        best_prob = float(probs[best_idx])

        spec, cat, super_type, is_illus, _, extra_tags = CLIP_CONCEPT_TAXONOMY[best_idx]

        # Collect tags from the winning concept plus any secondary concept that is very close in similarity
        collected_tags: Dict[Tuple[str, str], float] = {}
        conf_base = min(0.99, max(0.84, 0.70 + best_prob * 0.28))

        # Always include the specific concept label as a high-confidence attribute tag
        collected_tags[(spec.lower(), "attribute")] = round(conf_base, 3)
        for t_name, t_type in extra_tags:
            collected_tags[(t_name.lower(), t_type)] = round(conf_base, 3)

        # Secondary close concepts (within 0.015 cosine similarity of top match and same general domain)
        for rank_idx in top_indices[1:3]:
            r_idx = int(rank_idx)
            r_sim = float(similarities[r_idx])
            r_prob = float(probs[r_idx])
            if r_sim >= best_sim - 0.014 and r_prob >= 0.12:
                r_spec, r_cat, r_st, r_illus, _, r_tags = CLIP_CONCEPT_TAXONOMY[r_idx]
                if r_st == super_type and r_illus == is_illus:
                    r_conf = min(0.95, max(0.78, 0.65 + r_prob * 0.25))
                    collected_tags[(r_spec.lower(), "attribute")] = round(r_conf, 3)
                    for tn, tt in r_tags:
                        if tt != "category" or tn.lower() == cat.lower():
                            if (tn.lower(), tt) not in collected_tags:
                                collected_tags[(tn.lower(), tt)] = round(r_conf * 0.95, 3)

        # Determine Outdoor vs Indoor semantically via CLIP
        environment = None
        if self._env_embeds is not None:
            env_sims = np.dot(self._env_embeds, emb_full)
            out_sim, in_sim = float(env_sims[0]), float(env_sims[1])
            if out_sim > in_sim + 0.012:
                environment = "outdoor"
                if ("outdoor", "scene") not in collected_tags and ("indoor", "scene") not in collected_tags:
                    collected_tags[("outdoor", "scene")] = 0.88
            elif in_sim > out_sim + 0.012:
                environment = "indoor"
                if ("indoor", "scene") not in collected_tags and ("outdoor", "scene") not in collected_tags:
                    collected_tags[("indoor", "scene")] = 0.88

        return {
            "specific": spec,
            "category": cat,
            "super_type": super_type,
            "is_illustration": is_illus,
            "similarity": round(best_sim, 4),
            "probability": round(best_prob, 4),
            "confidence": round(conf_base, 3),
            "environment": environment,
            "tags": [(k[0], k[1], v) for k, v in collected_tags.items()],
            "full_embedding": emb_full,
        }

    def classify_image(self, pil_img: Image.Image, top_k: int = 8) -> List[Tuple[str, float]]:
        """
        Classifies an image against the precomputed photography taxonomy.
        Returns sorted list of (category_or_specific_label, probability_score).
        """
        if self._taxonomy_embeds is None or not self.is_ready:
            return []
        img_embed = self.embed_image(pil_img)
        if img_embed is None:
            return []

        similarities = np.dot(self._taxonomy_embeds, img_embed)
        temp = 0.01
        scaled = (similarities - np.max(similarities)) / temp
        probs = np.exp(scaled) / np.sum(np.exp(scaled))

        top_indices = np.argsort(similarities)[::-1][:top_k]
        results = []
        for idx in top_indices:
            spec, cat, _, _, _, _ = CLIP_CONCEPT_TAXONOMY[int(idx)]
            score = float(probs[int(idx)])
            results.append((spec.lower(), round(score, 3)))
        return results

    def compute_similarity(self, img_embed: np.ndarray, text_embed: np.ndarray) -> float:
        """Computes cosine similarity between an image embedding and a text embedding."""
        n1 = float(np.linalg.norm(img_embed))
        n2 = float(np.linalg.norm(text_embed))
        if n1 < 1e-6 or n2 < 1e-6:
            return 0.0
        return float(np.dot(img_embed, text_embed) / (n1 * n2))


clip_engine = CLIPEngine()
