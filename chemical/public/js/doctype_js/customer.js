frappe.ui.form.on("Customer", {
	onload_post_render: function(frm){
		if(frm.doc.alias && !frm.doc.__islocal && frm.doc.name != frm.doc.alias){
			frappe.call({
				method: "frappe.client.rename_doc",
				args: {
					'doctype': frm.doc.doctype,
					'old_name': frm.doc.name,
					'new_name': frm.doc.alias
				},
				callback: function(r){
					if(r.message){
						frappe.set_route('Form', 'Customer', r.message)
					}
				}
			})
		}
	},

});
