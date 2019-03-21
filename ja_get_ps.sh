#!/bin/bash
#[InstanceID: PSU.Slot.1]
#Device Type = PowerSupply
#LastUpdateTime = 2017-09-13T19:32:18
#LastSystemInventoryTime = 2017-09-11T18:46:55
#PMBusMonitoring = 1
#Range1MaxInputPower = 2400
#RedMinNumberNeeded = 1
#RedundancyStatus = Redundancy Lost
#Type = AC
#PrimaryStatus = Error
#TotalOutputPower = 2000 Watts
#InputVoltage = 0 Volts
#DetailedState = Failed to read
#Manufacturer = Dell
#PartNumber = 039K3HA00
#SerialNumber = PH162985AT001A
#Model = PWR SPLY,2000W,RDNT,ARTESYN
#DeviceDescription = Power Supply 1
#FQDD = PSU.Slot.1
#InstanceID = PSU.Slot.1
#
#00000000000000000
##################################################################
o=ps.out; cp /dev/null $o
ip=10.40.54.192
#
racadm -r $ip -u root -p Welcome1 hwinventory > $$.tmp
echo $ip >> $o; awk -v RS= '/PSU.Slot/' $$.tmp >> $o
