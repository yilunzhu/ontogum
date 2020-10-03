import io, os, sys
from argparse import ArgumentParser
import time
from copy import deepcopy
from process_data import process_doc
from func import Convert
from out import *


def main(depDir, corefDir, out_dir, out_format):
    """
    read dep conllu file and coref tsv file in the gum directory
    :return: a dictionary of one article containing all corefered entities
    """
    print('*** Start converting...')
    start_time = time.time()

    articles = []

    for f in os.listdir(corefDir):
        filename = f.split('.')[0]

        # test
        if filename != 'GUM_academic_huh':
            continue
        print(f'{filename}')
        articles.append(filename)

        coref_article = io.open(os.path.join(corefDir, f), encoding='utf-8').read().split('\n')
        dep_article = io.open(os.path.join(depDir, filename + '.conllu'), encoding='utf-8').read().split('\n')
        dep_article = [l.split('\t') for l in dep_article]

        doc, tokens, group_dict, next_dict, new_id2entity = process_doc(dep_article, coref_article)

        # antecedent entities
        antecedent_dict = {v: k for k, v in next_dict.items()}

        # make GUM as same as OntoNotes
        ori_doc = deepcopy(doc)
        convert = Convert(doc, next_dict, group_dict)
        converted_doc, non_singleton = convert.process()

        if out_format == 'html':    # visualization: write into a html file
            # visualization: original
            to_html(ori_doc, tokens, group_dict, antecedent_dict, out_dir+os.sep+'html'+os.sep+f'ori_{filename}.html')
            to_html(converted_doc, tokens, group_dict, antecedent_dict, out_dir+os.sep+'html'+os.sep+f'{filename}.html')
        elif out_format == 'tsv':   # write into tsv format
            to_tsv(converted_doc, coref_article, out_dir+os.sep+'tsv'+os.sep+f'{filename}.tsv', non_singleton, new_id2entity)
            a = 1

    end_time = time.time()

    print()
    print(f'*** Convert {len(articles)} documents.')
    print(f'*** Time cost: {int(end_time - start_time) // 60}:{int(end_time - start_time) % 60}s')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--dep', default=os.path.join('gum', 'dep'), help='Path to the gum/dep/ud directory')
    parser.add_argument('--coref', default=os.path.join('gum', 'coref', 'tsv'), help='Path to the gum/coref/tsv directory')
    parser.add_argument('--out_dir', default='out', help='output dir')
    parser.add_argument('--out_format', default='tsv', help='output format')

    args = parser.parse_args()

    dep_dir = args.dep
    coref_dir = args.coref
    out_dir = args.out_dir
    out_format = args.out_format
    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    if not os.path.exists(out_dir + os.sep + out_format):
        os.mkdir(out_dir + os.sep + out_format)

    main(dep_dir, coref_dir, out_dir, out_format)

    print('Done!')
