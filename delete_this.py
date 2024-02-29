# t = ["a", "b", "c"]
# print("len(t): ", len(t))
# s = "abc"
# for i in range(0, len(s)):
#     print(s[i])
    
    
def strStr(haystack: str, needle: str) -> int:
    if haystack == needle: return 0
    if len(needle) == 1:
        for i in range(0, len(haystack)):
            print(haystack[i], needle)
            if haystack[i] == needle: return i
    else:
        for i in range(0, len(haystack) - len(needle)):
            substring = haystack[i:i+len(needle)]
            if substring == needle:
                return i
    return -1

print(strStr("abc", "c"))
