#!/bin/bash
# date 2019-05-15 10:52:53
# author calllivecn <calllivecn@outlook.com>

HADOOP_HOME="/usr/local"


HADOOP_CMD="hadoop"

STREAM_JAR_PATH="${HADOOP_HOME}/share/hadoop/tools/lib/hadoop-streaming-3.1.2.jar"

INPUT_FILE_PATH_1="input/"

OUTPUT_PATH="output"

$HADOOP_CMD fs -rmr-skipTrash $OUTPUT_PATH

# Step 1.

$HADOOP_CMD jar $STREAM_JAR_PATH   \
	-input $INPUT_FILE_PATH_1   \
	-output $OUTPUT_PATH   \
	-mapper "python map.py"   \
	-reducer "python reduce.py"  \
	-file ./map.py   \
	-file ./reduce.py  \
