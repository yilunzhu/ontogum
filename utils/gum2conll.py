import io, os, sys
import re
from copy import deepcopy


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


def build_conll(conll, tsv, file_fields, doc_id):
    genre = file_fields[1]
    doc = file_fields[2]
    in_text = [f"#begin document ({genre}/{doc}); part 000"]
    for i in range(len(conll)):
        if i == 22:
            a = 1
        conll_fields = conll[i].split("\t")
        tsv_fields = tsv[i].split("\t")
        doc_key = f"{genre}/{doc}"
        # sent_id = int(tsv_fields[0].split("-")[0]) - 1
        token_id = int(tsv_fields[0].split("-")[1]) - 1
        if token_id == 0 and i != 0:
            in_text.append("")
        token = conll_fields[1]
        coref = conll_fields[-1]
        fields = [doc_key, str(doc_id), str(token_id), token, "_", "_", "_", "_", "_", "_", "*", "*", "*", "*", "*",
                  "*", coref]
        in_text.append("\t".join(fields))

    in_text.append("")
    in_text.append("#end document")
    return in_text


def write_file(filename, lst):
    text = to_text(lst)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def main(coref_path, gum_file_lists=None):
    train_list = []
    dev_list = []
    test_list = []
    train = []
    dev = []
    test = []

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

    for genre in genres:
        for filename in os.listdir(coref_path + os.sep + "conll"):
            if genre in filename:
                # if filename != 'GUM_news_homeopathic.conll':
                #     continue
                file_fields = filename.split(".")[0].split("_")
                conll_file = coref_path + os.sep + "conll" + os.sep + filename
                tsv_file = coref_path + os.sep + "tsv" + os.sep + filename.split(".")[0] + ".tsv"
                # tsv_file = coref_path + os.sep + "tsv" + os.sep + filename.split(".")[0] + ".tsv"

                if filename.split(".")[0] in train_list:
                    train += build_conll(read_conll_file(conll_file), read_tsv_file(tsv_file), file_fields, 0)
                elif filename.split(".")[0] in dev_list:
                    dev += build_conll(read_conll_file(conll_file), read_tsv_file(tsv_file), file_fields, 0)
                    corpus_by_genre[genre] += build_conll(read_conll_file(conll_file), read_tsv_file(tsv_file), file_fields, 0)
                elif filename.split(".")[0] in test_list:
                    test += build_conll(read_conll_file(conll_file), read_tsv_file(tsv_file), file_fields, 0)
                else:
                    sys.stderr.write(f"ERROR: file {filename} not in list.\n")
                    # sys.exit()

        # assert len(conll_lst) == len(tsv_lst)

    for genre, text in corpus_by_genre.items():
        write_file("../dataset" + os.sep + f"dev_{genre}.gum.english.v4_gold_conll", text)

        write_file("../dataset" + os.sep + "train.gum.english.v4_gold_conll", train)
        write_file("../dataset" + os.sep + "dev.gum.english.v4_gold_conll", dev)
        write_file("../dataset" + os.sep + "test.gum.english.v4_gold_conll", test)

    print("Done!")


if __name__ == "__main__":
    gum_coref_path = ".."+os.sep+"out"
    gum_file_lists = "splits"
    main(gum_coref_path, gum_file_lists=gum_file_lists)
