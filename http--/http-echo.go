/*
# date 2020-10-19 11:15:47
# author calllivecn <calllivecn@outlook.com>
*/


package main


import (
    "net/http"
    "fmt"
    "runtime"
    _ "time"
    _ "math/rand"
)

func init(){
    runtime.GOMAXPROCS(1)
}

/*
func echo_rand_sleep(w http.ResponseWriter, r *http.Request) {
    t := rand.Intn(3000)
    time.Sleep(time.Duration(t) * time.Millisecond)
    r.ParseForm()
    fmt.Fprintf(w, "%s\n", r.URL.Path)
}
*/

func echo(w http.ResponseWriter, r *http.Request) {
    r.ParseForm()
    fmt.Fprintf(w, "%s\n", r.URL.Path)
}

func main() {
    addr := "0.0.0.0:6789"
    fmt.Println("listen: ", addr)
    http.HandleFunc("/", echo)
    fmt.Println(http.ListenAndServe(addr, nil))

}


