# OntoGUM: Evaluating Contextualized SOTA Coreference Resolution on 12 More Genres

## Introduction
This repository contains the code for building up the OntoGUM dataset from:

- [OntoGUM: Evaluating Contextualized SOTA Coreference Resolution on 12 More Genres](https://arxiv.org/pdf/2106.00933.pdf)
- [Anatomy of OntoGUM—Adapting GUM to the OntoNotes Scheme to Evaluate Robustness of SOTA Coreference Algorithms](https://aclanthology.org/2021.crac-1.15.pdf)
- [Yilun Zhu](http://yilunzhu.com/), [Sameer Pradhan](https://cemantix.org/), and [Amir Zeldes](https://corpling.uis.georgetown.edu/amir/)


## Prerequisites
1. Python >= 3.6
2. Download GUM from <https://github.com/amir-zeldes/gum> and put the folder in the home directory of this repo

## Rebuilding the dataset
You can either use the scripts in this repository or the built bot from [GUM](https://github.com/amir-zeldes/gum) to rebuild the dataset.

* **To rebuild the dataset using this repo:**
1. Run `main.py` to start the conversion after following the prerequisites.
2. Adjust the arguments in `main.py` to output different formats. Please note that if you want to test models trained on OntoNotes, the conll format is needed.
* **To rebuild the dataset from GUM:**

   *Also Check [here](https://github.com/amir-zeldes/gum/tree/master/coref/ontogum) for differences between GUM and OntoNotes schema.*
1. Follow the instructions in the GUM repo to build up the dataset (including reddit data)
2. Find the OntoGUM data (tsv and conll) under `/gum/_build/target/coref/ontogum`

## Output
Two output formats are currently supported: tsv and conll. The default output is tsv. If you would like to have the conll format, specify it with the argument `--out_format`

## Visualization
To straightforwardly view a coref document, copy & paste the tsv file to [Spannotator](https://corpling.uis.georgetown.edu/gitdox/spannotator.html). If you want to visualize the predictions from SpanBert, go to `utils` and run `pred2tsv.py` to generate the tsv file from predicted output json file.

## Testing SpanBert
1. Go to `utils` and run `python gum2conll.py` to build up the dataset. It will generate train, dev (including by-genre set), and test set under ./dataset
2. Follow the instructions in [SpanBert](https://github.com/mandarjoshi90/coref). Note that change the data directory.

## Testing dcoref
1. Go to `utils` and run `./dcoref.sh`

## Results
Model      | OntoNotes  | OntoGUM
:----------| :--------: | :--------:
dcoref     | 57.8       | 39.7
SpanBert   | 79.6       | 64.6


## Citations
```
@inproceedings{zhu-etal-2021-ontogum,
    title = "{O}nto{GUM}: Evaluating Contextualized {SOTA} Coreference Resolution on 12 More Genres",
    author = "Zhu, Yilun  and
      Pradhan, Sameer  and
      Zeldes, Amir",
    editor = "Zong, Chengqing  and
      Xia, Fei  and
      Li, Wenjie  and
      Navigli, Roberto",
    booktitle = "Proceedings of the 59th Annual Meeting of the Association for Computational Linguistics and the 11th International Joint Conference on Natural Language Processing (Volume 2: Short Papers)",
    month = aug,
    year = "2021",
    address = "Online",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.acl-short.59",
    doi = "10.18653/v1/2021.acl-short.59",
    pages = "461--467",
}

@inproceedings{zhu-etal-2021-anatomy,
    title = "Anatomy of {O}nto{GUM}{---}{A}dapting {GUM} to the {O}nto{N}otes Scheme to Evaluate Robustness of {SOTA} Coreference Algorithms",
    author = "Zhu, Yilun  and
      Pradhan, Sameer  and
      Zeldes, Amir",
    editor = "Ogrodniczuk, Maciej  and
      Pradhan, Sameer  and
      Poesio, Massimo  and
      Grishina, Yulia  and
      Ng, Vincent",
    booktitle = "Proceedings of the Fourth Workshop on Computational Models of Reference, Anaphora and Coreference",
    month = nov,
    year = "2021",
    address = "Punta Cana, Dominican Republic",
    publisher = "Association for Computational Linguistics",
    url = "https://aclanthology.org/2021.crac-1.15",
    doi = "10.18653/v1/2021.crac-1.15",
    pages = "141--149",
}
```
