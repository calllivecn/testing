#!/bin/bash
# date 2023-06-13 20:09:48
# author calllivecn <c-all@qq.com>

EXCLUDE="--exclude server/dynmap/"

rsync -avHz $EXCLUDE --delete --progress -c tenw:/mnt/data1/mc18 .
