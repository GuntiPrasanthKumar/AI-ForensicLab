import io
from typing import Dict, Any, List
from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS

# Known AI Generation Software Signatures in Metadata
AI_SOFTWARE_SIGNATURES = [
    "STABLE DIFFUSION", "MIDJOURNEY", "DALL-E", "DALLE", "COMFYUI",
    "AUTOMATIC1111", "FOOCUS", "NOVELAI", "FLUX", "NIJIJOURNEY",
    "RUNWAY", "LEONARDO.AI", "BING IMAGE CREATOR", "ADOBE FIREFLY"
]

EDITING_SOFTWARE_SIGNATURES = [
    "PHOTOSHOP", "LIGHTROOM", "CANVA", "GIMP", "AFFINITY",
    "PAINT.NET", "SNAPSEED", "PIXLR", "FOTOR"
]

def analyze_metadata(pil_img: Image.Image, raw_bytes: bytes) -> Dict[str, Any]:
    """
    Parses EXIF, PNG text chunks, XMP tags, and camera parameters.
    Returns:
    - metadata_ai_score: float (0.0 to 100.0)
    - metadata_summary: Dict
    - detected_metadata_artifacts: List[str]
    - is_camera_authentic: bool
    - has_ai_signature: bool
    """
    artifacts: List[str] = []
    metadata_summary: Dict[str, Any] = {}

    has_camera_make = False
    has_camera_model = False
    has_date_time = False
    has_ai_signature = False
    has_editing_signature = False
    ai_signature_name = None

    # 1. Parse EXIF Metadata
    try:
        exif_data = pil_img.getexif()
        if exif_data:
            for tag_id, value in exif_data.items():
                tag_name = TAGS.get(tag_id, str(tag_id))
                val_str = str(value).strip()

                if tag_name == "Make" and val_str:
                    has_camera_make = True
                    metadata_summary["camera_make"] = val_str
                elif tag_name == "Model" and val_str:
                    has_camera_model = True
                    metadata_summary["camera_model"] = val_str
                elif tag_name in ("DateTimeOriginal", "DateTime", "CreateDate") and val_str:
                    has_date_time = True
                    metadata_summary["creation_date"] = val_str
                elif tag_name == "Software" and val_str:
                    metadata_summary["software"] = val_str
                    val_upper = val_str.upper()
                    for sig in AI_SOFTWARE_SIGNATURES:
                        if sig in val_upper:
                            has_ai_signature = True
                            ai_signature_name = val_str
                    for sig in EDITING_SOFTWARE_SIGNATURES:
                        if sig in val_upper:
                            has_editing_signature = True
                            metadata_summary["editing_software"] = val_str

                # Check LensModel (tag 42036) or LensInfo
                if tag_name in ("LensModel", "LensInfo", 42036) and val_str:
                    metadata_summary["lens"] = val_str

                # Check GPSInfo (tag 34853)
                if tag_name == "GPSInfo" or tag_id == 34853:
                    metadata_summary["has_gps"] = True

    except Exception as e:
        print(f"[Metadata Engine] EXIF parsing warning: {e}")

    # 2. Parse PNG Info Text Chunks (Stable Diffusion parameters, ComfyUI workflow)
    try:
        if hasattr(pil_img, "info") and isinstance(pil_img.info, dict):
            info = pil_img.info
            for key, val in info.items():
                key_upper = str(key).upper()
                val_str = str(val)
                val_upper = val_str.upper()

                if key_upper in ("PARAMETERS", "PROMPT", "WORKFLOW", "GENERATION_INFO"):
                    has_ai_signature = True
                    ai_signature_name = f"PNG Info: {key}"
                    metadata_summary["ai_generation_chunk"] = key

                for sig in AI_SOFTWARE_SIGNATURES:
                    if sig in val_upper or sig in key_upper:
                        has_ai_signature = True
                        ai_signature_name = f"Signature: {sig}"

                if "EXIF" not in metadata_summary and key_upper == "EXIF":
                    metadata_summary["has_raw_exif_chunk"] = True
    except Exception as e:
        print(f"[Metadata Engine] PNG Chunk parsing warning: {e}")

    # 3. Direct Byte Buffer Inspection for C2PA / XMP / Software String Signatures
    raw_str = raw_bytes[:16384].decode("latin1", errors="ignore")
    if not has_ai_signature:
        for sig in AI_SOFTWARE_SIGNATURES:
            if sig in raw_str.upper():
                has_ai_signature = True
                ai_signature_name = sig
                break

    # 4. Synthesize Metadata AI Score & Artifact Messages
    is_camera_authentic = (has_camera_make or has_camera_model) and has_date_time

    if has_ai_signature:
        metadata_ai_score = 98.0
        artifacts.append(f"AI Generation Metadata Signature: {ai_signature_name}")
    elif is_camera_authentic:
        metadata_ai_score = 2.0
        make = metadata_summary.get("camera_make", "")
        model = metadata_summary.get("camera_model", "")
        artifacts.append(f"Authentic Camera Hardware EXIF: {make} {model}".strip())
        if "creation_date" in metadata_summary:
            artifacts.append(f"Physical Capture Timestamp: {metadata_summary['creation_date']}")
    elif has_editing_signature:
        metadata_ai_score = 45.0
        artifacts.append(f"Digital Editing Software Metadata: {metadata_summary.get('editing_software')}")
    elif has_camera_make or has_camera_model:
        metadata_ai_score = 15.0
        artifacts.append(f"Partial Camera Metadata ({metadata_summary.get('camera_make', metadata_summary.get('camera_model', ''))})")
    else:
        # Missing EXIF is neutral (50%) - many web images strip EXIF
        metadata_ai_score = 50.0
        artifacts.append("Metadata Stripped / Missing Hardware EXIF Header")

    metadata_summary["is_camera_authentic"] = is_camera_authentic
    metadata_summary["has_ai_signature"] = has_ai_signature

    return {
        "metadata_ai_score": round(metadata_ai_score, 1),
        "metadata_summary": metadata_summary,
        "detected_metadata_artifacts": artifacts,
        "is_camera_authentic": is_camera_authentic,
        "has_ai_signature": has_ai_signature
    }
