/*
# date 2020-01-03 17:57:26
# author calllivecn <c-all@qq.com>
*/

package main

import (
    "fmt"
    "time"
)



func main() {

    var ch chan int

    go func() {
        fmt.Println(<-ch)
        time.Sleep(time.Second * 1)
    }()

    for i:= 0; i< 100;i++ {
        ch <- i
    }
}
