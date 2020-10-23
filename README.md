# coref_dataset_convert

This repo contains the scripts that can convert GUM to the OntoNotes format.

## Prerequisites
1. Python >= 3.6
2. Download GUM from <https://github.com/amir-zeldes/gum> and put the folder in the home directory of this repo

## Visualization
To straightforwardly view a coref document, copy & paste the tsv file to [Spannotator](https://corpling.uis.georgetown.edu/gitdox/spannotator.html).

## Testing SpanBert
1. Go to `utils` and run `python gum2conll.py` to build up the dataset. It will generate train, dev (including by-genre set), and test set under ./dataset
2. Follow the instructions in [SpanBert](https://github.com/mandarjoshi90/coref). Note that change the data directory.

## Results

### Results on SpanBert on dev set across genres
![image text](https://github.com/yilunzhu/coref_dataset_convert/blob/master/utils/pic/res_spanbert.png)
