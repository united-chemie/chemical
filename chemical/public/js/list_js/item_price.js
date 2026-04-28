frappe.provide("frappe.ui");

frappe.ui.Page = frappe.ui.Page.extend({
    add_new_button: function(label, click, opts) {
		if (!opts) opts = {};
		let button = $(`<button
			class="btn ${opts.btn_class || 'btn-default'} ${opts.btn_size || 'btn-sm'} ellipsis">
				${opts.icon ? frappe.utils.icon(opts.icon): ''}
				${label}
		</button>`);
		// Add actions as menu item in Mobile View (similar to "add_custom_button" in forms.js)
		let menu_item = this.add_menu_item(label, click, false);
		menu_item.parent().addClass("hidden-xl");

		button.prependTo(this.custom_actions);
		button.on('click', click);
		this.custom_actions.removeClass('hide');

		return button;
	},
})


frappe.listview_settings['Item Price'] = {
    onload: function() {
        let me = cur_list;

        me.page.add_new_button("Update latest price in all BOMs", function() {
            frappe.call({
                method: "erpnext.manufacturing.doctype.bom_update_tool.bom_update_tool.enqueue_update_cost",
                freeze: true,
                callback: result => {
                    // if (result && result.message && !result.exc) {
                    //     frm.events.confirm_job_start(frm, result.message);
                    // }
                }
            });
        }, {btn_class: "btn-primary"});
    }
}