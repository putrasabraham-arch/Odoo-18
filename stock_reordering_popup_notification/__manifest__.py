{
    "name": "Stock Reordering Popup Notification",
    "version": "18.0.1.0.0",
    "category": "Inventory/Inventory",
    "summary": "Show replenishment alerts when the backend starts",
    "depends": [
        "stock",
        "web",
    ],
    "data": [
        "security/reordering_notification_security.xml",
    ],
    "assets": {
        "web.assets_backend": [
            "stock_reordering_popup_notification/static/src/js/reordering_notification_service.js",
            "stock_reordering_popup_notification/static/src/xml/reordering_notification_dialog.xml",
            "stock_reordering_popup_notification/static/src/scss/reordering_notification.scss",
        ],
    },
    "installable": True,
    "application": False,
    "license": "LGPL-3",
}
