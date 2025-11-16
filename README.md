# Ingester
Repo that provides text chunkers, embedders and vector storage data saving.

# Known bugs and issues:
1. Returning chunks contains indexes of normalized text instead of original text.
2. If text contains a sentence longer than expected chunk_size then the whole sentence will be put into the chunk leads to chunks of bigger size then needed.

# Possible imporvements and new features:
1. Chunk by text structure first and by sentences after, prioritizing chunk bounds on structure blocks.
