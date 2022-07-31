# Tar Usage / Cheat Sheet

## Compress a file or directory

e.g: `tar -czvf name-of-archive.tar.gz /path/to/directory-or-file`

* -c: Create an archive.
* -z: Compress the archive with gzip.
* -v: makes tar talk a lot. Verbose output shows you all the files being archived and much.
* -f: Allows you to specify the filename of the archive.

## Extract an Archive

e.g: `tar -xvzf name-of-archive.tar.gz`


* f: this must be the last flag of the command, and the tar file must be immediately after. It tells tar the name and path of the compressed file.
* z: tells tar to decompress the archive using gzip
* x: tar can collect files or extract them. x does the latter.
* v: makes tar talk a lot. Verbose output shows you all the files being extracted.
