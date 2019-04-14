hex_string = "64000:64000"
hex_conv = hex_string.split(':')
converted_hex = (int(hex_conv[0], 16) + int(hex_conv[1], 16))/8192
print(converted_hex)
