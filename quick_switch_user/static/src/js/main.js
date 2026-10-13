/** @odoo-module */

import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";

function switchUserItem(env) {
    return {
        type: "item",
        id: "quick_switch_user",
        description: _t("Switch User"),
        callback: () => {
            env.services.action.doAction("quick_switch_user.action_open_switch_user_wizard");
        },
        sequence: 66,
    };
}

registry.category("user_menuitems").add("quick_switch_user", switchUserItem);
