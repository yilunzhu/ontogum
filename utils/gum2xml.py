import io, os, sys
from stanza.server import CoreNLPClient
os.environ["CORENLP_HOME"] = '..'+os.sep+'gum'+os.sep+'utils'+os.sep+'core_nlp'


def find_list(file):
    file_list = []
    with io.open(file) as f:
        for line in f.readlines():
            if line.startswith("GUM"):
                file_list.append(line.strip())
    return file_list


def build_text(file):
    lst = []
    with io.open(file, encoding="utf8") as f:
        lines = f.read().split('\n')
        for line in lines:
            if line.startswith('#Text='):
                sent = line.strip('#Text=')
                lst.append(sent)
    return '\n'.join(lst)


def write_file(filename, text):
    with open(filename, "w", encoding="utf-8") as f:
        f.write(text)


def main(coref_path, out_dir, gum_file_lists=None):
    train_list = []
    dev_list = []
    test_list = []

    for filename in os.listdir(gum_file_lists):
        file_path = gum_file_lists + os.sep + filename
        if "train" in filename:
            train_list = find_list(file_path)
        elif "dev" in filename:
            dev_list = find_list(file_path)
        else:
            test_list = find_list(file_path)

    genres = ["academic", "bio", "fiction", "interview", "news", "voyage", "whow", "reddit"]

    for genre in genres:
        for filename in os.listdir(coref_path + os.sep + "conll"):
            if genre in filename:
                tsv_file = coref_path + os.sep + "tsv" + os.sep + filename.split(".")[0] + ".tsv"

                text = build_text(tsv_file)
                with CoreNLPClient(
                        properties={
                                    'annotators': 'tokenize,ssplit,pos,lemma,ner,parse,dcoref',
                                    'ssplit.eolonly': True,
                                    'tokenize.whitespace': True,
                                },
                        output_format='xml',
                        timeout=60000,
                        memory='8G') as client:
                    xml_out = client.annotate(text)

                if filename.split(".")[0] in train_list:
                    write_file(out_dir + os.sep + 'train' + os.sep + filename.split(".")[0] + '.xml', xml_out)
                elif filename.split(".")[0] in dev_list:
                    write_file(out_dir + os.sep + 'dev' + os.sep + filename.split(".")[0] + '.xml', xml_out)
                elif filename.split(".")[0] in test_list:
                    write_file(out_dir + os.sep + 'test' + os.sep + filename.split(".")[0] + '.xml', xml_out)
                else:
                    sys.stderr.write(f"ERROR: file {filename} not in list.\n")

    print("Done!")


if __name__ == "__main__":
    gum_coref_path = ".."+os.sep+"out"
    # gum_coref_path = ".." + os.sep + "gum" + os.sep + "coref"
    gum_file_lists = "splits"
    out_dir = '..' + os.sep + 'predicted' + os.sep + 'hcoref' + os.sep + 'xml'
    main(gum_coref_path, out_dir, gum_file_lists=gum_file_lists)
