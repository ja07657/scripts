#!/bin/sh
#jason amato 2019
###########
repos=`drm -li=rep |egrep -v 'Listing|Name|----' |awk '{print $1}'`
#repos="r420 14G_linux 14G_windows 13G_linux 13G_windows"
###########
#-functions-----------------------------------------
check_job () {
  sleep 5
  job_status=`drm --list=job |grep 'RUNNING' |tail -1 |awk '{print $3}'`
  echo "job status: $job_status"
  while [ "$job_status" = "RUNNING" ] || [ "$job_status" = "" ]
  do
      echo "Waiting for job to complete..."
      echo "job status: $job_status"
      sleep 5 
      job_status=`drm --list=job |tail -1|awk '{print $3}'`
      echo "job status: $job_status"
      if [ "$job_status" = "" ]
      then
  	  job_status=`drm --list=job  |tail -2 |head -1 |awk '{print $3}'`
          
      fi
  done
}
#######
#-functions-end----------------------------------------
#######
#wget -O /tmp/Catalog.xml.gz http://ftp.dell.com/catalog/Catalog.xml.gz
#gunzip /tmp/Catalog.xml.gz
#drm --create --repository=${r} --inputplatformlist=${r} --dupformat="Windows-64" --source=/tmp/Catalog.xml
#0000
#update main catalog-----------------
drm --update --catalog=ALL |grep 'Updates not available'
if [ "$?" != "0" ]
then
	check_job
else
        echo "Updates not available"
fi
#
#update repos--------------------
for r in $repos
do
 #
 export_dest="/export/repo/${r}"
 #
 latest=`drm --details --repository=${r} |egrep 'MB|GB' |head -1 |awk '{print $1}'`
  echo "--------------------------------------------------------------------------------------"
 echo ${r}
 echo "Latest version: ${latest}"
 drm --compare --repository=${r}:${latest} |grep Upgrade
 if [ "$?" = "0" ]
 then
  echo "Updating repo...${r}"
  sleep 2
  drm --update --repository=${r}:${latest}
  check_job
    if [ "$job_status" = "FAILURE" ]
    then
		echo "repo update job FAILED for ${r}"
		drm --list=job |tail -1
		sleep 8
    else
      if [ ! -d /export/repo/${r} ]
      then
	mkdir ${export_dest}
        chown drmuser:drmuser ${export_dest}
        chmod 775 ${export_dest}
      fi
      drm --deployment-type=export --repository=${r}:${latest} --location=${export_dest}
      check_job
    fi
 else
  echo $?
  echo "--------------------------------------------------------------------------------------"
  echo "No updates for ${r}"
 fi
 drm --details --repository=${r}
done
#
drm --list=job
drm -li=rep
