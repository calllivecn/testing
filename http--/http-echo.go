/*
# date 2020-10-19 11:15:47
# author calllivecn <c-all@qq.com>
*/


package main


import (
    "net/http"
    "fmt"
    "runtime"
)

func init(){
    runtime.GOMAXPROCS(1)
}

func echo(w http.ResponseWriter, r *http.Request) {
    r.ParseForm()
    fmt.Fprintf(w, "%s\n", r.URL.Path)
}

func main() {

    http.HandleFunc("/", echo)
    fmt.Println(http.ListenAndServe("0.0.0.0:8080", nil))

}


