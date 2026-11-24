/* SPDX-License-Identifier: MIT */
/* Fit the fixed MacBook8,1 panel before initramfs asks for a keyboard layout.
 * No disk access or font changes. Nonmatching machines/drivers are skipped.
 */
#define _XOPEN_SOURCE 700
#include <errno.h>
#include <fcntl.h>
#include <glob.h>
#include <linux/kd.h>
#include <linux/vt.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/ioctl.h>
#include <unistd.h>

static int line(const char *path, char *buf, size_t len)
{
    FILE *f = fopen(path, "r");
    if (!f) return -1;
    int ok = fgets(buf, len, f) != NULL;
    fclose(f);
    if (!ok) return -1;
    buf[strcspn(buf, "\r\n")] = 0;
    return 0;
}

int main(int argc, char **argv)
{
    char buf[4096], path[4096], driver[4096];
    glob_t panels = {0};
    unsigned connected = 0;
    if (argc == 2 && strcmp(argv[1], "--help") == 0) {
        puts("Fit MacBook8,1 Intel text consoles to the native 2304x1440 panel.");
        return 0;
    }
    if (argc != 1) return 2;
    if (line("/sys/class/dmi/id/product_name", buf, sizeof(buf)) ||
        strcmp(buf, "MacBook8,1")) return 0;
    if (!realpath("/sys/bus/pci/devices/0000:00:02.0/driver", driver) ||
        strcmp(strrchr(driver, '/') + 1, "i915")) return 0;
    if (glob("/sys/class/drm/card*-eDP-1/status", 0, NULL, &panels)) {
        globfree(&panels);
        return 0;
    }
    for (size_t i = 0; i < panels.gl_pathc; i++) {
        if (line(panels.gl_pathv[i], buf, sizeof(buf)) || strcmp(buf, "connected"))
            continue;
        if (++connected != 1) break;
        size_t prefix = strlen(panels.gl_pathv[i]) - strlen("status");
        if (prefix + strlen("modes") + 1 > sizeof(path)) {
            globfree(&panels);
            return 1;
        }
        memcpy(path, panels.gl_pathv[i], prefix);
        strcpy(path + prefix, "modes");
    }
    globfree(&panels);
    if (connected != 1 || line(path, buf, sizeof(buf)) || strcmp(buf, "2304x1440"))
        return 0;

    int fd = open("/dev/tty1", O_RDWR | O_NOCTTY);
    if (fd < 0) { perror("console open"); return 1; }
    struct console_font_op font = {
        .op = KD_FONT_OP_GET, .width = 64, .height = 128, .data = NULL
    };
    if (ioctl(fd, KDFONTOP, &font) < 0) {
        perror("console font query"); close(fd); return 1;
    }
    if (!font.width || font.width > 64 || !font.height || font.height > 128) {
        fputs("Unexpected console font dimensions.\n", stderr);
        close(fd); return 1;
    }
    struct vt_sizes size = {
        .v_rows = 1440 / font.height, .v_cols = 2304 / font.width, .v_scrollsize = 0
    };
    if (ioctl(fd, VT_RESIZE, &size) < 0) {
        perror("console resize"); close(fd); return 1;
    }
    close(fd);
    printf("Console fitted: %u columns x %u rows; %ux%u font.\n",
           size.v_cols, size.v_rows, font.width, font.height);
    return 0;
}
