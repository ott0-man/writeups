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

3. The empty file ("SORRY") jumped out at me, I ran another find command to try
   to see what other files there are. Some other files are "TROLLOL",
   "NOFLAG4U", "HAHA", "NEGATORY", "NOMATCH", "LOLNOPE".

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
   and the example code at https://gist.github.com/jonte/4577833 was very
   useful. I based my scripts on jonte's code.
   
   The FAT32 file is laid out something like this:

   | Layout                |
   |-----------------------|
   | Boot Parameter Block  |
   | File Allocation Table |
   | Data Cluster #2       |
   | Data Cluster #3       |
   | Data Cluster #4       |
   | Data Cluster #5       |
   | Data Cluster #6       |

   The "Boot Parameter Block" contains lots of metadata about the filesystem,
   and I used that to workout where the other blocks were, the size of
   clusters etc.

   First I wrote a function to parse the File Allocation Table, and used that to
   see what clusters were in use. This wasn't useful as far as the challenge
   goes, but it helped me understand the file structure.

   The Data Clusters contain both file contents and directories. All of these
   contain the name of the file, and some metadata including the number of the
   cluster containing either the file or the directory.

   This all starts at Data Cluster #2, which contains the root directory of the
   filesystem tree. So, for example, cluster #2 can hold dir entries which can
   point to cluster #5, which contains a dir entry pointing to cluster #3. It's
   by doing this that the filesystem has so many loops and is impossible to
   fully enumerate from the top down.

6. My plan of action is:

   1. Find the "MATCH" file entry.
   2. Find the cluster at the start of its directory.
   3. Find directory entries pointing to that entry.
   4. For every directory entry pointing to that one, add it to a possible flag.
   5. If the possible flag doesn't start with "PCTF", goto step 4. If not, WIN!

   The only problem was around step 2. The directory entries were bigger than
   the clusters. You had to find the entry and go backwards until a NUL-byte to
   find the start of the directory entry. This cluster number is the one that
   I had to search for in the next step.

7. Time to win:

   Grab the [tar file](strcmp.tar.gz) and [solve.py](solve.py) to try it out.

```
root@kali# python3 solve.py                                
}                                                         
!}                                                        
M!}                                                       
EM!}                                                      
TEM!}                                                     
TEM!}                                                     
STEM!}                                                    
<<< SNIP >>>
F{WHAT_IN_TARNATION_IS_TH1S_FILESYSTEM!}
TF{WHAT_IN_TARNATION_IS_TH1S_FILESYSTEM!}
CTF{WHAT_IN_TARNATION_IS_TH1S_FILESYSTEM!}
PCTF{WHAT_IN_TARNATION_IS_TH1S_FILESYSTEM!}
```

   
   
