# Script for restoring MongoDB dump archive (tar gz)
Usage:
Move script to dir, where you store archives
Run script
`python3 restore_mongo_dump.py DB_NAME`
or
`./restore_mongo_dump.py DB_NAME`
`DB_NAME` - name of MongoDB database which wou want to be restored from archive
**Current database `DB_NAME` will be dropped!!!**

Script need permissions to remove and create folder `tmp_dump` at dir it is

*Tested at Debian 8*
