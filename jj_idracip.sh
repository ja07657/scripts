#!/bin/bash
#jason amato
##jj_idracip.sh
#called by main_ssh.sh
#get template and inventory, then update via idrac
#edit datadir and updatefile
#=========================================================================
#-----------------------------
#from main_ssh.sh
u=$1
p=$2
line=$3
oldip=`echo $line |cut -d',' -f1`
newip=`echo $line |cut -d',' -f2`
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------

echo $$' '$u' old='$oldip' new='$newip


#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#
> ${oldip}_script.out

script -c "
	sshpass -p ${p} ssh -o 'StrictHostKeyChecking no' ${u}@${oldip} <<-'ENDSSH'
	racadm get iDRAC.IPv4.Address
	racadm get iDRAC.IPv4.Netmask
	racadm get iDRAC.IPv4.Gateway
	exit
ENDSSH 
" ${oldip}_script.out
#
#
exit
exit
exit
exit

#--------------------------------------------------------------
#racadm get iDRAC.IPv4.Address
#racadm get iDRAC.IPv4.Netmask
#racadm get iDRAC.IPv4.Gateway
#--------------------------------------------------------------------------------------------
#racadm racreset 
#-----------------------------
#	racadm set iDRAC.IPv4.Address $newip
#	racadm set iDRAC.IPv4.Netmask 255.255.255.128
#	racadm set iDRAC.IPv4.Gateway 10.40.195.129
#-------------------------------
#-o "StrictHostKeyChecking no"







#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------
#	sshpass -p ${p} ssh ${u}@${d} <<-'ENDSSH'
#        racadm jobqueue delete -i ALL
#        racadm jobqueue delete -i JID_CLEARALL
#        racadm vmdisconnect
#        racadm closessn -a
#	racadm get -t xml -f ${d}.xml -l //10.40.54.65/share -u Dell -p Pass1234
#	racadm systemconfig backup -f image.img -l //10.40.54.65/share -u Dell -p Pass1234 
#       racadm update -f Catalog.xml -e 10.40.54.65/repo/r730 -a TRUE -t HTTP --verifycatalog
#       racadm update -f Catalog.xml -e 10.40.54.65/repo/r630 -a TRUE -t HTTP --verifycatalog
#racadm update -f Catalog.xml -l //10.40.54.65/share/repo/r730 -u Dell -p Pass1234 -t CIFS -a TRUE --verifycatalog
#racadm update -f Catalog.xml -l //10.40.54.65/share/repo/r630 -u Dell -p Pass1234 -t CIFS -a TRUE --verifycatalog
#racadm update -f Catalog.xml -l //10.40.54.65/share/repo/r740xd -u Dell -p Pass1234 -t CIFS -a TRUE --verifycatalog
#racadm update -f Catalog.xml -l //10.40.54.65/share/repo/fc430 -u Dell -p Pass1234 -t CIFS -a TRUE --verifycatalog
#racadm update -f Catalog.xml -l //10.40.54.65/share/repo/DellPowerEdgeMay2017Windows -u Dell -p Pass1234 -t CIFS -a TRUE --verifycatalog
#--------------------------------------------------------------------------------------------
#racadm jobqueue view
#racadm jobqueue delete -i ALL 
#racadm jobqueue delete -i JID_CLEARALL

#
#racadm racreset soft 
#racadm serveraction powercycle
#racadm serveraction powerdown
#racadm serveraction powerup
#
#racadm update -f Catalog.xml -e 10.40.54.65/repo/r630 -a TRUE -t HTTP --verifycatalog
#racadm update -f Catalog.xml -e 192.168.1.16/repo -a TRUE -t HTTP --verifycatalog
#racadm update viewreport
#racadm update -f Catalog.xml -l //192.168.1.14/share -u jj -p Pass12345 -a TRUE -t CIFS
#racadm update -f Catalog.xml -l //10.40.54.65/share -u jj -p Pass12345 -a TRUE -t CIFS
#racadm update -f Catalog.xml -e 192.168.1.16/repo -a TRUE -t HTTP 
#racadm update -f Power_Firmware_N7CW6_WN64_00.24.7D_Delta_750W.EXE -l //10.40.54.65/share -u Dell -p Pass1234
#racadm update -f Network_Firmware_539P6_WN64_18.0.17_A00.EXE -l //10.40.54.65/share/repo -u Dell -p Pass1234
#
#racadm hwinventory
#racadm swinventory
#racadm rollback iDRAC.Embedded.1-1
#racadm rollback BIOS.Setup.1-1 --reboot 
#
#
#racadm set idrac.Users.2.Password 'calvin'
#
#racadm systemconfig backup -f r420.img -l //192.168.1.14/share -u jj -p Pass12345
#NFS racadm systemconfig backup -f image.img –l 192.168.2.140:/share -u user -p pass
#CIFS racadm systemconfig backup -f image.img -l //192.168.2.140/share -u user -p pass
#CIFS racadm systemconfig backup -f image.img -l //10.40.54.65/share -u Dell -p Pass1234 
#vFlash racadm systemconfig backup -vFlash
#
#CIFS racadm systemconfig restore -f image.img -l //192.168.2.140/share -u user -p pass
#
#racadm config -g cfgServerInfo -o cfgServerBootOnce 1
#racadm config -g cfgServerInfo -o cfgServerFirstBootDevice FDD
#
#XML TEMPLATE
#racadm get -t xml -f ${d}.xml
#racadm get -t xml -f ${d}.xml -l //192.168.1.3/share -u jj -p Pass12345 --includeph
#racadm get -f <file name> -l <NFS / CIFS share> -u <username> -p <password>  -t <filetype> --includeph
#racadm get -t xml -f ${d}.xml -l 192.168.1.13:/share -u jj -p Pass12345 --includeph
#racadm -r 10.40.54.105 -u root -p Welcome1 get -t xml -f r63002.xml -l "//10.40.54.65/share" -u "Dell" -p "Pass1234"
#racadm set -t xml -f ${d}.xml
#racadm set -t xml -f jj.xml -l 192.168.1.13:/share -u jj -p Pass1234
#
#USERS
#racadm getconfig -g cfgUserAdmin -i 2
#racadm config -g cfgUserAdmin -o cfgUserAdminPassword -i 2 <newpassword>
#
#generate hashes
#SHA256 echo -n password | sha256sum | awk '{print $1}'
#SHA1 echo -n password | sha1sum | awk '{print $1}'
#MD5 echo -n password | md5sum | awk '{print $1}'
#
#idrac change
#racadm set iDRAC.IPv4.Address $newip
#racadm set iDRAC.IPv4.Netmask 255.255.255.128
#racadm set iDRAC.IPv4.Gateway 10.40.196.129



#----------------------------------------------------------------------------------------------------------------------------
#-----------------------------------------------------------
#RAC1118 : Update from repository operation has been initiated. Check the progress of the operation using "racadm jobqueue view -i JID_967692566322" command.
#------------
#autoconfig
#racadm get idrac.nic.autoconfig
#racadm set idrac.nic.autoconfig "enable once after reset"
#racadm racreset
#racadm set iDRAC.IPv4.DHCPEnable 1
#-----------------
#mountvirtualmedia
#1=enabled, 0=disabled
#racadm remoteimage -c -u Dell -p Pass1234 -l //10.40.54.189/iso/r805.iso
#racadm remoteimage -c -l 10.40.54.189:/export/nfs/13G_Apr2018_241.iso
#racadm remoteimage -s
#racadm set iDRAC.ServerBoot.FirstBootDevice VCD-DVD
#racadm set iDRAC.ServerBoot.BootOnce 1
#racadm serveraction powercycle
#----------------------------------------------------------

