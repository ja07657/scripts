#!/bin/bash
user=root
pass=….
oldip=10.40.85.
newip=10.40.195.
for ip in `cat /home/ipfile`
do
	racadm –r $ip –u $user –p $pass set iDRAC.IPv4.Address $newip 
	racadm –r $ip –u $user –p $pass set iDRAC.IPv4.Netmask 255.255.255.128
	racadm –r $ip –u $user –p $pass set iDRAC.IPv4.Gateway 10.40.196.129
	racadm –r $ip –u $user –p $pass racreset
done

