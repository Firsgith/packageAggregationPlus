# SPDX-License-Identifier: GPL-3.0-only
#
# Copyright (C) 2024 asvow

include $(TOPDIR)/rules.mk

LUCI_TITLE:=LuCI for Tailscale
LUCI_DEPENDS:=+tailscale
LUCI_PKGARCH:=all

PKG_VERSION:=1.2.6

# 定义编译前的预处理钩子，执行sed修改tailscale的Makefile
PKG_PREPARE_FUNC += tailscale_makefile_patch

define tailscale_makefile_patch
	# 检查tailscale的Makefile是否存在，避免报错
	if [ -f $(TOPDIR)/feeds/packages/net/tailscale/Makefile ]; then \
		sed -i '/\/etc\/init\.d\/tailscale/d;/\/etc\/config\/tailscale/d;' $(TOPDIR)/feeds/packages/net/tailscale/Makefile; \
		echo "Patched tailscale Makefile successfully"; \
	else \
		echo "Warning: tailscale Makefile not found at $(TOPDIR)/feeds/packages/net/tailscale/Makefile"; \
	fi
endef

include $(TOPDIR)/feeds/luci/luci.mk

# call BuildPackage - OpenWrt buildroot signature
