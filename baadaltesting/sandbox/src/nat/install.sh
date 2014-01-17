function run
{
  check_root
  #package_update_db
  package_install qemu-kvm
  package_install virtinst
  package_install virt-manager
  disk_create $NAT_DISK ${NAT_SPACE}G
  remaster_ubuntu $NAT_KICKSTART $NAT_TRANSFER $NAT_ISO

  $ECHO_PROGRESS Installing OS
  virt-install \
    --connect qemu:///system \
    --accelerate \
    --arch=$NAT_ARCH \
    --name $NAT_NAME \
    --ram=$NAT_RAM \
    --vcpus=$NAT_VCPUS \
    --os-type=Linux \
    --disk path=$NAT_DISK,format=qcow2,size=$NAT_SPACE \
    --cdrom $NAT_ISO \
    --network network=$OVS_NET_EXTERNAL \
    --network network=$OVS_NET_INTERNAL \
    --noautoconsole \
    1>$LOGS/log.out 2>/$LOGS/log.err
  status=$?

  if [[ $status -ne 0 ]]; then
    $ECHO_ER NAT vm creation error. Check logs.
  else
    $ECHO_OK NAT vm created
  fi
}
