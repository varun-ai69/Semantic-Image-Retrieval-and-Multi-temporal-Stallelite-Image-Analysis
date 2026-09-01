# Offline Training Scripts (`backend/training`)

Modules for fine-tuning machine learning models prior to offline deployment.

- `train_retrieval_encoder.py`: Fine-tunes RemoteCLIP on captioned datasets (RSICD, RSITMD, UCM-Captions).
- `train_change_model.py`: Fine-tunes Siamese / BIT change detection architectures on change detection datasets (LEVIR-CD, OSCD).
- `datasets/`: Dataset loaders and data augmentations.
