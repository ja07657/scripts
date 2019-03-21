#!/bin/bash
#check2.sh
#check jobqueue status and write to summary file, complete or not complete (running)
#----------------------------------
#uses ipfile
#-----------------------------------
u=root
p=Welcome1
#
firsttime="yes"
if [ "$firsttime" = "yes" ]
then
	rm *_jobqueue.out
else
	firsttime = "no"
fi
#
ip=""
donefile=jobs_donefile.ja; cp /dev/null $donefile
runfile=jobs_runfile.ja; cp /dev/null $runfile
failfile=jobs_failfile.ja; cp /dev/null $failfile

for ip in `cat ipfile`
do
	echo $ip
	racadm -r $ip -u $u -p $p --nocertwarn jobqueue view > $ip'_'jobqueue.out
done
for file in `ls *_jobqueue.out`
do
  readarray arrayj < $file
  acount=${#arrayj[@]}
  for (( i=0; i<${acount}; i++ ))
  do
	case ${arrayj[$i]} in 
	\[Job*)
		jobid=`echo ${arrayj[$i]} |tr -d '\r'`
	;;
	Job*Name*)
		jobname=`echo ${arrayj[$i]} |tr -d '\r'`
	;;
	Status*)
		status=`echo ${arrayj[$i]} |tr -d '\r'`
		echo $status |grep Failed 
		if [ "$?" = "0" ]
		then
			echo $ip","$jobid","$jobname","$status","`date` >> $failfile
		else
			echo $status |grep Completed
			if [ "$?" = "0" ]
			then 
				echo $ip","$jobid","$jobname","$status","`date` >> $donefile
			else
				echo $ip","$jobid","$jobname","$status","`date` >> $runfile
			fi
		fi
	;;
	
	esac
  done
done

echo "___________________________________________"
cat $donefile
echo "___________________________________________"
cat $failfile
echo "___________________________________________"
cat $runfile
