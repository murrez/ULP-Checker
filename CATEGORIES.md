# ULP category reference

`main.py` and `ulp_classify.py` share the same rules. One line may be written to **multiple** output files.

## Groups (`--categories`)

| Group | Meaning |
|-------|---------|
| `panels` | Hosting / server panels (20) |
| `cms` | CMS and e-commerce (18) |
| `tools` | phpMyAdmin, Adminer |
| `all` | Everything (default) |

Examples: `--categories panels,cms` or `--categories cpanel,joomla,phpmyadmin`

List: `python main.py --list-categories`

---

## Hosting panels

| Category | Hints |
|----------|--------|
| **cpanel** | `:2082–2096`, `/cpanel/`, `whm.` |
| **plesk** | `:8443`, `:8880`, `login_up.php`, `/smb/` |
| **cyberpanel** | `cyberpanel`, `/data/login`, `:7080`, `:8090` + cyber/lscpd |
| **directadmin** | `:2222`, `directadmin`, `/CMD_LOGIN` |
| **webmin** | `:10000`, `webmin`, `session_login.cgi` |
| **virtualmin** | `virtualmin`, `:10000` + virtualmin hint |
| **ispconfig** | `ispconfig`, `:8080` + ispconfig |
| **hestiacp** | `hestiacp`, `:8083` + hestia |
| **vestacp** | `vestacp`, `:8083` + vesta |
| **aapanel** | `aapanel`, `bt.cn`, `:8888` / `:7800` + hint |
| **cloudpanel** | `cloudpanel`, `:8443` + cloudpanel (not Plesk alone) |
| **froxlor** | `froxlor` |
| **ajenti** | `ajenti`, `:8000` + ajenti |
| **interworx** | `:2080`, `nodeworx`, `interworx` |
| **solidcp** | `solidcp` |
| **cwp** | CentOS Web Panel `:2030`, `:2031` |
| **runcloud** | `runcloud` |
| **spinupwp** | `spinupwp` |
| **gridpane** | `gridpane` |
| **keyhelp** | `keyhelp` |

## CMS / site software

| Category | Hints |
|----------|--------|
| **wordpress** | `wp-login.php`, `/wp-admin`, `/wp-json/` |
| **joomla** | `/administrator/`, `option=com_` |
| **drupal** | `drupal.js`, `/core/modules/` |
| **magento** | `magento`, `mage/adminhtml` |
| **prestashop** | `prestashop`, `/admin-dev/` |
| **opencart** | `opencart`, `route=common/login` |
| **bitrix** | `bitrix`, `/bitrix/admin/` |
| **typo3** | `typo3`, `/typo3/` |
| **ghost** | `/ghost/#/signin` |
| **shopify** | `myshopify.com` |
| **mediawiki** | `mediawiki`, `Special:UserLogin` |
| **concrete5** | `concrete5`, `/ccm/system` |
| **moodle** | `moodle`, `moodledata` |
| **laravel** | `/nova/login`, `laravel_session` |
| **django** | `django`, `csrfmiddlewaretoken` (narrow) |
| **sharepoint** | `sharepoint`, `/_layouts/` |
| **wix** | `wix.com` |
| **squarespace** | `squarespace.com` |

## Tools

| **phpmyadmin** | `phpmyadmin`, `/phpmyadmin/` |
| **adminer** | `adminer.php` |

---

## False positive notes

- Ports like **8080 / 8443 / 8090** require **brand/path** hints when possible.
- Generic paths such as Magento `/admin/` are intentionally excluded.
- Add categories in `ulp_classify.py` → `CATEGORIES` dict.
