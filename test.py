import re


FORMAT_CODE = re.compile(r"(?<!\$)\$[0-9a-gklmnor]")

print(
    FORMAT_CODE.sub(lambda x: x.group(0).replace("$", "§"), "$$rawa$r").replace(
        "$$", "$"
    )
)
