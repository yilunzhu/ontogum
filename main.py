import io, os, sys
from argparse import ArgumentParser
import time
from copy import deepcopy
from collections import defaultdict
from process_data import process_doc, count
from func import Convert
from out import *


def main(depDir, corefDir, out_dir, out_format, if_appos, if_singletons, if_count):
    """
    read dep conllu file and coref tsv file in the gum directory
    :return: a dictionary of one article containing all corefered entities
    """
    print('*** Start converting...')
    start_time = time.time()

    articles = []
    count_by_genre = defaultdict(lambda: defaultdict(int))
    entity_by_genre = defaultdict(lambda: defaultdict(int))

    for f in os.listdir(corefDir):
        if '.tsv' not in f:
            continue
        filename = f.split('.')[0]

        # test
        # if filename != 'GUM_academic_eegimaa':
        #     continue
        print(f'{filename}')
        articles.append(filename)
        name_fields = filename.split('_')
        new_name = f'GUM_{name_fields[1]}_{name_fields[2]}'

        coref_article = io.open(os.path.join(corefDir, f), encoding='utf-8').read().split('\n')
        dep_article = io.open(os.path.join(depDir, new_name + '.conllu'), encoding='utf-8').read().split('\n')
        dep_article = [l.split('\t') for l in dep_article]

        doc, tokens, group_dict, next_dict, new_id2entity, dep_sents = process_doc(dep_article, coref_article)

        # antecedent entities
        antecedent_dict = {v: k for k, v in next_dict.items()}

        # make GUM as same as OntoNotes
        ori_doc = deepcopy(doc)
        convert = Convert(doc, next_dict, group_dict, if_appos, if_singletons)
        converted_doc, non_singleton, new_id2entity = convert.process(new_id2entity)

        # count information for each genre
        if if_count:
            prp, nnp, nn, entity_by_doc = count(doc)
            cur_genre = filename.split('_')[1]
            count_by_genre[cur_genre]['prp'] += prp
            count_by_genre[cur_genre]['nnp'] += nnp
            count_by_genre[cur_genre]['nn'] += nn

            for e, c in entity_by_doc.items():
                entity_by_genre[cur_genre][e] += c

        if out_format == 'html':    # visualization: write into a html file
            # visualization: original
            to_html(ori_doc, tokens, group_dict, antecedent_dict, out_dir+os.sep+'html'+os.sep+f'ori_{filename}.html')
            to_html(converted_doc, tokens, group_dict, antecedent_dict, out_dir+os.sep+'html'+os.sep+f'{filename}.html')
        elif out_format == 'tsv':   # write into tsv format
            to_tsv(converted_doc, coref_article, out_dir+os.sep+'tsv'+os.sep+f'{filename}.tsv', non_singleton, new_id2entity)
            a = 1
        elif out_format == 'conll': # write into conll format
            to_conll(filename, converted_doc, coref_article, out_dir+os.sep+'conll'+os.sep+f'{filename}.conll', non_singleton, new_id2entity, dep_sents)

    end_time = time.time()

    print()
    print(f'*** Convert {len(articles)} documents.')
    print(f'*** Time cost: {int(end_time - start_time) // 60}:{int(end_time - start_time) % 60}s')

    if if_count:
        for g, v in count_by_genre.items():
            genre_count = sum(v.values())
            pron_count, nnp_count, nn_count = v['prp'], v['nnp'], v['nn']
            print(f'{g}\tTOTAL: {genre_count}\tPRON: {pron_count}\tNNP+NN: {nnp_count+nn_count}')
            print(
                f'Ratio\tPRON: {pron_count / genre_count}\tNNP+NN: {(nnp_count+nn_count) / genre_count}')
            print()

        for g, dic in entity_by_genre.items():
            # genre_sum = sum(dic.values())
            person = dic['person'] / sum(dic.values())
            out = '\t'.join([f'{e}: {c}' for e, c in dic.items()])
            print(f'{g}\t{out}\tPerson percentage: {person}')


if __name__ == '__main__':
    parser = ArgumentParser()
    parser.add_argument('--dep', default=os.path.join('gum', 'dep'), help='Path to the gum/dep/ud directory')
    parser.add_argument('--coref', default=os.path.join('gum', 'coref', 'tsv'), help='Path to the gum/coref/tsv directory')
    parser.add_argument('--out_dir', default='out', help='output dir')
    parser.add_argument('--out_format', default='tsv', help='Output format: tsv or conll')
    parser.add_argument('--appos', action='store_true', help='Keeping appositions (OntoNotes corpus format). Otherwise, coref task output')
    parser.add_argument('--singleton', action='store_true', help='Keeping singletons')
    parser.add_argument('--count', action='store_true', help='Counting PRON/NNP/NN')

    args = parser.parse_args()

    dep_dir = args.dep
    coref_dir = args.coref
    out_dir = args.out_dir
    out_format = args.out_format
    if_appos = args.appos
    if_singletons = args.singleton
    if_count = args.count

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)
    if not os.path.exists(out_dir + os.sep + out_format):
        os.mkdir(out_dir + os.sep + out_format)

    main(dep_dir, coref_dir, out_dir, out_format, if_appos, if_singletons, if_count)

    print('Done!')
