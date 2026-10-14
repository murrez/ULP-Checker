#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
ULP line classification — hosting panels + CMS (+ DB admin tools).

Used by main.py in a single pass. Add categories via the CATEGORIES dict.
"""
from __future__ import annotations

import re
from typing import Callable

# After port: / ? # : | (ULP pipe), whitespace, or EOL
_PORT_TAIL = r"(?=[/?#:|\s]|$)"


def _port_re(*ports: str) -> re.Pattern[str]:
    body = "|".join(re.escape(p) for p in ports)
    return re.compile(r":(?:" + body + ")" + _PORT_TAIL, re.IGNORECASE)


def _classifier(
    *,
    markers: tuple[str, ...] = (),
    port: re.Pattern[str] | None = None,
    port_hints: tuple[str, ...] = (),
    port_alone_ok: bool = True,
) -> Callable[[str], bool]:
    """
    markers: any marker substring in line matches.
    port: port regex match; if port_alone_ok is False, port_hints are required too.
    """

    def _fn(line: str) -> bool:
        low = line.lower()
        if markers and any(m in low for m in markers):
            return True
        if port is not None and port.search(line):
            if port_alone_ok and not port_hints:
                return True
            if port_hints and any(h in low for h in port_hints):
                return True
        return False

    return _fn


# ---------------------------------------------------------------------------
# Hosting / server panels
# ---------------------------------------------------------------------------

line_is_cpanel = _classifier(
    port=_port_re("2082", "2083", "2086", "2087", "2095", "2096"),
    markers=(
        "://cpanel.",
        "://www.cpanel.",
        "://whm.",
        "://www.whm.",
        "/cpanel/",
        "/cpanel?",
        "/cpanel#",
        "/cpanel:",
        "/cpanel/login",
        "/login/?goto_cpanel",
        ":2083/",
        ":2087/",
    ),
)

line_is_plesk = _classifier(
    port=_port_re("8443", "8880"),
    markers=(
        "login_up.php",
        "/smb/",
        "/smb?",
        "/smb#",
        "/smb:",
        "://plesk.",
        "://www.plesk.",
        "/enterprise/control/",
        "/modules/wp-toolkit/",
        "plesk-siteinstaller",
    ),
)

line_is_cyberpanel = _classifier(
    markers=(
        "cyberpanel",
        "/data/login",
        "/data/logout",
        "lscpd",
        "/base/login",
        "8090/data/login",
        "cyber panel",
    ),
    port=_port_re("7080", "8090"),
    port_hints=("cyber", "lscpd", "/data/", "openlitespeed", "ols/", "cyberpanel"),
    port_alone_ok=False,
)

line_is_directadmin = _classifier(
    port=_port_re("2222"),
    markers=(
        "directadmin",
        "/cmd_login",
        "://www.directadmin.",
        ":2222/user/",
        ":2222/cmd",
    ),
)

line_is_webmin = _classifier(
    port=_port_re("10000"),
    markers=(
        "webmin",
        "/session_login.cgi",
        "/password_change.cgi",
        "webmin/webmin",
    ),
)

line_is_virtualmin = _classifier(
    markers=(
        "virtualmin",
        ":10000/virtualmin",
        "/virtualmin/",
        "virtual-server",
    ),
    port=_port_re("10000"),
    port_hints=("virtualmin", "virtual-server", "webmin"),
    port_alone_ok=False,
)

line_is_ispconfig = _classifier(
    markers=(
        "ispconfig",
        "isp config",
        "/login/index.php",
        ":8080/login",
    ),
    port=_port_re("8080"),
    port_hints=("ispconfig", "isp config"),
    port_alone_ok=False,
)

line_is_hestiacp = _classifier(
    markers=(
        "hestiacp",
        "hestia cp",
        ":8083/login",
        "hestia.",
    ),
    port=_port_re("8083"),
    port_hints=("hestia", "hestiacp"),
    port_alone_ok=False,
)

line_is_vestacp = _classifier(
    markers=(
        "vestacp",
        "vesta cp",
        ":8083/",
        "/vst-login",
        "vestacp.",
    ),
    port=_port_re("8083"),
    port_hints=("vesta", "vestacp", "vst-"),
    port_alone_ok=False,
)

line_is_aapanel = _classifier(
    markers=(
        "aapanel",
        "aa panel",
        "bt.cn",
        "/login?d=aapanel",
        "宝塔",
    ),
    port=_port_re("8888", "7800", "888"),
    port_hints=("aapanel", "bt.cn", "宝塔", "/login"),
    port_alone_ok=False,
)

line_is_cloudpanel = _classifier(
    markers=(
        "cloudpanel",
        "mgtcp.cloudpanel",
        "/login/cloudpanel",
        "clp-login",
    ),
    port=_port_re("8443"),
    port_hints=("cloudpanel", "clp-"),
    port_alone_ok=False,
)

line_is_froxlor = _classifier(
    markers=(
        "froxlor",
        "froxlor/login",
        "/froxlor/",
    ),
    port=_port_re("443", "80"),
    port_hints=("froxlor",),
    port_alone_ok=False,
)

line_is_ajenti = _classifier(
    markers=(
        "ajenti",
        "/view/login/normal",
        "ajenti:server",
    ),
    port=_port_re("8000", "8001"),
    port_hints=("ajenti",),
    port_alone_ok=False,
)

line_is_interworx = _classifier(
    port=_port_re("2080"),
    markers=(
        "interworx",
        "nodeworx",
        ":2080/nodeworx",
        ":2080/iworx",
    ),
)

line_is_solidcp = _classifier(
    markers=(
        "solidcp",
        "enterprise server",
        "/solidcp/",
        "solidcp/login",
    ),
)

line_is_cwp = _classifier(
    markers=(
        "centos web panel",
        "control-webpanel",
        ":2030/",
        ":2031/",
        "cwp.login",
    ),
    port=_port_re("2030", "2031"),
)

line_is_runcloud = _classifier(
    markers=(
        "runcloud",
        "manage.runcloud.io",
        "app.runcloud.io",
    ),
)

line_is_spinupwp = _classifier(
    markers=(
        "spinupwp",
        "spinupwp.com",
    ),
)

line_is_gridpane = _classifier(
    markers=(
        "gridpane",
        "gridpane.com",
    ),
)

line_is_keyhelp = _classifier(
    markers=(
        "keyhelp",
        "key-web.de",
        ":8443/keyhelp",
    ),
)

line_is_phpmyadmin = _classifier(
    markers=(
        "phpmyadmin",
        "pma_",
        "/phpmyadmin/",
        "/phpmyadmin2/",
        "/dbadmin/",
        "setup/index.php",
    ),
)

line_is_adminer = _classifier(
    markers=(
        "adminer.php",
        "adminer-",
        "/adminer/",
    ),
)

# ---------------------------------------------------------------------------
# CMS / e-commerce / site software
# ---------------------------------------------------------------------------

line_is_wordpress = _classifier(
    markers=(
        "wp-login.php",
        "/wp-admin",
        "wp-admin.php",
        "xmlrpc.php",
        "/wp-json/",
        "wp-signup.php",
        "wp-register.php",
        "/wp-includes/",
        "/wp-content/plugins/",
        "/wp-content/themes/",
        "wordpress.com",
    ),
)

line_is_joomla = _classifier(
    markers=(
        "/administrator/",
        "option=com_",
        "index.php?option=com_users",
        "joomla!",
        "/components/com_",
    ),
)

line_is_drupal = _classifier(
    markers=(
        "drupal.js",
        "/core/modules/",
        "/sites/default/",
        "drupal/settings",
        "/user/login?destination=",
        "drupal.org",
    ),
)

line_is_magento = _classifier(
    markers=(
        "magento",
        "mage/adminhtml",
        "downloader/index.php",
        "/static/version",
        "magento_backend",
        "/admin/catalog/",
    ),
)

line_is_prestashop = _classifier(
    markers=(
        "prestashop",
        "/admin-dev/",
        "/my-admin/",
        "prestashop.com",
    ),
)

line_is_opencart = _classifier(
    markers=(
        "opencart",
        "route=common/login",
        "route=account/login",
        "/catalog/",
        "index.php?route=",
    ),
)

line_is_bitrix = _classifier(
    markers=(
        "bitrix",
        "/bitrix/admin/",
        "bitrix24",
        "1c-bitrix",
    ),
)

line_is_typo3 = _classifier(
    markers=(
        "typo3",
        "/typo3/",
        "typo3conf",
        "typo3temp",
    ),
)

line_is_ghost = _classifier(
    markers=(
        "/ghost/#/signin",
        "ghost.org",
        "/ghost/api/",
    ),
)

line_is_shopify = _classifier(
    markers=(
        "myshopify.com",
        "shopify.com/admin",
        "/admin/auth/login",
    ),
)

line_is_mediawiki = _classifier(
    markers=(
        "mediawiki",
        "special:userlogin",
        "title=special:userlogin",
        "/wiki/index.php",
    ),
)

line_is_concrete5 = _classifier(
    markers=(
        "concrete5",
        "concrete cms",
        "/index.php/login",
        "/ccm/system",
    ),
)

line_is_moodle = _classifier(
    markers=(
        "moodle",
        "moodledata",
        "/login/index.php?auth",
        "moodlecourse",
    ),
)

line_is_laravel = _classifier(
    markers=(
        "/nova/login",
        "laravel_session",
        "/horizon/login",
        "/telescope/login",
    ),
)

line_is_django = _classifier(
    markers=(
        "/admin/login/",
        "csrfmiddlewaretoken",
        "django admin",
    ),
)

# django /admin/login too broad alone - require django hint
_old_django = line_is_django


def line_is_django(line: str) -> bool:
    low = line.lower()
    if not _old_django(line):
        return False
    if "django" in low or "csrfmiddlewaretoken" in low:
        return True
    return "/admin/login" in low and ("8000" in low or "python" in low)


line_is_sharepoint = _classifier(
    markers=(
        "sharepoint",
        "/_layouts/15/authenticate.aspx",
        "/_layouts/login",
    ),
)

line_is_wix = _classifier(
    markers=(
        "wix.com",
        "editor.wix",
        "manage.wix",
    ),
)

line_is_squarespace = _classifier(
    markers=(
        "squarespace.com",
        "squarespace.com/config",
    ),
)


CategoryFn = Callable[[str], bool]

# Order: panels, then CMS, then tools (output filenames)
PANEL_CATEGORIES: tuple[str, ...] = (
    "cpanel",
    "plesk",
    "cyberpanel",
    "directadmin",
    "webmin",
    "virtualmin",
    "ispconfig",
    "hestiacp",
    "vestacp",
    "aapanel",
    "cloudpanel",
    "froxlor",
    "ajenti",
    "interworx",
    "solidcp",
    "cwp",
    "runcloud",
    "spinupwp",
    "gridpane",
    "keyhelp",
)

CMS_CATEGORIES: tuple[str, ...] = (
    "wordpress",
    "joomla",
    "drupal",
    "magento",
    "prestashop",
    "opencart",
    "bitrix",
    "typo3",
    "ghost",
    "shopify",
    "mediawiki",
    "concrete5",
    "moodle",
    "laravel",
    "django",
    "sharepoint",
    "wix",
    "squarespace",
)

TOOL_CATEGORIES: tuple[str, ...] = (
    "phpmyadmin",
    "adminer",
)

CATEGORIES: dict[str, CategoryFn] = {
    "cpanel": line_is_cpanel,
    "plesk": line_is_plesk,
    "cyberpanel": line_is_cyberpanel,
    "directadmin": line_is_directadmin,
    "webmin": line_is_webmin,
    "virtualmin": line_is_virtualmin,
    "ispconfig": line_is_ispconfig,
    "hestiacp": line_is_hestiacp,
    "vestacp": line_is_vestacp,
    "aapanel": line_is_aapanel,
    "cloudpanel": line_is_cloudpanel,
    "froxlor": line_is_froxlor,
    "ajenti": line_is_ajenti,
    "interworx": line_is_interworx,
    "solidcp": line_is_solidcp,
    "cwp": line_is_cwp,
    "runcloud": line_is_runcloud,
    "spinupwp": line_is_spinupwp,
    "gridpane": line_is_gridpane,
    "keyhelp": line_is_keyhelp,
    "wordpress": line_is_wordpress,
    "joomla": line_is_joomla,
    "drupal": line_is_drupal,
    "magento": line_is_magento,
    "prestashop": line_is_prestashop,
    "opencart": line_is_opencart,
    "bitrix": line_is_bitrix,
    "typo3": line_is_typo3,
    "ghost": line_is_ghost,
    "shopify": line_is_shopify,
    "mediawiki": line_is_mediawiki,
    "concrete5": line_is_concrete5,
    "moodle": line_is_moodle,
    "laravel": line_is_laravel,
    "django": line_is_django,
    "sharepoint": line_is_sharepoint,
    "wix": line_is_wix,
    "squarespace": line_is_squarespace,
    "phpmyadmin": line_is_phpmyadmin,
    "adminer": line_is_adminer,
}

DEFAULT_CATEGORY_ORDER: tuple[str, ...] = PANEL_CATEGORIES + CMS_CATEGORIES + TOOL_CATEGORIES

CATEGORY_GROUPS: dict[str, tuple[str, ...]] = {
    "panels": PANEL_CATEGORIES,
    "cms": CMS_CATEGORIES,
    "tools": TOOL_CATEGORIES,
    "all": DEFAULT_CATEGORY_ORDER,
}


def classify_line(line: str, active: tuple[str, ...] | None = None) -> tuple[str, ...]:
    """Return all categories matching a line (may be multiple)."""
    keys = active or DEFAULT_CATEGORY_ORDER
    return tuple(k for k in keys if k in CATEGORIES and CATEGORIES[k](line))


def expand_category_selection(spec: str) -> tuple[str, ...]:
    """
    Comma-separated category names or group aliases:
    panels, cms, tools, all
    """
    raw = [x.strip().lower() for x in spec.split(",") if x.strip()]
    if not raw:
        return DEFAULT_CATEGORY_ORDER
    out: list[str] = []
    for item in raw:
        if item in CATEGORY_GROUPS:
            for k in CATEGORY_GROUPS[item]:
                if k not in out:
                    out.append(k)
        elif item in CATEGORIES:
            if item not in out:
                out.append(item)
        else:
            raise ValueError(f"unknown category or group: {item}")
    return tuple(out)
