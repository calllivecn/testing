/*
# date 2020-08-21 10:46:14
# author calllivecn <c-all@qq.com>
*/


package main

import (
    "fmt"
    "encoding/binary"
    "unsafe"
)

type cmd struct{
    l uint16
    i uint16
    long uint32
}


func main(){
    cmd := cmd{}
    fmt.Println("binary.Size() 计算结构体大小: ", binary.Size(cmd))
    fmt.Println("unsafe.Sizeof()计算结构体大小: ", unsafe.Sizeof(cmd))
}
