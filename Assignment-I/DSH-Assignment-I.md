# E-commerce Search Analysis - DSH-Assignment-I 

## Search Results

**Keywords**(What I want to buy most):

- Apple Vision Pro 2025 M5 1TB (Regular specific keywords)
- **HASEBLED** X2D 100C + XCD 2,5/38V (With typo, which should be HASSEBLAD)
- drones with full-frame cameras (Fuzzy search)

**Results**:

Search the three 'items' on JD.com, Taobao, Amazon respectively. Only focus on the results on the first page.

- For 'Apple Vision Pro 2025 M5 1TB': **Partial**
    - **JD.com**: Many correct hits, including JD Self-Operated Stores, Official Stores, Third-Party Stores, etc. Also contains rental or second-hand.
    - **Taobao**: A few hits from Third-Party Stores. Some unwanted results. Some relevant results like 'iPhone 17 Pro'.
    - **Amazon**: No hit, but some other recommendations like 'Apple 2024 MacBook Pro Laptop'.
- For 'HASEBLED X2D 100C + XCD 2,5/38V': **Partial**
    - **JD.com**: Many correct hits, including JD Self-Operated Stores, Third-Party Stores, etc.
    - **Taobao**: No hit, only some accessories. (Not for typo, and no results even with correct spelling.)
    - **Amazon**: No hit, no recommendations. (Due to the typo. Fix the typo will obtain correct hits.)
- For 'drones with full-frame cameras': **Fail**
    - **JD.com**: No hits in English, but many correct hits in Chinese.
    - **Taobao**: No hits in English, but many correct hits in Chinese, while the wrong hits outranked the correct hits. 
    - **Amazon**: Multiple hits, but usually not 'full-frame', i.e. incorrect hits.

## Analysis

- **Fuzzy matching or Suggesters**: Some of the shopping websites can provide correct hits even with typos, it's for they are using fuzzy matching or Suggesters, like Levenshtein or Damara–Levenshtein distance.

- **No English hits but Chinese works**: Some Chinese websites won't automatically translate English into Chinese.
- **No hits for test3**: Some shopping websites can't map 'full-frame' into structured attributes with category constraints.

### Implementation principles of the search function

Based on all the results and other data, we conclude that:

- **Query understanding**: Tokenization, normalization, spelling correction, synonyms, attribute extraction, etc. (e.g. SmartChinese + ICU when in Chinese)
- **Candidate retrieval**: Lexical recall, Semantic recall, Hybrid recall, etc.
- **Reranking**: 
    - LTR(Learning-to-rank) models like LambdaMART which uses behavioral features to re-order top-K.
    - Neural re-ranking via BERT(Bidirectional Encoder Representations from Transformers)/ColBERT(Contextualized Late Interaction over BERT) improves complex intent handling.
    - Overlays self-operated/official/3P, rental/used, etc.
- **UX(User Experience) boosters**: Autocomplete and suggesters to avoid zero-results.

### Possible storage structures for the data

Based on all the results and other data, we conclude that:

- **Inverted index**: Maps each term to a list of IDs, ensuring fast look up.
- **DocValues(Columnar)**: Stores fields like price or brand column-wise for faster queries.
- **BKD-Tree**: Splits numeric or geometric space for faster range or 'nearby' queries.
- **Vector index + HNSW**: Encodes items or queries as vectors and finds nearest neighbors on an HNSW(Hierarchical Navigable Small World) graph.
- **Suggesters, Synonyms**: Ensures fuzzy search and corrects typos.
- **OLTP + CDC streams**: Masters data lives in OLTP(Online Transaction Processing), and changes stream via CDC(Change Data Capture) into the index to make sure the search stays in almost-real-time.

## Possible Further Improvement

- Unify to **single language**, or adopt **multilingual** vector models, to make sure finding correct results via any language.
- Involve **LLM** (already been used in some searching engines) to expand the docs and find **potential keywords** to avoid vocabulary mismatch and improve searching results.
- Involve **more factors** into ranking with the help of LLM. For instance, use LLM to judge the comprehensive behavior of items or merchants like comments, ratings, after-sales, etc, and effect the ranking process.
- Based on the current session behavior to **re-rank the results** to let users get to the targets faster.
- Provide **'AI Highlights'** on some of the top hits.
- Allow users to **order the keywords** by significance to better rank the results.