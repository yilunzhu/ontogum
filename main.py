import io, os, sys
from argparse import ArgumentParser
from process_data import process_doc
from func import Convert

def main(depDir, corefDir) -> dict:
    """
    read dep collnu file and coref tsv file in the gum directory
    :return: a dictionary of one article containing all corefered entities
    """
    articles = []

    for f in os.listdir(corefDir):
        filename = f.split('.')[0]
        # doc = {}

        coref_article = io.open(os.path.join(corefDir, f), encoding='utf-8').read().split('\n')
        dep_article = io.open(os.path.join(depDir, filename + '.conllu'), encoding='utf-8').read().split('\n')
        dep_article = [l.split('\t') for l in dep_article]

        doc = process_doc(dep_article, coref_article)

        convert = Convert(doc)

        # TODO: return what?
        return doc

if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--dep', default=os.path.join('gum', 'dep', 'ud'), help='Path to the gum/dep/ud directory')
    parser.add_argument('--coref', default=os.path.join('gum', 'coref', 'tsv'), help='Path to the gum/coref/tsv directory')
    args = parser.parse_args()

    dep_dir = args.dep
    coref_dir = args.coref

    main(dep_dir, coref_dir)
