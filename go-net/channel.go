/*
# date 2020-01-03 17:57:26
# author calllivecn <calllivecn@outlook.com>
*/

package main

import (
    "fmt"
    "time"
)



func main() {

    // 这样只是声明，它没有初始化(也就是没有容量，没有容量不会发生阻塞。go func(){...}()会立刻退出。
    // 导致"fatal error: all goroutines are asleep - deadlock!")
    //var ch chan int

    // 加上容量就好。

    ch := make(chan int, 1)
    //var ch chan int = {0};

    defer close(ch)

    go func() {
        for result := range ch {
            fmt.Println(result)
        }
    }()

    for i:= 0; i< 15;i++ {
        fmt.Println("write channel:", i)
        ch <- i
        time.Sleep(time.Second * 1)
    }
    //time.Sleep(time.Second * 10)
}
