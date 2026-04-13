
() => {

    const rso = document.getElementById("rso")
    if (!rso) return []

    // const a_list = rso.querySelectorAll("a")

    const result_div = rso.querySelectorAll("[data-snc]")

    const links = []

    for(const a_data_snc of result_div){

        const a = a_data_snc.querySelector("a")
        if (!a) continue

        const url = a.href
        // const text = a.innerText.trim()
        const title = a.querySelector("h3").innerText.trim()

        
        const data_sncf = a_data_snc.querySelector("div[data-sncf]")
        
        let text = ""
        if (data_sncf) {
            for (const span of data_sncf.querySelectorAll("span")) {
                text += span.innerText.trim()
            }
        }
        
        // console.log("url=", url, "\n", "text=", text, "\n", "spanText=", spanText)
        // console.log("=================================")

        links.push({
            "url": url,
            "title": title,
            "text": text,
        })
    }

    return links
}
