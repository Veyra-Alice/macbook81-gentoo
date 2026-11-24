// SPDX-License-Identifier: GPL-2.0-only
/*
 * Experimental MacBook8,1 s2idle EC-wake diagnostic workaround.
 *
 * Its EC runtime _GPE is not the GPE in its _PRW. The normal s2idle
 * wake-mask request consequently returned AE_TYPE on our test machine.
 * Mark the existing EC interrupt wake-capable, as the kernel does for
 * supported LPS0 systems. No EC registers or firmware tables are written.
 *
 * This runtime ACPICA flag persists after module removal. Reboot to undo.
 */
#include <linux/acpi.h>
#include <linux/dmi.h>
#include <linux/module.h>

static int __init macbook81_ec_wake_init(void)
{
	acpi_handle ec;
	unsigned long long gpe;
	acpi_status status;

	if (!dmi_match(DMI_PRODUCT_NAME, "MacBook8,1") ||
	    !dmi_match(DMI_SYS_VENDOR, "Apple Inc."))
		return -ENODEV;

	ec = ec_get_handle();
	if (!ec)
		return -ENODEV;
	status = acpi_evaluate_integer(ec, "_GPE", NULL, &gpe);
	if (ACPI_FAILURE(status) || gpe != 0x4e) {
		pr_err("macbook81_ec_wake: unexpected EC GPE; refusing workaround\n");
		return -ENODEV;
	}
	status = acpi_mark_gpe_for_wake(NULL, gpe);
	if (ACPI_FAILURE(status)) {
		pr_err("macbook81_ec_wake: mark failed: %s\n",
		       acpi_format_exception(status));
		return -EIO;
	}
	pr_info("macbook81_ec_wake: EC GPE 0x4e marked wake-capable; reboot to undo\n");
	return 0;
}

static void __exit macbook81_ec_wake_exit(void)
{
	pr_info("macbook81_ec_wake: removed; wake capability remains until reboot\n");
}

module_init(macbook81_ec_wake_init);
module_exit(macbook81_ec_wake_exit);
MODULE_LICENSE("GPL");
MODULE_DESCRIPTION("Experimental MacBook8,1 s2idle EC wake capability quirk");
