# Project 6: LoRA Fine-Tuning for Mathematical Reasoning

This workspace contains a complete experiment for training a mathematical reasoning model using a PRM-style dataset and LoRA/QLoRA fine-tuning. The project combines the SSC-CoT workflow with a Qwen-based language model to learn step-level reasoning supervision.

## Overview

The workflow in this project includes:
- loading reasoning examples from the SSC-CoT dataset,
- converting them into a PRM-style text format,
- tokenizing the data for causal language modeling,
- fine-tuning a model with LoRA/QLoRA,
- saving adapter weights and final model artifacts.

## Project Structure

- [project6_completed.ipynb](project6_completed.ipynb) — main notebook containing the end-to-end training pipeline.
- [ssc-cot](ssc-cot) — SSC-CoT source code, utilities, and dataset files.
- [prm_lora_output](prm_lora_output) — training checkpoints generated during experimentation.
- [prm_lora_final](prm_lora_final) — final LoRA-adapted model artifacts.
- [prm_lora_final_2](prm_lora_final_2) — an additional saved version of the fine-tuned model.

## Main Goal

The goal of this project is to adapt a pretrained language model for mathematical reasoning by training it on structured reasoning steps and their corresponding positive/negative labels.

## Requirements

A GPU-enabled environment is strongly recommended for training.

### Python packages

Install the required dependencies with:

```bash
pip install -q peft transformers datasets accelerate bitsandbytes trl
pip install openai==0.27.7 Levenshtein==0.23.0
```

### System requirements

- Python 3.9 or higher
- CUDA-capable GPU
- Sufficient VRAM for 4-bit/LoRA fine-tuning

## How to Run

1. Open [project6_completed.ipynb](project6_completed.ipynb).
2. Run the cells in order.
3. The notebook will:
   - load the dataset from [ssc-cot/Dataset](ssc-cot/Dataset),
   - prepare the PRM-style training text,
   - tokenize the data,
   - fine-tune the model with LoRA/QLoRA,
   - save the results to the output folders.

## Output Files

Training and model artifacts are stored in:
- [prm_lora_output](prm_lora_output)
- [prm_lora_final](prm_lora_final)
- [prm_lora_final_2](prm_lora_final_2)

## Notes

- The training setup is memory-intensive, so you may need to adjust batch size or gradient accumulation depending on your GPU.
- Dataset paths in the notebook may need to be adjusted if you run the code outside the current workspace layout.
- This project is based on the SSC-CoT methodology for stepwise mathematical reasoning.
