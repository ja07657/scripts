#!/bin/bash
#jason amato
#jj_idracipmain.sh
#calls jj_idracip.sh
#uses idrac_ipfile
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
cat idrac_ipfile | parallel -j 8 ./jj_idracip.sh $DRACUSER $DRACPASS >>$o 2>>$e 
#
echo "Jobs running...check job queues..." |tee -a $o 
date |tee -a $o
#---------------------------------------------------------------------------
# while true; do ./check2.sh; sleep 10; done

