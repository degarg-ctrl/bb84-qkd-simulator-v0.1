# Findings

Simulating 5,000,000 bits directly causes a `MemoryError`. Chunking bits in batches of 500k successfully bypasses the memory limitation but is computationally expensive (~2 minutes per repetition for 3 configurations).
At 175km, empirical validation breaks down due to extremely low detection yield (~60 bits).
