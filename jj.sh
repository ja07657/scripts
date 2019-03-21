#!/bin/bash
#jason amato
#
#get template and inventory, then update via idrac
#edit datadir and updatefile
#=========================================================================
#using ip from main.sh
d=$1
datadir="data"
repodir="repo"
updatefiles="bios.exe idrac.exe"
go="no"
creds="-r "$d" -u root -p calvin"
#--------------------------------------------------------------
echo $$ ${d}
#
#clear jobqueue
echo 'racadm jobqueue delete -i ALL '$creds
echo 'racadm jobqueue delete -i JID_CLEARALL_FORCE '$creds
#reset idrac
echo 'racadm racreset '$creds
#get stuff
echo 'racadm get -t xml -f ${datadir}/'${d}.xml $creds 
echo 'racadm swinventory '$creds' > swinv_${d}.out'
#update
for file in `echo $updatefiles`
do
 echo 'racadm update -f ${datadir}/${file} '$creds
 echo 'racadm jobqueue view '$creds
 do until [ "$go" = "yes" ]
	sleep 5 
	echo 'racadm jobqueue view |grep "Task successfully scheduled" '$creds
	if [ "$?" -eq "0" ]
	then
		echo "Task successfully scheduled"
		go="yes"
	fi
 done
done
#---------------------------------------------------------------------------
exit
#--------------------------------------------------------------------------------------
#powercycle if scheduled
if [ "$go" = "yes" ]
then
	go="no"
	echo 'racadm serveraction powercycle '$creds
fi
#wait for job completed successfully
echo 'racadm jobqueue view '$creds
do until [ "$go" = "yes" ]
        sleep 20 
        echo 'racadm jobqueue view |grep "completed successfully" '$creds
        if [ "$?" -eq "0" ]
        then
		echo 'racadm jobqueue view '$creds
                go="yes"
        fi
done
#RAC1118 : Update from repository operation has been initiated. Check the progress of the operation using "racadm jobqueue view -i JID_967692566322" command.

