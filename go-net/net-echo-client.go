/*
# date 2020-01-03 22:39:22
# author calllivecn <calllivecn@outlook.com>
*/


package main

import (
    "strings"
    "bufio"
    "fmt"
    "net"
    "os"
)

func main() {

    buf := make([]byte, 512)
    stdin := bufio.NewReader(os.Stdin)

    conn, err := net.Dial("tcp", "127.0.0.1:6789")
    if err != nil {
        fmt.Println("net.dial() error: ", err)
        os.Exit(1)
    }
    defer conn.Close()

    for {
        cmd, err := stdin.ReadString('\n')
        if err != nil {
            fmt.Println("stdin.ReadString error")
        }

        if strings.HasSuffix(cmd, "\n") {
            cmd = cmd[:len(cmd)-1]
        }

        if "quit" == cmd {
            fmt.Println("退出～～～！")
            os.Exit(0)
        }

        conn.Write([]byte(cmd))
        data , _ := conn.Read(buf[:])
        fmt.Println(string(data))

    }
}
