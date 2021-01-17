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
                    while ')(' in corefs:
                        corefs = re.sub('\)\(', ')|(', corefs)
                    while re.search('[0-9]\([0-9]', corefs):
                        corefs = re.sub('([0-9])(\([0-9])', '\g<1>|\g<2>', corefs)
                    while re.search('[0-9]\)[0-9]', corefs):
                        corefs = re.sub('([0-9]\))([0-9])', '\g<1>|\g<2>', corefs)
                new_line = '\t'.join(fields[:-1] + [corefs])
                conll_out.append(new_line)
    return conll_out


def read_dep_file(file):
    dic = {}
    filename = file.split('/')[-1].split('.')[0]
    with io.open(file, encoding="utf8") as f:
        sents = f.read().split('\n\n')
        for sent in sents[:-1]:
            sent_id = re.search(f'# sent_id = {filename}-([0-9]+?)\n', sent).group(1)
            speaker = re.search('# speaker=([\w\W]+?)\n', sent).group(1) if re.search('# speaker=([\w\W]+?)\n', sent) else '-'
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
        sent_id = int(tsv_fields[0].split("-")[0]) - 1
        token_id = int(tsv_fields[0].split("-")[1]) - 1
        if token_id == 0 and i != 0:
            in_text.append("")
        token = conll_fields[1]
        coref = conll_fields[-1]
        fields = [doc_key, str(doc_id), str(token_id), token, "-", "-", "-", "-", "-", f"{dep[str(sent_id+1)]}", "*", "*", "*", "*", "*",
                  "*", coref]
        in_text.append("\t".join(fields))

    in_text.append("")
    in_text.append("#end document")
    return in_text


def write_file(filename, lst):
    text = to_text(lst)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def main(if_genre, coref_path, dep_path, gum_file_lists=None):
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

    genres = ["academic", "bio", "fiction", "interview", "news", "voyage", "whow", "reddit"]
    corpus_by_genre = {g:[] for g in genres}

    for filename in os.listdir(coref_path + os.sep + "conll"):
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
                        corpus_by_genre[genre] += docs[filename]
                    elif filename.split(".")[0] in test_list:
                        test += docs[filename]

        for genre, text in corpus_by_genre.items():
            write_file("../dataset" + os.sep + f"dev_{genre}.gum.english.v4_gold_conll", text)

            write_file("../dataset" + os.sep + "train.gum.english.v4_gold_conll", train)
            write_file("../dataset" + os.sep + "dev.gum.english.v4_gold_conll", dev)
            write_file("../dataset" + os.sep + "test.gum.english.v4_gold_conll", test)

    else:
        out_dir = '../dataset/text'
        if not os.path.exists(out_dir):
            os.mkdir(out_dir)
        for filename, doc in docs.items():
            if filename.split(".")[0] in test_list:
                dep_file = dep_path + os.sep + filename.split(".")[0] + ".conllu"
                text = ''
                with io.open(dep_file, encoding='utf-8') as f:
                    lines = f.readlines()
                    for line in lines:
                        if line.startswith('# text'):
                            sent = line.split('=')[-1].strip(' ')
                            text += sent
                with open(out_dir+os.sep+filename.split(".")[0] + ".txt", "w", encoding="utf-8") as f:
                    f.write(text.strip('\n'))

    print("Done!")


if __name__ == "__main__":
    parser = ArgumentParser()
    parser.add_argument('--genre', action='store_true', help='If the conll file is combined by genre')
    args = parser.parse_args()

    gum_coref_path = ".."+os.sep+"out"
    gum_dep_path = ".."+os.sep+"gum"+os.sep+"dep"
    gum_file_lists = "splits"

    main(args.genre, gum_coref_path, gum_dep_path, gum_file_lists=gum_file_lists)
