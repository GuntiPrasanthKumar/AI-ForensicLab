# AI Forensic Lab - Benchmark & Validation Laboratory

This directory contains the Benchmark and Validation infrastructure for measuring, evaluating, and comparing computer vision and forensic models across standard dataset taxonomies.

---

## Directory Taxonomy & Structure

```
benchmark/
│
├── datasets/                 <-- Evaluation Image Datasets
│   ├── human/                <-- Authentic Human Photography
│   │   ├── phone_camera/     <-- Smartphone photos (iPhone, Samsung, Pixel)
│   │   ├── dslr/             <-- Professional DSLR/Mirrorless camera captures
│   │   ├── screenshots/      <-- Digital screen captures & crops
│   │   ├── edited/           <-- Photos edited via Lightroom/Photoshop
│   │   └── social_media/     <-- Compressed uploads (WhatsApp, Twitter, Instagram)
│   │
│   ├── ai/                   <-- Synthetic & AI-Generated Imagery
│   │   ├── chatgpt/          <-- DALL-E 3 images generated via ChatGPT
│   │   ├── gemini/           <-- Imagen 3 images generated via Gemini
│   │   ├── dall_e/           <-- DALL-E API generated images
│   │   ├── midjourney/       <-- Midjourney v5/v6 renders
│   │   ├── flux/             <-- Black Forest Labs FLUX.1 models
│   │   ├── stable_diffusion/ <-- Stable Diffusion 1.5 / 2.1
│   │   ├── sdxl/             <-- Stable Diffusion XL renders
│   │   ├── ideogram/         <-- Ideogram AI renders
│   │   └── leonardo/         <-- Leonardo.Ai renders
│   │
│   └── mixed/                <-- Multi-source evaluation batches
│
├── reports/                  <-- Exported evaluation reports (JSON, CSV, PDF, Markdown)
├── metrics/                  <-- Statistical metric calculation algorithms (Accuracy, Precision, F1, ROC-AUC)
├── scripts/                  <-- Dataset creation & automated runner scripts
├── results/                  <-- Model execution logs & evaluation runs
├── configs/                  <-- Model benchmark configurations & evaluation parameters
└── README.md                 <-- Benchmark documentation
```

---

## Usage Guidelines

- **Datasets:** Store sample images under their respective human or AI generator sub-category.
- **Configs:** Define confidence thresholds, model selection lists, and output directories in `configs/`.
- **Reports:** Benchmark runs generate exported performance reports in `reports/` along with misclassification diagnostic logs.
