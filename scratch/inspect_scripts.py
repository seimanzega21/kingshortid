with open("d:\\kingshortid\\scratch\\cubetv_page.html", "r", encoding="utf-8") as f:
    for line in f:
        if "self.__next_f.push" in line:
            # Print first 500 chars of the line
            print(line[:500])
            print("-" * 50)
