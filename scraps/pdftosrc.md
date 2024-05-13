## pdftosrc test

The following is an example of creating a PDF document with an "embedded object," then attempting to extract any objects using _pdftosrc_. This PDF file was created in LibreOffice as an ODT that was then exported. It contains that embedded ODT of itself.

```
$ seq 0 15 | xargs -n1 pdftosrc pdftosrc.pdf 
pdftosrc version 0.41.0
No SourceObject found           # [sic] stream 0 is the default if no stream-object-number is given
pdftosrc version 0.41.0
Not a Stream object
pdftosrc version 0.41.0
Stream object extracted to pdftosrc.2
pdftosrc version 0.41.0
Not a Stream object
pdftosrc version 0.41.0
Stream object extracted to pdftosrc.4
pdftosrc version 0.41.0
Stream object extracted to pdftosrc.5
pdftosrc version 0.41.0
Not a Stream object
pdftosrc version 0.41.0
Stream object extracted to pdftosrc.7
pdftosrc version 0.41.0
Not a Stream object
pdftosrc version 0.41.0
Stream object extracted to pdftosrc.9
pdftosrc version 0.41.0
Not a Stream object
pdftosrc version 0.41.0
Stream object extracted to pdftosrc.11
pdftosrc version 0.41.0
Not a Stream object
pdftosrc version 0.41.0
Not a Stream object
pdftosrc version 0.41.0
Stream object extracted to pdftosrc.14
pdftosrc version 0.41.0
Not a Stream object
(u) ~/Desktop/lingea
$ # there may have been more than 15 in this doc, but looks like we already found the embedded ODT (obj #11)
$ file pdftosrc.*
pdftosrc.11:  OpenDocument Text
pdftosrc.14:  data
pdftosrc.2:   ASCII text
pdftosrc.4:   data
pdftosrc.5:   Sendmail frozen configuration  - version )5#)7#)7(,8$(4''3**6+)4(&1*$.*'0)'2))3**4$$.)'4-+8#!.+)6)'4(&3.
pdftosrc.7:   data
pdftosrc.9:   data
pdftosrc.odt: OpenDocument Text
pdftosrc.pdf: PDF document, version 1.6
```

### the following is some copy that was added to this document to make it longer

