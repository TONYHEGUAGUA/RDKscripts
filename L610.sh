KVERSION=`uname -r`
echo "############## insmod L610 drivers ################\r\n"
insmod /lib/modules/$KVERSION/kernel/drivers/usb/serial/usbserial.ko
insmod /lib/modules/$KVERSION/kernel/drivers/usb/serial/usb_wwan.ko
insmod /lib/modules/$KVERSION/kernel/drivers/usb/serial/option.ko
echo "############## load L610 drivers ################\r\n"
echo "1782 4d11 ff" > /sys/bus/usb-serial/drivers/option1/new_id
echo "############## List Serial Port And ECM Port ################\r\n"
ls -al /dev/ttyUSB*
ls /sys/class/net
echo "############## ifconfig ################\r\n"
ifconfig
