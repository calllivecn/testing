
echo "start shell pid is  $$"

safe_exit(){
echo "safe exit... pid "$*""
kill "$@"
echo "成功安全退出"
}

start_func(){
set -e
polipo -c /config & 
pid1=$!
sslocal -c /sslocal.json &
pid2=$!
set +x
}

start_func

trap "safe_exit $pid1 $pid2" SIGTERM SIGINT

wait $pid1 $pid2
echo "start shell exit ..."
