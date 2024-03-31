/*
# date 2020-01-03 10:43:30
# author calllivecn <calllivecn@outlook.com>
*/

package main

import (
    "os"
    //"net"
    "bufio"
    "fmt"
    "strings"
)

func main(){

    ReadStdin()
    //BufRead()

}


func ReadStdin() {
    //var buf [128]byte

    for {

        buf := make([]byte, 128)

        n, err := os.Stdin.Read(buf)
        if err != nil {
            fmt.Println("read in stdin error OR EOF.  exit.")
            os.Exit(1)
        }else{
            fmt.Print("input bytes: ", n, "    ")
        }

        // why???
        //var cmd string

        /*
        if '\n' == buf[n] {
            cmd = string(buf[:n-1])
        }
        */

        cmd := string(buf[:n-1])

        fmt.Println("cmd len:", len(cmd))
        if "quit" == cmd {
            fmt.Println("exit~")
            break
        }
        fmt.Println("your input: ", cmd)
    }

}


func BufRead() {
    reader := bufio.NewReader(os.Stdin)
    for {

        cmd, err := reader.ReadString('\n')

        if err != nil {
            fmt.Println("read in os.stdin Error.")
            os.Exit(1)
        }

        if strings.HasSuffix(cmd, "\n") {
            //fmt.Print("有后缀: LF  ")
            //fmt.Printf("cmd 的类型:%t \n", cmd)
            //cmd = strings.Split(cmd, '\n')
            cmd = cmd[:len(cmd)-1]
        }

        if "quit" == cmd {
            fmt.Println("exit~")
            os.Exit(0)
        }else{
            fmt.Printf("your input: %s\t len cmd: %d\n", cmd, len(cmd))
        }
    }
}
