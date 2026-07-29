# Project 6: LoRA Fine-Tuning for Mathematical Reasoning

This file documents a separate project added to the repository for experimenting with LoRA-based fine-tuning on mathematical reasoning data.

## Overview

The objective of this project is to adapt a pretrained language model for stepwise mathematical reasoning using a PRM-style dataset and LoRA/QLoRA fine-tuning.

## What is included

- A Jupyter notebook workflow for preparing reasoning examples.
- A dataset processing pipeline that converts reasoning steps into text samples.
- A QLoRA-based fine-tuning setup using Hugging Face Transformers and PEFT.
- Saved model adapter artifacts and training checkpoints.

## Main workflow

1. Load mathematical reasoning examples from the SSC-CoT dataset.
2. Convert the examples into a prompt-style training format.
3. Tokenize the data for causal language modeling.
4. Fine-tune a model using LoRA with 4-bit quantization.
5. Save the resulting adapter and model weights.

## Key libraries

- transformers
- datasets
- peft
- accelerate
- bitsandbytes
- trl

## Notes

- A GPU-enabled environment is recommended for training.
- The training configuration is memory-intensive and may need tuning depending on available VRAM.
- The project is intended as an experimental setup for mathematical reasoning adaptation.
