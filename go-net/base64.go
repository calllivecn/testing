/*
# date 2020-01-03 17:18:45
# author calllivecn <calllivecn@outlook.com>
*/

package main

import b64 "encoding/base64"
import "fmt"

func main() {

    data := "张旭"
    senc := b64.StdEncoding.EncodeToString([]byte(data))
    fmt.Println(senc)
}
