#
# USB gadget drivers
#

ccflags-y			:= -I$(srctree)/drivers/usb/gadget/
ccflags-y			+= -I$(srctree)/drivers/usb/gadget/udc/
ccflags-y			+= -I$(srctree)/drivers/usb/gadget/function/

g_hid-y				:= hid.o

obj-$(CONFIG_USB_G_HID)		+= g_hid.o

all:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) modules

clean:
	make -C /lib/modules/$(shell uname -r)/build M=$(PWD) clean
