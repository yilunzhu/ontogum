- This folder contains scores and errors of encoding gold span mentions into OntoGUM.
1. The adjusted model assigns a fixed weight (tentatively -5.0) to every gold spans, this will give every spans the same mention scores. In this case, the coref scores highly relies on features (span distance and metadata)

- Results
1. Mention scores
| Option    | Precision  |  Recall  |   F1   |
| --------  |  :-----:   |  :----:  | :----: |
| Baseline  |  85.41%    |  69.23%  | 76.47% |
| Adjusted  |  87.33%    |  74.87%  | 80.62% |

2. Coref scores
| Option    | Precision  |  Recall  |   F1   |
| --------  |  :-----:   |  :----:  | :----: |
| Baseline  |  72.28%    |  58.57%  | 64.66% |
| Adjusted  |  75.19%    |  64.47%  | 69.39% |

- Errors
Mention (precision and recall) and coref errors are avaialbe under `errors`.

1. Mention detection
2. Pair matching
| Categories	| Numbs |
| ------	| :---: |
| others	| 62 |
| missing_rels	| 83 |
| pronouns	| 116 |
| def	| 56 |
| indef	| 2 |