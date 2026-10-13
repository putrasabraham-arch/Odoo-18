/** @odoo-module **/

import { Dialog } from "@web/core/dialog/dialog";
import { _t } from "@web/core/l10n/translation";
import { registry } from "@web/core/registry";
import { formatFloat } from "@web/views/fields/formatters";

import { Component } from "@odoo/owl";


export class ReorderingNotificationDialog extends Component {
    static template =
        "stock_reordering_popup_notification.ReorderingNotificationDialog";
    static components = { Dialog };
    static props = {
        close: Function,
        data: Object,
        openReplenishment: { type: Function, optional: true },
        openPurchaseOrder: { type: Function, optional: true },
        openPurchaseRequest: { type: Function, optional: true },
    };

    get title() {
        return _t("Peringatan Reordering Rules");
    }

    formatQuantity(value) {
        return formatFloat(value, {
            digits: [16, this.props.data.quantity_precision],
        });
    }

    async onOpenReplenishment() {
        await this.openAction(this.props.openReplenishment);
    }

    async onOpenPurchaseOrder() {
        await this.openAction(this.props.openPurchaseOrder);
    }

    async onOpenPurchaseRequest() {
        await this.openAction(this.props.openPurchaseRequest);
    }

    async openAction(callback) {
        if (callback) {
            const shouldClose = await callback();
            if (shouldClose === false) {
                return;
            }
        }
        this.props.close();
    }
}

export const reorderingNotificationService = {
    dependencies: ["action", "dialog", "notification", "orm"],

    start(env, { action, dialog, notification, orm }) {
        function makeOpenAction(actionXmlId, errorMessage) {
            return async () => {
                try {
                    await action.doAction(actionXmlId);
                    return true;
                } catch (error) {
                    console.warn(`Unable to open ${actionXmlId}.`, error);
                    notification.add(errorMessage, { type: "warning" });
                    return false;
                }
            };
        }

        async function checkReorderingRules() {
            try {
                const data = await orm.call(
                    "stock.warehouse.orderpoint",
                    "get_reordering_notification_data",
                    []
                );
                if (!data.show || !data.items.length) {
                    return;
                }
                dialog.add(ReorderingNotificationDialog, {
                    data,
                    openReplenishment: data.can_open_replenishment
                        ? makeOpenAction(
                              data.replenishment_action,
                              _t("Replenishment tidak dapat dibuka.")
                          )
                        : undefined,
                    openPurchaseOrder: data.can_open_purchase_order
                        ? makeOpenAction(
                              data.purchase_order_action,
                              _t("Purchase Order tidak dapat dibuka.")
                          )
                        : undefined,
                    openPurchaseRequest: data.can_open_purchase_request
                        ? makeOpenAction(
                              data.purchase_request_action,
                              _t("Purchase Request tidak dapat dibuka.")
                          )
                        : undefined,
                });
            } catch (error) {
                console.warn("Unable to load reordering rule notifications.", error);
            }
        }

        void checkReorderingRules();
    },
};

registry
    .category("services")
    .add("stock_reordering_popup_notification", reorderingNotificationService);
