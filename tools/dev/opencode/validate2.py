with open(r'G:\Downloads\Documents\go-model-benchmarks.md', 'rb') as f:
    md = f.read()
emdash = b'\xe2\x80\x94'
section = b'\xc2\xa7'
rightarrow = b'\xe2\x86\x92'
yen = b'\xc2\xa5'
multiplication = b'\xc3\x97'
en_dash = b'\xe2\x80\x93'
ellipsis = b'\xe2\x80\xa6'
leq = b'\xe2\x89\xa4'
geq = b'\xe2\x89\xa5'

print(f"em-dash: {md.count(emdash)} occurrences")
print(f"section sign: {md.count(section)} occurrences")
print(f"right arrow: {md.count(rightarrow)} occurrences")
print(f"yen: {md.count(yen)} occurrences")
print(f"multiplication: {md.count(multiplication)} occurrences")
print(f"en-dash: {md.count(en_dash)} occurrences")
print(f"ellipsis: {md.count(ellipsis)} occurrences")
print(f"less-equal: {md.count(leq)} occurrences")
print(f"greater-equal: {md.count(geq)} occurrences")
