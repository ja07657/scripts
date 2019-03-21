#!/bin/bash
newbranch=new1
#
git checkout -b $newbranch dev
exit
# make code changes in $newbranch
#
git commit -a -m "new code"
git push origin $newbranch
exit
#
git checkout dev
git pull origin dev
git checkout $newbranch
git pull origin $newbranch
git merge dev
git checkout dev
git pull origin dev
git merge --no-ff $newbranch
git push origin dev
exit
# remove new branch once merged
git branchd -d $newbranch
git push origin --delete $newbranch
exit
