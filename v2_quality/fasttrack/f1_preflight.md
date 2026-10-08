# F1 Preflight Evidence (NO GPU)

## Phenotype uniqueness (gsm8k): True
- B0: `ecb85abd958d3855`
- B1: `6cf221a5692df0e5`
- B2: `845748c58c69a263`
- B3: `844ed32d32728c7e`
- B4: `bc6d852a6335b36b`
- B5: `024835a1f7f59da6`
- REF: `688b45fe75197889`
## Phenotype uniqueness (qasper): True
- B0: `dccdd922083034b9`
- B1: `ef438be05971cfd4`
- B2: `14e4b4df23394e69`
- B3: `9c47dce23fc98c3b`
- B4: `d71a91c1ff6db776`
- B5: `6d30bdcac44ec52c`
- REF: `5e66b7436080236d`
## Prompt hashes on DEV item (gsm8k)
- B0: `67bdf7cd023ca539`
- B1: `dc5d4c43ee0716b7`
- B2: `94a900c2902ec98c`
- B3: `3c04438cfbbe3f58`
- B4: `e965af9e821d924a`
- B5: `74f5cbc76c0ba7dd`
- REF: `3c1c8b1c09657bde`
B5/REF share exemplar block: True
## Prompt hashes on DEV item (qasper)
- B0: `10f2937f802efda7`
- B1: `29c9ae6e65063246`
- B2: `de4902c9a9291572`
- B3: `7beb824a985b03a4`
- B4: `0e6668be7aa3b882`
- B5: `3bca866f417d80aa`
- REF: `0e6668be7aa3b882`
## B3 retrieval metric implementation
- enum: `tfidf`, controller metric: `tfidf` (term-frequency cosine; no IDF)
- implementation: `tfidf_scores` computes TF-cosine only (no IDF term) — verified in src/evaluator/memory.py
## REF matches locked A_gsm: True
## Isolation
- V2 cache dir: `v2_quality/fasttrack/caches/` (fresh, isolated)
- V2 results dir: `v2_quality/fasttrack/f1_results/` (fresh)
- F1 reads only DEV slices: GSM8K test[0:100], QASPER items[0:50]
- No read/write under results/ or experiments/ during F1

## VERDICT: PASS

## Note on QASPER prompt-hash coincidence

On the QASPER DEV probe item, B4 and REF produce identical prompts
(`0e6668be…`): QASPER calibration answers are single-line, so
answer_only+128w rendering equals full rendering for that exemplar. This is
semantically correct (not a duplicate phenotype — task-aware hashes differ:
d71a91c1 vs 5e66b743) and the mandated distinctness pairs (B0/B5, B1/B4)
hold on GSM8K. Recorded for transparency; no action.
