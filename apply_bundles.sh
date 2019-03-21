#!/bin/sh
STATUS=0
SCRIPT_DIR="/opt/dell/toolkit/systems/drm_files/repository/"
PAYLOAD_DIR="/bundleapplicationlogs/"
cd /
mkdir "$PAYLOAD_DIR"
chmod -Rf 777 "$PAYLOAD_DIR"
cd "$SCRIPT_DIR"

MY_TIME=`date`
echo "apply_bundles.sh start time:$MY_TIME" | tee -a /bundleapplicationlogs/apply_components.log

##The following code to eject the disc is commented out since the plugin does not always support the eject command
##
##usingCD=0
##DRM_BOOT_DEVICE=`mount | grep "opt/dell/toolkit/systems" | awk '{print $1}'`
##
##echo $DRM_BOOT_DEVICE | grep "cdrom" 1>/dev/null 2>&1
##if [ "$?" -eq "0" ]; then
##    let usingCD=1
##fi
##
##echo $DRM_BOOT_DEVICE | grep "dvd" 1>/dev/null 2>&1
##if [ "$?" -eq "0" ]; then
##    let usingCD=1
##fi
##
##echo $DRM_BOOT_DEVICE | grep "cdrw" 1>/dev/null 2>&1
##if [ "$?" -eq "0" ]; then
##    let usingCD=1
##fi
##
##echo $DRM_BOOT_DEVICE | grep "cdwrite" 1>/dev/null 2>&1
##if [ "$?" -eq "0" ]; then
##    let usingCD=1
##f1    

####if running from CD   
##if [ "$usingCD" == "1" ]; then
	####Create and start script to eject disc
	##cat>/tmp/DRMeject.sh<<_EOF
	###!/bin/bash
	##DRMid=\`ps ax | grep apply_bundles.sh | grep -v grep | awk '{print \$1}'\`
	##if [ "x\$DRMid" != "x" ]; then
	##	while ps -p \$DRMid > /dev/null
	##	do
   	##		sleep 1
	##	done
	##fi
	##cd /
	##eject $DRM_BOOT_DEVICE
	##rm /tmp/DRM_mount
##_EOF
##	
##chmod +xxx /tmp/DRMeject.sh
##nohup /tmp/DRMeject.sh & > /dev/null
##fi

## Check for supported system, if the system is supported by this Deployment Media
## then, apply the components directly. Otherwise, a user shall select from a menu

# preset matched bundle location
MATCHEDBUNDLE=""
# execute check sysid script if the script is found
if [ -f "/opt/dell/toolkit/systems/drm_files/reserved/checksysid.sh" ]
then
	. "/opt/dell/toolkit/systems/drm_files/reserved/checksysid.sh"
fi

if [ "$MATCHEDBUNDLE" != "" ]
then
	cd "$SCRIPT_DIR""$MATCHEDBUNDLE"
else
	DIR_ARRAY_LENGTH=0
	echo "Please select a bundle to deploy on this system"
	echo ""

	find ./* -type d  > "$PAYLOAD_DIR"tempDirList.tmp

	while read file;
	do
		echo `expr $DIR_ARRAY_LENGTH + 1`". ""${file:2}"
		DIR_ARRAY[${#DIR_ARRAY[*]}]="${file:2}"
		DIR_ARRAY_LENGTH="${#DIR_ARRAY[*]}"
	done < "$PAYLOAD_DIR"tempDirList.tmp

	for i in ${!DIR_ARRAY[*]}
	do
		VALID_INPUT_ARRAY[i]=`expr $i + 1`
	done

	echo ""
	SELECTION_INDEX=-1
	MAX_VALID_INDEX=`expr $DIR_ARRAY_LENGTH - 1`


	while [  "$SELECTION_INDEX" -lt 0 ] || [ "$SELECTION_INDEX" -gt "$MAX_VALID_INDEX" ]
	do
		#if [ "$MAX_VALID_INDEX" -eq 0 ]
		#then
		#	SELECTION_INDEX=1
		#else
			echo ""
			echo "Input the number corresponding to the bundle you would like to apply to this system followed by <ENTER>"
			read SELECTION_INDEX
		#fi
		
		#validate selection index
		VALID=false
		for INDEX in ${VALID_INPUT_ARRAY[*]}
		do
			
			if [ "$INDEX" == "$SELECTION_INDEX" ]
			then
				VALID=true
				break
			fi
		done

		if [ $VALID == true ]
		then
			SELECTION_INDEX=`expr $SELECTION_INDEX - 1`	
		else
			SELECTION_INDEX=-1
		fi
	done


	# change directory to a bundle folder, then execute all .sh files from there
	cd "$SCRIPT_DIR""${DIR_ARRAY[SELECTION_INDEX]}"
fi

for i in `ls *.sh`
do
	echo "executing script $i"
	./"${i}"
	if [ "$?" != 0 ]
	then
		STATUS=1
		break
	fi
done

if [ -f "$PAYLOAD_DIR"tempDirList.tmp ]
then
	rm "$PAYLOAD_DIR"tempDirList.tmp
fi

# run custom scripts
cd $(dirname $0)

for i in `ls *.sh`
do
	if [ "$i" != "$(basename $0)" ]
	then
		echo "executing user's custom script: $i"
		./"${i}"
		if [ "$?" != 0 ]
		then
			STATUS=1
			break
		fi
	fi
done
MY_TIME=`date`
echo "apply_bundles.sh end time:$MY_TIME" | tee -a /bundleapplicationlogs/apply_components.log

reboot
exit "$STATUS"
