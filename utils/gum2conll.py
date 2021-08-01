import io, os, sys
import re
from copy import deepcopy
from argparse import ArgumentParser


def to_text(lst):
    text = ""
    for line in lst:
        new_line = line + "\n"
        text += new_line
    return text


def find_list(file):
    file_list = []
    with io.open(file) as f:
        for line in f.readlines():
            if line.startswith("GUM"):
                file_list.append(line.strip())
    return file_list


def read_tsv_file(file):
    lst = []
    with io.open(file, encoding="utf8") as f:
        for line in f.readlines():
            if "\t" in line:
                lst.append(line)
    return lst


def read_conll_file(file):
    conll_out = []
    with io.open(file, encoding="utf8") as f:
        for i, line in enumerate(f.read().split('\n')):
            if "\t" in line:
                fields = line.strip().split("\t")
                if len(fields) == 2:
                    corefs = "_"
                else:
                    corefs = fields[2]
                if corefs == '_':
                    corefs = '-'
                else:
                    new_corefs = ''
                    for i in corefs:
                        if i == ')':
                            new_corefs += i + '|'
                        elif i == '(':
                            new_corefs += '|' + i
                        else:
                            new_corefs += i

                    corefs = new_corefs.replace('||', '|').strip('|')
                new_line = '\t'.join(fields[:-1] + [corefs])
                conll_out.append(new_line)
    return conll_out


def read_dep_file(file):
    dic = {}
    filename = file.split('/')[-1].split('.')[0]
    with io.open(file, encoding="utf8") as f:
        sents = f.read().split('\n\n')
        for sent in sents:
            if sent == '' or sent == '\n':
                continue
            sent_id = re.search(f'# sent_id = {filename}-([0-9]+?)\n', sent).group(1)
            speaker = re.search('# speaker\s?=\s?([\w\W]+?)\n', sent).group(1) if re.search('# speaker\s?=\s?([\w\W]+?)\n', sent) else '-'
            dic[sent_id] = speaker
    return dic


def build_conll(conll, tsv, dep, file_fields, doc_id):
    genre = file_fields[1]
    doc = file_fields[2]
    in_text = [f"#begin document ({genre}/{doc}); part 000"]
    for i in range(len(conll)):
        if i == 22:
            a = 1
        conll_fields = conll[i].split("\t")
        tsv_fields = tsv[i].split("\t")
        doc_key = f"{genre}/{doc}"
        sent_id = tsv_fields[0].split("-")[0]
        token_id = int(tsv_fields[0].split("-")[1]) - 1
        if token_id == 0 and i != 0:
            in_text.append("")
        token = conll_fields[1]
        coref = conll_fields[-1]
        fields = [doc_key, str(doc_id), str(token_id), token, "-", "-", "-", "-", "-", f"{dep[sent_id]}", "*", "*", "*", "*", "*",
                  "*", coref]
        in_text.append("\t".join(fields))

    in_text.append("")
    in_text.append("#end document")
    return in_text


def write_file(filename, lst):
    text = to_text(lst)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def main(if_genre, coref_path, dep_path, out_dir, gum_file_lists=None):
    train_list = []
    dev_list = []
    test_list = []
    train = []
    dev = []
    test = []
    docs = {}

    for filename in os.listdir(gum_file_lists):
        file_path = gum_file_lists + os.sep + filename
        if "train" in filename:
            train_list = find_list(file_path)
        elif "dev" in filename:
            dev_list = find_list(file_path)
        else:
            test_list = find_list(file_path)

    genres = ["academic", "bio", "fiction", "interview", "news", "voyage", "whow", "reddit", "conversation", "speech", "textbook", "vlog"]
    corpus_by_genre = {g:[] for g in genres}

    for filename in os.listdir(coref_path + os.sep + "conll"):
        print(filename)
        # if filename != 'GUM_reddit_conspiracy.conll':
        #     continue

        file_fields = filename.split(".")[0].split("_")
        conll_file = coref_path + os.sep + "conll" + os.sep + filename
        tsv_file = coref_path + os.sep + "tsv" + os.sep + filename.split(".")[0] + ".tsv"
        dep_file = dep_path + os.sep + filename.split(".")[0] + ".conllu"
        # tsv_file = coref_path + os.sep + "tsv" + os.sep + filename.split(".")[0] + ".tsv"
        docs[filename] = build_conll(read_conll_file(conll_file), read_tsv_file(tsv_file), read_dep_file(dep_file), file_fields, 0)

    if if_genre:
        for genre in genres:
            for filename in docs.keys():
                if genre in filename:
                    if filename.split(".")[0] in train_list:
                        train += docs[filename]
                    elif filename.split(".")[0] in dev_list:
                        dev += docs[filename]
                    elif filename.split(".")[0] in test_list:
                        test += docs[filename]
                        corpus_by_genre[genre] += docs[filename]

        for genre, text in corpus_by_genre.items():
            write_file(out_dir + os.sep + f"test.{genre}.gum.english.v4_gold_conll", text)

            write_file(out_dir + os.sep + "train.gum.english.v4_gold_conll", train)
            write_file(out_dir + os.sep + "dev.gum.english.v4_gold_conll", dev)
            write_file(out_dir + os.sep + "test.gum.english.v4_gold_conll", test)

    else:
        if not os.path.exists(os.path.join(out_dir, 'text')):
            os.mkdir(os.path.join(out_dir, 'text'))
            os.mkdir(os.path.join(out_dir, 'docs'))
            os.mkdir(os.path.join(out_dir, 'text', 'train'))
            os.mkdir(os.path.join(out_dir, 'text', 'dev'))
            os.mkdir(os.path.join(out_dir, 'text', 'test'))
            os.mkdir(os.path.join(out_dir, 'docs', 'train'))
            os.mkdir(os.path.join(out_dir, 'docs', 'dev'))
            os.mkdir(os.path.join(out_dir, 'docs', 'test'))
        data_split_mapping = {}
        for f in train_list:
            data_split_mapping[f] = 'train'
        for f in dev_list:
            data_split_mapping[f] = 'dev'
        for f in test_list:
            data_split_mapping[f] = 'test'

        for filename, doc in docs.items():
            name = filename.split(".")[0]
            dep_file = dep_path + os.sep + filename.split(".")[0] + ".conllu"
            text = ''
            with io.open(dep_file, encoding='utf-8') as f:
                lines = f.readlines()
                for line in lines:
                    if line.startswith('# text'):
                        sent = line.split('=')[-1].strip(' ')
                        text += sent
            with open(out_dir+os.sep+'text'+os.sep+data_split_mapping[name]+os.sep+filename.split(".")[0] + ".txt", "w", encoding="utf-8") as f:
                f.write(text.strip('\n'))

            with open(out_dir+os.sep+'docs'+os.sep+data_split_mapping[name]+os.sep+filename.split(".")[0] + ".conll", "w", encoding="utf-8") as f:
                f.write('\n'.join(doc))

    print("Done!")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--gum_coref_path', default=os.path.join('..', 'out'), help='Path to the ontogum (converted) coref out/ directory')
    parser.add_argument('--gum_dep_path', default=os.path.join('..', 'gum', 'dep'), help='Path to the gum/dep/ud directory')
    parser.add_argument('--split', default='splits', help='Path to the gum file split directory')
    parser.add_argument('--genre', action='store_true', help='If the conll file is combined by genre')
    parser.add_argument('--out_dir', default=os.path.join('..', 'dataset', 'converted'), help='Path to the output directory')
    args = parser.parse_args()

    gum_coref_path = args.gum_coref_path
    gum_dep_path = args.gum_dep_path
    gum_file_lists = args.split
    genre = args.genre
    out_dir = args.out_dir

    if not os.path.exists(out_dir):
        os.mkdir(out_dir)

    main(genre, gum_coref_path, gum_dep_path, out_dir, gum_file_lists=gum_file_lists)
