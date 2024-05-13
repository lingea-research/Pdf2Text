## Tesseract Test
---
### Hand-written OCR
---
![alt text](file:///home/pablo/LINGEA/MASAPI/handwritten.png "Logo Title Text 1")
```
$ time { pdftoppm handwritten.pdf | tesseract - -; }
Estimating resolution as 538
In Australla, the Abc news «te
temporardy crashed under the wecght
of clucks and came back shortly after
woth a home page that only drsplayed
the one story that everyone wanted +o
read,

real	0m3.782s
user	0m6.073s
sys	0m0.215s
```
---
### Digital-font OCR
---
![alt text](file:///home/pablo/LINGEA/MASAPI/digital_font.png "Logo Title Text 1")
```
$ time { pdftoppm digital_font.pdf | tesseract - -; }
Estimating resolution as 496
In Australia, the ABC news site
temporarily crashed under the weight
of clicks and came back shortly after
with a home page that only displayed
the one story that everyone wanted to
read.

real	0m3.247s
user	0m5.408s
sys	0m0.194s
```
