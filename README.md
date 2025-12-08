# Ingester
Repo that provides text chunkers, embedders and vector storage data saving.

# Known bugs and issues:
1. Returning chunks contains indexes of normalized text instead of original text.
2. If text contains a sentence longer than expected chunk_size then the whole sentence will be put into the chunk leads to chunks of bigger size then needed.

# TODO:
1. Move LLM prompts to a separate file.
2. Move all settings related constants (LLM, retriever, etc.) to constants file.
3. Move all connection settings to .env file.
