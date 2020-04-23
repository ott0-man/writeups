file-system-based strcmp go brrrr
=================================

The Problem
-----------

strcmp go brrrr

Solving
-------

1. Downloaded and untarred the file, it has a file extension .fat32 and
   according to file does contain a DOS/MBR boot sector.

```
root@kali# file strcmp.fat32 
strcmp.fat32: DOS/MBR boot sector, code offset 0xfe+2, OEM-ID "strcmp  ",
reserved sectors 8, FAT  1, Media descriptor 0xf8, sectors/track 1, heads 1,
sectors 66057 (volumes > 32 MB), FAT (32 bit), sectors/FAT 513, reserved 0x1,
dos < 4.0 BootSector (0x0)
```

2. I mounted the file as a vfat device unveiling a whole load of single
   character subdirectories. Exploring around, it doesn't take long until the
   filesystem throws errors ("Too many levels of symbolic links").

   This error is slightly odd considering none of the files are symbolic links,
   but this is the same error given if there are loops defined in the filesystem
   itself.

```
root@kali# mount -t vfat strcmp.fat32 mnt/  
root@kali# ls -al mnt                                     
total 110                                                 
drwxr-xr-x 52 root root 2048 Jan  1  1980 '!'
drwxr-xr-x 52 root root 2048 Jan  1  1980 '#'
drwxr-xr-x 52 root root 2048 Jan  1  1980  %
<<< SNIP >>>
-rwxr-xr-x  1 root root    0 Jan  1  1980  SORRY
drwxr-xr-x 52 root root 2048 Jan  1  1980  SPACE
drwxr-xr-x 52 root root 2048 Jan  1  1980  T
drwxr-xr-x 52 root root 2048 Jan  1  1980  U
drwxr-xr-x 52 root root 2048 Jan  1  1980  V
drwxr-xr-x 52 root root 2048 Jan  1  1980  W
drwxr-xr-x 52 root root 2048 Jan  1  1980  X
drwxr-xr-x 52 root root 2048 Jan  1  1980  Y
drwxr-xr-x 52 root root 2048 Jan  1  1980  Z
root@kali# cd mnt/
root@kali# find
.
./SPACE
./SPACE/SPACE
./SPACE/SPACE/SPACE
find: ‘./SPACE/SPACE/SPACE/SPACE’: Too many levels of symbolic links
./SPACE/SPACE/SPACE/!
./SPACE/SPACE/SPACE/!/SPACE
./SPACE/SPACE/SPACE/!/SPACE/SPACE
./SPACE/SPACE/SPACE/!/SPACE/SPACE/SPACE
find: ‘./SPACE/SPACE/SPACE/!/SPACE/SPACE/SPACE/SPACE’: Too many levels of symbolic links
./SPACE/SPACE/SPACE/!/SPACE/SPACE/SPACE/!
find: ‘./SPACE/SPACE/SPACE/!/SPACE/SPACE/SPACE/!/SPACE’: Too many levels of symbolic links
```

3. The file ("SORRY") jumped out at me, I ran another find command to try to see
   what other files there are. Some other files are "TROLLOL", "LOLNOPE",
   "NOFLAG4U", "HAHA", "NEGATORY", "NOMATCH".

```
root@kali# find -t file 2> /dev/null
<<< SNIP - output far too long >>>
```

4. I decided to stop looking at the mounted version - I thought the too many
   levels issue would make inspecting it with find infeasible.

   Running strings on the strcmp.fat32 file reveals more filenames, and I am
   definitely interested in finding the directory containing the "MATCH" file.

   My theory now is that the path to the directory containing that file is the
   path.

```
root@kali# strings strcmp.fat32 | tr -s " " | strings -n 4 | sort | uniq
fat32 
HAHA 
LOLNOPE 
MATCH 
NEGATORY 
NOFLAG4U 
NOMATCH 
NOPE 
rrAa
RRaA
SORRY 
SPACE 
strcmp 
TOOBAD 
TROLLOL
```

5. Seeing as I chose not to use find, or other filesystem tools, I had to learn
   how the FAT32 filesystem is laid out.

   The PDF file at http://read.pudn.com/downloads77/ebook/294884/FAT32%20Spec%20%28SDA%20Contribution%29.pdf
   was very useful. The FAT32 file is laid out something like this:

   | Boot Parameter Block  |
   | File Allocation Table |
   | Data Cluster #2       |
   | Data Cluster #3       |
   | Data Cluster #4       |
   | Data Cluster #5       |
   | Data Cluster #6       |
