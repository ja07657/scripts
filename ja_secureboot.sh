#!/bin/bash
#14G secureboot uefi Vmware autodeploy cert
exit
racadm set BIOS.SysSecurity.SecureBoot Enabled
racadm set BIOS.BiosBootSettings.BootMode UEFI
racadm set BIOS.SysSecurity.SecureBootPolicy Custom
racadm bioscert import -t 2 -k 1 -f 2148532_vmware_esx40.der -l 10.40.54.99:/export/nfs
racadm jobqueue create BIOS.Setup.1-1
racadm serveraction powercycle
