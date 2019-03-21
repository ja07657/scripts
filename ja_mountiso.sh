#1=enabled, 0=disabled
racadm jobqueue delete -i ALL
racadm jobqueue delete -i JID_CLEARALL
racadm vmdisconnect
racadm closessn -a
racadm remoteimage -d

racadm remoteimage -c -u Dell -p Pass1234 -l //10.40.54.65/share/iso/Dell_13G_Oct2018_firmware.iso
racadm remoteimage -s
racadm set iDRAC.ServerBoot.FirstBootDevice VCD-DVD
racadm set iDRAC.ServerBoot.BootOnce 1
racadm serveraction powercycle


#cifs# racadm remoteimage -c -u root -p Welcome1 -l '//10.40.54.99/iso/Dell_13G_June2018_firmware.iso'
#nfs# racadm remoteimage -c -l 10.40.54.199:/export/nfs/iso/10.40.54.199/iso/Dell_13G_Feb2019b_firmware.iso
#http# racadm remoteimage -c -l http://10.40.196.209/iso/Dell_13G_June2018_firmware.iso
#http# racadm remoteimage -c -l http://10.40.54.199/iso/Dell_13G_Feb2019b_firmware.iso
#10.40.196.209 10.40.54.199
