# OntoGUM

Convert GUM to be consistent with OntoNotes scheme.

## Prerequisites
1. Python >= 3.6
2. Download GUM from <https://github.com/amir-zeldes/gum> and put the folder in the home directory of this repo

## Output
Two output formats are currently supported: tsv and conll. The default output is tsv. If you would like to have the conll format, specify it with the argument `--out_format`

## Visualization
To straightforwardly view a coref document, copy & paste the tsv file to [Spannotator](https://corpling.uis.georgetown.edu/gitdox/spannotator.html).

## Testing SpanBert
1. Go to `utils` and run `python gum2conll.py` to build up the dataset. It will generate train, dev (including by-genre set), and test set under ./dataset
2. Follow the instructions in [SpanBert](https://github.com/mandarjoshi90/coref). Note that change the data directory.

## Testing dcoref
1. Go to `utils` and run `./dcoref.sh`

## Results
Model      | OntoNotes  | OntoGUM
:----------| :--------: | :--------:
dcoref     | 57.8       | 39.7
SpanBert   | 79.6       | 60.7
