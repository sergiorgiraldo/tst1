# Tar Usage / Cheat Sheet

## TL;DR;
## Compress a file or directory

> tar -czvf name-of-archive.tar.gz /path/to/directory-or-file

* -c: Create an archive.
* -z: Compress the archive with gzip.
* -v: makes tar talk a lot. Verbose output shows you all the files being archived and much.
* -f: Allows you to specify the filename of the archive.

## Extract an Archive

> tar -xzvf name-of-archive.tar.gz

* f: this must be the last flag of the command, and the tar file must be immediately after. It tells tar the name and path of the compressed file.
* z: tells tar to decompress the archive using gzip
* x: tar can collect files or extract them. x does the latter.
* v: makes tar talk a lot. Verbose output shows you all the files being extracted.

## More details

### TAR command examples usage and options
* c – create a archive file.
* x – extract a archive file.
* v – show the progress of archive file.
* f – filename of archive file.
* t – viewing content of archive file.
* j – filter archive through bzip2.
* z – filter archive through gzip.
* r – append or update files or directories to existing archive file.
* W – Verify a archive file.
* wildcards – Specify patterns in unix tar command.

## Create tar Archive

Create a tar archive file called archive.tar for a directory /home/cyberpunk/testdir in current working directory:

> tar -cvf archive.tar /home/cyberpunk/testdir/

/home/cyberpunk/testdir/

/home/cyberpunk/testdir/file1.txt

/home/cyberpunk/testdir/file2.sh

/home/cyberpunk/testdir/file3.tar

Option used in this example are:

* c – Creates a new .tar archive file.
* v – Verbosely show the .tar file progress.
* f – File name type of the archive file.
## Create Compressed tar.gz Archive

To create a compressed gzip archive we need use switch ‘z’.

> tar -cvzf compressedArchive.tar.gz /home/cyberpunk/testdir

/home/cyberpunk/testdir/

/home/cyberpunk/testdir/file1.txt

/home/cyberpunk/testdir/file2.jpg

/home/cyberpunk/testdir/file3.png

## Compress Even More – tar.bz2

TAR can create archives which are smaller than gzip file. To create highly compressed tar file you will need to pass a “j” switch to tar command. bz2 option takes more time to perform archive compression and decompression than gzip would take. Usually this time difference is negligible, but if you are archiving huge files, or very large number of files these timings add up and time difference can be significant.

> tar -cvfj Archive.tar.bz2 /home/cyberpunk/testdir

/home/cyberpunk/testdir/

/home/cyberpunk/testdir/file1.txt

/home/cyberpunk/testdir/file2.txt

/home/cyberpunk/testdir/file3.txt
## unTAR Archive

To untar ( extract ) a tar file, pass the ‘x‘ (extract) switch to the command

Issuing command without ‘-C’ switch will extract the archive in the current working directory. The -C switch tells the command WHERE to extract archive files

> tar -xvf Archive.tar -C /home/cyberpunk/testdir/

/home/cyberpunk/testdir/

/home/cyberpunk/testdir/file1.txt

/home/cyberpunk/testdir/file2.txt

/home/cyberpunk/testdir/file3.txt

## Extract tar.gz Archive 

All archive files tar can create are extracted in the same manner. Here’s the example:

Issuing command without ‘-C’ switch will extract the archive in the current working directory. The -C switch tells the command WHERE to extract archive files

> tar -xvf Archive.tar.gz

/home/cyberpunk/testdir/ 

/home/cyberpunk/testdir/file1.txt 

/home/cyberpunk/testdir/file2.txt 

/home/cyberpunk/testdir/file3.txt 

... and tar.bz2

> tar -xvf Archive.tar.bz2

/home/cyberpunk/testdir/

/home/cyberpunk/testdir/file1.txt

/home/cyberpunk/testdir/file2.txt

/home/cyberpunk/testdir/file3.txt
## List Content

To list the content of a tar archive use ‘ t ‘ switch:

> tar -tvf uploadprogress.tar

-rwxr--r-- root/root   1111 2014-10-19 12:33:42 file1.txt

-rwxr--r-- root/root   1111 2014-10-19 12:33:42 file2.txt

-rwxr--r-- root/root   1111 2014-10-19 12:33:42 file3.txt

-rwxr--r-- root/root   1111 2014-10-19 12:33:42 file4.txt

## Extract Single File From tar Archive

To extract a single file called file1.txt from archive.tar use the following command.

> tar --extract --file=archive.tar file1.txt

file1.txt

## Extract Multiple Files From tar Archive

To extract multiple files:

> tar -xvf Archive.tar "file 1" "file 2"

## Extract Group of Files using Wildcard

To extract a group of files we can use a wildcard format:

> tar -xvf Archive.tar --wildcards *.txt'

/home/cyberpunk/testdir/file1.txt

/home/cyberpunk/testdir/file2.txt

/home/cyberpunk/testdir/file3.txt

## Add Files or Directories to tar Archive

To add files or directories to existing tar file you can use the ‘ r ‘ switch. For example we add file xyz.txt and directory php to existing tecmint-14-09-12.tar archive file.

> tar -rvf Archive.tar xyz.txt  #add file

or

> tar -rvf Archive.tar php      # add directory