- This folder contains two possible options for encoding gold span mentions into OntoGUM test set.
1. This option assigns a fixed weight to every gold spans, this will give every spans the same mention scores. In this case, the coref scores highly relies on features (span distance and metadata)
2.  let the pretrained model decide which gold span has which score (the weight is decided by the model)

- Results
1. Mention scores
| Option    | Precision  |  Recall  |   F1   |
| --------  |  :-----:   |  :----:  | :----: |
| Baseline  |  85.41%    |  69.23%  | 76.47% |
| Fixed weight  |  87.33%    |  74.87%  | 80.62% |
| Model weight  |  92.76%    |  69.28%  | 79.32% |

2. Coref scores
| Option    | Precision  |  Recall  |   F1   |
| --------  |  :-----:   |  :----:  | :----: |
| Baseline  |  72.28%    |  58.57%  | 64.66% |
| Fixed weight  |  75.19%    |  64.47%  | 69.39% |
| Model weight  |  80.60%    |  59.23%  | 68.18% |

- Errors
Mention (precision and recall) and coref errors are avaialbe under `fixed_weight` and `model_weight`.