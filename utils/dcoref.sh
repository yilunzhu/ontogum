# !/bin/bash

# predict each document by using dcoref
echo "dcoref..."
python gum2xml.py

echo "xml to conll..."
PREDICT_DIR=../predicted/dcoref/xml
FINAL_OUT_DIR=../predicted/dcoref/conll
mkdir ../predicted/dcoref/conll
mkdir ../predicted/dcoref/conll/train ../predicted/dcoref/conll/dev ../predicted/dcoref/conll/test

for split_dir in $PREDICT_DIR/*
do
	split=${split_dir##*/}

	for file_dir in $PREDICT_DIR/$split/*.xml
	do
		# echo $file_dir
		file=${file_dir##*/}
		filename=${file%.xml}
		python corenlpxmltoconll2012.py $file_dir > $FINAL_OUT_DIR/$split/"${filename}.conll"
	done
done

# merge docs in the same genre
echo "Merging docs in the same genre..."
conll_dir='../predicted/dcoref/conll'
out_dir='../predicted/dcoref/out'
python conll_merge.py $conll_dir $out_dir

# evaluate
echo "Evaluating..."
cd scorer/v8.01
mkdir ../../../predicted/dcoref/res
perl scorer.pl all ../../../dataset/dev.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.conll > ../../../predicted/dcoref/res/dev/dev
perl scorer.pl all ../../../dataset/dev_academic.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.academic.conll > ../../../predicted/dcoref/res/dev/academic
perl scorer.pl all ../../../dataset/dev_bio.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.bio.conll > ../../../predicted/dcoref/res/dev/bio
perl scorer.pl all ../../../dataset/dev_fiction.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.fiction.conll > ../../../predicted/dcoref/res/dev/fiction
perl scorer.pl all ../../../dataset/dev_interview.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.interview.conll > ../../../predicted/dcoref/res/dev/interview
perl scorer.pl all ../../../dataset/dev_news.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.news.conll > ../../../predicted/dcoref/res/dev/news
perl scorer.pl all ../../../dataset/dev_reddit.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.reddit.conll > ../../../predicted/dcoref/res/dev/reddit
perl scorer.pl all ../../../dataset/dev_voyage.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.voyage.conll > ../../../predicted/dcoref/res/dev/voyage
perl scorer.pl all ../../../dataset/dev_whow.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.whow.conll > ../../../predicted/dcoref/res/dev/whow
perl scorer.pl all ../../../dataset/dev_conversation.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.conversation.conll > ../../../predicted/dcoref/res/dev/conversation
perl scorer.pl all ../../../dataset/dev_speech.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.speech.conll > ../../../predicted/dcoref/res/dev/speech
perl scorer.pl all ../../../dataset/dev_textbook.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.textbook.conll > ../../../predicted/dcoref/res/dev/textbook
perl scorer.pl all ../../../dataset/dev_vlog.gum.english.v4_gold_conll ../../../predicted/dcoref/out/dev.gum.vlog.conll > ../../../predicted/dcoref/res/dev/vlog



echo "Done."