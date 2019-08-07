/*
# date 2019-08-07 17:24:17
# author calllivecn <c-all@qq.com>
*/

package main


import (
    "fmt"
    "net"
    //"bufio"
    "os"
    //"io"
    //"strings"
    //"bytes"
)


func main(){

    accept, err := net.Listen("tcp", "0.0.0.0:6789")
    if err != nil {
        fmt.Println("start verser Failed, %s\n", err)
        os.Exit(1)
    }

    fmt.Println("server start done")

    for{
        conn, err := accept.Accept()

        if err != nil {
            fmt.Println("Fail to connect %s\n", err)
        }

        fmt.Println("recv log: %s --> %s\n", conn.RemoteAddr(), conn.LocalAddr())
        go Echo(conn)
    }
}



func Echo(conn net.Conn) {

    if conn == nil {
        fmt.Println("exit...")
        return
    }

    //defer conn.Close()
    buf := make([]byte, 1<<10)
    //got := []byte("Got: ")
    for{

        data_len, err := conn.Read(buf)
        if err != nil || data_len == 0 {
            conn.Close()
            break
        }

        fmt.Println("Got: %s", buf)

        conn.Write(buf)

    }
}

