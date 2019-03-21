#!/bin/bash
u=root
p=calvin
#
j="";job="";file="";checkifdone=""
donefile=jobs_donefile.ja; cp /dev/null $donefile
runfile=jobs_runfile.ja; cp /dev/null $runfile
checkrunfile="go"

while [ "$checkrunfile" != "" ]
do
   for file in `ls *_script.out`
   do
        ip=`echo $file |cut -d'_' -f1`
        for job in `grep 'i JID' $file |awk '{print $10}' |cut -d'"' -f1`
        do
                checkifdone=""; checkifdone=`grep $job $donefile`
                if [ "$checkifdone" = "" ]
                then
                        #status=`racadm -r $ip -u $u -p $p jobqueue view -i $job |grep 'Status=' |cut -d'=' -f2 |tr -d '\r'`
			racadm -r $ip -u $u -p $p jobqueue view > $ip'_'jobqueue.out
			echo $ip','$job','$status','`date`
                        if [ "$status" = "Completed" ]
                        then
                                echo $file','$job','$status','`date` >> $donefile
                                sed -i '/$job/d' $runfile
                        else
                                if [ "$?" != "0" ]
                                then
                                        echo $file','$job','$status >> $runfile
                                fi
                        fi
                fi
        done
   done
 sleep 10 
 checkrunfile=`tail -1 $runfile`
done

