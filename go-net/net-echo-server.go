/*
# date 2020-01-03 10:43:30
# author calllivecn <calllivecn@outlook.com>
*/

package main

import (
    "os"
    "net"
    "bufio"
    "fmt"
    //"strings"
)

func main(){

    go func(){
        accept()
    }()

    for {
        if cmd, err := bufio.NewReader(os.Stdin).ReadString('\n'); err != nil {
            fmt.Println("read stdin error exit...")
            os.Exit(1)
        }else if cmd == "quit\n" {
            fmt.Println("server exit...")
            os.Exit(0)
        }else if cmd != "quit\n" {
            fmt.Println("pleace enter `quit` exit program.")
        }
    }
}

func accept(){

    server, err := net.Listen("tcp", ":6789")
    if err != nil {
        fmt.Println("listen error:", err)
        os.Exit(1)
    }
    fmt.Println("listen Start:")

    for {
        sock, err := server.Accept()
        if err != nil {
            fmt.Println(err)
        }else{
            fmt.Println(sock.LocalAddr(), "<--", sock.RemoteAddr())
        }

        go Client(sock)
    }
}



func Client(conn net.Conn) {

    defer conn.Close()

    //buf_r := bufio.NewReader(conn)
    //buf_w := bufio.NewWriter(conn)

    for {
        recv_buf := make([]byte, 128)
        n, err := conn.Read(recv_buf)
        if err != nil || n == 0 {
            fmt.Println("disconnect ...")
            fmt.Printf("err: %v\tn: %d\n", err.Error(), n)
            return
        }

        fmt.Println("recv data:", string(recv_buf))

        n, err = conn.Write(append([]byte("Got: "), recv_buf[:n]...))
        if err != nil {
            fmt.Println("write error:", err)
            return
        }
    }
}
