# AI Forensic Lab — Benchmark & Validation Framework

This directory contains the structured Benchmark and Validation framework for evaluating, measuring, and testing computer vision, NLP, and multimodal forensic AI models against standard dataset taxonomies.

---

## Folder Taxonomy & Structure

```
benchmark/
│
├── datasets/                 <-- Evaluation Datasets Storage
│   ├── human/                <-- Authentic Human-Generated Content
│   │   ├── phone_camera/     <-- Photos captured via mobile device cameras (iOS / Android)
│   │   ├── dslr/             <-- Photos captured via digital single-lens reflex / mirrorless cameras
│   │   ├── screenshots/      <-- Uncompressed screen captures and digital crops
│   │   ├── edited/           <-- Authentic photos processed through post-processing software
│   │   └── social_media/     <-- Compressed uploads retrieved from social messaging & web platforms
│   │
│   ├── ai/                   <-- Synthetic & AI-Generated Imagery & Media
│   │   ├── chatgpt/          <-- DALL-E 3 imagery generated via OpenAI ChatGPT
│   │   ├── gemini/           <-- Imagen 3 imagery generated via Google Gemini
│   │   ├── dall_e/           <-- Direct DALL-E API outputs
│   │   ├── midjourney/       <-- Midjourney v5/v6 synthetic renders
│   │   ├── flux/             <-- Black Forest Labs FLUX.1 model outputs
│   │   ├── stable_diffusion/ <-- Stable Diffusion 1.5 / 2.1 outputs
│   │   ├── sdxl/             <-- Stable Diffusion XL renders
│   │   ├── ideogram/         <-- Ideogram AI typography and graphics
│   │   └── leonardo/         <-- Leonardo.Ai synthetic renders
│   │
│   └── mixed/                <-- Heterogeneous evaluation batches combining human & AI media
│
├── reports/                  <-- Exported evaluation reports (JSON, CSV, PDF, Markdown)
├── metrics/                  <-- Statistical metric calculation models (Accuracy, F1, ROC-AUC)
├── scripts/                  <-- Automated benchmark runners & dataset preparation utilities
├── results/                  <-- Raw benchmark execution logs & model output predictions
├── configs/                  <-- Model benchmark configurations & evaluation parameters
└── README.md                 <-- Framework documentation & usage guidelines
```

---

## Directory Purpose & Guidelines

- **`datasets/`**: Isolated storage for benchmark evaluation datasets.
  - **`datasets/human/`**: Categorized authentic media across capture devices and processing workflows.
  - **`datasets/ai/`**: Categorized synthetic media across specific generative models and engines.
  - **`datasets/mixed/`**: Blended test sets for stress-testing model classification accuracy.
- **`reports/`**: Destination directory for generated performance summaries and diagnostic reports.
- **`metrics/`**: Evaluation metric definitions and scoring formulas.
- **`scripts/`**: Automation scripts for executing benchmarks and managing datasets.
- **`results/`**: Execution outputs, raw prediction arrays, and run timestamps.
- **`configs/`**: Parameter definitions, confidence thresholds, and model evaluation settings.
