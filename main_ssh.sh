#!/bin/bash
#jason amato
#main_ssh.sh
#calls jj_ssh.sh
#uses ipfile
#========================
#-o "StrictHostKeyChecking no"
o=/tmp/out
e=/tmp/err
#-----------------------
echo "Enter iDRAC user name for the account you will use: "
read -s DRACUSER
echo "Enter iDRAC password for the account you will use: "
read -s DRACPASS
#----------------------
date > $o
date
date > $e
echo "STARTING..." |tee -a $o
#
#cat ipfile | parallel --dry-run -j 8 ./jj.sh $DRACUSER $DRACPASS >>$o 2>>$e
cat ipfile | parallel -j 8 ./jj_ssh.sh $DRACUSER $DRACPASS >>$o 2>>$e 
#
echo "Jobs running...check job queues..." |tee -a $o 
date |tee -a $o
#---------------------------------------------------------------------------
# while true; do ./check2.sh; sleep 10; done

