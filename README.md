# FAS Helper
A RAG system that helps find answers to questions in the Federal Antimonopoly Service database

# Known bugs and issues:
1. Returning chunks contains indexes of normalized text instead of original text.
2. If text contains a sentence longer than expected chunk_size then the whole sentence will be put into the chunk leads to chunks of bigger size then needed.
